"""
Critique loop entry point — Phase 3.

    from critique.loop import critique, CritiqueResult

    result = critique(renders, spec="a coffee mug", script=src)
    if result.passed:
        ...
    else:
        for issue in result.issues:
            print(issue)

renders: list of {"azimuth": float, "image": np.ndarray} dicts
         (the .renders field on any checkpoint from sandbox.executor.run())
"""

import json
import re
from dataclasses import dataclass, field


@dataclass
class CritiqueResult:
    passed:       bool
    issues:       list = field(default_factory=list)
    suggestions:  list = field(default_factory=list)
    pattern_gaps: list = field(default_factory=list)
    raw:          str  = ""


def critique(
    renders:    list,
    spec:       str,
    script:     str  = None,
    client      = None,
    grid_cols:  int  = 4,
) -> CritiqueResult:
    """
    renders:   list of render dicts from executor.run() checkpoints
    spec:      natural-language description of the intended object
    script:    optional MeshScript source (improves op-level feedback)
    client:    VLMClient; created from OPENROUTER_API_KEY env var if None
    grid_cols: columns in the assembled image grid
    """
    from .grid   import make_grid
    from .prompt import build_messages
    from .client import VLMClient, DEFAULT_VLM_MODEL

    if not renders:
        return CritiqueResult(
            passed=False,
            issues=["No renders available — run with --views to enable critique"],
        )

    if client is None:
        client = VLMClient(model=DEFAULT_VLM_MODEL)

    grid_bytes = make_grid(renders, cols=grid_cols)
    messages   = build_messages(grid_bytes, spec=spec, script=script)
    raw        = client.chat(messages, temperature=0.1)

    return _parse(raw)


def _parse(raw: str) -> CritiqueResult:
    text = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("`").strip()
    try:
        data = json.loads(text)
        return CritiqueResult(
            passed       = bool(data.get("passed", False)),
            issues       = data.get("issues",       []),
            suggestions  = data.get("suggestions",  []),
            pattern_gaps = data.get("pattern_gaps", []),
            raw          = raw,
        )
    except json.JSONDecodeError:
        # Model didn't respect the JSON schema — treat as failed, preserve full text
        return CritiqueResult(
            passed  = False,
            issues  = ["VLM response was not valid JSON — see .raw for full text"],
            raw     = raw,
        )
