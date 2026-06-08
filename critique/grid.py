"""
Assemble render frames into a labelled image grid for VLM consumption.

make_grid(renders, cols=4) -> bytes   (PNG)

renders: list of {"azimuth": float, "image": np.ndarray (H, W, 3) uint8}
"""

import io
import math


def make_grid(
    renders: list,
    cols: int = 4,
    padding: int = 6,
    label_height: int = 18,
    bg: tuple = (24, 24, 24),
) -> bytes:
    """
    Returns PNG bytes suitable for embedding in a VLM message as a base64 data URL.
    Requires Pillow.
    """
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        raise ImportError("Pillow is required for grid assembly: pip install Pillow")

    n = len(renders)
    if n == 0:
        raise ValueError("make_grid: empty renders list")

    h, w = renders[0]["image"].shape[:2]
    rows = math.ceil(n / cols)
    cell_w = w + padding
    cell_h = h + label_height + padding

    canvas = Image.new("RGB", (cell_w * cols, cell_h * rows), bg)
    draw   = ImageDraw.Draw(canvas)

    for i, rv in enumerate(renders):
        row, col = divmod(i, cols)
        px = col * cell_w + padding // 2
        py = row * cell_h + label_height

        frame = rv["image"]
        # Handle RGBA frames from pyrender (drop alpha if present)
        if frame.ndim == 3 and frame.shape[2] == 4:
            frame = frame[:, :, :3]

        canvas.paste(Image.fromarray(frame), (px, py))

        label = f"{rv['azimuth']:.0f}°"
        draw.text((px + 3, py - label_height + 2), label, fill=(180, 180, 180))

    buf = io.BytesIO()
    canvas.save(buf, format="PNG", optimize=True)
    return buf.getvalue()
