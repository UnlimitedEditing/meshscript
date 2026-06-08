# MeshScript Design Patterns

Patterns are organized by **construction strategy** (how a shape is built), not by domain (what it represents). The same construction strategy recurs across disciplines — a domain tag flags which fields it appears in.

## Structure

**Micro-patterns** — a single construction strategy applied with a specific design intent. Building blocks.
**Macro-patterns** — named composed forms built from multiple micro-patterns. Domain-specific canonical objects.

## Tag vocabulary

| Tag | Domain |
|---|---|
| `math` | Mathematical geometry (Platonic solids, symmetry groups, minimal surfaces) |
| `mech` | Mechanical / precision manufacturing |
| `arch` | Classical & parametric architecture |
| `natural` | Natural form & biological geometry |
| `product` | Industrial & product design |
| `game` | Digital / game asset conventions |
| `craft` | Traditional crafts & making |
| `struct` | Scientific & structural systems |
| `art` | Sculpture & fine art |

---

## Family 1: Profile-Driven

Shapes defined by a 2D cross-section moved, rotated, or morphed through space.
Core ops: `extrude`, `revolve`, `sweep`, `loft`, `arc_path`, `helix_path`.

---

### P1.1 — Extruded Prism

*tags: math, mech, arch, game*

**Goal:** A solid with a constant cross-section and uniform depth — bar stock, structural sections, floor slabs, prismatic solids.

```python
# Hexagonal rod:
rod = extrude(ngon_profile(6, r=0.5), height=3.0)
rod = ground(rod)

# L-section rail:
L_pts = [(0,0),(0,1),(0.1,1),(0.1,0.1),(0.5,0.1),(0.5,0)]
rail = extrude(polygon_profile(L_pts), height=4.0)
```

Note: `extrude()` always grows along +Z. Rotate after to reorient.

---

### P1.2 — Surface of Revolution

*tags: arch, art, natural, product, mech*

**Goal:** Any shape with full rotational symmetry — columns, vases, goblets, gear blanks, domes, shells.

```python
# Goblet: define right-side silhouette as (radius, height) pairs
profile = [
    (0,   0.0),   # base center
    (1.2, 0.0),   # base rim
    (0.8, 0.2),   # base taper
    (0.3, 1.5),   # stem
    (0.3, 2.5),   # stem top
    (1.5, 3.0),   # bowl base
    (1.8, 4.5),   # bowl widest
    (1.6, 5.0),   # rim
    (0,   5.0),   # top center — omit for open bowl
]
goblet = revolve(profile, segments=64)
goblet = ground(goblet)
```

The profile traces the outer silhouette from base to top along the right side (r ≥ 0). r=0 closes a flat end. Relationships: P5.2 (open vessel) removes the closing point; P5.6 (bore) adds a center hole.

---

### P1.3 — Open Vessel

*tags: art, product, arch*

**Goal:** Bowl, cup, or basin — revolved profile with no top closure and a wall thickness, open at the top.

```python
wall = 0.12
profile_outer = [(0,0),(1.5,0),(2.0,1.5),(2.2,3.0),(2.0,4.0)]
profile_inner = [(0,wall),(1.5-wall,wall),(2.0-wall,1.5),(2.2-wall,3.0),(2.0-wall,4.0)]

outer = revolve(profile_outer, segments=64)
inner = revolve(profile_inner, segments=64)
bowl  = subtract(outer, inner)
bowl  = ground(bowl)
```

Both profiles must have the same number of points. `inner` is inset by `wall` in radius and elevated by `wall` at the base. Alternatively use `shell()` for simpler convex bowls (less control over wall profile).

---

### P1.4 — Partial Revolution (Arc Solid)

*tags: arch, mech, struct*

**Goal:** A solid spanning only part of a circle — arch voussoir, bracket with curved face, sector.

```python
# Quarter-circle bracket: 90° sweep of a rectangular profile around Z
profile = [(1.0,0),(2.0,0),(2.0,0.4),(1.0,0.4)]  # annular rectangle
bracket = revolve(profile, angle=90, segments=24)
bracket = ground(bracket)

# Semicircular arch cross-section (2D arch rib extruded, then cut — see P2.3 for full arch)
```

`angle < 360` creates an open solid (two flat end faces). The profile should not cross r=0 for partial sweeps.

---

### P1.5 — Swept Tube

*tags: mech, arch, struct*

**Goal:** A circular tube following a curved or custom centreline — pipe, handrail, arch rib, conduit, cable.

```python
# 90° elbow:
path  = arc_path(r=2.0, angle=90, plane='xz', segments=24)
elbow = pipe(path, r=0.25, segments=16)
elbow = ground(elbow)

# Freeform handrail:
path = [[0,0,1.0],[0,1,1.1],[0,2,1.0],[0,3,0.9],[0,4,1.0]]
rail = pipe(path, r=0.04, segments=12)
```

`pipe()` is shorthand for `sweep(circle_profile(r, segments), path)`. For non-circular cross-sections, use P1.6.

---

### P1.6 — Swept Rail (Non-Circular Section)

*tags: mech, arch, craft*

**Goal:** Structural rail, molding, cable tray, or any extruded profile following a custom path — cornice, gutter, edge bead.

```python
# Rectangular section along an arc (structural rail):
path    = arc_path(r=3.0, angle=180, plane='xy', segments=32)
section = rect_profile(0.15, 0.08)
rail    = sweep(section, path)
rail    = ground(rail)

# L-section cornice along a straight run:
cornice_pts = [(0,0),(0,0.4),(0.3,0.4),(0.3,0.05),(0.05,0.05),(0.05,0)]
path = [[0,y,0] for y in range(6)]
cornice = sweep(polygon_profile(cornice_pts), path)
```

The profile lies in the XY plane at path start; `sweep()` rotates it to stay perpendicular to the path tangent (rotation-minimizing frame, no twist).

---

### P1.7 — Helical Sweep

*tags: mech, natural, struct*

**Goal:** Spring, coil, screw thread approximation, DNA helix, helical stair rail.

```python
# Compression spring:
spring = helix(r=0.8, pitch=0.4, h=4.0, tube_r=0.07, segments=48)

# Non-circular coil (rectangular wire):
path = helix_path(r=1.0, pitch=0.6, h=5.0, segments=64)
coil = sweep(rect_profile(0.1, 0.06), path)

# Thread approximation on a shaft (wrap tight, use as cutter or additive):
thread_path = helix_path(r=0.5, pitch=0.1, h=2.0, segments=48)
thread_bead = sweep(ngon_profile(3, r=0.04), thread_path)  # triangular thread profile
```

For actual threads, use `thread_bead` as an additive union or a subtractive cutter on a cylinder.

---

### P1.8 — Lofted Taper

*tags: arch, mech, art, math*

**Goal:** Shape that narrows (or widens) continuously from base to top — column, spire, obelisk, pin, chess piece, rocket nose.

```python
# Simple linear taper:
shaft = loft(
    [circle_profile(1.0, 32), circle_profile(0.3, 32)],
    heights=[0, 6.0]
)

# Entasis — classical column bulge (wider at 1/3 height, narrower at top):
shaft = loft(
    [circle_profile(1.00, 32),   # base diameter
     circle_profile(1.05, 32),   # max swell at 1/3
     circle_profile(0.85, 32)],  # neck at top
    heights=[0, 2.0, 6.0]
)
shaft = ground(shaft)
```

All profiles must share the same vertex count. Use `circle_profile(r, N)` with explicit `N` on every profile. Entasis is the key architectural refinement that makes columns look straight to the eye.

---

### P1.9 — Lofted Shape Morph

*tags: arch, product, game, art*

**Goal:** Transition between fundamentally different cross-sections — square base to round dome, gothic spire from octagon to point, organic shape change.

```python
# Square base → round dome transition (use ngon at same N throughout):
N = 32
base   = ngon_profile(N, r=2.0)   # 32-gon ≈ square footprint at low N, circle at high N
mid    = ngon_profile(N, r=1.6)
top    = ngon_profile(N, r=0.1)   # near-point

transition = loft([base, mid, top], heights=[0, 1.5, 4.0])
transition  = ground(transition)

# Gothic spire: octagonal to near-point
N = 8
spire = loft(
    [ngon_profile(8, 1.0), ngon_profile(8, 0.6), ngon_profile(8, 0.05)],
    heights=[0, 2.0, 6.0]
)
```

The vertex count determines the "polygonal character" of the form. 8 = faceted octagonal; 32 = smooth round.

---

## Family 2: Boolean Composition

Shapes built by combining, carving, or clipping solids.
Core ops: `union`, `subtract`, `intersect`.

---

### P2.1 — Additive Boss

*tags: mech, product*

**Goal:** Attach a raised feature (lug, boss, handle ear, rib) flush to the surface of a body.

```python
body = cylinder(r=1.5, h=4.0)

# Flat mounting ear on the side:
ear  = box(w=0.4, h=0.6, d=0.8)
ear  = translate(ear, x=xy_radius(body) - 0.05)  # overlap slightly to ensure union
ear  = translate(ear, z=center_z(body) - height(ear)/2)
ear  = center_on(ear, body, x=False, y=True)

result = union(body, ear)
```

Always overlap the boss into the body by a small amount (0.05–0.1) so the boolean closes cleanly without a zero-thickness interface.

---

### P2.2 — Intersective Clip

*tags: mech, arch, game, math*

**Goal:** Trim a shape to fit within a boundary — clip a sphere to a cube, cut an arch opening flat to a wall face, create faceted gem from sphere.

```python
# Gem: sphere clipped by a cube (creates faceted form):
gem = intersect(sphere(r=1.5), cube(s=2.0))
gem = ground(gem)

# Arch opening cut into a wall slab:
wall   = box(w=5.0, h=3.0, d=0.4)
arch   = cylinder(r=0.6, h=depth(wall) + 0.02, segments=32)
arch   = rotate(arch, 90, 'x')
arch   = place_at(arch, z=0)           # base of arch at z=0
arch   = center_on(arch, wall)         # centered in wall
wall   = subtract(wall, arch)
```

Intersect is underused. It's the cleanest way to confine organic geometry to a hard boundary.

---

### P2.3 — Dome Cut

*tags: arch, struct, math*

**Goal:** Convert a sphere or geodesic into a dome by removing the lower portion.

```python
r = 2.0
ball   = geodesic(r=r, frequency=3)
# Cutter: a box that removes everything below z=0 (equator):
cutter = box(w=r*3, h=r*2, d=r*3, center=True)
cutter = translate(cutter, z=-r)

dome = subtract(ball, cutter)
dome = ground(dome)

# Raised dome (only top quarter):
cutter2 = translate(cutter, z=r * 0.5)   # cut at half-height instead of equator
shallow_dome = subtract(geodesic(r=r, frequency=3), cutter2)
shallow_dome = ground(shallow_dome)
```

The cut height determines the dome's rise-to-span ratio. Equator cut = hemisphere (rise = radius). Higher cut = shallower, wider dome.

---

### P2.4 — Radial Boolean Array

*tags: arch, mech, math*

**Goal:** Features repeated in a ring by boolean operation — column flutes, gear tooth approximation, ventilation holes, knurled surface.

```python
# Column fluting: subtract 16 elongated cylinders around a shaft
shaft  = cylinder(r=1.0, h=6.0, segments=64)
r_flute = xy_radius(shaft)

# One flute cutter: thin cylinder positioned at surface
flute  = cylinder(r=0.12, h=height(shaft) + 0.02, segments=16)
flute  = translate(flute, x=r_flute - 0.06)  # half-embedded

all_flutes = polar_array(flute, count=16)
fluted_shaft = subtract(shaft, all_flutes)

# Radial ventilation holes in a disc:
disc  = cylinder(r=3.0, h=0.3, segments=64)
hole  = cylinder(r=0.2, h=0.4, segments=16)
hole  = translate(hole, x=2.0)           # at orbit radius 2.0
holes = polar_array(hole, count=12)
vented = subtract(disc, holes)
```

Position the cutter at the right orbital radius before `polar_array`. The cutter should penetrate the body slightly to ensure clean boolean.

---

### P2.5 — Linear Boolean Array

*tags: mech, arch, game*

**Goal:** A row of identical cutouts or additions — slot array, window series, rack teeth, grille.

```python
# Grille: slots across a panel
panel  = box(w=4.0, h=2.0, d=0.15)
slot   = box(w=3.6, h=0.12, d=0.2)   # slightly wider and deeper than panel
slot   = center_on(slot, panel)
slot   = place_at(slot, z=bottom(panel) - 0.02)

# Array 8 slots along Z with 0.22 spacing:
slots  = linear_array(slot, count=8, axis='z', spacing=0.22)
grille = subtract(panel, slots)
grille = ground(grille)
```

Make the cutter slightly oversized (wider/deeper) than the body thickness to guarantee it exits the far face cleanly.

---

### P2.6 — Compound Boolean Chain

*tags: mech, arch, product*

**Goal:** A part built through multiple additive and subtractive steps in sequence — machined bracket, molding profile, complex fitting.

```python
# Bracket: base plate + upright rib, with mounting holes
base    = box(w=4.0, h=0.4, d=3.0)
rib     = box(w=0.5, h=3.0, d=3.0)
rib     = align_to(rib, base, 'top')    # rib sits on base top
rib     = align_to(rib, base, 'back')   # flush to back face

bracket = union(base, rib)

# Two mounting holes through the base:
hole    = cylinder(r=0.2, h=height(base) + 0.02, segments=16)
hole_l  = translate(hole, x=-1.2, y=center_y(base))
hole_r  = translate(hole, x= 1.2, y=center_y(base))
hole_l  = place_at(hole_l, z=bottom(base) - 0.01)
hole_r  = place_at(hole_r, z=bottom(base) - 0.01)

bracket = subtract(bracket, union(hole_l, hole_r))
bracket = ground(bracket)
```

Accumulate geometry into a named variable at each step. Union additive features first, then subtract all cutters.

---

## Family 3: Surface Quality

Controlling edge sharpness, join smoothness, and surface character.
Core ops: `fillet`, `blend_union`, `blend_subtract`, `offset`.

---

### P3.1 — Edge Fillet

*tags: product, mech, game, craft*

**Goal:** Round all convex edges of a solid uniformly — stress relief, consumer-product finish, hard-surface bevel.

```python
b = box(w=3.0, h=2.0, d=4.0, center=True)
b = fillet(b, radius=0.2, resolution=56)
b = ground(b)

# Rule of thumb: radius < 1/6 of the shortest dimension to avoid geometry collapse
```

`fillet()` operates on all convex edges at once — there is no per-edge selection. For chamfer-like faceting at low resolution (game assets), use a small radius with `resolution=32`.

---

### P3.2 — Smooth Join

*tags: art, product, natural*

**Goal:** Two parts that blend into each other with no visible seam — handle into body, branch from trunk, organic junction.

```python
body   = cylinder(r=1.2, h=3.0, segments=48)
handle = torus(r_major=0.85, r_minor=0.18)
handle = rotate(handle, 90, 'x')
handle = translate(handle, x=xy_radius(body) + 0.18, z=center_z(body))

# blend radius ≈ 10–20% of the smaller part's diameter
merged = blend_union(body, handle, radius=0.12, resolution=48)
merged = ground(merged)
```

Larger `radius` = wider, softer transition. If the two bodies barely touch, increase overlap before blending. `blend_union` is slower than `union` — use only where the join is visually important.

---

### P3.3 — Smooth Subtract

*tags: product, arch*

**Goal:** Carved recess or cutout with blended edges rather than a sharp rim — soft grip depression, rounded window reveal.

```python
block  = box(w=4.0, h=2.0, d=4.0)
cutter = sphere(r=1.5)
cutter = translate(cutter, z=top(block))   # sphere centered at top face

carved = blend_subtract(block, cutter, radius=0.15, resolution=48)
carved = ground(carved)
```

The blend radius softens the edge where the cutter exits the surface. Works best when the cutter is significantly larger than the blend radius.

---

### P3.4 — Outward Offset (Rounded Cuboid)

*tags: product, arch*

**Goal:** A box-like solid with uniformly rounded edges and corners — packaging, electronic enclosure, keycap, pillow.

```python
# Build a smaller inner box, then offset outward by the desired rounding:
rounding = 0.3
inner = box(w=4.0 - 2*rounding, h=2.0 - 2*rounding, d=3.0 - 2*rounding, center=True)
outer = offset(inner, rounding, resolution=56)
outer = ground(outer)
```

This is more predictable than `fillet()` for cases where you know the target outer dimensions. The result has equal rounding on all 12 edges and all 8 corners.

---

### P3.5 — Inward Offset (Surface Erosion)

*tags: mech, product*

**Goal:** Shrink a surface inward uniformly — generate a clearance shell, erode a solid for tolerance fitting, find the "core" of a complex shape.

```python
# Tolerance gap: create a slightly smaller version of a part
part    = revolve([(0,0),(1.0,0),(1.2,1.5),(0.8,3.0),(0,3.0)], segments=48)
smaller = offset(part, -0.05, resolution=48)   # 0.05 clearance all around
```

Negative `distance` in `offset()` moves the surface inward. If the mesh has thin features, shrinking too much can collapse them — watch for `None` return (fallback to original).

---

## Family 4: Spatial Arrangement

Repeating, mirroring, or distributing geometry in space.
Core ops: `linear_array`, `polar_array`, `mirror`, `translate`.

---

### P4.1 — Linear Repeat

*tags: arch, mech, craft, game*

**Goal:** N identical elements spaced along a line — fence posts, brick row, rack teeth, shelf pins, pillar series.

```python
post   = cylinder(r=0.05, h=2.0)
# spacing = center-to-center distance:
fence  = linear_array(post, count=8, axis='y', spacing=1.2)
fence  = ground(fence)

# Edge-to-edge spacing: space = element_width + gap
tooth_w = 0.15
gap     = 0.08
rack    = linear_array(box(w=tooth_w, h=0.3, d=0.5), count=12,
                       axis='x', spacing=tooth_w + gap)
```

---

### P4.2 — Radial Repeat

*tags: arch, mech, math, struct*

**Goal:** N identical elements distributed evenly around a central axis — circular colonnade, bolt flange, fan blades, rose window radials.

```python
# Critical: position the element at its orbit radius BEFORE polar_array
r_orbit = 4.0
col     = cylinder(r=0.3, h=5.0)
col     = translate(col, x=r_orbit)   # move to orbit
cols    = polar_array(col, count=8)   # array around Z
cols    = ground(cols)

# Bolt circle (for a flange):
flange  = cylinder(r=2.5, h=0.4, segments=64)
bolt    = cylinder(r=0.15, h=0.5, segments=12)
bolt    = translate(bolt, x=1.8)      # bolt circle radius = 1.8
bolts   = polar_array(bolt, count=6)
flange  = subtract(flange, bolts)
```

---

### P4.3 — Bilateral Mirror

*tags: product, arch, mech, art*

**Goal:** Build one half, mirror to get the other — symmetric grip, facade, bracket, face.

```python
# Right arm of a handle cross:
arm = box(w=1.5, h=0.3, d=0.3)
arm = translate(arm, x=0.5)          # offset so inner edge is at x=0.5

arm_l  = mirror(arm, axis='x')       # reflects across X, creating left arm
cross  = union(arm, arm_l)

# Add vertical arm:
v_arm  = box(w=0.3, h=2.0, d=0.3, center=True)
handle = union(cross, v_arm)
handle = ground(handle)
```

Position the original with its symmetry plane at the world axis (x=0 for X-mirror) before mirroring.

---

### P4.4 — Compound Mirror (4-Fold Symmetry)

*tags: arch, math, product*

**Goal:** Objects with 4-way symmetry — classical floor plans, ornamental cross, cruciform column capital.

```python
# Build one quadrant, mirror twice:
quadrant = box(w=1.5, h=0.4, d=0.8)
quadrant = translate(quadrant, x=0.2, y=0.2)   # offset from center axes

q_x = mirror(quadrant, axis='x')        # reflect across X
half = union(quadrant, q_x)
q_y = mirror(half, axis='y')            # reflect the pair across Y
full = union(half, q_y)
full = ground(full)
```

Works for any 4-fold form. For n-fold symmetry, use `polar_array` instead.

---

### P4.5 — Grid Array

*tags: arch, mech, game*

**Goal:** 2D grid of identical elements — tile pattern, window grid, PCB standoffs, bolt grid.

```python
# 5×5 grid of posts:
post   = cylinder(r=0.1, h=1.0)
row    = linear_array(post, count=5, axis='x', spacing=1.0)
grid   = linear_array(row, count=5, axis='y', spacing=1.0)
grid   = ground(grid)
```

Chain two `linear_array` calls for 2D. The inner call produces a row; the outer call replicates the row.

---

### P4.6 — Staggered Grid

*tags: arch, game, craft*

**Goal:** Offset rows (brick coursing, ashlar masonry, hex tiling approximation).

```python
brick_w, brick_h, brick_d = 0.9, 0.3, 0.4
gap = 0.05

brick = box(w=brick_w, h=brick_h, d=brick_d)

# Even rows at x=0; odd rows offset by half brick + half gap:
even_row = linear_array(brick, count=6, axis='x', spacing=brick_w + gap)
odd_row  = translate(even_row, x=(brick_w + gap) / 2)
odd_row  = translate(odd_row,  z=brick_h + gap)

course   = union(even_row, odd_row)
# Stack 3 double-courses:
wall     = linear_array(course, count=3, axis='z', spacing=(brick_h + gap) * 2)
wall     = ground(wall)
```

---

### P4.7 — Concentric Nesting

*tags: mech, arch, math*

**Goal:** Parts at increasing radii sharing the same axis — bearing races, nested rings, target rings, annular patterns.

```python
r_values = [0.5, 1.0, 1.5, 2.0]
rings = [
    subtract(
        cylinder(r=r, h=0.3, segments=64),
        cylinder(r=r - 0.08, h=0.4, segments=64)   # thin-wall ring
    )
    for r in r_values
]
# Union all rings at same Z position:
target = rings[0]
for ring in rings[1:]:
    target = union(target, ring)
target = ground(target)
```

Each ring is an annular tube (P5.6). The nesting emerges from increasing r values, all centered at the origin.

---

## Family 5: Interior & Void

Creating internal space by controlled subtraction.
Core ops: `subtract`, `shell`, and spatial queries for precise positioning.

---

### P5.1 — Uniform Shell

*tags: product, arch, struct*

**Goal:** Hollow a convex solid with a uniform wall thickness — enclosure, thin-shell dome, hollow casting.

```python
# Precise method: subtract a scaled-down interior
wall_t = 0.15
body   = sphere(r=2.0)
inner  = offset(body, -(wall_t), resolution=56)   # shrink by wall thickness
hollow = subtract(body, inner)

# Fast approximation for simple convex shapes:
hollow = shell(body, thickness=0.15)
```

`shell()` is fast but uses centroid scaling (less accurate for non-spherical shapes). `offset()` + `subtract` is accurate for any shape but slower.

---

### P5.2 — Directional Hollow (Open Vessel)

*tags: art, product, arch*

**Goal:** Container open at one face — cup, bowl, bucket, room interior, socket.

```python
wall_t  = 0.15
floor_t = 0.2

body = cylinder(r=1.2, h=3.0, segments=64)

# Interior fits inside body with wall and floor offset:
interior = cylinder(r=xy_radius(body) - wall_t,
                    h=height(body) - floor_t,
                    segments=64)
interior = place_at(interior, z=bottom(body) + floor_t)

vessel = subtract(body, interior)
vessel = ground(vessel)
```

Interior is placed above the floor (`place_at`) to preserve a solid floor. The open face (top) is created naturally because the interior exits through it.

---

### P5.3 — Through-Hole

*tags: mech, arch, game*

**Goal:** A hole that passes completely through a solid — fastener hole, window opening, bearing bore.

```python
block = box(w=4, h=2, d=4)

hole  = cylinder(r=0.4, h=height(block) + 0.02, segments=32)  # +0.02 to exit both faces
hole  = center_on(hole, block)
hole  = place_at(hole, z=bottom(block) - 0.01)

result = subtract(block, hole)

# Countersunk variant (wider at top):
counter = cone(r=0.7, h=0.4, segments=32)
counter = center_on(counter, block)
counter = align_to(counter, block, 'top')
result  = subtract(result, counter)
```

Extend the cutter 0.01 past each face it exits. For a countersunk hole, stack a cone cutter on top of the cylinder cutter.

---

### P5.4 — Blind Pocket

*tags: mech, product*

**Goal:** Recessed cavity that does not break through — socket, battery compartment, counterbore, grip depression.

```python
block = box(w=4, h=3, d=4)

pocket_d = 1.5   # depth of pocket
pocket   = box(w=2.5, h=pocket_d, d=2.5)
pocket   = center_on(pocket, block)
pocket   = align_to(pocket, block, 'top')   # pocket opens at top

result = subtract(block, pocket)

# Rounded pocket (fillet cutter before subtraction):
pocket_r = cylinder(r=1.2, h=pocket_d + 0.01, segments=32)
pocket_r = center_on(pocket_r, block)
pocket_r = align_to(pocket_r, block, 'top')
result_r = subtract(block, pocket_r)
```

---

### P5.5 — Internal Channel

*tags: mech, arch*

**Goal:** A passage running through the interior of a solid — coolant channel, wire routing, hollow column interior, manifold passage.

```python
body = box(w=3, h=3, d=8)

# Straight axial channel:
channel = cylinder(r=0.3, h=height(body) + 0.02, segments=16)
channel = center_on(channel, body)
channel = place_at(channel, z=bottom(body) - 0.01)

# Cross-channel (perpendicular, exits a side face):
cross   = cylinder(r=0.2, h=width(body) + 0.02, segments=16)
cross   = rotate(cross, 90, 'y')       # align along X axis
cross   = center_on(cross, body)
cross   = translate(cross, z=center_z(body))

result = subtract(subtract(body, channel), cross)
```

Channels that must meet at a junction: route both to intersect inside the body — the boolean union of their void volumes creates the junction automatically.

---

### P5.6 — Concentric Bore

*tags: mech, arch*

**Goal:** Hollow cylinder (tube) or sleeve — pipe wall, bushing, hollow column drum.

```python
r_out = 1.0
r_in  = 0.75
h     = 4.0

# Method A: subtract inner from outer cylinder
tube = subtract(
    cylinder(r=r_out, h=h, segments=48),
    cylinder(r=r_in,  h=h + 0.02, segments=48)
)

# Method B: extrude a ring profile (equivalent, one op)
tube = extrude(ring_profile(r_outer=r_out, r_inner=r_in, segments=48), height=h)

tube = ground(tube)
```

Both methods are equivalent. Method B is simpler. Method A is more flexible when the inner radius is derived from spatial queries.

---

### P5.7 — Perimeter Groove

*tags: mech, product*

**Goal:** Circumferential channel running around a cylindrical part — O-ring groove, snap-ring groove, decorative band, grip ring.

```python
shaft_r = 1.0
shaft_h = 5.0
shaft   = cylinder(r=shaft_r, h=shaft_h, segments=64)

groove_r     = 0.08   # groove half-width (radius of torus minor)
groove_depth = 0.06   # how deep the groove cuts in

# A torus cutter centered at the groove position:
groove_z   = center_z(shaft)
groove_cut = torus(r_major=shaft_r - groove_depth, r_minor=groove_r,
                   major_segments=64, minor_segments=16)
groove_cut = translate(groove_cut, z=groove_z)

result = subtract(shaft, groove_cut)
result = ground(result)
```

For multiple grooves, use `linear_array` on the torus cutter before subtracting.

---

## Family 6: Positional Assembly

Placing parts relative to each other using spatial queries rather than hardcoded coordinates.
Core ops: `place_on`, `place_at`, `center_on`, `align_to`, spatial queries.

---

### P6.1 — Vertical Stack

*tags: arch, mech, art*

**Goal:** Chain of parts sitting on top of each other — classical orders (base, shaft, capital), tiered structures, assembly stack.

```python
base    = box(w=3.0, h=0.4, d=3.0)
shaft   = cylinder(r=0.45, h=5.0)
capital = cylinder(r=0.8, h=0.3, segments=32)
abacus  = box(w=1.8, h=0.2, d=1.8)

# Stack each piece on the one below:
shaft   = place_on(shaft,   base)
shaft   = center_on(shaft,  base)

capital = place_on(capital, shaft)
capital = center_on(capital, shaft)

abacus  = place_on(abacus,  capital)
abacus  = center_on(abacus, capital)

column  = union(union(union(base, shaft), capital), abacus)
column  = ground(column)
```

`place_on(a, b)` sets `a.bottom = b.top` exactly. No height arithmetic needed.

---

### P6.2 — XY Centering

*tags: arch, product, mech*

**Goal:** Center one part over another in the horizontal plane, leaving Z unchanged.

```python
# Capital centered on shaft:
capital = center_on(capital, shaft)          # x=True, y=True, z=False by default

# Center only on X (align left-right, not front-back):
part = center_on(part, reference, x=True, y=False)
```

`center_on()` aligns bounding box midpoints on chosen axes. For mass centroid alignment, use `centroid()` manually.

---

### P6.3 — Face Flush Mount

*tags: mech, arch, product*

**Goal:** Snap one part's face to the same plane as another's — bolt head flush to plate, cornice flush to wall face, shelf flush to column face.

```python
# Bolt head flush with top of plate:
plate    = box(w=4, h=0.5, d=4)
bolt_hex = prism(n=6, r=0.4, h=0.4)
bolt_hex = center_on(bolt_hex, plate)
bolt_hex = align_to(bolt_hex, plate, 'top')   # bolt top = plate top (recessed)

result   = subtract(plate, bolt_hex)          # or union if raised

# Part back-face flush to wall front-face:
bracket  = align_to(bracket, wall, 'front')
```

`align_to(mesh, target, face)` matches the named face of `mesh` to the same face of `target`.

---

### P6.4 — Orbital Placement

*tags: arch, mech, math*

**Goal:** Position a part at a precise radius from the Z axis, ready for radial array — or place a single satellite part at a specified orbit.

```python
# Single part at orbit radius:
r_orbit  = 5.0
satellite = cylinder(r=0.3, h=2.0)
satellite = translate(satellite, x=r_orbit)   # orbit along +X initially

# Rotate to a specific angle on the orbit (45°):
satellite = rotate(satellite, 45, 'z')

# Full radial array:
all_sats = polar_array(translate(cylinder(r=0.3, h=2.0), x=r_orbit), count=12)
```

Always express the orbit radius explicitly as a variable — it's the architectural dimension (column layout radius, bolt circle diameter / 2).

---

### P6.5 — Proportion-Locked Dimension

*tags: arch, mech, product*

**Goal:** Derive a dimension from an existing part's size rather than a fixed number — Vitruvian module scaling, wall thickness as fraction of outer, classical proportioning.

```python
# Classical column: height = 7× the base diameter (Doric module rule)
base_d = 1.0
module = base_d / 2          # 1 module = half the lower diameter (Vitruvius)
shaft_h = 14 * module        # 14 modules = 7 diameters height

shaft = loft(
    [circle_profile(module, 32), circle_profile(module * 0.83, 32)],   # slight taper
    heights=[0, shaft_h]
)

# Wall thickness as 10% of outer radius:
outer_r = xy_radius(body)
wall_t  = outer_r * 0.10
inner_r = outer_r - wall_t
```

Proportion-locked dimensions survive design changes — if you scale the base diameter, all derived dimensions update automatically.

---

### P6.6 — Cylindrical Surface Attachment

*tags: mech, product*

**Goal:** Attach a feature flush to the outside of a cylindrical body — boss, ear, handle anchor, lug.

```python
body   = cylinder(r=1.5, h=4.0, segments=64)
feature = box(w=0.5, h=0.5, d=0.8)

# Push feature so its inner face is flush to body outer surface:
r_surf   = xy_radius(body)
feature  = translate(feature, x=r_surf - 0.02)   # -0.02 to embed slightly
feature  = translate(feature, z=center_z(body) - height(feature) / 2)
feature  = center_on(feature, body, x=False, y=True)

result   = union(body, feature)
```

The slight inward overlap (−0.02) ensures the boolean closes cleanly. For a smooth transition, replace `union` with `blend_union` (P3.2).

---

### P6.7 — Embedded Part

*tags: mech, product*

**Goal:** One part set into a cavity in another — inset button, embedded sensor, recessed logo.

```python
housing = box(w=4, h=2, d=4)

# Inset circular button 0.1 below the top surface:
btn_r   = 0.4
inset_d = 0.1

cavity  = cylinder(r=btn_r + 0.02, h=inset_d + 0.01, segments=32)
cavity  = center_on(cavity, housing)
cavity  = align_to(cavity, housing, 'top')
housing = subtract(housing, cavity)

button  = cylinder(r=btn_r, h=inset_d, segments=32)
button  = center_on(button, housing)
button  = align_to(button, housing, 'top')

result  = union(housing, button)   # button sits in cavity, flush or proud
```

---

## Macro-Patterns

Composed forms built from multiple micro-patterns. Each names the micro-patterns it uses.

These are stubs — full implementations will expand as domain vocabularies are developed.

---

### M1 — Classical Column (Doric)

*tags: arch*
*uses: P1.8 (entasis taper), P2.4 (fluting), P6.1 (vertical stack), P6.5 (proportion-locked)*

```python
# Module = half the lower shaft diameter
base_d = 1.0
mod    = base_d / 2

# Shaft with entasis (3-stage loft):
shaft = loft(
    [circle_profile(mod, 32), circle_profile(mod * 1.04, 32), circle_profile(mod * 0.83, 32)],
    heights=[0, 4 * mod, 14 * mod]
)
# Fluting: 20 channels via radial boolean (P2.4)
# Capital: echinus + abacus stacked (P6.1)
# Full build: see domain vocabulary module (forthcoming)
```

---

### M2 — Turned Part with Bore (Shaft + Hole)

*tags: mech*
*uses: P1.2 (surface of revolution), P5.6 (concentric bore), P5.7 (perimeter groove), P3.1 (edge fillet)*

```python
# Knob profile (outer silhouette):
profile = [(0,0),(1.5,0),(1.8,0.5),(1.8,1.5),(1.2,2.5),(0.8,3.0),(0,3.0)]
knob    = revolve(profile, segments=64)

# Bore for shaft (P5.6):
bore    = cylinder(r=0.25, h=height(knob) + 0.02, segments=24)
bore    = center_on(bore, knob)
bore    = place_at(bore, z=bottom(knob) - 0.01)
knob    = subtract(knob, bore)

# Grip groove (P5.7) + edge fillet (P3.1) — forthcoming
knob    = ground(knob)
```

---

### M3 — Flanged Pipe Connection

*tags: mech, struct*
*uses: P5.6 (concentric bore), P1.5 (swept tube), P4.2 (radial repeat), P5.3 (through-holes)*

```python
# Flange plate with bolt circle:
flange  = cylinder(r=2.0, h=0.4, segments=64)
bore    = cylinder(r=0.8, h=0.5, segments=32)
flange  = subtract(flange, center_on(bore, flange))

bolt_h  = cylinder(r=0.15, h=0.5, segments=12)
bolt_h  = translate(bolt_h, x=1.5)
bolts   = polar_array(bolt_h, count=6)
flange  = subtract(flange, bolts)

# Pipe stub extending from flange (P1.5 / P5.6):
pipe_stub = extrude(ring_profile(r_outer=0.82, r_inner=0.7, segments=32), height=2.0)
pipe_stub = place_on(pipe_stub, flange)
pipe_stub = center_on(pipe_stub, flange)

result  = union(flange, pipe_stub)
result  = ground(result)
```

---

### M4 — Arch Opening in Wall

*tags: arch*
*uses: P1.4 (partial revolution), P2.2 (intersective clip), P5.3 (through-hole)*

```python
wall_w, wall_h, wall_d = 6.0, 4.0, 0.5
arch_r = 0.8
arch_x = 0.0   # centered

wall = box(w=wall_w, h=wall_h, d=wall_d)

# Semicircular arch cutter: cylinder lying on its side (axis along Y)
arch_barrel = cylinder(r=arch_r, h=wall_d + 0.02, segments=48)
arch_barrel = rotate(arch_barrel, 90, 'x')
arch_barrel = place_at(arch_barrel, z=wall_h * 0.45)
arch_barrel = center_on(arch_barrel, wall, y=False)
arch_barrel = translate(arch_barrel, x=arch_x)

# Rectangular door below the arch:
door = box(w=arch_r * 2, h=wall_h * 0.45, d=wall_d + 0.02)
door = center_on(door, arch_barrel, y=False)
door = place_at(door, z=0)

opening = union(arch_barrel, door)
wall    = subtract(wall, opening)
wall    = ground(wall)
```
