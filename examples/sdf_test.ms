# sdf_test.ms — compare hard union vs blend_union, and fillet on a box

# Hard union: sharp crease at join
body = cylinder(r=1.2, h=3.0, segments=48)
handle = torus(r_major=0.85, r_minor=0.18)
handle = rotate(handle, 90, 'x')
handle = translate(handle, x=xy_radius(body) + 0.18, z=center_z(body))
mug_hard = union(body, handle)
show(mug_hard, "mug_hard_union")

# Blend union: smooth join at handle-body interface
body2 = cylinder(r=1.2, h=3.0, segments=48)
handle2 = torus(r_major=0.85, r_minor=0.18)
handle2 = rotate(handle2, 90, 'x')
handle2 = translate(handle2, x=xy_radius(body2) + 0.18, z=center_z(body2))
mug_blend = blend_union(body2, handle2, radius=0.12, resolution=48)
show(mug_blend, "mug_blend_union")

# Fillet on a box — rounds the 12 edges
b = box(w=2, h=2, d=2, center=True)
show(b, "box_sharp")
b_filleted = fillet(b, radius=0.2, resolution=48)
show(b_filleted, "box_filleted")
