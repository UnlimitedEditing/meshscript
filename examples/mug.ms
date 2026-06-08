# mug.ms — rebuilt using spatial ops (no hardcoded coordinate arithmetic)

body = cylinder(r=1.2, h=3.0, segments=64)
show(body, "body")

# Handle: torus rotated into XZ plane, then positioned relative to body
handle = torus(r_major=0.85, r_minor=0.18, major_segments=40, minor_segments=16)
handle = rotate(handle, 90, 'x')
handle = translate(handle, x=xy_radius(body) + 0.18, z=center_z(body))
show(handle, "handle")

mug = union(body, handle)
show(mug, "mug_solid")

# Hollow: leave 0.15 wall, 0.2 base — expressed as intent, not magic numbers
wall = 0.15
base = 0.2
interior = cylinder(r=xy_radius(body) - wall, h=height(body) - base, segments=64)
interior = place_at(interior, z=bottom(body) + base)
mug = subtract(mug, interior)
show(mug, "mug_hollow")
