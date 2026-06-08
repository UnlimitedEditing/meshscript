# MeshScript Op Reference

All ops are available in the script namespace without import.
Every op returns a `Trimesh` object unless noted otherwise.
Coordinate system: **X = width (left/right), Y = depth (front/back), Z = height (up/down).**

---

## Primitives

### `box(w=1, h=1, d=1, center=False)`
Rectangular box. `w`=X extent, `h`=Z extent (height), `d`=Y extent.
`center=False` (default): base sits on z=0, grows up. `center=True`: centered at origin.
```python
slab = box(w=4, h=0.2, d=3)           # flat slab on z=0
cube = box(w=1, h=1, d=1, center=True) # centered at origin
```

### `sphere(r=1, subdivisions=3)`
Icosphere. `subdivisions` controls tessellation density (3=smooth, 1=coarse).
Always centered at origin.
```python
ball = sphere(r=0.5)
rough = sphere(r=1, subdivisions=1)  # low-poly look
```

### `cylinder(r=1, h=1, segments=32, center=False)`
Upright cylinder. `segments` = sides (32=smooth, 8=octagonal).
`center=False`: base at z=0. `center=True`: centered at origin.
```python
post = cylinder(r=0.05, h=2.0)
axle = cylinder(r=0.2, h=3.0, center=True)
```

### `cone(r=1, h=1, segments=32, center=False)`
Cone with apex at top. Base at z=0 (when `center=False`).
```python
spike = cone(r=0.3, h=1.5)
```

### `torus(r_major=1, r_minor=0.3, major_segments=32, minor_segments=16)`
Ring. `r_major`=ring radius (center-to-tube-center), `r_minor`=tube radius.
Lies in XY plane, centered at origin.
```python
ring = torus(r_major=2.0, r_minor=0.4)
```

### `wedge(w=1, h=1, d=1)`
Right-angle triangular prism. Triangle in XZ plane (width × height), depth along Y.
```python
ramp = wedge(w=2, h=1, d=3)
```

### `capsule(r=0.5, h=1, segments=32)`
Cylinder with hemispherical caps. `h`=total height including caps.
Always centered at origin.
```python
pill = capsule(r=0.3, h=2.0)
```

---

## Booleans

All booleans take two meshes and return one merged mesh.
Uses manifold3d (fast, no external deps) when available; falls back to trimesh boolean.

### `union(a, b)`
Merge two meshes. Hard crease at the join. For smooth join, use `blend_union`.
```python
body = union(chassis, cabin)
```

### `subtract(a, b)`
Remove `b` from `a`. `b`'s volume is carved out of `a`. Hard edge.
```python
hollow = subtract(box(2, 2, 2, center=True), box(1.6, 1.6, 1.6, center=True))
```

### `intersect(a, b)`
Keep only the volume where `a` and `b` overlap.
```python
clipped = intersect(sphere(r=1.5), box(w=2, h=2, d=2, center=True))
```

---

## Transforms

All transforms return a **copy** of the mesh — the original is not modified.

### `translate(mesh, x=0, y=0, z=0)`
Move mesh by offset in world space.
```python
raised = translate(part, z=top(base))
```

### `rotate(mesh, angle, axis='z')`
Rotate `angle` degrees around `axis`. `axis`: `'x'`, `'y'`, `'z'`.
Rotation is about the world origin, not the mesh center.
```python
handle = rotate(torus(...), 90, 'x')   # lay torus flat → upright ring
```

### `scale(mesh, x=1, y=1, z=1)`
Non-uniform scale. Use to stretch or squash along any axis.
```python
squashed = scale(sphere(r=1), x=1, y=1, z=0.5)  # oblate spheroid
```

### `mirror(mesh, axis='x')`
Reflect across the plane perpendicular to `axis` through the world origin.
```python
right_half = mirror(left_half, axis='x')
```

### `linear_array(mesh, count, axis='x', spacing=1.0)`
Duplicate mesh `count` times along `axis` with given `spacing` between copies.
```python
fence = linear_array(post, count=8, axis='y', spacing=1.2)
```

### `polar_array(mesh, count, axis='z')`
Duplicate mesh `count` times, evenly distributed around `axis` (360°/count each).
Rotation is around world origin — position the mesh at the correct radius first.
```python
columns = polar_array(column, count=6, axis='z')
```

---

## Modifiers

### `shell(mesh, thickness)`
Hollow out a solid by subtracting a scaled-down inner copy.
Works best on convex shapes. `thickness` in world units.
```python
hollow_sphere = shell(sphere(r=2), thickness=0.15)
```

### `extrude(profile, height)`
Extrude a Shapely Polygon vertically (along Z) by `height`.
Use profiles from the Profiles section, or Shapely geometry directly.
```python
slab = extrude(rect_profile(3, 1), height=0.5)
hex_rod = extrude(ngon_profile(6, r=0.5), height=4)
```

### `revolve(profile_points, angle=360, segments=64)`
Revolve a 2D profile around the Z axis. `profile_points`: list of `(r, z)` tuples, `r >= 0`.
`angle=360`: full revolution. `angle<360`: partial sweep (open solid).
```python
# Vase profile — wide base, narrow neck, flared rim
profile = [(0,0),(1.2,0),(1.0,1),(0.6,2.5),(0.8,3),(0.7,3.5)]
vase = revolve(profile, segments=64)
```

---

## Profiles

Profiles are 2D cross-sections (Shapely Polygons) used with `extrude()`, `sweep()`, and `loft()`.
**Critical constraint for `loft()`:** all profiles must have the same vertex count. Use `ngon_profile(n)` or `circle_profile(r, segments)` with an explicit segment count to guarantee this.

### `circle_profile(r=1, segments=32)`
Circular profile. `segments` controls how many vertices the polygon has.
```python
tube_cs = circle_profile(r=0.1, segments=16)
```

### `rect_profile(w=1, h=1)`
Rectangular profile, centered at origin. `w`=X, `h`=Y.
```python
rail_cs = rect_profile(w=0.2, h=0.1)
```

### `polygon_profile(points)`
Arbitrary polygon from a list of `(x, y)` tuples.
```python
L = polygon_profile([(0,0),(0,1),(0.1,1),(0.1,0.1),(0.5,0.1),(0.5,0)])
```

### `ngon_profile(n, r=1.0)`
Regular n-sided polygon. `n=3` → triangle, `n=4` → square, `n=6` → hexagon.
**Preferred for loft**: vertex count is exactly `n` and predictable.
```python
hex = ngon_profile(6, r=1.0)
tri = ngon_profile(3, r=0.5)
```

### `ring_profile(r_outer=1, r_inner=0.5, segments=32)`
Annular (donut-shaped) profile. Extrude it to get a tube wall.
```python
pipe_wall = extrude(ring_profile(r_outer=0.5, r_inner=0.4), height=3)
```

### `star_profile(points=5, r_outer=1.0, r_inner=0.4)`
Star polygon. `points`=number of points, `r_outer`/`r_inner`=tip and valley radii.
```python
star = extrude(star_profile(points=5, r_outer=1.0, r_inner=0.45), height=0.3)
```

---

## Mathematical Solids

### `tetrahedron(r=1)`
Regular tetrahedron. `r`=circumradius. 4 faces.
```python
t = tetrahedron(r=1.5)
```

### `cube(s=1)`
Regular cube (hexahedron). `s`=side length. Centered at origin.
```python
c = cube(s=2)
```

### `octahedron(r=1)`
Regular octahedron. `r`=circumradius.
```python
o = octahedron(r=1.2)
```

### `dodecahedron(r=1)`
Regular dodecahedron. `r`=circumradius. Built via convex hull for robustness.
```python
d = dodecahedron(r=1.0)
```

### `icosahedron(r=1)`
Regular icosahedron. `r`=circumradius. 12 verts, 20 faces.
```python
i = icosahedron(r=1.0)
```

### `prism(n=6, r=1, h=1)`
Regular n-gon prism. `n`=sides, `r`=circumradius of base, `h`=height.
```python
hex_prism = prism(n=6, r=1.0, h=2.0)
```

### `antiprism(n=6, r=1, h=1)`
Regular n-antiprism: twisted prism with triangular lateral faces.
```python
ap = antiprism(n=5, r=1.0, h=0.8)
```

### `geodesic(r=1, frequency=2)`
Geodesic sphere by icosahedron subdivision.
`frequency=1` = icosahedron (20 faces), `frequency=2` = 80 faces, `frequency=3` = 320 faces.
```python
dome = geodesic(r=3.0, frequency=3)
```

---

## SDF Operations

SDF ops voxelise the mesh, operate in signed-distance-field space, and reconstruct via marching cubes.
Slower than polygon booleans (~1–5 seconds) but produces smooth blends and rounded edges.
`resolution` controls voxel grid density: 40=fast/coarse, 56=default, 80=fine.

### `blend_union(mesh_a, mesh_b, radius, resolution=48)`
Smooth boolean union. The join between meshes blends over a zone of width `radius`.
Use instead of `union()` wherever a hard crease would look wrong.
```python
body_with_handle = blend_union(body, handle, radius=0.12, resolution=48)
```

### `blend_subtract(mesh_a, mesh_b, radius, resolution=48)`
Smooth boolean subtract. The cut edge blends rather than being sharp.
```python
carved = blend_subtract(block, cutter, radius=0.08)
```

### `fillet(mesh, radius, resolution=56)`
Round convex edges. Uses morphological open (erode then dilate).
Rounds all convex corners/edges uniformly — there is no per-edge selection.
`radius` should be smaller than the thinnest feature you want to preserve.
```python
b = box(w=2, h=2, d=2, center=True)
b_rounded = fillet(b, radius=0.15, resolution=56)
```

### `offset(mesh, distance, resolution=48)`
Expand (`distance > 0`) or shrink (`distance < 0`) the mesh surface uniformly.
Expanding a box produces a rounded cuboid. Equivalent to a Minkowski sum with a sphere.
```python
bloated = offset(mesh, 0.1)   # expand by 0.1 units all around
inset   = offset(mesh, -0.05) # shrink by 0.05 units
```

---

## Sweep & Path Ops

### `sweep(profile, path, closed=False)`
Extrude a 2D profile along a 3D polyline path using a rotation-minimizing frame (no twist).
`profile`: Shapely Polygon or (N, 2) array.
`path`: list or (M, 3) array of 3D points (at least 2).
`closed=True`: connect last cross-section back to first (for loop-shaped sweeps).
```python
rail = sweep(rect_profile(0.2, 0.1), arc_path(r=1.0, angle=90, plane='xz'))
```

### `pipe(path, r=0.1, segments=16)`
Circular tube swept along a 3D path. Shorthand for `sweep(circle_profile(...), path)`.
```python
elbow = pipe(arc_path(r=2.0, angle=90, plane='xz'), r=0.3, segments=16)
```

### `loft(profiles, heights=None, cap=True)`
Blend between a sequence of 2D profiles at increasing Z heights.
**All profiles must have the same vertex count** — use `ngon_profile(n)` or `circle_profile(r, n)` with matching `n`.
`heights`: list of Z values (default: 0, 1, 2, …). `cap=True`: add end caps.
```python
# Taper from circle to circle (same segment count!)
column = loft([circle_profile(1.0, 32), circle_profile(0.4, 32)], heights=[0, 4])

# Taper from hexagon to hexagon (use ngon_profile for exact vertex count)
hex_taper = loft([ngon_profile(6, 1.0), ngon_profile(6, 0.2)], heights=[0, 5])
```

### `arc_path(r=1.0, angle=180, segments=32, plane='xy')`
Returns `(N, 3)` array: a circular arc path.
`plane`: `'xy'`, `'xz'`, or `'yz'` — which plane the arc lies in.
Use as input to `sweep()` or `pipe()`.
```python
elbow_path = arc_path(r=2.0, angle=90, plane='xz')
```

### `helix_path(r=1.0, pitch=0.5, h=3.0, segments=64)`
Returns `(N, 3)` array: a helical centreline.
`r`=helix radius, `pitch`=vertical rise per turn, `h`=total height.
Use as input to `sweep()` for a non-circular cross-section spring.
```python
path = helix_path(r=1.0, pitch=0.5, h=4.0, segments=48)
coil = sweep(rect_profile(0.1, 0.05), path)
```

### `helix(r=1.0, pitch=0.5, h=3.0, tube_r=0.05, segments=64, tube_segments=12)`
Helical tube (spring, coil, screw-thread approximation). Combines `helix_path` + `sweep`.
```python
spring = helix(r=0.8, pitch=0.4, h=3.0, tube_r=0.08)
```

---

## Spatial Queries

These return numbers (floats or lists), not meshes. Use them to position geometry precisely without hardcoding coordinates.

### `bounds(mesh)` → `[[min_x,min_y,min_z],[max_x,max_y,max_z]]`
Full bounding box as nested list.

### `top(mesh)` → float
Maximum Z of the mesh.

### `bottom(mesh)` → float
Minimum Z of the mesh.

### `front(mesh)` → float
Minimum Y of the mesh.

### `back(mesh)` → float
Maximum Y of the mesh.

### `left(mesh)` → float
Minimum X of the mesh.

### `right(mesh)` → float
Maximum X of the mesh.

### `height(mesh)` → float
Z extent (top − bottom).

### `width(mesh)` → float
X extent (right − left).

### `depth(mesh)` → float
Y extent (back − front).

### `center_x(mesh)` → float
X midpoint of bounding box.

### `center_y(mesh)` → float
Y midpoint of bounding box.

### `center_z(mesh)` → float
Z midpoint of bounding box.

### `centroid(mesh)` → `[x, y, z]`
Volume centroid (mass center). Different from bounding-box center for asymmetric shapes.

### `xy_radius(mesh)` → float
Maximum distance from the Z axis across all vertices. Useful for placing things flush to a cylindrical surface.

---

## Spatial Alignment

These return a **copy** of the mesh, repositioned.

### `ground(mesh)`
Translate mesh so its lowest point sits exactly on z=0.
**Convention:** always call `ground()` on the final assembled object before `show()`.
```python
car = ground(assemble(chassis, wheels, cabin))
show(car, "toy_car")
```

### `place_on(mesh, target)`
Move `mesh` so its bottom sits on top of `target`.
```python
capital = place_on(capital_block, column_shaft)
```

### `place_at(mesh, z)`
Move `mesh` so its bottom is at the given Z value.
```python
shelf = place_at(shelf, z=1.5)
```

### `center_on(mesh, target, x=True, y=True, z=False)`
Align `mesh`'s bounding-box center to `target`'s center on chosen axes.
`z=False` by default — usually you want XY centering only.
```python
cap = center_on(sphere(r=1.1), column)   # center cap over column in XY
```

### `align_to(mesh, target, face)`
Snap a named face of `mesh` flush to the same face of `target`.
`face`: `'top'`, `'bottom'`, `'left'`, `'right'`, `'front'`, `'back'`.
```python
bolt_head = align_to(bolt_head, shaft, 'bottom')
```

### `convex_hull(*meshes)`
Convex hull of one or more meshes (combines all vertices).
```python
wrap = convex_hull(sphere_a, sphere_b)   # capsule-like hull
```

---

## Checkpoint

### `show(mesh, name)`
Render the mesh and save it as a checkpoint named `name`.
Use after each meaningful construction step. The name becomes the output filename.
`name` should be a short identifier (letters, digits, underscores). No extension needed.
```python
show(body, "body")
show(handle, "handle")
show(mug, "mug_final")
```
