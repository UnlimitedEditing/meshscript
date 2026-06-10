from .blend import composite
from .document import Document


def layer_size(layer):
    """(width, height) of a Layer."""
    return layer.size


def doc_size(doc):
    """(width, height) of a Document."""
    return (doc.width, doc.height)


def place(doc, layer, x=0, y=0, anchor="top-left", opacity=1.0, blend="normal"):
    """
    Composite `layer` onto `doc` such that `anchor` of the layer lands at (x, y).

    anchor: 'top-left', 'top', 'top-right', 'left', 'center', 'right',
            'bottom-left', 'bottom', 'bottom-right'
    """
    lw, lh = layer.size
    ax, ay = _anchor_offset(anchor, lw, lh)
    base = doc.image.copy()
    composite(base, layer, int(x - ax), int(y - ay), opacity=opacity, blend=blend)
    return Document(width=doc.width, height=doc.height, image=base)


def align(doc, layer, anchor, margin=0, opacity=1.0, blend="normal"):
    """
    Composite `layer` onto `doc`, aligned within the canvas using a 9-point
    anchor (e.g. 'center', 'top-right', 'bottom', ...), inset by `margin` px.
    """
    lw, lh = layer.size
    dw, dh = doc.width, doc.height
    margin = int(margin)

    x_anchor, y_anchor = _split_anchor(anchor)

    if x_anchor == "left":
        x = margin
    elif x_anchor == "right":
        x = dw - lw - margin
    else:  # center
        x = (dw - lw) // 2

    if y_anchor == "top":
        y = margin
    elif y_anchor == "bottom":
        y = dh - lh - margin
    else:  # center
        y = (dh - lh) // 2

    base = doc.image.copy()
    composite(base, layer, int(x), int(y), opacity=opacity, blend=blend)
    return Document(width=doc.width, height=doc.height, image=base)


def _split_anchor(anchor):
    """'top-right' -> ('right', 'top'); 'center' -> ('center', 'center')."""
    parts = anchor.split("-")
    x_anchor, y_anchor = "center", "center"
    for p in parts:
        if p in ("left", "right"):
            x_anchor = p
        elif p in ("top", "bottom"):
            y_anchor = p
    return x_anchor, y_anchor


def _anchor_offset(anchor, w, h):
    """Pixel offset from a layer's top-left to its `anchor` point."""
    x_anchor, y_anchor = _split_anchor(anchor)
    ax = {"left": 0, "center": w / 2, "right": w}[x_anchor]
    ay = {"top": 0, "center": h / 2, "bottom": h}[y_anchor]
    return ax, ay
