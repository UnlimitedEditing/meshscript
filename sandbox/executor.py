import traceback
import numpy as np
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ops import (
    box, sphere, cylinder, cone, torus, wedge, capsule,
    tetrahedron, cube, octahedron, dodecahedron, icosahedron, prism, antiprism, geodesic,
    blend_union, blend_subtract, fillet, offset,
    union, subtract, intersect,
    translate, rotate, scale, mirror, linear_array, polar_array,
    shell, extrude, revolve,
    sweep, pipe, loft, arc_path, helix_path, helix,
    circle_profile, rect_profile, polygon_profile, ngon_profile, ring_profile, star_profile,
    bounds, top, bottom, front, back, left, right,
    height, width, depth,
    center_x, center_y, center_z, centroid, xy_radius,
    ground, place_on, place_at, center_on, align_to, convex_hull,
)


def run(script: str, reference=None, render_config=None, export_dir=None) -> dict:
    """
    Execute a meshscript and return a self-contained result dict.

    Args:
        script:        meshscript source code
        reference:     opaque value identifying the design target — URL, text
                       description, local path, or None.  Echoed into the result
                       unchanged so the VLM critique layer can pair renders with
                       the intended subject.
        render_config: if not None, render each checkpoint from multiple views
                       using pyrender.  Pass {} for all defaults (see render.py).
                       Keys: views, elevation_deg, cam_dist, fov_deg, width,
                       height, key_intensity, fill_intensity.
        export_dir:    write GLBs and render PNGs here; None = in-memory only.

    Result dict schema
    ------------------
    {
        "success":       bool,
        "error":         str | None,
        "reference":     <whatever was passed in>,
        "render_config": dict | None,        # effective config used, or None
        "checkpoints": [
            {
                "label":     str,
                "mesh":      trimesh.Trimesh,  # in-memory only, not serialised
                "vertices":  int,
                "faces":     int,
                "watertight": bool,
                "volume":    float | None,
                "bounds":    list,
                "line":      int | None,
                "renders": [               # present only when render_config != None
                    {
                        "azimuth":    float,         # degrees
                        "image":      np.ndarray,    # (H, W, 3) uint8
                        "image_path": str | None,    # abs path if written to disk
                    },
                    ...
                ],
            },
            ...
        ],
        "final": trimesh.Trimesh | None,
    }

    Batch usage
    -----------
    run() is pure — no global state, no shared resources between calls.
    A batch is simply:  results = [run(s, ref, cfg) for s, ref, cfg in jobs]
    or parallelised with ThreadPoolExecutor / multiprocessing.Pool.
    """
    # Import lazily so pyrender is only required when render_config is set.
    _render_fn = None
    if render_config is not None:
        from render import render_views as _render_fn

    checkpoints = []

    def show(mesh, label=None):
        label = label or f"step_{len(checkpoints) + 1}"
        try:
            line = sys._getframe(1).f_lineno
        except Exception:
            line = None

        entry = {
            "label":     label,
            "mesh":      mesh,
            "vertices":  len(mesh.vertices),
            "faces":     len(mesh.faces),
            "watertight": mesh.is_watertight,
            "volume":    float(mesh.volume) if mesh.is_watertight else None,
            "bounds":    mesh.bounds.tolist(),
            "line":      line,
        }

        vol_str = f", vol={entry['volume']:.4f}" if entry["volume"] else ""
        print(f"[show:{label}] {entry['vertices']} verts  {entry['faces']} faces"
              f"  watertight={entry['watertight']}{vol_str}")

        # ── GLB export ──
        if export_dir:
            os.makedirs(export_dir, exist_ok=True)
            path = os.path.join(export_dir, f"{label}.glb")
            import trimesh as _tr
            _export = mesh.copy()
            # glTF/model-viewer is Y-up; meshscript uses Z-up.
            _T = _tr.transformations.rotation_matrix(np.radians(-90), [1, 0, 0])
            _export.apply_transform(_T)
            _export.export(path)
            print(f"         -> {path}")

        # ── Multi-view render ──
        renders = []
        if _render_fn is not None:
            print(f"         rendering {render_config.get('views', 8)} views …", end="", flush=True)
            view_dicts = _render_fn(mesh, render_config)
            for vd in view_dicts:
                image_path = None
                if export_dir:
                    renders_dir = os.path.join(export_dir, "renders")
                    os.makedirs(renders_dir, exist_ok=True)
                    fname = f"{label}_az{vd['azimuth']:06.1f}.png"
                    image_path = os.path.join(renders_dir, fname)
                    _write_png(vd["image"], image_path)
                renders.append({
                    "azimuth":    vd["azimuth"],
                    "image":      vd["image"],
                    "image_path": image_path,
                })
            print(f" done ({len(renders)} views)")
            entry["renders"] = renders

        checkpoints.append(entry)
        return mesh  # passthrough so show() can wrap an expression

    namespace = {
        "__builtins__": __builtins__,
        "np": np,
        # Primitives
        "box": box, "sphere": sphere, "cylinder": cylinder,
        "cone": cone, "torus": torus, "wedge": wedge, "capsule": capsule,
        # Platonic & derived solids
        "tetrahedron": tetrahedron, "cube": cube, "octahedron": octahedron,
        "dodecahedron": dodecahedron, "icosahedron": icosahedron,
        "prism": prism, "antiprism": antiprism, "geodesic": geodesic,
        # SDF ops
        "blend_union": blend_union, "blend_subtract": blend_subtract,
        "fillet": fillet, "offset": offset,
        # Booleans
        "union": union, "subtract": subtract, "intersect": intersect,
        # Transforms
        "translate": translate, "rotate": rotate, "scale": scale,
        "mirror": mirror, "linear_array": linear_array, "polar_array": polar_array,
        # Modifiers
        "shell": shell, "extrude": extrude, "revolve": revolve,
        # Sweep / path ops
        "sweep": sweep, "pipe": pipe, "loft": loft,
        "arc_path": arc_path, "helix_path": helix_path, "helix": helix,
        # Profiles
        "circle_profile": circle_profile, "rect_profile": rect_profile,
        "polygon_profile": polygon_profile, "ngon_profile": ngon_profile,
        "ring_profile": ring_profile, "star_profile": star_profile,
        # Spatial queries
        "bounds": bounds, "top": top, "bottom": bottom,
        "front": front, "back": back, "left": left, "right": right,
        "height": height, "width": width, "depth": depth,
        "center_x": center_x, "center_y": center_y, "center_z": center_z,
        "centroid": centroid, "xy_radius": xy_radius,
        # Alignment & hull
        "ground": ground, "place_on": place_on, "place_at": place_at,
        "center_on": center_on, "align_to": align_to, "convex_hull": convex_hull,
        # Checkpoint
        "show": show,
    }

    try:
        exec(compile(script, "<meshscript>", "exec"), namespace)
        return {
            "success":       True,
            "error":         None,
            "reference":     reference,
            "render_config": render_config,
            "checkpoints":   checkpoints,
            "final":         checkpoints[-1]["mesh"] if checkpoints else None,
        }
    except Exception:
        return {
            "success":       False,
            "error":         traceback.format_exc(),
            "reference":     reference,
            "render_config": render_config,
            "checkpoints":   checkpoints,
            "final":         checkpoints[-1]["mesh"] if checkpoints else None,
        }


def _write_png(image: np.ndarray, path: str) -> None:
    """Write a (H, W, 3) uint8 array to a PNG file without PIL dependency."""
    try:
        from PIL import Image
        Image.fromarray(image).save(path)
        return
    except ImportError:
        pass
    try:
        import cv2
        cv2.imwrite(path, cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
        return
    except ImportError:
        pass
    # Fallback: trimesh's built-in PNG writer via imageio
    import imageio
    imageio.imwrite(path, image)
