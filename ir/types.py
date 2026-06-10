"""
ir.types — shared type tags and spec dataclasses for the structured-output IR.

An OpSpec describes one callable op (from canvas_ops or ops): its name, its
typed parameters, and the IRType it returns (if any). This registry is the
single source of truth for:

  - ir.schema   — generates the JSON Schema used for constrained decoding
  - ir.validate — checks $ref type-compatibility between steps
  - ir.compile  — emits .cnv / .ms source text
  - ir.prompt   — renders the human-readable "dictionary" for the system prompt
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class IRType(str, Enum):
    # JSON-literal types
    INT        = "int"
    FLOAT      = "float"
    STRING     = "string"
    BOOL       = "bool"
    COLOR      = "color"        # [r, g, b, a], each 0-255
    POINT      = "point"        # [x, y]
    POINT_LIST = "point_list"   # [[x, y], ...]
    STOPS      = "stops"        # [{"pos": 0..1, "color": [r,g,b,a]}, ...]
    ENUM       = "enum"         # string, restricted to `choices`

    # object-reference types — may only be supplied as {"$ref": "<var>"}
    DOCUMENT = "document"   # canvas_ops
    LAYER    = "layer"      # canvas_ops

    MESH    = "mesh"        # ops (phase 2)
    PROFILE = "profile"     # ops (phase 2)
    PATH    = "path"        # ops (phase 2)

    # list-of-reference / list-of-number types (ops phase 2)
    MESH_LIST    = "mesh_list"     # [{"$ref": "<var>"}, ...] each referencing a MESH
    PROFILE_LIST = "profile_list"  # [{"$ref": "<var>"}, ...] each referencing a PROFILE
    FLOAT_LIST   = "float_list"    # [number, ...]


# Types that must be passed by reference (to a prior step's `var`), never as
# an inline literal.
REF_TYPES = {
    IRType.DOCUMENT,
    IRType.LAYER,
    IRType.MESH,
    IRType.PROFILE,
    IRType.PATH,
}

# Maps a list-of-reference IRType to the IRType its elements must reference.
LIST_ELEM_TYPES = {
    IRType.MESH_LIST:    IRType.MESH,
    IRType.PROFILE_LIST: IRType.PROFILE,
}


def is_ref_type(t: IRType) -> bool:
    return t in REF_TYPES


@dataclass
class ParamSpec:
    name: str
    type: IRType
    required: bool = True
    default: Any = None
    choices: Optional[list] = None   # for IRType.ENUM
    doc: str = ""


@dataclass
class OpSpec:
    name: str
    params: list = field(default_factory=list)   # list[ParamSpec]
    returns: Optional[IRType] = None              # None = no usable return value
    doc: str = ""

    def param(self, name: str) -> Optional[ParamSpec]:
        for p in self.params:
            if p.name == name:
                return p
        return None
