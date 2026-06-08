"""
LLM designer agent — Phase 4.

    from agent.designer import design, DesignResult

    result = design(
        spec          = "a flanged pipe fitting",
        max_revisions = 3,
        render_config = {"views": 4},
        export_dir    = "output/flanged_pipe",
    )

    if result.converged:
        print("converged after", len(result.critique_history), "critique(s)")
    else:
        print("did not converge — last critique:")
        for issue in result.critique_history[-1].issues:
            print(" ", issue)

Environment:
    OPENROUTER_API_KEY  — required for both designer and VLM critique
    OPENROUTER_DESIGNER_MODEL — override text model  (default: deepseek/deepseek-chat:free)
    OPENROUTER_VLM_MODEL      — override vision model (default: google/gemini-2.0-flash-exp:free)
"""

import os
import sys
from dataclasses import dataclass, field

# Ensure repo root is on the path regardless of where this file is imported from.
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)


@dataclass
class DesignResult:
    script:          str
    mesh:            object       # trimesh.Trimesh | None
    checkpoints:     list         = field(default_factory=list)
    critique_history: list        = field(default_factory=list)
    converged:       bool         = False
    error:           str          = None


def design(
    spec:          str,
    max_revisions: int  = 3,
    render_config: dict = None,
    export_dir:    str  = None,
    designer_client      = None,
    vlm_client           = None,
) -> DesignResult:
    """
    Generates MeshScript for *spec*, iterating with VLM critique up to
    *max_revisions* times.

    render_config:
        Pass {} for default render settings (8 views, 512px).
        Pass {"views": 4} for a faster 4-view critique.
        Pass None to skip rendering and critique (executor-only mode).

    designer_client / vlm_client:
        VLMClient instances.  If None, created from env vars.
        They can be the same object if the model handles both text and vision
        (e.g. google/gemini-2.0-flash-exp:free does both).
    """
    from critique.client import VLMClient, DEFAULT_DESIGNER_MODEL, DEFAULT_VLM_MODEL
    from critique.loop   import critique as run_critique
    from sandbox.executor import run as execute
    from agent.prompts   import initial_messages, revision_message, extract_script

    designer_model = os.environ.get("OPENROUTER_DESIGNER_MODEL", DEFAULT_DESIGNER_MODEL)
    vlm_model      = os.environ.get("OPENROUTER_VLM_MODEL",      DEFAULT_VLM_MODEL)

    if designer_client is None:
        designer_client = VLMClient(model=designer_model)
    if vlm_client is None:
        vlm_client = VLMClient(model=vlm_model)

    messages = initial_messages(spec)
    script   = ""
    critique_history = []
    exec_result = None

    for attempt in range(max_revisions + 1):
        temperature = 0.7 if attempt == 0 else 0.5
        raw    = designer_client.chat(messages, temperature=temperature)
        script = extract_script(raw)

        if not script:
            return DesignResult(
                script = raw,
                mesh   = None,
                error  = "LLM did not produce a fenced code block.",
            )

        print(f"\n[design] attempt {attempt + 1}/{max_revisions + 1} — executing …")
        exec_result = execute(
            script,
            reference     = spec,
            render_config = render_config,
            export_dir    = export_dir,
        )

        if not exec_result["success"]:
            print(f"[design] execution error — feeding back to LLM")
            messages.append({"role": "assistant", "content": raw})
            messages.append({
                "role":    "user",
                "content": (
                    f"Execution failed with this error:\n```\n{exec_result['error']}\n```\n\n"
                    "Fix the script. Wrap the corrected version in ```python fences."
                ),
            })
            continue

        renders = (
            exec_result["checkpoints"][-1].get("renders", [])
            if exec_result["checkpoints"] else []
        )

        if render_config is None or not renders:
            # No renders — accept without critique
            return DesignResult(
                script      = script,
                mesh        = exec_result["final"],
                checkpoints = exec_result["checkpoints"],
                converged   = True,
            )

        print(f"[design] critiquing {len(renders)} render(s) …")
        crit = run_critique(renders, spec=spec, script=script, client=vlm_client)
        critique_history.append(crit)

        verdict = "PASS" if crit.passed else "FAIL"
        print(f"[design] critique: {verdict}")
        for issue in crit.issues:
            print(f"         issue: {issue}")

        if crit.passed:
            return DesignResult(
                script           = script,
                mesh             = exec_result["final"],
                checkpoints      = exec_result["checkpoints"],
                critique_history = critique_history,
                converged        = True,
            )

        if attempt < max_revisions:
            messages.append({"role": "assistant", "content": raw})
            messages.append({"role": "user",      "content": revision_message(crit)})

    return DesignResult(
        script           = script,
        mesh             = exec_result["final"] if exec_result else None,
        checkpoints      = exec_result["checkpoints"] if exec_result else [],
        critique_history = critique_history,
        converged        = False,
    )
