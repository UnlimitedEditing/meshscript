"""
ir.compile — translate a validated IR document into .cnv / .ms source text.

The output is plain script source using the same op names as canvas_ops/ops,
fed unchanged into canvas_sandbox.executor.run / sandbox.executor.run.
Each step becomes one line: `{var} = {op}({args...})`. Terminal ops
(`returns is None`, e.g. `show`) are emitted as bare calls with no assignment.

Call `validate()` first — this module assumes the IR is well-formed (every
`$ref` resolves, every required arg is present) and does not re-check it.
"""

from __future__ import annotations

from .types import IRType, is_ref_type, LIST_ELEM_TYPES


def _format_literal(t: IRType, val):
    if t == IRType.COLOR:
        return repr(tuple(val))
    if t == IRType.POINT:
        return repr(tuple(val))
    if t == IRType.POINT_LIST:
        return repr([tuple(p) for p in val])
    if t == IRType.STOPS:
        return repr([(stop["pos"], tuple(stop["color"])) for stop in val])
    if t == IRType.FLOAT_LIST:
        return repr(list(val))
    return repr(val)


def _format_arg(p, val):
    if p.type == IRType.FLOAT and isinstance(val, dict) and "$ref" in val:
        return val["$ref"]
    if p.type in LIST_ELEM_TYPES:
        return f"[{', '.join(x['$ref'] for x in val)}]"
    if is_ref_type(p.type):
        return val["$ref"]
    return _format_literal(p.type, val)


def compile_ir(ir: dict, specs_by_name: dict) -> str:
    """Compile a validated IR document into .cnv / .ms source text."""
    lines = []

    for step in ir["steps"]:
        op_name = step["op"]
        var = step["var"]
        args = step.get("args", {})
        spec = specs_by_name[op_name]

        parts = []
        for p in spec.params:
            if p.name not in args:
                continue
            if p.type == IRType.MESH_LIST:
                # variadic params (e.g. convex_hull(*meshes)) — unpack the list
                parts.append(f"*{_format_arg(p, args[p.name])}")
            else:
                parts.append(f"{p.name}={_format_arg(p, args[p.name])}")

        call = f"{op_name}({', '.join(parts)})"

        if spec.returns is None:
            lines.append(call)
        else:
            lines.append(f"{var} = {call}")

    return "\n".join(lines) + "\n"
