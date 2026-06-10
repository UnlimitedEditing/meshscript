from PIL import Image, ImageChops


_CHOPS = {
    "multiply": ImageChops.multiply,
    "screen":   ImageChops.screen,
    "add":      ImageChops.add,
    "subtract": ImageChops.subtract,
    "darken":   ImageChops.darker,
    "lighten":  ImageChops.lighter,
    "overlay":  ImageChops.overlay,
    "difference": ImageChops.difference,
}


def composite(base, layer, x, y, opacity=1.0, blend="normal"):
    """
    In-place composite of `layer` (RGBA) onto `base` (RGBA) at (x, y).

    blend: 'normal' or one of the ImageChops modes
           ('multiply', 'screen', 'add', 'subtract', 'darken', 'lighten',
            'overlay', 'difference').
    opacity: 0..1, applied on top of the layer's own alpha.
    """
    layer = layer.convert("RGBA")
    if opacity < 1.0:
        r, g, b, a = layer.split()
        a = a.point(lambda v: int(v * opacity))
        layer = Image.merge("RGBA", (r, g, b, a))

    bw, bh = base.size
    lw, lh = layer.size

    # Clip to base bounds so out-of-canvas placement doesn't error.
    src_x0, src_y0 = max(0, -x), max(0, -y)
    dst_x0, dst_y0 = max(0, x), max(0, y)
    src_x1 = min(lw, bw - x)
    src_y1 = min(lh, bh - y)
    if src_x1 <= src_x0 or src_y1 <= src_y0:
        return

    layer = layer.crop((src_x0, src_y0, src_x1, src_y1))

    if blend != "normal":
        region = base.crop((dst_x0, dst_y0, dst_x0 + layer.width, dst_y0 + layer.height)).convert("RGBA")
        chop_fn = _CHOPS.get(blend)
        if chop_fn is None:
            raise ValueError(f"unknown blend mode: {blend!r}")
        blended_rgb = chop_fn(region.convert("RGB"), layer.convert("RGB"))
        blended = Image.merge("RGBA", (*blended_rgb.split(), layer.split()[3]))
        layer = blended

    base.alpha_composite(layer, dest=(dst_x0, dst_y0))
