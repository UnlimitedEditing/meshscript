"""
MeshScript interactive chat — conversational 3D modelling session.

Usage:
    python chat.py
    python chat.py --views 4 --render-size 384

In-session commands:
    /save [file.ms]   write current script to disk
    /view             open viewer.html in browser
    /reset            start a new object from scratch
    /script           print current script
    /quit  (or /exit) end session

Environment:
    OPENROUTER_API_KEY          required (or set in .env at project root)
    OPENROUTER_DESIGNER_MODEL   override designer LLM  (default: deepseek/deepseek-chat:free)
    OPENROUTER_VLM_MODEL        override vision critic (default: google/gemini-2.0-flash-exp:free)
"""

import argparse
import os
import sys
import webbrowser
import textwrap

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

_DIVIDER = "─" * 60


def main():
    parser = argparse.ArgumentParser(description="MeshScript conversational session")
    parser.add_argument("--views",       type=int,   default=4,   help="Render views per checkpoint (0 = skip critique)")
    parser.add_argument("--render-size", type=int,   default=384, help="Render width=height px (default 384)")
    parser.add_argument("--elevation",   type=float, default=20.0)
    parser.add_argument("--revisions",   type=int,   default=2,   help="Max auto-revision rounds per prompt (default 2)")
    parser.add_argument("--out",         default=None,            help="Output directory (default: session_out/)")
    parser.add_argument("--designer",    default=None)
    parser.add_argument("--vlm",         default=None)
    args = parser.parse_args()

    _load_dotenv()

    render_config = None
    if args.views > 0:
        render_config = {
            "views":         args.views,
            "elevation_deg": args.elevation,
            "width":         args.render_size,
            "height":        args.render_size,
        }

    export_dir = os.path.abspath(args.out or "session_out")

    from critique.client import VLMClient, DEFAULT_DESIGNER_MODEL, DEFAULT_VLM_MODEL
    from agent.prompts   import extract_script, revision_message
    from critique.loop   import critique as run_critique
    from sandbox.executor import run as execute

    designer_model = args.designer or os.environ.get("OPENROUTER_DESIGNER_MODEL", DEFAULT_DESIGNER_MODEL)
    vlm_model      = args.vlm      or os.environ.get("OPENROUTER_VLM_MODEL",      DEFAULT_VLM_MODEL)

    designer = VLMClient(model=designer_model)
    vlm      = VLMClient(model=vlm_model)

    print(f"\n{'MeshScript':^60}")
    print(_DIVIDER)
    print(f"  Designer: {designer_model}")
    print(f"  Critic:   {vlm_model if render_config else '(off — run with --views N to enable)'}")
    print(f"  Output:   {export_dir}")
    print(_DIVIDER)
    print("  Describe an object to build it.  Type /help for commands.")
    print(_DIVIDER + "\n")

    session = _Session(
        designer      = designer,
        vlm           = vlm,
        render_config = render_config,
        export_dir    = export_dir,
        max_revisions = args.revisions,
        execute_fn    = execute,
        critique_fn   = run_critique,
        extract_fn    = extract_script,
        revision_fn   = revision_message,
    )

    while True:
        try:
            user_input = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            break

        if not user_input:
            continue

        if user_input.startswith("/"):
            if _handle_command(user_input, session, export_dir):
                break
            continue

        session.turn(user_input)


# ── Session state ────────────────────────────────────────────────────────────

class _Session:
    def __init__(self, designer, vlm, render_config, export_dir,
                 max_revisions, execute_fn, critique_fn, extract_fn, revision_fn):
        self.designer      = designer
        self.vlm           = vlm
        self.render_config = render_config
        self.export_dir    = export_dir
        self.max_revisions = max_revisions
        self._execute      = execute_fn
        self._critique     = critique_fn
        self._extract      = extract_fn
        self._revision_msg = revision_fn

        self.messages      = []   # full LLM conversation history
        self.script        = ""   # last executed script
        self.spec          = ""   # description of current object
        self.viewer_path   = None

    def reset(self):
        self.messages    = []
        self.script      = ""
        self.spec        = ""
        self.viewer_path = None
        print("Session reset.\n")

    def turn(self, user_input: str):
        from agent.prompts import initial_messages

        if not self.messages:
            # First turn — start a fresh conversation
            self.spec     = user_input
            self.messages = initial_messages(user_input)
        else:
            # Follow-up — append as a revision request
            self.messages.append({
                "role":    "user",
                "content": user_input,
            })

        self._run_design_loop()

    def _run_design_loop(self):
        """Run LLM → execute → critique up to max_revisions times, updating self.messages."""
        import time

        for attempt in range(self.max_revisions + 1):
            temp = 0.7 if attempt == 0 else 0.5
            print(f"\n{'generating' if attempt == 0 else 'revising'} …", flush=True)
            t0  = time.time()
            raw = self.designer.chat(self.messages, temperature=temp)
            elapsed = time.time() - t0

            script = self._extract(raw)
            if not script:
                print(f"[!] No code block in response. Raw:\n{raw[:400]}")
                return

            print(f"executing  … ({elapsed:.1f}s to generate)", flush=True)
            result = self._execute(
                script,
                reference     = self.spec,
                render_config = self.render_config,
                export_dir    = self.export_dir,
            )

            if not result["success"]:
                _print_error(result["error"])
                self.messages.append({"role": "assistant", "content": raw})
                self.messages.append({
                    "role":    "user",
                    "content": f"Execution failed:\n```\n{result['error']}\n```\nFix the script.",
                })
                continue

            self.script = script
            cps = result["checkpoints"]
            _print_checkpoints(cps)

            # Write viewer
            _write_output(result, script, self.spec, self.export_dir)
            self.viewer_path = os.path.join(self.export_dir, "viewer.html")

            renders = cps[-1].get("renders", []) if cps else []
            if not renders or self.render_config is None:
                print(f"\nDone. {self.viewer_path}")
                self.messages.append({"role": "assistant", "content": raw})
                return

            print("critiquing …", flush=True)
            crit = self._critique(renders, spec=self.spec, script=script, client=self.vlm)
            verdict = "PASS" if crit.passed else "FAIL"
            _print_critique(crit, verdict)

            self.messages.append({"role": "assistant", "content": raw})

            if crit.passed:
                print(f"\nDone. {self.viewer_path}")
                return

            if attempt < self.max_revisions:
                self.messages.append({
                    "role":    "user",
                    "content": self._revision_msg(crit),
                })
            else:
                print(f"\nMax revisions reached. Last result: {self.viewer_path}")


# ── Commands ─────────────────────────────────────────────────────────────────

def _handle_command(cmd: str, session: _Session, export_dir: str) -> bool:
    """Returns True if the session should exit."""
    parts = cmd.split(None, 1)
    verb  = parts[0].lower()
    arg   = parts[1] if len(parts) > 1 else ""

    if verb in ("/quit", "/exit", "/q"):
        print("Bye.")
        return True

    elif verb == "/help":
        print(textwrap.dedent("""
          /save [file.ms]  — write current script to disk
          /view            — open viewer.html in browser
          /script          — print current script
          /reset           — clear session, start a new object
          /quit            — exit
        """))

    elif verb == "/save":
        if not session.script:
            print("Nothing to save yet.")
        else:
            path = arg or os.path.join(export_dir, "result.ms")
            with open(path, "w", encoding="utf-8") as f:
                f.write(session.script)
            print(f"Saved: {path}")

    elif verb == "/view":
        if session.viewer_path and os.path.exists(session.viewer_path):
            webbrowser.open(f"file://{session.viewer_path}")
            print(f"Opening {session.viewer_path}")
        else:
            print("No viewer yet — build something first.")

    elif verb == "/script":
        if session.script:
            print("\n" + session.script + "\n")
        else:
            print("No script yet.")

    elif verb == "/reset":
        session.reset()

    else:
        print(f"Unknown command: {verb}  (type /help)")

    return False


# ── Output helpers ────────────────────────────────────────────────────────────

def _print_checkpoints(cps):
    for cp in cps:
        wt  = "watertight" if cp["watertight"] else "open"
        vol = f"  vol={cp['volume']:.4f}" if cp.get("volume") else ""
        print(f"  [{cp['label']}]  {cp['vertices']}v  {cp['faces']}f  {wt}{vol}")


def _print_critique(crit, verdict):
    print(f"  critique: {verdict}")
    for issue in crit.issues:
        print(f"    issue:      {issue}")
    for sug in crit.suggestions:
        print(f"    suggestion: {sug}")


def _print_error(error: str):
    lines = error.strip().split("\n")
    print(f"\n[error] {lines[-1]}")
    if len(lines) > 1:
        print("        (run /script then check the traceback above)")


def _write_output(result, script, spec, export_dir):
    """Minimal manifest + viewer write — reuses run.py logic."""
    import json, base64
    os.makedirs(export_dir, exist_ok=True)

    checkpoints_data = []
    for cp in result["checkpoints"]:
        fname = cp["label"] + ".glb"
        entry = {
            "label":     cp["label"],
            "file":      fname,
            "vertices":  cp["vertices"],
            "faces":     cp["faces"],
            "watertight": cp["watertight"],
            "volume":    cp["volume"],
            "bounds":    cp["bounds"],
            "line":      cp.get("line"),
        }
        glb_path = os.path.join(export_dir, fname)
        if os.path.exists(glb_path):
            with open(glb_path, "rb") as f:
                entry["data_url"] = "data:model/gltf-binary;base64," + base64.b64encode(f.read()).decode()
        if cp.get("renders"):
            entry["renders"] = [
                {"azimuth": rv["azimuth"],
                 "file": os.path.relpath(rv["image_path"], export_dir).replace("\\", "/")
                         if rv.get("image_path") else None}
                for rv in cp["renders"]
            ]
        checkpoints_data.append(entry)

    manifest = {
        "name":        "session",
        "script":      script,
        "reference":   spec,
        "checkpoints": checkpoints_data,
        "critique":    None,
    }
    with open(os.path.join(export_dir, "checkpoints.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    template = os.path.join(SCRIPT_DIR, "viewer.html")
    if os.path.exists(template):
        with open(template, encoding="utf-8") as f:
            html = f.read()
        inject = f"<script>window.__CHECKPOINTS__ = {json.dumps(manifest)};</script>\n"
        html = html.replace("</head>", inject + "</head>", 1)
        with open(os.path.join(export_dir, "viewer.html"), "w", encoding="utf-8") as f:
            f.write(html)


# ── .env loader ──────────────────────────────────────────────────────────────

def _load_dotenv():
    """Read .env from the project root into os.environ, skipping already-set vars."""
    env_path = os.path.join(SCRIPT_DIR, ".env")
    if not os.path.exists(env_path):
        return
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = val


if __name__ == "__main__":
    main()
