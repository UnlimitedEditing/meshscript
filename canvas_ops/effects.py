from PIL import Image, ImageEnhance, ImageFilter


def blur(layer, radius):
    """Gaussian blur a layer by `radius` pixels."""
    return layer.filter(ImageFilter.GaussianBlur(radius))


def drop_shadow(layer, offset=(8, 8), blur_radius=8, color=(0, 0, 0, 128)):
    """
    Return a new layer with a blurred shadow composited behind `layer`.
    The result canvas is padded to fit both the shadow and the original.
    """
    ox, oy = int(offset[0]), int(offset[1])
    pad = blur_radius * 2 + max(abs(ox), abs(oy))
    w, h = layer.size
    out_w, out_h = w + pad * 2, h + pad * 2

    # Shadow shape: alpha mask of the layer, filled with `color`.
    alpha = layer.split()[3]
    shadow_shape = Image.new("RGBA", layer.size, color)
    shadow_shape.putalpha(alpha)

    canvas = Image.new("RGBA", (out_w, out_h), (0, 0, 0, 0))
    canvas.alpha_composite(shadow_shape, dest=(pad + ox, pad + oy))
    canvas = canvas.filter(ImageFilter.GaussianBlur(blur_radius))

    canvas.alpha_composite(layer, dest=(pad, pad))
    return canvas


def set_opacity(layer, alpha):
    """Return a copy of `layer` with its alpha channel scaled by `alpha` (0..1)."""
    layer = layer.convert("RGBA")
    r, g, b, a = layer.split()
    a = a.point(lambda v: int(v * alpha))
    return Image.merge("RGBA", (r, g, b, a))


def tint(layer, color, amount=1.0):
    """
    Tint a layer toward `color` (RGB or RGBA) by `amount` (0..1).
    Alpha channel is preserved.
    """
    layer = layer.convert("RGBA")
    r, g, b, a = layer.split()
    rgb = Image.merge("RGB", (r, g, b))

    tint_layer = Image.new("RGB", layer.size, tuple(color[:3]))
    blended = Image.blend(rgb, tint_layer, amount)

    r2, g2, b2 = blended.split()
    return Image.merge("RGBA", (r2, g2, b2, a))


def _enhance(layer, factory, factor):
    layer = layer.convert("RGBA")
    r, g, b, a = layer.split()
    rgb = Image.merge("RGB", (r, g, b))
    rgb = factory(rgb).enhance(factor)
    r2, g2, b2 = rgb.split()
    return Image.merge("RGBA", (r2, g2, b2, a))


def brightness(layer, factor):
    """Adjust brightness. factor=1.0 is unchanged, <1 darker, >1 brighter."""
    return _enhance(layer, ImageEnhance.Brightness, factor)


def contrast(layer, factor):
    """Adjust contrast. factor=1.0 is unchanged."""
    return _enhance(layer, ImageEnhance.Contrast, factor)
