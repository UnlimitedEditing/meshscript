import os
import urllib.request
import ssl
import tempfile

from PIL import Image, ImageDraw, ImageFont


_FONT_CACHE = {}


def _fetch_font_bytes(url):
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    with urllib.request.urlopen(url, timeout=60, context=ctx) as r:
        return r.read()


def _resolve_font(font, size):
    """
    font: None -> Pillow's built-in scalable font (always available).
          local path to .ttf/.otf, or http(s) URL to one.
    """
    key = (font, size)
    if key in _FONT_CACHE:
        return _FONT_CACHE[key]

    if font is None:
        loaded = ImageFont.load_default(size=size)
    elif font.startswith("http://") or font.startswith("https://"):
        data = _fetch_font_bytes(font)
        suffix = os.path.splitext(font)[1] or ".ttf"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
            f.write(data)
            tmp_path = f.name
        loaded = ImageFont.truetype(tmp_path, size=size)
    else:
        loaded = ImageFont.truetype(font, size=size)

    _FONT_CACHE[key] = loaded
    return loaded


def text(content, size=48, color=(0, 0, 0, 255), font=None, align="left",
         max_width=None, line_spacing=1.2, stroke_width=0, stroke_color=None):
    """
    Render `content` as a Layer, auto-sized to fit the rendered text.

    font:       None for Pillow's built-in scalable font, else a path or
                URL to a .ttf/.otf file.
    align:      'left', 'center', or 'right' (multi-line only).
    max_width:  if set, word-wrap text to fit within this pixel width.
    stroke_width / stroke_color: optional outline around glyphs.
    """
    pil_font = _resolve_font(font, size)

    if max_width is not None:
        lines = _wrap(content, pil_font, int(max_width), stroke_width)
    else:
        lines = content.split("\n")

    spacing = int(size * (line_spacing - 1.0))

    # Measure using a scratch image.
    scratch = Image.new("RGBA", (1, 1))
    draw = ImageDraw.Draw(scratch)
    text_block = "\n".join(lines)
    bbox = draw.multiline_textbbox(
        (0, 0), text_block, font=pil_font, align=align,
        spacing=spacing, stroke_width=stroke_width,
    )
    w = max(1, int(round(bbox[2] - bbox[0])))
    h = max(1, int(round(bbox[3] - bbox[1])))

    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.multiline_text(
        (-bbox[0], -bbox[1]), text_block, font=pil_font, fill=color, align=align,
        spacing=spacing, stroke_width=stroke_width, stroke_fill=stroke_color,
    )
    return img


def _wrap(content, pil_font, max_width, stroke_width):
    lines = []
    for paragraph in content.split("\n"):
        words = paragraph.split(" ")
        if not words:
            lines.append("")
            continue
        current = words[0]
        for word in words[1:]:
            candidate = f"{current} {word}"
            w = pil_font.getlength(candidate) + stroke_width * 2
            if w <= max_width:
                current = candidate
            else:
                lines.append(current)
                current = word
        lines.append(current)
    return lines
