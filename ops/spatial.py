import numpy as np
import trimesh


# ── Queries ──────────────────────────────────────────────────────────────────

def bounds(mesh):
    """[[min_x, min_y, min_z], [max_x, max_y, max_z]]"""
    return mesh.bounds.tolist()

def top(mesh):
    """Max Z."""
    return float(mesh.bounds[1][2])

def bottom(mesh):
    """Min Z."""
    return float(mesh.bounds[0][2])

def front(mesh):
    """Min Y."""
    return float(mesh.bounds[0][1])

def back(mesh):
    """Max Y."""
    return float(mesh.bounds[1][1])

def left(mesh):
    """Min X."""
    return float(mesh.bounds[0][0])

def right(mesh):
    """Max X."""
    return float(mesh.bounds[1][0])

def height(mesh):
    """Z extent."""
    b = mesh.bounds
    return float(b[1][2] - b[0][2])

def width(mesh):
    """X extent."""
    b = mesh.bounds
    return float(b[1][0] - b[0][0])

def depth(mesh):
    """Y extent."""
    b = mesh.bounds
    return float(b[1][1] - b[0][1])

def center_x(mesh):
    b = mesh.bounds
    return float((b[0][0] + b[1][0]) / 2)

def center_y(mesh):
    b = mesh.bounds
    return float((b[0][1] + b[1][1]) / 2)

def center_z(mesh):
    b = mesh.bounds
    return float((b[0][2] + b[1][2]) / 2)

def centroid(mesh):
    """Mass centroid as [x, y, z]."""
    return mesh.centroid.tolist()

def xy_radius(mesh):
    """Max distance from Z axis across all vertices — bounding radius in XY."""
    v = mesh.vertices
    return float(np.max(np.sqrt(v[:, 0] ** 2 + v[:, 1] ** 2)))


# ── Alignment ─────────────────────────────────────────────────────────────────

def ground(mesh):
    """Translate mesh so its lowest point sits exactly on z=0.
    Convention: call ground() on any finished object before show()."""
    return place_at(mesh, z=0)


def place_on(mesh, target):
    """Translate mesh so its bottom sits on top of target."""
    gap = top(target) - bottom(mesh)
    m = mesh.copy()
    m.apply_translation([0, 0, gap])
    return m

def place_at(mesh, z):
    """Translate mesh so its bottom is at z."""
    m = mesh.copy()
    m.apply_translation([0, 0, z - bottom(mesh)])
    return m

def center_on(mesh, target, x=True, y=True, z=False):
    """Align mesh centroid to target centroid on chosen axes."""
    m = mesh.copy()
    dx = (center_x(target) - center_x(mesh)) if x else 0
    dy = (center_y(target) - center_y(mesh)) if y else 0
    dz = (center_z(target) - center_z(mesh)) if z else 0
    m.apply_translation([dx, dy, dz])
    return m

def convex_hull(*meshes):
    """
    Convex hull of one or more meshes.

    convex_hull(mesh)           — hull of a single mesh
    convex_hull(a, b, c, ...)   — hull of all vertices combined

    Produces the tightest convex shape that contains all input geometry.
    Useful for:
    - Simplifying complex geometry for collision purposes
    - Wrapping multiple objects in a single convex skin
    - Generating convex approximations for physics engines

    Example
    -------
    a = sphere(r=0.5)
    b = translate(sphere(r=0.3), x=2.0)
    wrap = convex_hull(a, b)   # capsule-like convex hull of both
    """
    if len(meshes) == 0:
        raise ValueError("convex_hull requires at least one mesh")
    verts = np.vstack([m.vertices for m in meshes])
    return trimesh.convex.convex_hull(verts)


def align_to(mesh, target, face):
    """Snap a face of mesh flush to the same face of target.
    face: 'top' | 'bottom' | 'left' | 'right' | 'front' | 'back'
    """
    m = mesh.copy()
    getters = {
        'top':    (top,    top),
        'bottom': (bottom, bottom),
        'left':   (left,   left),
        'right':  (right,  right),
        'front':  (front,  front),
        'back':   (back,   back),
    }
    mesh_fn, tgt_fn = getters[face]
    axis = {'top': 2, 'bottom': 2, 'left': 0, 'right': 0, 'front': 1, 'back': 1}[face]
    delta = tgt_fn(target) - mesh_fn(mesh)
    offset = [0, 0, 0]
    offset[axis] = delta
    m.apply_translation(offset)
    return m
