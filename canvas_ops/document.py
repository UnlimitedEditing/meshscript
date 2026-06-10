from dataclasses import dataclass

from PIL import Image

from .blend import composite


@dataclass
class Document:
    """The canvas. `image` is RGBA. Origin is top-left, x right, y down."""
    width:  int
    height: int
    image:  Image.Image


def new_document(width, height, background=(255, 255, 255, 255)):
    """Create a blank Document of the given size filled with `background` (RGBA)."""
    img = Image.new("RGBA", (int(width), int(height)), tuple(background))
    return Document(width=int(width), height=int(height), image=img)


def paste(doc, layer, x=0, y=0, opacity=1.0, blend="normal"):
    """Composite `layer` onto `doc` at (x, y). Returns a new Document."""
    base = doc.image.copy()
    composite(base, layer.image, int(x), int(y), opacity=opacity, blend=blend)
    return Document(width=doc.width, height=doc.height, image=base)


def crop(doc, x, y, w, h):
    """Crop `doc` to the rectangle (x, y, x+w, y+h). Returns a new Document."""
    x, y, w, h = int(x), int(y), int(w), int(h)
    img = doc.image.crop((x, y, x + w, y + h))
    return Document(width=w, height=h, image=img)


def resize_canvas(doc, width, height, resample="lanczos"):
    """Resize the whole canvas to (width, height). Returns a new Document."""
    width, height = int(width), int(height)
    resample_map = {
        "nearest":  Image.NEAREST,
        "bilinear": Image.BILINEAR,
        "bicubic":  Image.BICUBIC,
        "lanczos":  Image.LANCZOS,
    }
    img = doc.image.resize((width, height), resample_map.get(resample, Image.LANCZOS))
    return Document(width=width, height=height, image=img)
