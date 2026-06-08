"""
Multi-view renderer for meshscript.

Entry point: render_views(mesh, config=None) -> list[dict]

Each dict: {"azimuth": float, "image": np.ndarray(H, W, 3) uint8}

Config keys (all optional, merged over RENDER_DEFAULTS):
    views          int    number of evenly-spaced azimuth angles
    elevation_deg  float  camera elevation above the equator
    cam_dist       float  camera distance from origin
    fov_deg        float  vertical field of view
    width          int    render width in pixels
    height         int    render height in pixels
    key_intensity  float  key light intensity
    fill_intensity float  fill light intensity

pyrender uses EGL automatically on Linux (Graydient) when no display is present.
On Windows it uses the system OpenGL context via a hidden window.
"""

import math
import numpy as np

RENDER_DEFAULTS: dict = {
    "views":          8,
    "elevation_deg":  20.0,
    "cam_dist":       2.5,
    "fov_deg":        35.0,
    "width":          512,
    "height":         512,
    "key_intensity":  3.0,
    "fill_intensity": 1.2,
}


def render_views(mesh, config=None) -> list:
    """
    Render *mesh* from N evenly-spaced azimuth angles at a fixed elevation.

    Returns a list of dicts, one per view:
        {"azimuth": <degrees float>, "image": <(H, W, 3) uint8 ndarray>}

    Pass config={} to use all defaults, or override individual keys.
    """
    cfg = {**RENDER_DEFAULTS, **(config or {})}
    n = cfg["views"]
    azimuths = [360.0 * i / n for i in range(n)]
    frames = _render_multiview(mesh, azimuths, cfg)
    return [{"azimuth": az, "image": img} for az, img in zip(azimuths, frames)]


# ── Internal helpers (camera math copied from ComfyUI-TripoSG/nodes_rigging.py) ──

def _lookat(eye: np.ndarray, target: np.ndarray, up: np.ndarray) -> np.ndarray:
    z = eye - target
    z_n = np.linalg.norm(z)
    z = z / z_n if z_n > 1e-8 else np.array([0.0, 0.0, 1.0])
    x = np.cross(up, z)
    x_n = np.linalg.norm(x)
    x = x / x_n if x_n > 1e-8 else np.array([1.0, 0.0, 0.0])
    y = np.cross(z, x)
    pose = np.eye(4)
    pose[:3, 0] = x
    pose[:3, 1] = y
    pose[:3, 2] = z
    pose[:3, 3] = eye
    return pose


def _camera_pose(azimuth_deg: float, elevation_deg: float, dist: float) -> np.ndarray:
    az  = math.radians(azimuth_deg)
    el  = math.radians(elevation_deg)
    eye = dist * np.array([
        math.cos(el) * math.sin(az),
        math.sin(el),
        math.cos(el) * math.cos(az),
    ])
    return _lookat(eye, np.zeros(3), np.array([0.0, 1.0, 0.0]))


def _light_pose(azimuth_deg: float, elevation_deg: float) -> np.ndarray:
    return _camera_pose(azimuth_deg, elevation_deg, dist=1.0)


def _render_multiview(mesh, azimuths_deg, cfg):
    try:
        import pyrender
    except ImportError:
        raise ImportError("pyrender is required: pip install pyrender")

    scene = pyrender.Scene(
        bg_color      = [0, 0, 0, 0],
        ambient_light = [0.1, 0.1, 0.1],
    )

    # Vertex colours are preserved through the MetallicRoughness material.
    if (hasattr(mesh, "visual") and
            hasattr(mesh.visual, "vertex_colors") and
            mesh.visual.vertex_colors is not None):
        material = pyrender.MetallicRoughnessMaterial(
            baseColorFactor = [1.0, 1.0, 1.0, 1.0],
            metallicFactor  = 0.0,
            roughnessFactor = 1.0,
        )
        pr_mesh = pyrender.Mesh.from_trimesh(mesh, material=material, smooth=True)
    else:
        pr_mesh = pyrender.Mesh.from_trimesh(mesh, smooth=True)

    mesh_node = scene.add(pr_mesh)

    scene.add(pyrender.DirectionalLight(color=np.ones(3), intensity=cfg["key_intensity"]),
              pose=_light_pose(45,  60))
    scene.add(pyrender.DirectionalLight(color=np.ones(3), intensity=cfg["fill_intensity"]),
              pose=_light_pose(-60, 30))

    camera   = pyrender.PerspectiveCamera(
        yfov        = math.radians(cfg["fov_deg"]),
        aspectRatio = cfg["width"] / cfg["height"],
    )
    renderer = pyrender.OffscreenRenderer(cfg["width"], cfg["height"])
    frames: list[np.ndarray] = []

    try:
        for az in azimuths_deg:
            cam_node      = scene.add(camera, pose=_camera_pose(az, cfg["elevation_deg"], cfg["cam_dist"]))
            color, _depth = renderer.render(scene, flags=pyrender.RenderFlags.RGBA)
            scene.remove_node(cam_node)
            frames.append(color[:, :, :3])  # (H, W, 3) uint8, drop alpha
    finally:
        renderer.delete()

    scene.remove_node(mesh_node)
    return frames
