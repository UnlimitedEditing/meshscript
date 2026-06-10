"""
ir.specs_mesh — op-spec registry ("dictionary") for MeshScript / ops.

Each OpSpec mirrors the signature of the corresponding function in
ops/*.py (see prompt/system-prompt.md for the human-facing reference).

Two ops are intentionally omitted:
  - `bounds(mesh)`   returns [[min_x,min_y,min_z],[max_x,max_y,max_z]] — a
                      nested structure that doesn't fit a single IRType.
                      Use the individual `top`/`bottom`/`left`/`right`/
                      `front`/`back`/`height`/`width`/`depth` queries instead.
  - `centroid(mesh)` returns [x,y,z] for the same reason — use `center_x`/
                      `center_y`/`center_z` instead.

Scalar spatial queries (`top`, `height`, `xy_radius`, `center_x`, ...) return
IRType.FLOAT. A FLOAT-typed argument elsewhere may be either a literal number
or `{"$ref": "<var>"}` pointing to one of these steps — this lets positions
be derived from geometry instead of hardcoded, e.g.
`translate(mesh=part, z={"$ref": "base_top"})`.

A built-in `show` op is included; it has no `returns` (terminal step).
"""

from __future__ import annotations

from .types import IRType, OpSpec, ParamSpec

# ── shared enum choice lists ────────────────────────────────────────────────

AXES = ["x", "y", "z"]
PLANES = ["xy", "xz", "yz"]
FACES = ["top", "bottom", "left", "right", "front", "back"]


# ── op specs ─────────────────────────────────────────────────────────────────

MESH_SPECS = [

    # -- primitives.py --
    OpSpec("box", returns=IRType.MESH, params=[
        ParamSpec("w",      IRType.FLOAT, required=False, default=1),
        ParamSpec("h",      IRType.FLOAT, required=False, default=1),
        ParamSpec("d",      IRType.FLOAT, required=False, default=1),
        ParamSpec("center", IRType.BOOL,  required=False, default=False),
    ], doc="w=width(X), h=height(Z, up), d=depth(Y). center=False sits on z=0."),
    OpSpec("sphere", returns=IRType.MESH, params=[
        ParamSpec("r",            IRType.FLOAT, required=False, default=1),
        ParamSpec("subdivisions", IRType.INT,   required=False, default=3),
    ], doc="Icosphere centered at origin."),
    OpSpec("cylinder", returns=IRType.MESH, params=[
        ParamSpec("r",        IRType.FLOAT, required=False, default=1),
        ParamSpec("h",        IRType.FLOAT, required=False, default=1),
        ParamSpec("segments", IRType.INT,   required=False, default=32),
        ParamSpec("center",   IRType.BOOL,  required=False, default=False),
    ], doc="center=False sits on z=0, grows up."),
    OpSpec("cone", returns=IRType.MESH, params=[
        ParamSpec("r",        IRType.FLOAT, required=False, default=1),
        ParamSpec("h",        IRType.FLOAT, required=False, default=1),
        ParamSpec("segments", IRType.INT,   required=False, default=32),
        ParamSpec("center",   IRType.BOOL,  required=False, default=False),
    ], doc="center=False: base at z=0, apex at z=h."),
    OpSpec("torus", returns=IRType.MESH, params=[
        ParamSpec("r_major",        IRType.FLOAT, required=False, default=1),
        ParamSpec("r_minor",        IRType.FLOAT, required=False, default=0.3),
        ParamSpec("major_segments", IRType.INT,   required=False, default=32),
        ParamSpec("minor_segments", IRType.INT,   required=False, default=16),
    ], doc="Lies in the XY plane, centered at origin."),
    OpSpec("wedge", returns=IRType.MESH, params=[
        ParamSpec("w", IRType.FLOAT, required=False, default=1),
        ParamSpec("h", IRType.FLOAT, required=False, default=1),
        ParamSpec("d", IRType.FLOAT, required=False, default=1),
    ], doc="Right-angle triangular prism."),
    OpSpec("capsule", returns=IRType.MESH, params=[
        ParamSpec("r",        IRType.FLOAT, required=False, default=0.5),
        ParamSpec("h",        IRType.FLOAT, required=False, default=1),
        ParamSpec("segments", IRType.INT,   required=False, default=32),
    ], doc="Cylinder with hemispherical caps, centered at origin."),

    # -- booleans.py --
    OpSpec("union", returns=IRType.MESH, params=[
        ParamSpec("a", IRType.MESH, required=True),
        ParamSpec("b", IRType.MESH, required=True),
    ], doc="Merge two meshes (hard crease at the join)."),
    OpSpec("subtract", returns=IRType.MESH, params=[
        ParamSpec("a", IRType.MESH, required=True),
        ParamSpec("b", IRType.MESH, required=True),
    ], doc="Carve b out of a."),
    OpSpec("intersect", returns=IRType.MESH, params=[
        ParamSpec("a", IRType.MESH, required=True),
        ParamSpec("b", IRType.MESH, required=True),
    ], doc="Keep only the overlap of a and b."),

    # -- transforms.py --
    OpSpec("translate", returns=IRType.MESH, params=[
        ParamSpec("mesh", IRType.MESH,  required=True),
        ParamSpec("x",    IRType.FLOAT, required=False, default=0),
        ParamSpec("y",    IRType.FLOAT, required=False, default=0),
        ParamSpec("z",    IRType.FLOAT, required=False, default=0),
    ]),
    OpSpec("rotate", returns=IRType.MESH, params=[
        ParamSpec("mesh",  IRType.MESH,  required=True),
        ParamSpec("angle", IRType.FLOAT, required=True),
        ParamSpec("axis",  IRType.ENUM,  required=False, default="z", choices=AXES),
    ], doc="angle in degrees. Rotation orbits the world origin unless mesh is centered."),
    OpSpec("scale", returns=IRType.MESH, params=[
        ParamSpec("mesh", IRType.MESH,  required=True),
        ParamSpec("x",    IRType.FLOAT, required=False, default=1),
        ParamSpec("y",    IRType.FLOAT, required=False, default=1),
        ParamSpec("z",    IRType.FLOAT, required=False, default=1),
    ]),
    OpSpec("mirror", returns=IRType.MESH, params=[
        ParamSpec("mesh", IRType.MESH, required=True),
        ParamSpec("axis", IRType.ENUM, required=False, default="x", choices=AXES),
    ]),
    OpSpec("linear_array", returns=IRType.MESH, params=[
        ParamSpec("mesh",    IRType.MESH,  required=True),
        ParamSpec("count",   IRType.INT,   required=True),
        ParamSpec("axis",    IRType.ENUM,  required=False, default="x", choices=AXES),
        ParamSpec("spacing", IRType.FLOAT, required=False, default=1.0),
    ], doc="Repeats mesh `count` times along axis, `spacing` apart."),
    OpSpec("polar_array", returns=IRType.MESH, params=[
        ParamSpec("mesh",  IRType.MESH, required=True),
        ParamSpec("count", IRType.INT,  required=True),
        ParamSpec("axis",  IRType.ENUM, required=False, default="z", choices=AXES),
    ], doc="Rotates mesh into `count` copies around axis. Mesh must already be at orbit radius (translate it off-axis first)."),

    # -- modifiers.py --
    OpSpec("shell", returns=IRType.MESH, params=[
        ParamSpec("mesh",      IRType.MESH,  required=True),
        ParamSpec("thickness", IRType.FLOAT, required=True),
    ], doc="Hollow with a uniform wall. Best for convex shapes."),
    OpSpec("extrude", returns=IRType.MESH, params=[
        ParamSpec("profile", IRType.PROFILE, required=True),
        ParamSpec("height",  IRType.FLOAT,   required=True),
    ], doc="Extrude a 2D profile straight up along Z."),
    OpSpec("revolve", returns=IRType.MESH, params=[
        ParamSpec("profile_points", IRType.POINT_LIST, required=True),
        ParamSpec("angle",          IRType.FLOAT,      required=False, default=360),
        ParamSpec("segments",       IRType.INT,        required=False, default=64),
    ], doc="profile_points: list of [r, z] pairs (r >= 0), revolved around the Z axis."),

    # -- profiles.py --
    OpSpec("circle_profile", returns=IRType.PROFILE, params=[
        ParamSpec("r",        IRType.FLOAT, required=False, default=1),
        ParamSpec("segments", IRType.INT,   required=False, default=32),
    ]),
    OpSpec("rect_profile", returns=IRType.PROFILE, params=[
        ParamSpec("w", IRType.FLOAT, required=False, default=1),
        ParamSpec("h", IRType.FLOAT, required=False, default=1),
    ]),
    OpSpec("polygon_profile", returns=IRType.PROFILE, params=[
        ParamSpec("points", IRType.POINT_LIST, required=True),
    ], doc="Arbitrary polygon from a list of [x, y] points."),
    OpSpec("ngon_profile", returns=IRType.PROFILE, params=[
        ParamSpec("n", IRType.INT,   required=True),
        ParamSpec("r", IRType.FLOAT, required=False, default=1.0),
    ], doc="Regular n-sided polygon, circumradius r. Preferred for loft() — gives an exact, predictable vertex count."),
    OpSpec("ring_profile", returns=IRType.PROFILE, params=[
        ParamSpec("r_outer",  IRType.FLOAT, required=False, default=1),
        ParamSpec("r_inner",  IRType.FLOAT, required=False, default=0.5),
        ParamSpec("segments", IRType.INT,   required=False, default=32),
    ]),
    OpSpec("star_profile", returns=IRType.PROFILE, params=[
        ParamSpec("points",  IRType.INT,   required=False, default=5),
        ParamSpec("r_outer", IRType.FLOAT, required=False, default=1.0),
        ParamSpec("r_inner", IRType.FLOAT, required=False, default=0.4),
    ]),

    # -- solids.py --
    OpSpec("tetrahedron", returns=IRType.MESH, params=[
        ParamSpec("r", IRType.FLOAT, required=False, default=1),
    ], doc="Regular tetrahedron, circumradius r."),
    OpSpec("cube", returns=IRType.MESH, params=[
        ParamSpec("s", IRType.FLOAT, required=False, default=1),
    ], doc="Regular hexahedron, side length s."),
    OpSpec("octahedron", returns=IRType.MESH, params=[
        ParamSpec("r", IRType.FLOAT, required=False, default=1),
    ], doc="Regular octahedron, circumradius r."),
    OpSpec("dodecahedron", returns=IRType.MESH, params=[
        ParamSpec("r", IRType.FLOAT, required=False, default=1),
    ], doc="Regular dodecahedron, circumradius r."),
    OpSpec("icosahedron", returns=IRType.MESH, params=[
        ParamSpec("r", IRType.FLOAT, required=False, default=1),
    ], doc="Regular icosahedron, circumradius r."),
    OpSpec("prism", returns=IRType.MESH, params=[
        ParamSpec("n", IRType.INT,   required=False, default=6),
        ParamSpec("r", IRType.FLOAT, required=False, default=1),
        ParamSpec("h", IRType.FLOAT, required=False, default=1),
    ], doc="Regular n-gon prism. r = circumradius of base, h = height."),
    OpSpec("antiprism", returns=IRType.MESH, params=[
        ParamSpec("n", IRType.INT,   required=False, default=6),
        ParamSpec("r", IRType.FLOAT, required=False, default=1),
        ParamSpec("h", IRType.FLOAT, required=False, default=1),
    ], doc="Regular n-antiprism. r = circumradius, h = height."),
    OpSpec("geodesic", returns=IRType.MESH, params=[
        ParamSpec("r",         IRType.FLOAT, required=False, default=1),
        ParamSpec("frequency", IRType.INT,   required=False, default=2),
    ], doc="Subdivided icosphere. frequency=1 = icosahedron."),

    # -- sdf.py --
    OpSpec("blend_union", returns=IRType.MESH, params=[
        ParamSpec("mesh_a",    IRType.MESH,  required=True),
        ParamSpec("mesh_b",    IRType.MESH,  required=True),
        ParamSpec("radius",    IRType.FLOAT, required=True),
        ParamSpec("resolution", IRType.INT,  required=False, default=48),
    ], doc="Smooth boolean union — surfaces blend together over a zone of width `radius`."),
    OpSpec("blend_subtract", returns=IRType.MESH, params=[
        ParamSpec("mesh_a",    IRType.MESH,  required=True),
        ParamSpec("mesh_b",    IRType.MESH,  required=True),
        ParamSpec("radius",    IRType.FLOAT, required=True),
        ParamSpec("resolution", IRType.INT,  required=False, default=48),
    ], doc="Smooth boolean subtract — the cut edge blends rather than being sharp."),
    OpSpec("fillet", returns=IRType.MESH, params=[
        ParamSpec("mesh",      IRType.MESH,  required=True),
        ParamSpec("radius",    IRType.FLOAT, required=True),
        ParamSpec("resolution", IRType.INT,  required=False, default=56),
    ], doc="Round all sharp convex edges by radius. Use resolution 48-64 for production quality."),
    OpSpec("offset", returns=IRType.MESH, params=[
        ParamSpec("mesh",      IRType.MESH,  required=True),
        ParamSpec("distance",  IRType.FLOAT, required=True),
        ParamSpec("resolution", IRType.INT,  required=False, default=48),
    ], doc="Expand (distance > 0) or shrink (distance < 0) the surface uniformly."),

    # -- sweep.py --
    OpSpec("sweep", returns=IRType.MESH, params=[
        ParamSpec("profile", IRType.PROFILE, required=True),
        ParamSpec("path",    IRType.PATH,    required=True),
        ParamSpec("closed",  IRType.BOOL,    required=False, default=False),
    ], doc="Extrude a 2D profile along a 3D path (e.g. from arc_path/helix_path)."),
    OpSpec("pipe", returns=IRType.MESH, params=[
        ParamSpec("path",     IRType.PATH,  required=True),
        ParamSpec("r",        IRType.FLOAT, required=False, default=0.1),
        ParamSpec("segments", IRType.INT,   required=False, default=16),
    ], doc="Circular tube swept along a 3D path."),
    OpSpec("loft", returns=IRType.MESH, params=[
        ParamSpec("profiles", IRType.PROFILE_LIST, required=True),
        ParamSpec("heights",  IRType.FLOAT_LIST,   required=False),
        ParamSpec("cap",      IRType.BOOL,         required=False, default=True),
    ], doc="Blend between profiles at increasing heights. All profiles must have the SAME vertex count — use ngon_profile(n, r) for every profile in the list."),
    OpSpec("arc_path", returns=IRType.PATH, params=[
        ParamSpec("r",        IRType.FLOAT, required=False, default=1.0),
        ParamSpec("angle",    IRType.FLOAT, required=False, default=180),
        ParamSpec("segments", IRType.INT,   required=False, default=32),
        ParamSpec("plane",    IRType.ENUM,  required=False, default="xy", choices=PLANES),
    ], doc="Circular arc path. angle in degrees (360 = full circle)."),
    OpSpec("helix_path", returns=IRType.PATH, params=[
        ParamSpec("r",        IRType.FLOAT, required=False, default=1.0),
        ParamSpec("pitch",    IRType.FLOAT, required=False, default=0.5),
        ParamSpec("h",        IRType.FLOAT, required=False, default=3.0),
        ParamSpec("segments", IRType.INT,   required=False, default=64),
    ], doc="Helical centreline path. pitch = vertical rise per full turn."),
    OpSpec("helix", returns=IRType.MESH, params=[
        ParamSpec("r",             IRType.FLOAT, required=False, default=1.0),
        ParamSpec("pitch",         IRType.FLOAT, required=False, default=0.5),
        ParamSpec("h",             IRType.FLOAT, required=False, default=3.0),
        ParamSpec("tube_r",        IRType.FLOAT, required=False, default=0.05),
        ParamSpec("segments",      IRType.INT,   required=False, default=64),
        ParamSpec("tube_segments", IRType.INT,   required=False, default=12),
    ], doc="Helical tube (spring/coil/thread approximation)."),

    # -- spatial.py: scalar queries (-> float) --
    OpSpec("top", returns=IRType.FLOAT, params=[
        ParamSpec("mesh", IRType.MESH, required=True),
    ], doc="Max Z."),
    OpSpec("bottom", returns=IRType.FLOAT, params=[
        ParamSpec("mesh", IRType.MESH, required=True),
    ], doc="Min Z."),
    OpSpec("front", returns=IRType.FLOAT, params=[
        ParamSpec("mesh", IRType.MESH, required=True),
    ], doc="Min Y."),
    OpSpec("back", returns=IRType.FLOAT, params=[
        ParamSpec("mesh", IRType.MESH, required=True),
    ], doc="Max Y."),
    OpSpec("left", returns=IRType.FLOAT, params=[
        ParamSpec("mesh", IRType.MESH, required=True),
    ], doc="Min X."),
    OpSpec("right", returns=IRType.FLOAT, params=[
        ParamSpec("mesh", IRType.MESH, required=True),
    ], doc="Max X."),
    OpSpec("height", returns=IRType.FLOAT, params=[
        ParamSpec("mesh", IRType.MESH, required=True),
    ], doc="Z extent."),
    OpSpec("width", returns=IRType.FLOAT, params=[
        ParamSpec("mesh", IRType.MESH, required=True),
    ], doc="X extent."),
    OpSpec("depth", returns=IRType.FLOAT, params=[
        ParamSpec("mesh", IRType.MESH, required=True),
    ], doc="Y extent."),
    OpSpec("center_x", returns=IRType.FLOAT, params=[
        ParamSpec("mesh", IRType.MESH, required=True),
    ]),
    OpSpec("center_y", returns=IRType.FLOAT, params=[
        ParamSpec("mesh", IRType.MESH, required=True),
    ]),
    OpSpec("center_z", returns=IRType.FLOAT, params=[
        ParamSpec("mesh", IRType.MESH, required=True),
    ]),
    OpSpec("xy_radius", returns=IRType.FLOAT, params=[
        ParamSpec("mesh", IRType.MESH, required=True),
    ], doc="Max distance from the Z axis across all vertices — bounding radius in XY."),

    # -- spatial.py: alignment (-> mesh) --
    OpSpec("ground", returns=IRType.MESH, params=[
        ParamSpec("mesh", IRType.MESH, required=True),
    ], doc="Translate so the lowest point sits on z=0. Call on the final object before show()."),
    OpSpec("place_on", returns=IRType.MESH, params=[
        ParamSpec("mesh",   IRType.MESH, required=True),
        ParamSpec("target", IRType.MESH, required=True),
    ], doc="Translate so mesh's bottom sits on target's top."),
    OpSpec("place_at", returns=IRType.MESH, params=[
        ParamSpec("mesh", IRType.MESH,  required=True),
        ParamSpec("z",    IRType.FLOAT, required=True),
    ], doc="Translate so mesh's bottom is at the given z."),
    OpSpec("center_on", returns=IRType.MESH, params=[
        ParamSpec("mesh",   IRType.MESH, required=True),
        ParamSpec("target", IRType.MESH, required=True),
        ParamSpec("x",      IRType.BOOL, required=False, default=True),
        ParamSpec("y",      IRType.BOOL, required=False, default=True),
        ParamSpec("z",      IRType.BOOL, required=False, default=False),
    ], doc="Align mesh's centroid to target's centroid on the chosen axes (XY by default)."),
    OpSpec("align_to", returns=IRType.MESH, params=[
        ParamSpec("mesh",   IRType.MESH, required=True),
        ParamSpec("target", IRType.MESH, required=True),
        ParamSpec("face",   IRType.ENUM, required=True, choices=FACES),
    ], doc="Snap a face of mesh flush to the same face of target."),
    OpSpec("convex_hull", returns=IRType.MESH, params=[
        ParamSpec("meshes", IRType.MESH_LIST, required=True),
    ], doc="Convex hull of one or more meshes — the tightest convex shape containing all of them."),

    # -- built-in terminal op --
    OpSpec("show", returns=None, params=[
        ParamSpec("mesh",  IRType.MESH,   required=True),
        ParamSpec("label", IRType.STRING, required=True),
    ]),
]

MESH_SPECS_BY_NAME = {spec.name: spec for spec in MESH_SPECS}
