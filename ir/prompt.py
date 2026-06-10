"""
ir.prompt — render an OpSpec registry as a markdown "dictionary" for the
LLM-facing system prompt. This is the single source of truth shared with
ir.schema (the constrained-decoding schema) and ir.compile (the source
emitter), so the documented op set can never drift from what's enforced.
"""

from __future__ import annotations

from .types import IRType, is_ref_type

_REF_NAMES = {
    IRType.DOCUMENT: "Document",
    IRType.LAYER:    "Layer",
    IRType.MESH:     "Mesh",
    IRType.PROFILE:  "Profile",
    IRType.PATH:     "Path",
}


def _type_str(p) -> str:
    t = p.type
    if is_ref_type(t):
        return _REF_NAMES[t]
    if t == IRType.INT:
        return "int"
    if t == IRType.FLOAT:
        return 'float, or {"$ref": "<step that returns float>"}'
    if t == IRType.MESH_LIST:
        return '[{"$ref": "<Mesh var>"}, ...]'
    if t == IRType.PROFILE_LIST:
        return '[{"$ref": "<Profile var>"}, ...]'
    if t == IRType.FLOAT_LIST:
        return "[float, ...]"
    if t == IRType.STRING:
        return "string"
    if t == IRType.BOOL:
        return "bool"
    if t == IRType.COLOR:
        return "[r,g,b,a] ints 0-255"
    if t == IRType.POINT:
        return "[x,y]"
    if t == IRType.POINT_LIST:
        return "[[x,y], ...]"
    if t == IRType.STOPS:
        return '[{"pos": 0..1, "color": [r,g,b,a]}, ...]'
    if t == IRType.ENUM:
        return "one of " + ", ".join(repr(c) for c in (p.choices or []))
    return t.value


def _param_str(p) -> str:
    s = f"{p.name}: {_type_str(p)}"
    if not p.required:
        if p.default is not None:
            s += f" = {p.default!r}"
        else:
            s += " (optional)"
    return s


def dictionary_section(specs: list) -> str:
    """Render an OpSpec list as a markdown reference, one entry per op."""
    lines = []
    for spec in specs:
        sig = ", ".join(_param_str(p) for p in spec.params)
        ret = _REF_NAMES.get(spec.returns, spec.returns.value if spec.returns else "(none)")
        lines.append(f"- `{spec.name}({sig})` -> {ret}")
        if spec.doc:
            lines.append(f"  {spec.doc}")
    return "\n".join(lines)
