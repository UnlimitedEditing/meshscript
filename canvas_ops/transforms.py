from PIL import Image


def rotate(layer, angle, expand=True):
    """Rotate a layer by `angle` degrees counter-clockwise."""
    return layer.rotate(angle, resample=Image.BICUBIC, expand=expand)


def flip(layer, axis="x"):
    """Flip a layer. axis='x' mirrors left-right, axis='y' flips top-bottom."""
    if axis == "x":
        return layer.transpose(Image.FLIP_LEFT_RIGHT)
    if axis == "y":
        return layer.transpose(Image.FLIP_TOP_BOTTOM)
    raise ValueError(f"axis must be 'x' or 'y', got {axis!r}")


def resize_layer(layer, w, h):
    """Resize a layer to exactly (w, h) pixels."""
    return layer.resize((int(w), int(h)), Image.LANCZOS)
