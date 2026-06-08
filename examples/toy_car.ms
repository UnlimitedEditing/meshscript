wheel_r = 0.5
wheel_thick = 0.25

# Build components in their natural local positions.
# chassis centered at origin; cabin placed on top.
chassis = box(w=2.0, h=0.5, d=4.0, center=True)
show(chassis, "chassis")

cabin = box(w=1.7, h=0.8, d=2.0, center=True)
cabin = translate(cabin, z=top(chassis) + height(cabin)/2, y=-0.3)
show(cabin, "cabin")

body = union(chassis, cabin)
show(body, "body")

# Wheels in local space (centered at origin, lying on X axis).
def make_wheel(x, y, z):
    w = cylinder(r=wheel_r, h=wheel_thick, segments=12, center=True)
    w = rotate(w, 90, 'y')
    return translate(w, x=x, y=y, z=z)

wheel_x = width(chassis)/2 + wheel_thick/2 + 0.05
wheel_z = bottom(chassis) - wheel_r   # axle sits below chassis bottom

fl = make_wheel(-wheel_x,  1.5, wheel_z)
fr = make_wheel( wheel_x,  1.5, wheel_z)
rl = make_wheel(-wheel_x, -1.5, wheel_z)
rr = make_wheel( wheel_x, -1.5, wheel_z)
show(fl, "wheel")

wheels = union(union(fl, fr), union(rl, rr))
car = union(body, wheels)

# ground() drops the whole assembly so the lowest point sits on z=0.
# Convention: always ground the final object.
car = ground(car)
show(car, "toy_car")
