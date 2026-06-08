import numpy as np


def circle_profile(r=1, segments=32):
    from shapely.geometry import Point
    return Point(0, 0).buffer(r, resolution=max(segments // 4, 4))


def rect_profile(w=1, h=1):
    from shapely.geometry import box
    return box(-w / 2, -h / 2, w / 2, h / 2)


def polygon_profile(points):
    """Arbitrary polygon from a list of (x, y) tuples."""
    from shapely.geometry import Polygon
    return Polygon(points)


def ngon_profile(n, r=1.0):
    """
    Regular n-sided polygon (n-gon) centered at origin.

    n : number of sides / vertices (3=triangle, 4=square, 6=hexagon, …)
    r : circumradius (vertex-to-centre distance)

    Because the vertex count is exact and predictable, ngon_profile is
    the right choice for loft() profiles — all profiles in a loft must
    have the same vertex count.

    Example
    -------
    # Hexagonal column that tapers to a triangle tip
    hex_base = ngon_profile(6, r=1.0)
    tri_top  = ngon_profile(3, r=0.5)
    # Note: n must match! For tapers keep the same n.
    column   = loft([ngon_profile(6, 1.0), ngon_profile(6, 0.3)], heights=[0, 4])
    """
    from shapely.geometry import Polygon
    angles = np.linspace(np.pi / 2, np.pi / 2 + 2 * np.pi, int(n), endpoint=False)
    pts = [(float(r * np.cos(a)), float(r * np.sin(a))) for a in angles]
    return Polygon(pts)


def ring_profile(r_outer=1, r_inner=0.5, segments=32):
    return circle_profile(r_outer, segments).difference(circle_profile(r_inner, segments))


def star_profile(points=5, r_outer=1.0, r_inner=0.4):
    from shapely.geometry import Polygon
    angles_outer = np.linspace(np.pi / 2, np.pi / 2 + 2 * np.pi, points, endpoint=False)
    angles_inner = angles_outer + np.pi / points
    pts = []
    for ao, ai in zip(angles_outer, angles_inner):
        pts.append((r_outer * np.cos(ao), r_outer * np.sin(ao)))
        pts.append((r_inner * np.cos(ai), r_inner * np.sin(ai)))
    return Polygon(pts)
