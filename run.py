import sys
import os
import json
import shutil
import argparse

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def main():
    parser = argparse.ArgumentParser(description="Run a MeshScript program")
    parser.add_argument("script", help="Path to .ms script")
    parser.add_argument("output_dir", nargs="?", help="Output directory (default: <script>_out)")
    parser.add_argument("--serve", action="store_true", help="Serve the output dir and open browser")
    parser.add_argument("--port", type=int, default=8765, help="Port for --serve (default 8765)")
    # Multi-view render options (all off by default — omit --views to skip rendering)
    parser.add_argument("--reference", default=None,
                        help="Reference for this design: URL, text description, or local image path")
    parser.add_argument("--views", type=int, default=None,
                        help="Render N evenly-spaced views per checkpoint (requires pyrender)")
    parser.add_argument("--elevation", type=float, default=20.0,
                        help="Camera elevation in degrees for --views (default 20)")
    parser.add_argument("--cam-dist", type=float, default=2.5,
                        help="Camera distance for --views (default 2.5)")
    parser.add_argument("--render-size", type=int, default=512,
                        help="Render width=height in pixels for --views (default 512)")
    # VLM critique (requires --views and OPENROUTER_API_KEY)
    parser.add_argument("--critique", default=None, metavar="SPEC",
                        help="Run VLM critique on the final checkpoint renders. "
                             "SPEC is the natural-language goal (e.g. 'a coffee mug'). "
                             "Requires --views and OPENROUTER_API_KEY env var.")
    parser.add_argument("--vlm-model", default=None,
                        help="OpenRouter model for VLM critique "
                             "(default: google/gemini-2.0-flash-exp:free)")
    args = parser.parse_args()

    script_path = os.path.abspath(args.script)
    export_dir = args.output_dir or os.path.splitext(script_path)[0] + "_out"
    export_dir = os.path.abspath(export_dir)

    with open(script_path, encoding="utf-8") as f:
        script = f.read()

    render_config = None
    if args.views is not None:
        render_config = {
            "views":         args.views,
            "elevation_deg": args.elevation,
            "cam_dist":      args.cam_dist,
            "width":         args.render_size,
            "height":        args.render_size,
        }

    sys.path.insert(0, SCRIPT_DIR)
    from sandbox.executor import run

    result = run(script, reference=args.reference, render_config=render_config, export_dir=export_dir)

    if not result["success"]:
        print(f"\nFailed:\n{result['error']}")
        if result["checkpoints"]:
            print(f"({len(result['checkpoints'])} checkpoint(s) captured before failure)")

    # ── VLM critique ──
    critique_result = None
    if args.critique and result["checkpoints"]:
        renders = result["checkpoints"][-1].get("renders", [])
        if not renders:
            print("\nCritique skipped — no renders (add --views N to enable)")
        else:
            print(f"\nCritiquing with spec: {args.critique!r} …")
            sys.path.insert(0, SCRIPT_DIR)
            from critique.loop   import critique as run_critique
            from critique.client import VLMClient, DEFAULT_VLM_MODEL
            vlm_model = args.vlm_model or DEFAULT_VLM_MODEL
            client = VLMClient(model=vlm_model)
            critique_result = run_critique(renders, spec=args.critique, script=script, client=client)
            verdict = "PASS" if critique_result.passed else "FAIL"
            print(f"Critique: {verdict}")
            for issue in critique_result.issues:
                print(f"  issue:      {issue}")
            for sug in critique_result.suggestions:
                print(f"  suggestion: {sug}")
            for gap in critique_result.pattern_gaps:
                print(f"  gap:        {gap}")

    _write_manifest(result, script, script_path, export_dir, critique_result)

    checkpoint_count = len(result["checkpoints"])
    print(f"\n{'Done' if result['success'] else 'Partial'} - {checkpoint_count} checkpoint(s) in {export_dir}/")
    print(f"  Viewer: {os.path.join(export_dir, 'viewer.html')}")

    if args.serve:
        _serve(export_dir, args.port)
    elif not result["success"]:
        sys.exit(1)


def _write_manifest(result, script, script_path, export_dir, critique_result=None):
    import base64
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
        # Embed GLB as data URL so model-viewer loads on file:// without a server.
        glb_path = os.path.join(export_dir, fname)
        if os.path.exists(glb_path):
            with open(glb_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            entry["data_url"] = "data:model/gltf-binary;base64," + b64
        # Render view file list (paths relative to export_dir for portability).
        if cp.get("renders"):
            entry["renders"] = [
                {
                    "azimuth": rv["azimuth"],
                    "file":    os.path.relpath(rv["image_path"], export_dir).replace("\\", "/")
                               if rv.get("image_path") else None,
                }
                for rv in cp["renders"]
            ]
        checkpoints_data.append(entry)

    critique_data = None
    if critique_result is not None:
        from dataclasses import asdict
        critique_data = asdict(critique_result)
        del critique_data["raw"]  # raw text is noisy in the manifest

    manifest = {
        "name":          os.path.basename(script_path),
        "script":        script,
        "reference":     result.get("reference"),
        "render_config": result.get("render_config"),
        "checkpoints":   checkpoints_data,
        "critique":      critique_data,
    }

    manifest_path = os.path.join(export_dir, "checkpoints.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    # Write viewer with checkpoints JSON inlined so it works on file:// without a server.
    template = os.path.join(SCRIPT_DIR, "viewer.html")
    if os.path.exists(template):
        with open(template, encoding="utf-8") as f:
            html = f.read()
        inject = f"<script>window.__CHECKPOINTS__ = {json.dumps(manifest)};</script>\n"
        html = html.replace("</head>", inject + "</head>", 1)
        with open(os.path.join(export_dir, "viewer.html"), "w", encoding="utf-8") as f:
            f.write(html)


def _serve(directory, port):
    import http.server
    import socketserver
    import threading
    import webbrowser
    import socket

    # Find a free port if the requested one is busy
    def try_port(p):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("", p))
                return True
            except OSError:
                return False

    while not try_port(port):
        port += 1

    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=directory, **kwargs)
        def log_message(self, fmt, *args):
            pass  # suppress access log

    url = f"http://localhost:{port}/viewer.html"
    print(f"\nServing at {url}")
    print("Press Ctrl+C to stop.\n")

    with socketserver.TCPServer(("", port), Handler) as httpd:
        threading.Thread(target=lambda: webbrowser.open(url), daemon=True).start()
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")


if __name__ == "__main__":
    main()
