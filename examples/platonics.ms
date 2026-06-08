# platonics.ms — all five Platonic solids + derived, laid out in a row

gap = 2.8

t = tetrahedron(r=1)
t = place_at(t, z=0)
show(t, "tetrahedron")

c = cube(s=1.6)
c = place_at(c, z=0)
c = translate(c, x=gap)
show(c, "cube")

o = octahedron(r=1)
o = translate(o, x=gap * 2)
show(o, "octahedron")

d = dodecahedron(r=1)
d = translate(d, x=gap * 3)
show(d, "dodecahedron")

i = icosahedron(r=1)
i = translate(i, x=gap * 4)
show(i, "icosahedron")

p = prism(n=6, r=1, h=1.6)
p = place_at(p, z=0)
p = translate(p, x=gap * 5)
show(p, "hex_prism")

g = geodesic(r=1, frequency=3)
g = translate(g, x=gap * 6)
show(g, "geodesic_f3")
