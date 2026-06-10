from PIL import Image, ImageDraw


def rect(w, h, fill=None, outline=None, outline_width=1, radius=0):
    """Rectangle layer (w x h). `radius` > 0 draws rounded corners."""
    w, h = int(w), int(h)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    box = (0, 0, w - 1, h - 1)
    if radius > 0:
        draw.rounded_rectangle(box, radius=int(radius), fill=fill, outline=outline, width=outline_width)
    else:
        draw.rectangle(box, fill=fill, outline=outline, width=outline_width)
    return img


def ellipse(w, h, fill=None, outline=None, outline_width=1):
    """Ellipse layer inscribed in a (w x h) bounding box."""
    w, h = int(w), int(h)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse((0, 0, w - 1, h - 1), fill=fill, outline=outline, width=outline_width)
    return img


def polygon(points, fill=None, outline=None, outline_width=1):
    """
    Polygon layer. `points` is a list of (x, y) tuples; the layer is sized
    to the polygon's bounding box and the points are shifted to (0, 0)-relative.
    """
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    min_x, min_y = min(xs), min(ys)
    w = int(max(xs) - min_x) + 1
    h = int(max(ys) - min_y) + 1
    shifted = [(x - min_x, y - min_y) for x, y in points]
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.polygon(shifted, fill=fill, outline=outline, width=outline_width)
    return img


def line(points, fill=(0, 0, 0, 255), width=1):
    """
    Line layer through `points` (list of (x, y) tuples). The layer is sized
    to the bounding box of the points plus `width`, points shifted to be
    (0, 0)-relative.
    """
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    pad = max(1, width)
    min_x, min_y = min(xs) - pad, min(ys) - pad
    w = int(max(xs) - min_x) + pad + 1
    h = int(max(ys) - min_y) + pad + 1
    shifted = [(x - min_x, y - min_y) for x, y in points]
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.line(shifted, fill=fill, width=width)
    return img


def gradient(w, h, stops, direction="vertical"):
    """
    Linear gradient layer (w x h).

    stops: list of (pos, RGBA) where pos is 0..1, sorted by pos.
    direction: 'vertical' (top->bottom), 'horizontal' (left->right).
    """
    w, h = int(w), int(h)

    def _rgba(c):
        c = tuple(c)
        return c if len(c) == 4 else (*c, 255)

    stops = sorted(((p, _rgba(c)) for p, c in stops), key=lambda s: s[0])

    length = h if direction == "vertical" else w
    ramp = Image.new("RGBA", (1, length) if direction == "vertical" else (length, 1))
    px = ramp.load()

    for i in range(length):
        t = i / max(1, length - 1)
        color = _sample_stops(stops, t)
        if direction == "vertical":
            px[0, i] = color
        else:
            px[i, 0] = color

    return ramp.resize((w, h), Image.NEAREST)


def _sample_stops(stops, t):
    if t <= stops[0][0]:
        return tuple(stops[0][1])
    if t >= stops[-1][0]:
        return tuple(stops[-1][1])
    for (p0, c0), (p1, c1) in zip(stops, stops[1:]):
        if p0 <= t <= p1:
            span = (p1 - p0) or 1.0
            f = (t - p0) / span
            return tuple(int(c0[i] + (c1[i] - c0[i]) * f) for i in range(4))
    return tuple(stops[-1][1])
