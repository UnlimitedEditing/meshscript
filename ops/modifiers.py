import trimesh
import numpy as np


def shell(mesh, thickness):
    # Approximate: subtract a centroid-scaled inner copy.
    # Works well for convex shapes; less accurate for complex topology.
    bounds = mesh.bounds
    size = bounds[1] - bounds[0]
    min_dim = np.min(size[size > 0])
    factor = 1 - (2 * thickness / min_dim)
    if factor <= 0:
        raise ValueError(f"thickness {thickness} is too large for this mesh (min dimension {min_dim:.3f})")
    inner = mesh.copy()
    c = mesh.centroid
    inner.apply_translation(-c)
    inner.apply_transform(np.diag([factor, factor, factor, 1.0]))
    inner.apply_translation(c)
    from .booleans import subtract
    return subtract(mesh, inner)


def extrude(profile, height):
    # profile: shapely Polygon
    return trimesh.creation.extrude_polygon(profile, height)


def revolve(profile_points, angle=360, segments=64):
    # profile_points: list of (r, z) tuples — r >= 0, revolves around Z axis
    pts = np.array(profile_points, dtype=float)
    step = np.radians(angle) / (segments if angle < 360 else segments)
    angles = np.linspace(0, np.radians(angle), segments + 1 if angle < 360 else segments, endpoint=(angle < 360))
    n = len(pts)
    verts = []
    for a in angles:
        for r, z in pts:
            verts.append([r * np.cos(a), r * np.sin(a), z])
    verts = np.array(verts)
    m = len(angles)
    faces = []
    for i in range(m - 1):
        for j in range(n - 1):
            a = i * n + j
            b = i * n + j + 1
            c = (i + 1) * n + j
            d = (i + 1) * n + j + 1
            faces += [[a, b, d], [a, d, c]]
    if angle >= 360:
        for j in range(n - 1):
            a = (m - 1) * n + j
            b = (m - 1) * n + j + 1
            c, d = j, j + 1
            faces += [[a, b, d], [a, d, c]]
    return trimesh.Trimesh(vertices=verts, faces=np.array(faces), process=True)
