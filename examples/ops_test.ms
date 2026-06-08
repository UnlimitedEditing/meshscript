# ops_test.ms — smoke-test every new op in the library

# ── pipe + arc_path ──────────────────────────────────────────────────────────
path_elbow = arc_path(r=1.5, angle=90, segments=24, plane='xz')
elbow = pipe(path_elbow, r=0.2, segments=16)
elbow = ground(elbow)
show(elbow, "elbow_pipe")

# ── helix ────────────────────────────────────────────────────────────────────
spring = helix(r=0.6, pitch=0.35, h=2.5, tube_r=0.07, segments=48, tube_segments=10)
spring = ground(spring)
show(spring, "spring")

# ── sweep with a rect profile ────────────────────────────────────────────────
# A simple L-shaped rail: go up, then go sideways
rail_path = [
    [0, 0, 0], [0, 0, 1.0], [0, 0, 2.0],
    [0.5, 0, 2.0], [1.0, 0, 2.0], [1.5, 0, 2.0],
]
rail = sweep(rect_profile(0.25, 0.12), rail_path)
rail = ground(rail)
show(rail, "rect_sweep")

# ── loft: taper from wide to narrow (same n = 32 both ends) ──────────────────
tapered = loft(
    [circle_profile(1.0, 32), circle_profile(0.4, 32)],
    heights=[0, 3.0]
)
tapered = ground(tapered)
show(tapered, "loft_taper")

# ── loft: bulge in the middle (vase shape) ───────────────────────────────────
vase = loft(
    [circle_profile(0.5, 32), circle_profile(1.2, 32), circle_profile(0.3, 32)],
    heights=[0, 1.5, 3.0]
)
vase = ground(vase)
show(vase, "loft_vase")

# ── loft: hexagonal prism tapering to a point via ngon_profile ───────────────
hex_col = loft(
    [ngon_profile(6, 1.0), ngon_profile(6, 0.1)],
    heights=[0, 4.0]
)
hex_col = ground(hex_col)
show(hex_col, "hex_column")

# ── offset: expand a box (rounds corners via SDF) ────────────────────────────
b = box(w=1.5, h=1.5, d=1.5, center=True)
b_fat = offset(b, 0.2, resolution=40)
b_fat = ground(b_fat)
show(b_fat, "offset_expand")

# ── offset: shrink a sphere ───────────────────────────────────────────────────
s = sphere(r=1.2, subdivisions=3)
s_small = offset(s, -0.25, resolution=40)
s_small = ground(s_small)
show(s_small, "offset_shrink")

# ── convex_hull of two separated spheres ─────────────────────────────────────
a = sphere(r=0.5)
b2 = translate(sphere(r=0.4), x=2.5)
hull = convex_hull(a, b2)
hull = ground(hull)
show(hull, "convex_hull")
