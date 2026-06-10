"""
ir.schema — generates a JSON Schema for the IR from an OpSpec registry.

The schema is generic across domains (CanvasScript, MeshScript): given a list
of OpSpec, it produces:

    { "type": "object",
      "properties": { "steps": { "type": "array",
                                  "items": { "oneOf": [ <one schema per op> ] } } },
      "required": ["steps"] }

Each op's item schema uses `"op": {"const": "<name>"}` as a discriminator and
constrains `args` to exactly that op's parameters. Object-reference params
(Document/Layer/Mesh/...) must be `{"$ref": "<var>"}`; everything else is a
JSON literal.

This schema is compiled by `xgrammar.GrammarCompiler.compile_json_schema` to
constrain `transformers.generate` token-by-token.
"""

from __future__ import annotations

from .types import IRType, OpSpec, ParamSpec, is_ref_type

_REF_SCHEMA = {
    "type": "object",
    "properties": {"$ref": {"type": "string"}},
    "required": ["$ref"],
    "additionalProperties": False,
}

_COLOR_SCHEMA = {
    "type": "array",
    "items": {"type": "integer", "minimum": 0, "maximum": 255},
    "minItems": 4,
    "maxItems": 4,
}

_POINT_SCHEMA = {
    "type": "array",
    "items": {"type": "number"},
    "minItems": 2,
    "maxItems": 2,
}

_POINT_LIST_SCHEMA = {
    "type": "array",
    "items": _POINT_SCHEMA,
    "minItems": 1,
}

_STOP_SCHEMA = {
    "type": "object",
    "properties": {
        "pos":   {"type": "number"},
        "color": _COLOR_SCHEMA,
    },
    "required": ["pos", "color"],
    "additionalProperties": False,
}

_STOPS_SCHEMA = {
    "type": "array",
    "items": _STOP_SCHEMA,
    "minItems": 1,
}

# A FLOAT param may be a literal number, or a reference to an earlier step
# that returns a float (e.g. `top(mesh)`, `xy_radius(mesh)`) — lets spatial
# queries feed back into later args without hardcoded coordinates.
_FLOAT_SCHEMA = {
    "oneOf": [
        {"type": "number"},
        _REF_SCHEMA,
    ],
}

_REF_LIST_SCHEMA = {
    "type": "array",
    "items": _REF_SCHEMA,
    "minItems": 1,
}

_FLOAT_LIST_SCHEMA = {
    "type": "array",
    "items": {"type": "number"},
    "minItems": 1,
}


def _param_schema(p: ParamSpec, has_float_refs: bool) -> dict:
    if p.type == IRType.FLOAT:
        return _FLOAT_SCHEMA if has_float_refs else {"type": "number"}
    if p.type in (IRType.MESH_LIST, IRType.PROFILE_LIST):
        return _REF_LIST_SCHEMA
    if p.type == IRType.FLOAT_LIST:
        return _FLOAT_LIST_SCHEMA
    if is_ref_type(p.type):
        return _REF_SCHEMA
    if p.type == IRType.INT:
        return {"type": "integer"}
    if p.type == IRType.STRING:
        return {"type": "string"}
    if p.type == IRType.BOOL:
        return {"type": "boolean"}
    if p.type == IRType.COLOR:
        return _COLOR_SCHEMA
    if p.type == IRType.POINT:
        return _POINT_SCHEMA
    if p.type == IRType.POINT_LIST:
        return _POINT_LIST_SCHEMA
    if p.type == IRType.STOPS:
        return _STOPS_SCHEMA
    if p.type == IRType.ENUM:
        return {"type": "string", "enum": list(p.choices or [])}
    raise ValueError(f"unhandled IRType: {p.type!r}")


def _op_schema(spec: OpSpec, has_float_refs: bool) -> dict:
    props = {}
    required = []
    for p in spec.params:
        props[p.name] = _param_schema(p, has_float_refs)
        if p.required:
            required.append(p.name)

    return {
        "type": "object",
        "properties": {
            "var": {"type": "string"},
            "op": {"const": spec.name},
            "args": {
                "type": "object",
                "properties": props,
                "required": required,
                "additionalProperties": False,
            },
        },
        "required": ["var", "op", "args"],
        "additionalProperties": False,
    }


def build_schema(specs: list) -> dict:
    """Build the top-level `{"steps": [...]}` JSON Schema for a list of OpSpec.

    FLOAT params are allowed to be `{"$ref": "<var>"}` (referencing an
    earlier step's numeric output, e.g. `top(mesh)`) only if this domain's
    spec registry actually contains FLOAT-returning ops (MeshScript). For
    domains without any FLOAT-returning ops (CanvasScript), FLOAT params are
    constrained to a plain JSON number — this avoids an `oneOf` between two
    object-shaped schemas, which constrained decoding does not enforce
    reliably.
    """
    has_float_refs = any(s.returns == IRType.FLOAT for s in specs)
    return {
        "type": "object",
        "properties": {
            "steps": {
                "type": "array",
                "items": {"oneOf": [_op_schema(s, has_float_refs) for s in specs]},
                "minItems": 1,
            }
        },
        "required": ["steps"],
        "additionalProperties": False,
    }
