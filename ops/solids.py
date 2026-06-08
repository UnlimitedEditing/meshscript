import trimesh
import numpy as np


# ── Platonic Solids ───────────────────────────────────────────────────────────

def tetrahedron(r=1):
    """Regular tetrahedron. r = circumradius. 4 verts, 4 faces."""
    # Vertices of a regular tetrahedron on a unit sphere, then scaled
    verts = np.array([
        [ 0,       0,       1      ],
        [ 2*np.sqrt(2)/3, 0, -1/3  ],
        [-np.sqrt(2)/3,  np.sqrt(6)/3, -1/3],
        [-np.sqrt(2)/3, -np.sqrt(6)/3, -1/3],
    ]) * r
    faces = np.array([[0,1,2],[0,2,3],[0,3,1],[1,3,2]])
    mesh = trimesh.Trimesh(vertices=verts, faces=faces, process=True)
    trimesh.repair.fix_normals(mesh)
    return mesh


def cube(s=1):
    """Regular hexahedron (cube). s = side length."""
    return trimesh.creation.box(extents=[s, s, s])


def octahedron(r=1):
    """Regular octahedron. r = circumradius."""
    a = r / np.sqrt(2)
    verts = np.array([
        [ a,  0,  0], [-a,  0,  0],
        [ 0,  a,  0], [ 0, -a,  0],
        [ 0,  0,  a], [ 0,  0, -a],
    ])
    faces = np.array([
        [4, 0, 2], [4, 2, 1], [4, 1, 3], [4, 3, 0],
        [5, 2, 0], [5, 1, 2], [5, 3, 1], [5, 0, 3],
    ])
    mesh = trimesh.Trimesh(vertices=verts, faces=faces, process=True)
    trimesh.repair.fix_normals(mesh)
    return mesh


def dodecahedron(r=1):
    """Regular dodecahedron. r = circumradius."""
    phi = (1 + np.sqrt(5)) / 2
    a = 1 / np.sqrt(3)
    b = a / phi
    c = a * phi
    verts = np.array([
        [ a,  a,  a], [ a,  a, -a], [ a, -a,  a], [ a, -a, -a],
        [-a,  a,  a], [-a,  a, -a], [-a, -a,  a], [-a, -a, -a],
        [ 0,  b,  c], [ 0,  b, -c], [ 0, -b,  c], [ 0, -b, -c],
        [ b,  c,  0], [ b, -c,  0], [-b,  c,  0], [-b, -c,  0],
        [ c,  0,  b], [ c,  0, -b], [-c,  0,  b], [-c,  0, -b],
    ])
    scale = r / np.max(np.linalg.norm(verts, axis=1))
    verts = verts * scale
    faces = np.array([
        [0,  8,  4, 14, 12], [0, 12,  1,  9,  8],  # noqa
        [0, 16,  2, 10,  8], [0, 12, 14,  5, 17],
        [0, 17,  3, 13, 16], [4,  8, 10,  6, 18],
        [4, 18, 19,  5, 14], [1, 12, 17,  9, 11],  # fixed: 11 not full
        [2, 16, 13, 15, 10], [3, 17,  5, 19,  7],
        [3,  7, 15, 13, 11], [1, 11,  9, 17,  3],  # note: some may need fixing
        [6, 10, 15,  7, 19], [9,  1, 11,  3, 17],
    ])
    # Build via convex hull for correctness — dodecahedron verts are unique
    hull = trimesh.convex.convex_hull(verts)
    hull.apply_scale(r / np.max(np.linalg.norm(hull.vertices, axis=1)))
    trimesh.repair.fix_normals(hull)
    return hull


def icosahedron(r=1):
    """Regular icosahedron. r = circumradius. 12 verts, 20 faces."""
    return trimesh.creation.icosphere(subdivisions=0, radius=r)


# ── Archimedean / Derived Solids ──────────────────────────────────────────────

def prism(n=6, r=1, h=1):
    """Regular n-gon prism. r = circumradius of base, h = height."""
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False)
    pts = [(r * np.cos(a), r * np.sin(a)) for a in angles]
    from shapely.geometry import Polygon as SPoly
    profile = SPoly(pts)
    return trimesh.creation.extrude_polygon(profile, h)


def antiprism(n=6, r=1, h=1):
    """Regular n-antiprism. r = circumradius, h = height."""
    angles_bot = np.linspace(0, 2 * np.pi, n, endpoint=False)
    angles_top = angles_bot + np.pi / n
    verts_bot = np.column_stack([r * np.cos(angles_bot), r * np.sin(angles_bot), np.zeros(n)])
    verts_top = np.column_stack([r * np.cos(angles_top), r * np.sin(angles_top), np.full(n, h)])
    verts = np.vstack([verts_bot, verts_top])
    faces = []
    for i in range(n):
        j = (i + 1) % n
        faces.append([i, j, n + i])          # lower triangle
        faces.append([j, n + j, n + i])      # upper triangle
    # top and bottom caps as fans
    center_bot = len(verts)
    center_top = len(verts) + 1
    verts = np.vstack([verts, [[0, 0, 0]], [[0, 0, h]]])
    for i in range(n):
        j = (i + 1) % n
        faces.append([center_bot, j, i])
        faces.append([center_top, n + i, n + j])
    mesh = trimesh.Trimesh(vertices=verts, faces=np.array(faces), process=True)
    trimesh.repair.fix_normals(mesh)
    return mesh


def geodesic(r=1, frequency=2):
    """Geodesic sphere — icosahedron subdivided. frequency=1 = icosahedron, frequency=2 = 1 subdivision, etc."""
    subdivisions = max(0, frequency - 1)
    return trimesh.creation.icosphere(subdivisions=subdivisions, radius=r)
