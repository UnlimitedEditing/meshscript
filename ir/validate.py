"""
ir.validate — semantic validation of an IR document, beyond what the JSON
Schema already guarantees.

Checks performed:
  - every step references a known op
  - every required arg is present
  - every `{"$ref": "<var>"}` argument points to a `var` defined by a
    strictly earlier step, and that step's `returns` type matches the
    expected parameter type (e.g. catches passing a Layer where a Document
    is expected)
  - literal arguments have plausible shapes (enum membership, color length, ...)
    — defense in depth for hand-written/non-constrained IR
  - at least one terminal `show` step (an op with `returns is None`) exists

Returns a list of human-readable error strings (empty list = valid). Each
error names the step index, op, and arg so it can be dropped directly into a
retry prompt.
"""

from __future__ import annotations

from .types import IRType, is_ref_type, LIST_ELEM_TYPES


def _check_literal(op_name, i, p, val):
    t = p.type
    if t == IRType.INT:
        if not isinstance(val, int) or isinstance(val, bool):
            return f"step {i} ('{op_name}'): arg '{p.name}' must be an integer, got {val!r}"
    elif t == IRType.FLOAT:
        if not isinstance(val, (int, float)) or isinstance(val, bool):
            return f"step {i} ('{op_name}'): arg '{p.name}' must be a number, got {val!r}"
    elif t == IRType.STRING:
        if not isinstance(val, str):
            return f"step {i} ('{op_name}'): arg '{p.name}' must be a string, got {val!r}"
    elif t == IRType.BOOL:
        if not isinstance(val, bool):
            return f"step {i} ('{op_name}'): arg '{p.name}' must be a boolean, got {val!r}"
    elif t == IRType.ENUM:
        if val not in (p.choices or []):
            return (f"step {i} ('{op_name}'): arg '{p.name}' = {val!r} is not one of "
                    f"{p.choices!r}")
    elif t == IRType.COLOR:
        if not (isinstance(val, list) and len(val) == 4
                and all(isinstance(c, int) and 0 <= c <= 255 for c in val)):
            return (f"step {i} ('{op_name}'): arg '{p.name}' must be a [r,g,b,a] array "
                    f"of four ints 0-255, got {val!r}")
    elif t == IRType.POINT:
        if not (isinstance(val, list) and len(val) == 2
                and all(isinstance(c, (int, float)) and not isinstance(c, bool) for c in val)):
            return f"step {i} ('{op_name}'): arg '{p.name}' must be a [x,y] pair, got {val!r}"
    elif t == IRType.POINT_LIST:
        if not (isinstance(val, list) and len(val) >= 1
                and all(isinstance(pt, list) and len(pt) == 2 for pt in val)):
            return (f"step {i} ('{op_name}'): arg '{p.name}' must be a non-empty list of "
                    f"[x,y] pairs, got {val!r}")
    elif t == IRType.STOPS:
        if not (isinstance(val, list) and len(val) >= 1
                and all(isinstance(s, dict) and "pos" in s and "color" in s for s in val)):
            return (f"step {i} ('{op_name}'): arg '{p.name}' must be a non-empty list of "
                    f"{{\"pos\": <0..1>, \"color\": [r,g,b,a]}} stops, got {val!r}")
    return None


def validate(ir: dict, specs_by_name: dict) -> list:
    errors = []

    if not isinstance(ir, dict) or "steps" not in ir:
        return ["IR must be a JSON object with a top-level 'steps' array."]

    steps = ir["steps"]
    if not isinstance(steps, list) or not steps:
        return ["'steps' must be a non-empty array."]

    var_types = {}   # var name -> IRType | None, from the most recent step that set it
    has_terminal = False

    for i, step in enumerate(steps):
        if not isinstance(step, dict):
            errors.append(f"step {i}: must be an object")
            continue

        op_name = step.get("op")
        var = step.get("var")
        args = step.get("args")

        spec = specs_by_name.get(op_name)
        if spec is None:
            errors.append(f"step {i}: unknown op '{op_name}'")
            continue

        if not isinstance(var, str) or not var:
            errors.append(f"step {i} ('{op_name}'): 'var' must be a non-empty string")
        elif not var.isidentifier():
            errors.append(f"step {i} ('{op_name}'): 'var' = {var!r} is not a valid Python identifier")

        if not isinstance(args, dict):
            errors.append(f"step {i} ('{op_name}'): 'args' must be an object")
            args = {}

        if spec.returns is None:
            has_terminal = True

        for p in spec.params:
            if p.name not in args:
                if p.required:
                    errors.append(f"step {i} ('{op_name}'): missing required arg '{p.name}'")
                continue

            val = args[p.name]

            if p.type == IRType.FLOAT and isinstance(val, dict) and "$ref" in val:
                if not isinstance(val.get("$ref"), str):
                    errors.append(
                        f"step {i} ('{op_name}'): arg '{p.name}' has a malformed "
                        f"$ref object, got {val!r}"
                    )
                    continue
                ref_name = val["$ref"]
                if ref_name not in var_types:
                    errors.append(
                        f"step {i} ('{op_name}'): arg '{p.name}' references '{ref_name}', "
                        f"which is not defined by any earlier step"
                    )
                    continue
                ref_type = var_types[ref_name]
                if ref_type != IRType.FLOAT:
                    got = ref_type.value if ref_type is not None else "no return value"
                    errors.append(
                        f"step {i} ('{op_name}'): arg '{p.name}' expects a number or a "
                        f"$ref to a float-returning step, but '{ref_name}' is a {got}"
                    )
            elif p.type in LIST_ELEM_TYPES:
                elem_type = LIST_ELEM_TYPES[p.type]
                if not (isinstance(val, list) and len(val) >= 1
                        and all(isinstance(x, dict) and isinstance(x.get("$ref"), str) for x in val)):
                    errors.append(
                        f"step {i} ('{op_name}'): arg '{p.name}' must be a non-empty list of "
                        f"{{\"$ref\": \"<var>\"}} objects each referencing a {elem_type.value}, "
                        f"got {val!r}"
                    )
                else:
                    for x in val:
                        ref_name = x["$ref"]
                        if ref_name not in var_types:
                            errors.append(
                                f"step {i} ('{op_name}'): arg '{p.name}' references '{ref_name}', "
                                f"which is not defined by any earlier step"
                            )
                            continue
                        ref_type = var_types[ref_name]
                        if ref_type != elem_type:
                            got = ref_type.value if ref_type is not None else "no return value"
                            errors.append(
                                f"step {i} ('{op_name}'): arg '{p.name}' expects "
                                f"{elem_type.value} refs, but '{ref_name}' is a {got}"
                            )
            elif p.type == IRType.FLOAT_LIST:
                if not (isinstance(val, list) and len(val) >= 1
                        and all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in val)):
                    errors.append(
                        f"step {i} ('{op_name}'): arg '{p.name}' must be a non-empty list of "
                        f"numbers, got {val!r}"
                    )
            elif is_ref_type(p.type):
                if not (isinstance(val, dict) and isinstance(val.get("$ref"), str)):
                    errors.append(
                        f"step {i} ('{op_name}'): arg '{p.name}' must be "
                        f"{{\"$ref\": \"<var>\"}} referencing a {p.type.value}, got {val!r}"
                    )
                    continue
                ref_name = val["$ref"]
                if ref_name not in var_types:
                    errors.append(
                        f"step {i} ('{op_name}'): arg '{p.name}' references '{ref_name}', "
                        f"which is not defined by any earlier step"
                    )
                    continue
                ref_type = var_types[ref_name]
                if ref_type != p.type:
                    got = ref_type.value if ref_type is not None else "no return value"
                    errors.append(
                        f"step {i} ('{op_name}'): arg '{p.name}' expects a {p.type.value}, "
                        f"but '{ref_name}' is a {got}"
                    )
            else:
                err = _check_literal(op_name, i, p, val)
                if err:
                    errors.append(err)

        for extra in args:
            if spec.param(extra) is None:
                errors.append(f"step {i} ('{op_name}'): unknown arg '{extra}' for op '{op_name}'")

        if isinstance(var, str) and var:
            var_types[var] = spec.returns

    if not has_terminal:
        errors.append("IR must include at least one terminal 'show' step.")

    return errors
