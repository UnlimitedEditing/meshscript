import ssl
import urllib.request
from io import BytesIO

from PIL import Image


def _fetch_bytes(url_or_path):
    if url_or_path.startswith("http://") or url_or_path.startswith("https://"):
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with urllib.request.urlopen(url_or_path, timeout=60, context=ctx) as r:
            return r.read()
    with open(url_or_path, "rb") as f:
        return f.read()


def load_image(url_or_path, w=None, h=None, fit="contain"):
    """
    Load an image from a URL or local path as a Layer (RGBA).

    fit (only applies if both w and h are given):
        'contain' - scale to fit within (w, h), preserving aspect ratio,
                    centered on a transparent (w, h) canvas
        'cover'   - scale to fill (w, h), preserving aspect ratio, cropped to fit
        'stretch' - resize to exactly (w, h), ignoring aspect ratio
    """
    data = _fetch_bytes(url_or_path.strip())
    img = Image.open(BytesIO(data)).convert("RGBA")

    if w is None or h is None:
        return img

    w, h = int(w), int(h)
    src_w, src_h = img.size

    if fit == "stretch":
        return img.resize((w, h), Image.LANCZOS)

    src_ratio = src_w / src_h
    dst_ratio = w / h

    if fit == "cover":
        if src_ratio > dst_ratio:
            new_h = h
            new_w = int(round(h * src_ratio))
        else:
            new_w = w
            new_h = int(round(w / src_ratio))
        resized = img.resize((new_w, new_h), Image.LANCZOS)
        x = (new_w - w) // 2
        y = (new_h - h) // 2
        return resized.crop((x, y, x + w, y + h))

    # 'contain' (default)
    if src_ratio > dst_ratio:
        new_w = w
        new_h = int(round(w / src_ratio))
    else:
        new_h = h
        new_w = int(round(h * src_ratio))
    resized = img.resize((new_w, new_h), Image.LANCZOS)
    canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    canvas.paste(resized, ((w - new_w) // 2, (h - new_h) // 2), resized)
    return canvas
