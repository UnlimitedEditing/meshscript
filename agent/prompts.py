"""
Prompt templates for the designer agent.

Loads prompt/system-prompt.md lazily so this module imports without touching disk.
"""

import os
import re

_SYSTEM_CACHE: str = None


def _system() -> str:
    global _SYSTEM_CACHE
    if _SYSTEM_CACHE is None:
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        path = os.path.join(root, "prompt", "system-prompt.md")
        with open(path, encoding="utf-8") as f:
            _SYSTEM_CACHE = f.read()
    return _SYSTEM_CACHE


def initial_messages(spec: str) -> list:
    return [
        {"role": "system", "content": _system()},
        {
            "role": "user",
            "content": (
                f"Design spec: {spec}\n\n"
                "Write a complete MeshScript program that constructs this object.\n"
                "- Wrap the code in ```python fences.\n"
                "- Use show(mesh, name) after each major component.\n"
                "- Call ground(mesh) on the final result before the last show()."
            ),
        },
    ]


def revision_message(critique_result) -> str:
    lines = ["The VLM critique reviewed the renders and found problems:\n"]
    for issue in critique_result.issues:
        lines.append(f"- {issue}")
    if critique_result.suggestions:
        lines.append("\nSuggested fixes:")
        for s in critique_result.suggestions:
            lines.append(f"- {s}")
    if critique_result.pattern_gaps:
        lines.append("\nPattern gaps (no named pattern covers these — worth noting):")
        for g in critique_result.pattern_gaps:
            lines.append(f"- {g}")
    lines.append(
        "\nRevise the full MeshScript to address these issues. "
        "Wrap the revised script in ```python fences."
    )
    return "\n".join(lines)


def extract_script(text: str) -> str:
    """
    Pull code from the first ```python/meshscript block.
    Strips <think>...</think> sections emitted by reasoning models (Qwen3-Coder etc.)
    before searching.
    """
    # Remove reasoning traces
    text = re.sub(r"<think>[\s\S]*?</think>", "", text, flags=re.IGNORECASE).strip()
    m = re.search(r"```(?:python|meshscript)\s*\n([\s\S]+?)```", text)
    return m.group(1).strip() if m else ""
