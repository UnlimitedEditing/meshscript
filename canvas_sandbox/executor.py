import os
import sys
import traceback

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from canvas_ops import (
    Document, new_document, paste, crop, resize_canvas,
    rect, ellipse, polygon, line, gradient,
    text,
    load_image,
    rotate, flip, resize_layer,
    blur, drop_shadow, set_opacity, tint, brightness, contrast,
    layer_size, doc_size, place, align,
)


def run(script: str, reference=None, export_dir=None) -> dict:
    """
    Execute a CanvasScript and return a self-contained result dict.

    Args:
        script:     CanvasScript source code
        reference:  opaque value identifying the design target — echoed into
                    the result unchanged (for pairing with VLM critique later).
        export_dir: write PNGs here for each show() checkpoint; None = in-memory only.

    Result dict schema
    -------------------
    {
        "success":   bool,
        "error":     str | None,
        "reference": <whatever was passed in>,
        "checkpoints": [
            {
                "label":  str,
                "width":  int,
                "height": int,
                "line":   int | None,
                "renders": [
                    {"azimuth": 0, "image": np.ndarray (H,W,3) uint8, "image_path": str | None},
                ],
            },
            ...
        ],
        "final": Document | None,
    }
    """
    checkpoints = []

    def show(doc, label=None):
        label = label or f"step_{len(checkpoints) + 1}"
        try:
            line_no = sys._getframe(1).f_lineno
        except Exception:
            line_no = None

        flat = Image.new("RGBA", doc.image.size, (255, 255, 255, 255))
        flat.alpha_composite(doc.image)
        rgb = flat.convert("RGB")
        arr = np.array(rgb)

        print(f"[show:{label}] {doc.width}x{doc.height}")

        image_path = None
        if export_dir:
            os.makedirs(export_dir, exist_ok=True)
            image_path = os.path.join(export_dir, f"{label}.png")
            rgb.save(image_path)
            print(f"         -> {image_path}")

        entry = {
            "label":  label,
            "width":  doc.width,
            "height": doc.height,
            "line":   line_no,
            "renders": [
                {"azimuth": 0, "image": arr, "image_path": image_path},
            ],
            "_doc": doc,
        }
        checkpoints.append(entry)
        return doc  # passthrough so show() can wrap an expression

    namespace = {
        "__builtins__": __builtins__,
        "np": np,
        # Document
        "Document": Document, "new_document": new_document,
        "paste": paste, "crop": crop, "resize_canvas": resize_canvas,
        # Shapes
        "rect": rect, "ellipse": ellipse, "polygon": polygon,
        "line": line, "gradient": gradient,
        # Text
        "text": text,
        # Images
        "load_image": load_image,
        # Transforms
        "rotate": rotate, "flip": flip, "resize_layer": resize_layer,
        # Effects
        "blur": blur, "drop_shadow": drop_shadow, "set_opacity": set_opacity,
        "tint": tint, "brightness": brightness, "contrast": contrast,
        # Spatial
        "layer_size": layer_size, "doc_size": doc_size,
        "place": place, "align": align,
        # Checkpoint
        "show": show,
    }

    try:
        exec(compile(script, "<canvasscript>", "exec"), namespace)
        return {
            "success":     True,
            "error":       None,
            "reference":   reference,
            "checkpoints": checkpoints,
            "final":       checkpoints[-1].get("_doc") if checkpoints else None,
        }
    except Exception:
        return {
            "success":     False,
            "error":       traceback.format_exc(),
            "reference":   reference,
            "checkpoints": checkpoints,
            "final":       checkpoints[-1].get("_doc") if checkpoints else None,
        }
