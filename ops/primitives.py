import trimesh
import numpy as np


def box(w=1, h=1, d=1, center=False):
    # w=width (X), h=height (Z, up), d=depth (Y)
    # center=False: sits on z=0, grows up. center=True: centered at origin.
    mesh = trimesh.creation.box(extents=[w, d, h])
    if not center:
        mesh.apply_translation([0, 0, h / 2])
    return mesh


def sphere(r=1, subdivisions=3):
    return trimesh.creation.icosphere(subdivisions=subdivisions, radius=r)


def cylinder(r=1, h=1, segments=32, center=False):
    # center=False: sits on z=0, grows up. center=True: centered at origin.
    mesh = trimesh.creation.cylinder(radius=r, height=h, sections=segments)
    if not center:
        mesh.apply_translation([0, 0, h / 2])
    return mesh


def cone(r=1, h=1, segments=32, center=False):
    # center=False: base at z=0, apex at z=h. center=True: centered at origin.
    mesh = trimesh.creation.cone(radius=r, height=h, sections=segments)
    if not center:
        mesh.apply_translation([0, 0, h / 2])
    return mesh


def torus(r_major=1, r_minor=0.3, major_segments=32, minor_segments=16):
    theta = np.linspace(0, 2 * np.pi, major_segments, endpoint=False)
    phi = np.linspace(0, 2 * np.pi, minor_segments, endpoint=False)
    verts = []
    for t in theta:
        for p in phi:
            x = (r_major + r_minor * np.cos(p)) * np.cos(t)
            y = (r_major + r_minor * np.cos(p)) * np.sin(t)
            z = r_minor * np.sin(p)
            verts.append([x, y, z])
    verts = np.array(verts)
    n, m = major_segments, minor_segments
    faces = []
    for i in range(n):
        for j in range(m):
            a = i * m + j
            b = i * m + (j + 1) % m
            c = ((i + 1) % n) * m + j
            d_ = ((i + 1) % n) * m + (j + 1) % m
            faces += [[a, b, d_], [a, d_, c]]
    mesh = trimesh.Trimesh(vertices=verts, faces=np.array(faces), process=True)
    trimesh.repair.fix_normals(mesh)
    return mesh


def wedge(w=1, h=1, d=1):
    # Right-angle triangular prism
    verts = np.array([
        [0, 0, 0], [w, 0, 0], [0, h, 0],
        [0, 0, d], [w, 0, d], [0, h, d],
    ], dtype=float)
    faces = np.array([
        [0, 2, 1], [3, 4, 5],
        [0, 1, 4], [0, 4, 3],
        [1, 2, 5], [1, 5, 4],
        [0, 3, 5], [0, 5, 2],
    ])
    mesh = trimesh.Trimesh(vertices=verts, faces=faces, process=True)
    trimesh.repair.fix_normals(mesh)
    return mesh


def capsule(r=0.5, h=1, segments=32):
    return trimesh.creation.capsule(radius=r, height=h, count=[segments // 2, segments])
