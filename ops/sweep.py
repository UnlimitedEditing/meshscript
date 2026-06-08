"""
Path-based construction ops: sweep, loft, pipe, helix.

sweep — extrude a 2D profile along any 3D polyline using trimesh's
        rotation-minimising frame (no twist artefacts on curved paths).

loft  — blend between a sequence of 2D profiles at different heights.
        All profiles must have the same vertex count; use polygon_profile(n)
        to get consistent counts when mixing shapes.
"""

import numpy as np
import trimesh
from shapely.geometry import Polygon as ShapelyPolygon


# ── Internal helpers ──────────────────────────────────────────────────────────

def _to_pts(profile):
    """Return (N, 2) float array from a shapely Polygon or array-like."""
    if isinstance(profile, ShapelyPolygon):
        pts = np.array(profile.exterior.coords, dtype=float)[:-1]  # drop closing dup
    else:
        pts = np.asarray(profile, dtype=float)
    if pts.ndim != 2 or pts.shape[1] != 2:
        raise ValueError(f"Profile must be (N, 2), got shape {pts.shape}")
    return pts


def _as_shapely(profile):
    """Return shapely Polygon from profile (needed by trimesh.creation.sweep_polygon)."""
    if isinstance(profile, ShapelyPolygon):
        return profile
    pts = _to_pts(profile)
    return ShapelyPolygon(pts)


# ── Public ops ────────────────────────────────────────────────────────────────

def sweep(profile, path, closed=False):
    """
    Extrude a 2D profile along a 3D path.

    profile : shapely Polygon (from circle_profile, rect_profile, …) or (N, 2) array
    path    : list or (M, 3) array of 3D centreline points (at least 2)
    closed  : connect the last cross-section back to the first (for loops)

    Returns Trimesh.

    Example
    -------
    # L-shaped rail
    path = arc_path(r=1.0, angle=90, plane='xz')
    rail = sweep(rect_profile(0.2, 0.1), path)
    """
    poly = _as_shapely(profile)
    path_arr = np.asarray(path, dtype=float)
    if path_arr.ndim != 2 or path_arr.shape[1] != 3:
        raise ValueError(f"path must be (M, 3), got shape {path_arr.shape}")
    if len(path_arr) < 2:
        raise ValueError("sweep path needs at least 2 points")

    mesh = trimesh.creation.sweep_polygon(poly, path_arr, cap=not closed)
    trimesh.repair.fix_normals(mesh)
    return mesh


def pipe(path, r=0.1, segments=16):
    """
    Circular tube swept along a 3D path.

    path     : list or (M, 3) array of centreline points
    r        : tube radius
    segments : sides on the circular cross-section (8 = octagonal, 32 = smooth)

    Example
    -------
    # Bent pipe
    path = arc_path(r=2.0, angle=90, plane='xz')
    elbow = pipe(path, r=0.3, segments=16)
    """
    from .profiles import circle_profile
    return sweep(circle_profile(r, segments), path)


def loft(profiles, heights=None, cap=True):
    """
    Blend between a sequence of 2D profiles at increasing heights.

    profiles : list of shapely Polygons or (N, 2) arrays.
               All profiles must have the *same vertex count* — use
               polygon_profile(n, …) to control this explicitly.
    heights  : list of Z values (default: 0, 1, 2, …)
    cap      : triangulate top/bottom end caps (default True)

    Returns Trimesh.

    Example
    -------
    # Taper from circle to square
    bot = circle_profile(1.0, 32)
    top = polygon_profile(32, 0.8)   # 32-sided approximation of square
    column = loft([bot, top], heights=[0, 4])
    """
    if len(profiles) < 2:
        raise ValueError("loft needs at least 2 profiles")
    if heights is None:
        heights = list(range(len(profiles)))
    if len(heights) != len(profiles):
        raise ValueError("profiles and heights must have the same length")

    loops = [_to_pts(p) for p in profiles]
    n = loops[0].shape[0]
    if not all(loop.shape[0] == n for loop in loops):
        counts = [loop.shape[0] for loop in loops]
        raise ValueError(
            f"All profiles must have the same vertex count. Got: {counts}. "
            "Tip: use polygon_profile(n, r) to match counts across shapes."
        )

    m = len(loops)

    # ── Vertices ──────────────────────────────────────────────────────────────
    verts = []
    for loop, z in zip(loops, heights):
        for x, y in loop:
            verts.append([x, y, float(z)])
    verts = np.array(verts)

    # ── Side faces (quads → 2 triangles) ──────────────────────────────────────
    faces = []
    for layer in range(m - 1):
        base = layer * n
        top  = (layer + 1) * n
        for i in range(n):
            j = (i + 1) % n
            faces.append([base + i, base + j, top  + i])
            faces.append([base + j, top  + j, top  + i])

    # ── End caps (fan triangulation — correct for convex profiles) ────────────
    if cap:
        # Bottom cap: normal points downward → reverse winding
        for i in range(1, n - 1):
            faces.append([0, i + 1, i])
        # Top cap: normal points upward → forward winding
        tb = (m - 1) * n
        for i in range(1, n - 1):
            faces.append([tb, tb + i, tb + i + 1])

    mesh = trimesh.Trimesh(vertices=verts, faces=np.array(faces), process=False)
    trimesh.repair.fix_normals(mesh)
    return mesh


# ── Path generators ───────────────────────────────────────────────────────────

def arc_path(r=1.0, angle=180, segments=32, plane='xy'):
    """
    Circular arc path as (N, 3) array.

    r        : arc radius
    angle    : arc extent in degrees (360 = full circle)
    segments : number of path points
    plane    : 'xy' | 'xz' | 'yz'

    Example
    -------
    elbow_path = arc_path(r=2.0, angle=90, plane='xz')
    elbow = pipe(elbow_path, r=0.3)
    """
    t = np.linspace(0, np.radians(angle), max(segments, 2))
    c, s = r * np.cos(t), r * np.sin(t)
    z = np.zeros_like(t)
    if plane == 'xy':
        return np.column_stack([c, s, z])
    elif plane == 'xz':
        return np.column_stack([c, z, s])
    elif plane == 'yz':
        return np.column_stack([z, c, s])
    else:
        raise ValueError(f"plane must be 'xy', 'xz', or 'yz', got {plane!r}")


def helix_path(r=1.0, pitch=0.5, h=3.0, segments=64):
    """
    Helical centreline path as (N, 3) array.

    r        : helix radius (axis-to-centre distance)
    pitch    : vertical rise per full turn
    h        : total height
    segments : path points per full turn
    """
    n_turns = h / pitch
    n_pts   = max(4, int(segments * n_turns))
    t = np.linspace(0, 2 * np.pi * n_turns, n_pts)
    x = r * np.cos(t)
    y = r * np.sin(t)
    z = (t / (2 * np.pi)) * pitch
    return np.column_stack([x, y, z])


def helix(r=1.0, pitch=0.5, h=3.0, tube_r=0.05, segments=64, tube_segments=12):
    """
    Helical tube (spring, coil, thread approximation).

    r            : helix radius
    pitch        : vertical rise per turn
    h            : total height
    tube_r       : radius of the tube cross-section
    segments     : path resolution (points per turn)
    tube_segments: sides on the tube cross-section

    Example
    -------
    spring = helix(r=0.8, pitch=0.4, h=3.0, tube_r=0.08)
    """
    from .profiles import circle_profile
    path = helix_path(r, pitch, h, segments)
    return sweep(circle_profile(tube_r, tube_segments), path)
