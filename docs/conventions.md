# MeshScript Conventions

## Coordinate System

**Z is up. X is width. Y is depth.**

```
       +Z (up)
        │
        │
        └──── +X (right)
       /
      /
    +Y (back)
```

- **+X / −X**: right / left
- **+Y / −Y**: back / front (positive Y goes away from viewer)
- **+Z / −Z**: up / down

This is the CAD/engineering convention (not OpenGL's Y-up convention). All primitives default to this orientation: `cylinder`, `box`, `cone` grow up along +Z.

---

## Default Placement Convention

Primitives with `center=False` (the default) sit **on the z=0 plane**, growing upward:
- `box(w, h, d)` → base at z=0, top at z=h
- `cylinder(r, h)` → base at z=0, top at z=h
- `cone(r, h)` → base at z=0, apex at z=h

Primitives that are always centered:
- `sphere(r)`, `torus(...)`, `capsule(...)`, `cube(s)` — all centered at origin
- Mathematical solids (`tetrahedron`, `octahedron`, etc.) — all centered at origin

`center=True` centers the primitive at the world origin instead.

**Implication**: when assembling parts, use spatial queries (`top()`, `bottom()`, `center_z()`, etc.) rather than arithmetic on known dimensions. This makes scripts robust if dimensions change.

---

## The `ground()` Convention

Always call `ground(mesh)` on the final assembled object before the last `show()`. This drops the assembly so its lowest point touches z=0, which is the expected position for export, preview, and critique.

```python
# Always do this on the finished object:
result = ground(final_assembly)
show(result, "final")
```

Do NOT `ground()` every intermediate part — only the final assembly, or sub-assemblies you are about to preview standalone.

---

## `show()` as Construction Checkpoint

`show(mesh, name)` renders and saves the mesh at that point in the script. Use it:
- After each major component is complete
- After each significant boolean operation
- At the end for the final result

The name becomes the output filename. Use descriptive identifiers: `"body"`, `"handle"`, `"mug_hollow"`, not `"step1"`.

```python
body = cylinder(r=1.2, h=3.0)
show(body, "body")               # checkpoint 1

handle = ...
show(handle, "handle")           # checkpoint 2

mug = union(body, handle)
show(mug, "mug_assembled")       # checkpoint 3

mug = subtract(mug, interior)
show(mug, "mug_final")           # final
```

---

## Spatial Idioms — Position Without Hardcoded Numbers

Never hardcode coordinate arithmetic like `translate(part, z=3.0)` when you could derive it from the geometry. Use spatial queries:

### Stack vertically
```python
# Place thing2 on top of thing1:
thing2 = place_on(thing2, thing1)       # thing2.bottom = thing1.top
```

### Center horizontally
```python
# Center cap over column (XY only):
cap = center_on(cap, column)
```

### Flush to a cylindrical surface
```python
# Push a bolt head flush to the outer surface of a cylinder:
r_surface = xy_radius(shaft)
bolt = translate(bolt, x=r_surface + bolt_head_r)
```

### Position relative to a face
```python
# Drop bracket's bottom to z=0.5:
bracket = place_at(bracket, z=0.5)

# Snap two parts' tops to the same level:
bracket = align_to(bracket, reference, 'top')
```

### Centering in a parent's footprint
```python
# Center label on a box face (X and Y):
label = center_on(label, box_face)
```

---

## Profile / Loft Vertex-Count Constraint

**`loft()` requires all profiles to have exactly the same number of vertices.** If they differ, loft raises a `ValueError`.

Rules:
1. `ngon_profile(n, r)` always produces exactly `n` vertices — safest choice for loft.
2. `circle_profile(r, segments)` produces `segments` vertices — specify `segments` explicitly and keep it consistent across profiles.
3. `rect_profile` and `polygon_profile` produce variable counts — avoid in loft unless you've verified the count matches.
4. `star_profile(points, ...)` produces `2 × points` vertices.

```python
# CORRECT — both have 32 vertices:
column = loft([circle_profile(1.0, 32), circle_profile(0.4, 32)], heights=[0, 4])

# CORRECT — both have 6 vertices:
hex_taper = loft([ngon_profile(6, 1.0), ngon_profile(6, 0.2)], heights=[0, 5])

# WRONG — vertex counts will differ (circle_profile default vs specified):
# loft([circle_profile(1.0), circle_profile(0.4, 16)])  ← ERROR
```

When mixing shapes in a loft, force the same vertex count by approximating both with `ngon_profile(n)` at the same `n`:
```python
# Taper from "circle" to "square" by using 32-gon approximations of both:
bot = ngon_profile(32, r=1.0)    # 32-gon ≈ circle
top = ngon_profile(4, r=0.8)     # ← only 4 verts — WRONG, counts must match
# Instead: use 32 for both:
top = ngon_profile(32, r=0.8)    # 32-gon ≈ square (at low r, looks angular enough)
```

---

## SDF Resolution Guidance

SDF ops (`blend_union`, `blend_subtract`, `fillet`, `offset`) operate on a voxel grid. Resolution is the number of voxels along the longest axis.

| Resolution | Quality | Speed | Use when |
|---|---|---|---|
| 32–40 | Coarse | Fast | Quick iteration, rough shapes |
| 48–56 | Default | Medium | Most production use |
| 64–80 | Fine | Slow | Final output, small features |

Rule of thumb: `radius` or `distance` should be at least 3× the voxel pitch (`pitch = span / resolution`). If the feature you are blending is smaller than ~3 voxels, increase resolution.

```python
# radius=0.2 on a 4-unit box → pitch ≈ 0.1 at resolution=56 → ratio=2 (borderline)
b_filleted = fillet(box(4,4,4, center=True), radius=0.2, resolution=64)

# radius=0.5 → safe at resolution=48
blend_union(a, b, radius=0.5, resolution=48)
```

---

## Boolean vs SDF — When to Use Each

| Situation | Use |
|---|---|
| Two solids join cleanly (flat faces) | `union()` |
| Carve a precise hole | `subtract()` |
| Need smooth rounded join between two surfaces | `blend_union()` |
| Need rounded edges on a single object | `fillet()` |
| Smooth cut with a blended edge | `blend_subtract()` |
| Expand/shrink surface uniformly | `offset()` |

`fillet()` and `offset()` operate on a single mesh. Blend ops require two meshes.

---

## Rotation Convention

`rotate(mesh, angle, axis)` rotates **degrees** (not radians) around the world origin.

If the mesh is not at the origin, it will orbit around the origin rather than spinning in place. To spin in place:
1. Center the mesh at origin first, rotate, then retranslate. Or:
2. If the mesh is already centered (`center=True` primitive), rotate directly.

```python
# Correct: center=True cylinder rotated about its own axis:
axle = cylinder(r=0.1, h=3.0, center=True)
axle = rotate(axle, 90, 'y')   # lies along X axis now

# Careful: a torus at origin, rotated:
ring = torus(r_major=1.0, r_minor=0.2)   # lies in XY at origin
ring = rotate(ring, 90, 'x')             # now upright in XZ plane
```

---

## `polar_array` Radius Convention

`polar_array(mesh, count, axis)` rotates copies around the world origin. The mesh must already be at the correct orbital radius before calling `polar_array`.

```python
# Place one column at r=5 from center, then array 8 copies:
col = cylinder(r=0.3, h=4.0)
col = translate(col, x=5.0)           # position at radius 5
cols = polar_array(col, count=8)       # 8 columns around Z axis
```

---

## Functional Style — Immutable Operations

Every op returns a **new** mesh. The original is never modified. This means operations must be reassigned:

```python
mesh = rotate(mesh, 45, 'z')   # correct — reassign
rotate(mesh, 45, 'z')          # wrong — result discarded
```

Variable names are mutable — reassign freely through a construction chain.
