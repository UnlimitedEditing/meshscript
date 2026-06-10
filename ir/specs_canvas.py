"""
ir.specs_canvas — op-spec registry ("dictionary") for CanvasScript / canvas_ops.

Each OpSpec mirrors the signature of the corresponding function in
canvas_ops/*.py (see prompt/canvas-system-prompt.md for the human-facing
reference). `layer_size`/`doc_size` are intentionally omitted — the IR's
constructive style means the LLM always knows the sizes it asked for.

A built-in `show` op is included; it has no `returns` (terminal step).
"""

from __future__ import annotations

from .types import IRType, OpSpec, ParamSpec

# ── shared enum choice lists ────────────────────────────────────────────────

BLEND_MODES = [
    "normal", "multiply", "screen", "add", "subtract",
    "darken", "lighten", "overlay", "difference",
]

ANCHORS = [
    "top-left", "top", "top-right",
    "left", "center", "right",
    "bottom-left", "bottom", "bottom-right",
]

RESAMPLE_MODES = ["nearest", "bilinear", "bicubic", "lanczos"]
GRADIENT_DIRECTIONS = ["vertical", "horizontal"]
TEXT_ALIGN = ["left", "center", "right"]
FLIP_AXES = ["x", "y"]
FIT_MODES = ["contain", "cover", "stretch"]


# ── op specs ─────────────────────────────────────────────────────────────────

CANVAS_SPECS = [

    # -- document.py --
    OpSpec("new_document", returns=IRType.DOCUMENT, params=[
        ParamSpec("width",      IRType.INT,   required=True),
        ParamSpec("height",     IRType.INT,   required=True),
        ParamSpec("background", IRType.COLOR, required=False, default=(255, 255, 255, 255)),
    ]),
    OpSpec("paste", returns=IRType.DOCUMENT, params=[
        ParamSpec("doc",     IRType.DOCUMENT, required=True),
        ParamSpec("layer",   IRType.LAYER,    required=True),
        ParamSpec("x",       IRType.INT,      required=False, default=0),
        ParamSpec("y",       IRType.INT,      required=False, default=0),
        ParamSpec("opacity", IRType.FLOAT,    required=False, default=1.0),
        ParamSpec("blend",   IRType.ENUM,     required=False, default="normal", choices=BLEND_MODES),
    ]),
    OpSpec("crop", returns=IRType.DOCUMENT, params=[
        ParamSpec("doc", IRType.DOCUMENT, required=True),
        ParamSpec("x",   IRType.INT,      required=True),
        ParamSpec("y",   IRType.INT,      required=True),
        ParamSpec("w",   IRType.INT,      required=True),
        ParamSpec("h",   IRType.INT,      required=True),
    ]),
    OpSpec("resize_canvas", returns=IRType.DOCUMENT, params=[
        ParamSpec("doc",      IRType.DOCUMENT, required=True),
        ParamSpec("width",    IRType.INT,      required=True),
        ParamSpec("height",   IRType.INT,      required=True),
        ParamSpec("resample", IRType.ENUM,     required=False, default="lanczos", choices=RESAMPLE_MODES),
    ]),

    # -- shapes.py --
    OpSpec("rect", returns=IRType.LAYER, params=[
        ParamSpec("w",             IRType.INT,   required=True),
        ParamSpec("h",             IRType.INT,   required=True),
        ParamSpec("fill",          IRType.COLOR, required=False),
        ParamSpec("outline",       IRType.COLOR, required=False),
        ParamSpec("outline_width", IRType.INT,   required=False, default=1),
        ParamSpec("radius",        IRType.INT,   required=False, default=0),
    ]),
    OpSpec("ellipse", returns=IRType.LAYER, params=[
        ParamSpec("w",             IRType.INT,   required=True),
        ParamSpec("h",             IRType.INT,   required=True),
        ParamSpec("fill",          IRType.COLOR, required=False),
        ParamSpec("outline",       IRType.COLOR, required=False),
        ParamSpec("outline_width", IRType.INT,   required=False, default=1),
    ]),
    OpSpec("polygon", returns=IRType.LAYER, params=[
        ParamSpec("points",        IRType.POINT_LIST, required=True),
        ParamSpec("fill",          IRType.COLOR,      required=False),
        ParamSpec("outline",       IRType.COLOR,      required=False),
        ParamSpec("outline_width", IRType.INT,        required=False, default=1),
    ]),
    OpSpec("line", returns=IRType.LAYER, params=[
        ParamSpec("points", IRType.POINT_LIST, required=True),
        ParamSpec("fill",   IRType.COLOR,      required=False, default=(0, 0, 0, 255)),
        ParamSpec("width",  IRType.INT,        required=False, default=1),
    ]),
    OpSpec("gradient", returns=IRType.LAYER, params=[
        ParamSpec("w",         IRType.INT,   required=True),
        ParamSpec("h",         IRType.INT,   required=True),
        ParamSpec("stops",     IRType.STOPS, required=True),
        ParamSpec("direction", IRType.ENUM,  required=False, default="vertical", choices=GRADIENT_DIRECTIONS),
    ]),

    # -- text.py --
    OpSpec("text", returns=IRType.LAYER, params=[
        ParamSpec("content",      IRType.STRING, required=True),
        ParamSpec("size",         IRType.INT,    required=False, default=48),
        ParamSpec("color",        IRType.COLOR,  required=False, default=(0, 0, 0, 255)),
        ParamSpec("font",         IRType.STRING, required=False),
        ParamSpec("align",        IRType.ENUM,   required=False, default="left", choices=TEXT_ALIGN),
        ParamSpec("max_width",    IRType.INT,    required=False),
        ParamSpec("line_spacing", IRType.FLOAT,  required=False, default=1.2),
        ParamSpec("stroke_width", IRType.INT,    required=False, default=0),
        ParamSpec("stroke_color", IRType.COLOR,  required=False),
    ]),

    # -- images.py --
    OpSpec("load_image", returns=IRType.LAYER, params=[
        ParamSpec("url_or_path", IRType.STRING, required=True),
        ParamSpec("w",           IRType.INT,    required=False),
        ParamSpec("h",           IRType.INT,    required=False),
        ParamSpec("fit",         IRType.ENUM,   required=False, default="contain", choices=FIT_MODES),
    ]),

    # -- transforms.py --
    OpSpec("rotate", returns=IRType.LAYER, params=[
        ParamSpec("layer",  IRType.LAYER, required=True),
        ParamSpec("angle",  IRType.FLOAT, required=True),
        ParamSpec("expand", IRType.BOOL,  required=False, default=True),
    ]),
    OpSpec("flip", returns=IRType.LAYER, params=[
        ParamSpec("layer", IRType.LAYER, required=True),
        ParamSpec("axis",  IRType.ENUM,  required=False, default="x", choices=FLIP_AXES),
    ]),
    OpSpec("resize_layer", returns=IRType.LAYER, params=[
        ParamSpec("layer", IRType.LAYER, required=True),
        ParamSpec("w",     IRType.INT,   required=True),
        ParamSpec("h",     IRType.INT,   required=True),
    ]),

    # -- effects.py --
    OpSpec("blur", returns=IRType.LAYER, params=[
        ParamSpec("layer",  IRType.LAYER, required=True),
        ParamSpec("radius", IRType.FLOAT, required=True),
    ]),
    OpSpec("drop_shadow", returns=IRType.LAYER, params=[
        ParamSpec("layer",       IRType.LAYER, required=True),
        ParamSpec("offset",      IRType.POINT, required=False, default=(8, 8)),
        ParamSpec("blur_radius", IRType.FLOAT, required=False, default=8),
        ParamSpec("color",       IRType.COLOR, required=False, default=(0, 0, 0, 128)),
    ]),
    OpSpec("set_opacity", returns=IRType.LAYER, params=[
        ParamSpec("layer", IRType.LAYER, required=True),
        ParamSpec("alpha", IRType.FLOAT, required=True),
    ]),
    OpSpec("tint", returns=IRType.LAYER, params=[
        ParamSpec("layer",  IRType.LAYER, required=True),
        ParamSpec("color",  IRType.COLOR, required=True),
        ParamSpec("amount", IRType.FLOAT, required=False, default=1.0),
    ]),
    OpSpec("brightness", returns=IRType.LAYER, params=[
        ParamSpec("layer",  IRType.LAYER, required=True),
        ParamSpec("factor", IRType.FLOAT, required=True),
    ]),
    OpSpec("contrast", returns=IRType.LAYER, params=[
        ParamSpec("layer",  IRType.LAYER, required=True),
        ParamSpec("factor", IRType.FLOAT, required=True),
    ]),

    # -- spatial.py --
    OpSpec("place", returns=IRType.DOCUMENT, params=[
        ParamSpec("doc",     IRType.DOCUMENT, required=True),
        ParamSpec("layer",   IRType.LAYER,    required=True),
        ParamSpec("x",       IRType.INT,      required=False, default=0),
        ParamSpec("y",       IRType.INT,      required=False, default=0),
        ParamSpec("anchor",  IRType.ENUM,     required=False, default="top-left", choices=ANCHORS),
        ParamSpec("opacity", IRType.FLOAT,    required=False, default=1.0),
        ParamSpec("blend",   IRType.ENUM,     required=False, default="normal", choices=BLEND_MODES),
    ]),
    OpSpec("align", returns=IRType.DOCUMENT, params=[
        ParamSpec("doc",     IRType.DOCUMENT, required=True),
        ParamSpec("layer",   IRType.LAYER,    required=True),
        ParamSpec("anchor",  IRType.ENUM,     required=True, choices=ANCHORS),
        ParamSpec("margin",  IRType.INT,      required=False, default=0),
        ParamSpec("opacity", IRType.FLOAT,    required=False, default=1.0),
        ParamSpec("blend",   IRType.ENUM,     required=False, default="normal", choices=BLEND_MODES),
    ]),

    # -- built-in terminal op --
    OpSpec("show", returns=None, params=[
        ParamSpec("doc",   IRType.DOCUMENT, required=True),
        ParamSpec("label", IRType.STRING,   required=True),
    ]),
]

CANVAS_SPECS_BY_NAME = {spec.name: spec for spec in CANVAS_SPECS}
