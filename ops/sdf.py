"""
SDF-based mesh operations.

Core idea: represent shapes as signed distance fields (SDF), operate in that
continuous space, reconstruct with marching cubes. Avoids the hard topology
constraints of polygon boolean ops — blending and edge rounding become
arithmetic on scalar grids.

SDF convention: positive outside, negative inside, zero at surface.
"""

import numpy as np
import trimesh


# ── Grid helpers ─────────────────────────────────────────────────────────────

def _build_sdf(mesh, grid_min, dims, pitch):
    """
    Compute a signed distance field on a regular grid.

    Uses mesh.contains() for inside/outside classification (ray cast, sub-voxel
    accurate), then scipy EDT for distance magnitude. EDT measures voxel-centre to
    voxel-centre, so distances are accurate to ~1 pitch at the surface, which is
    sufficient for morphological open/close and smooth blending.

    SDF convention: negative inside, positive outside, zero at surface.
    """
    from scipy.ndimage import distance_transform_edt

    x = np.arange(dims[0]) * pitch + grid_min[0]
    y = np.arange(dims[1]) * pitch + grid_min[1]
    z = np.arange(dims[2]) * pitch + grid_min[2]
    xx, yy, zz = np.meshgrid(x, y, z, indexing='ij')
    pts = np.column_stack([xx.ravel(), yy.ravel(), zz.ravel()])

    inside = mesh.contains(pts).reshape(dims)

    d_out = distance_transform_edt(inside)   # 0 outside, depth inside from nearest surface voxel
    d_in  = distance_transform_edt(~inside)  # 0 inside, depth outside from nearest surface voxel

    return (d_in - d_out) * pitch


def _setup_grid(bounds_list, padding, resolution):
    """Return (grid_min, dims, pitch) for a list of bounds arrays."""
    all_bounds = np.vstack(bounds_list)
    grid_min = all_bounds.min(axis=0) - padding
    grid_max = all_bounds.max(axis=0) + padding
    span = grid_max - grid_min
    pitch = span.max() / resolution
    dims = (np.ceil(span / pitch) + 2).astype(int)
    return grid_min, dims, pitch


def _mc_to_mesh(sdf, grid_min, pitch, level=0.0, fallback=None):
    """Run marching cubes on sdf at level, transform to world space."""
    from skimage.measure import marching_cubes
    try:
        verts, faces, _, _ = marching_cubes(sdf, level=level)
    except (ValueError, RuntimeError):
        return fallback
    verts = verts * pitch + grid_min
    # process=False: marching cubes mesh is already clean; process=True can merge verts
    # in ways that remove needed faces and open the mesh.
    m = trimesh.Trimesh(vertices=verts, faces=faces, process=False)
    trimesh.repair.fix_normals(m)
    return m


# ── Public ops ────────────────────────────────────────────────────────────────

def blend_union(mesh_a, mesh_b, radius, resolution=48):
    """
    Smooth boolean union. Instead of a hard crease at the join, the two
    surfaces blend together over a zone of width `radius`.

    Uses Inigo Quilez's polynomial smooth-minimum in SDF space.
    Slower than manifold union but produces naturally filleted joins.
    """
    from .booleans import union as hard_union

    pad = radius * 2.5
    grid_min, dims, pitch = _setup_grid([mesh_a.bounds, mesh_b.bounds], pad, resolution)

    sdf_a = _build_sdf(mesh_a, grid_min, dims, pitch)
    sdf_b = _build_sdf(mesh_b, grid_min, dims, pitch)

    # Smooth min — blends two SDFs with a rounded transition of width k
    k = radius
    h = np.clip(0.5 + 0.5 * (sdf_b - sdf_a) / k, 0.0, 1.0)
    blended = sdf_b * (1 - h) + sdf_a * h - k * h * (1 - h)

    result = _mc_to_mesh(blended, grid_min, pitch, level=0.0)
    return result if result is not None else hard_union(mesh_a, mesh_b)


def blend_subtract(mesh_a, mesh_b, radius, resolution=48):
    """Smooth boolean subtract — the cut edge blends rather than being sharp."""
    pad = radius * 2.5
    grid_min, dims, pitch = _setup_grid([mesh_a.bounds, mesh_b.bounds], pad, resolution)

    sdf_a = _build_sdf(mesh_a, grid_min, dims, pitch)
    sdf_b = _build_sdf(mesh_b, grid_min, dims, pitch)

    # Smooth subtract = smooth max of (a, -b)
    sdf_nb = -sdf_b
    k = radius
    h = np.clip(0.5 - 0.5 * (sdf_a - sdf_nb) / k, 0.0, 1.0)
    blended = sdf_a * (1 - h) + sdf_nb * h + k * h * (1 - h)

    from .booleans import subtract as hard_subtract
    result = _mc_to_mesh(blended, grid_min, pitch, level=0.0)
    return result if result is not None else hard_subtract(mesh_a, mesh_b)


def fillet(mesh, radius, resolution=56):
    """
    Round sharp convex edges by morphological open: erode by radius then dilate by radius.
    The open removes protrusions smaller than radius and rounds convex corners.

    Both passes stay in voxel space to avoid the non-watertight intermediate mesh
    that marching cubes produces at the erode level.
    """
    from scipy.ndimage import distance_transform_edt

    pad = radius * 3
    grid_min, dims, pitch = _setup_grid([mesh.bounds], pad, resolution)
    sdf1 = _build_sdf(mesh, grid_min, dims, pitch)

    # Erode: voxels at depth >= radius inside the original surface.
    eroded_matrix = (sdf1 <= -radius)
    if not eroded_matrix.any():
        return mesh  # radius too large — mesh would vanish

    # Dilate the eroded voxel set: recompute SDF on it, sample at +radius.
    d_out2 = distance_transform_edt(eroded_matrix)
    d_in2  = distance_transform_edt(~eroded_matrix)
    sdf2   = (d_in2 - d_out2) * pitch

    return _mc_to_mesh(sdf2, grid_min, pitch, level=+radius, fallback=mesh)


def offset(mesh, distance, resolution=48):
    """
    Expand or shrink a mesh by moving its surface uniformly outward/inward.

    distance > 0 : expand (shell grows outward)
    distance < 0 : shrink (shell moves inward)
    resolution   : voxel grid resolution — increase for smoother results

    Internally: build SDF, then sample the iso-surface at level=distance.
    Equivalent to a Minkowski sum/difference with a sphere of the given radius.

    Example
    -------
    # Inflate a box into a rounded cuboid
    b = box(w=2, h=2, d=2, center=True)
    b_fat = offset(b, 0.15)

    # Shrink a sphere slightly
    s = sphere(r=1.0)
    s_small = offset(s, -0.1)
    """
    pad = abs(distance) * 3 + 0.5
    grid_min, dims, pitch = _setup_grid([mesh.bounds], pad, resolution)
    sdf = _build_sdf(mesh, grid_min, dims, pitch)
    result = _mc_to_mesh(sdf, grid_min, pitch, level=distance, fallback=mesh)
    return result
