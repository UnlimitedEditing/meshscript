"""
MeshScript designer agent — CLI entry point.

Usage:
    python design.py "a flanged pipe fitting"
    python design.py "a coffee mug" --views 4 --revisions 3 --out mug_out
    python design.py "a doric column" --views 4 --designer deepseek/deepseek-chat:free
    python design.py "a hex bolt" --no-critique --out bolt_out

Environment:
    OPENROUTER_API_KEY          required
    OPENROUTER_DESIGNER_MODEL   override designer LLM   (default: deepseek/deepseek-chat:free)
    OPENROUTER_VLM_MODEL        override vision critic  (default: google/gemini-2.0-flash-exp:free)
"""

import argparse
import json
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)


def _load_dotenv():
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


def main():
    _load_dotenv()
    parser = argparse.ArgumentParser(description="LLM designer agent for MeshScript")
    parser.add_argument("spec",             help="Natural-language object description")
    parser.add_argument("--out",            default=None,  help="Output directory (default: <slug>_out)")
    parser.add_argument("--revisions", "-r", type=int, default=3,  help="Max VLM critique revisions (default 3)")
    parser.add_argument("--views",          type=int, default=4,   help="Render views per checkpoint (default 4, 0=skip critique)")
    parser.add_argument("--render-size",    type=int, default=384, help="Render width=height in px (default 384)")
    parser.add_argument("--elevation",      type=float, default=20.0)
    parser.add_argument("--no-critique",    action="store_true",   help="Skip rendering and critique loop")
    parser.add_argument("--designer",       default=None,  help="Override designer LLM model")
    parser.add_argument("--vlm",            default=None,  help="Override VLM critique model")
    parser.add_argument("--save-script",    default=None,  help="Write final script to this .ms file")
    args = parser.parse_args()

    render_config = None
    if not args.no_critique and args.views > 0:
        render_config = {
            "views":         args.views,
            "elevation_deg": args.elevation,
            "width":         args.render_size,
            "height":        args.render_size,
        }

    slug = args.spec[:40].lower().replace(" ", "_").replace("/", "_")
    export_dir = args.out or f"{slug}_out"
    export_dir = os.path.abspath(export_dir)

    from critique.client import VLMClient, DEFAULT_DESIGNER_MODEL, DEFAULT_VLM_MODEL
    from agent.designer  import design

    designer_model = args.designer or os.environ.get("OPENROUTER_DESIGNER_MODEL", DEFAULT_DESIGNER_MODEL)
    vlm_model      = args.vlm      or os.environ.get("OPENROUTER_VLM_MODEL",      DEFAULT_VLM_MODEL)

    print(f"Spec:      {args.spec}")
    print(f"Designer:  {designer_model}")
    print(f"VLM:       {vlm_model if render_config else '(skipped)'}")
    print(f"Output:    {export_dir}\n")

    designer_client = VLMClient(model=designer_model)
    vlm_client      = VLMClient(model=vlm_model)

    result = design(
        spec             = args.spec,
        max_revisions    = args.revisions,
        render_config    = render_config,
        export_dir       = export_dir,
        designer_client  = designer_client,
        vlm_client       = vlm_client,
    )

    print(f"\n{'Converged' if result.converged else 'Did not converge'} "
          f"({len(result.critique_history)} critique round(s))")

    if result.error:
        print(f"Error: {result.error}")
        sys.exit(1)

    if result.critique_history and not result.converged:
        last = result.critique_history[-1]
        print("\nFinal critique issues:")
        for issue in last.issues:
            print(f"  - {issue}")

    if args.save_script and result.script:
        with open(args.save_script, "w", encoding="utf-8") as f:
            f.write(result.script)
        print(f"\nScript saved to {args.save_script}")

    if result.script:
        script_path = os.path.join(export_dir, "result.ms")
        os.makedirs(export_dir, exist_ok=True)
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(result.script)
        print(f"Script:    {script_path}")

    viewer = os.path.join(export_dir, "viewer.html")
    if os.path.exists(viewer):
        print(f"Viewer:    {viewer}")


if __name__ == "__main__":
    main()
