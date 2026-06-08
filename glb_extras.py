"""
GLB binary utilities — embed and extract MeshScript source code from a GLB file.

The GLTF 2.0 spec (§3.7.1) allows a free-form `extras` object anywhere in the
JSON chunk.  We write to the root-level extras, which is preserved by Blender,
three.js, Babylon.js, and all standard viewers (they simply ignore unknown keys).

API
---
    inject_script(glb_bytes, script, spec="") -> bytes
        Return new GLB bytes with script + spec embedded.

    extract_script(glb_bytes) -> (script: str, spec: str)
        Pull script + spec back out.  Returns ("", "") if none present.

GLB binary layout (little-endian)
----------------------------------
    [12-byte header]  magic=0x46546C67  version=2  totalLength
    [JSON chunk]      chunkLength  chunkType=0x4E4F534A  data (space-padded)
    [BIN  chunk]      chunkLength  chunkType=0x004E4942  data (null-padded)
"""

import json
import struct

_MAGIC      = 0x46546C67   # "glTF"
_CHUNK_JSON = 0x4E4F534A   # "JSON"
_CHUNK_BIN  = 0x004E4942   # "BIN\0"


# ── internal ──────────────────────────────────────────────────────────────────

def _parse_chunks(data: bytes) -> list:
    magic, version, length = struct.unpack_from("<III", data, 0)
    assert magic == _MAGIC, f"Not a GLB file (magic=0x{magic:08X})"
    chunks = []
    off = 12
    while off < len(data):
        clen, ctype = struct.unpack_from("<II", data, off)
        chunks.append((ctype, data[off + 8 : off + 8 + clen]))
        off += 8 + clen
    return chunks


def _pack(chunks: list) -> bytes:
    body = b""
    for ctype, cdata in chunks:
        body += struct.pack("<II", len(cdata), ctype) + cdata
    header = struct.pack("<III", _MAGIC, 2, 12 + len(body))
    return header + body


def _pad(data: bytes, pad_byte: bytes) -> bytes:
    rem = len(data) % 4
    return data + pad_byte * ((4 - rem) % 4)


# ── public API ────────────────────────────────────────────────────────────────

def inject_script(glb_bytes: bytes, script: str, spec: str = "") -> bytes:
    """Return new GLB bytes with script + spec in root extras."""
    chunks = _parse_chunks(glb_bytes)
    new_chunks = []
    for ctype, cdata in chunks:
        if ctype == _CHUNK_JSON:
            gltf = json.loads(cdata.rstrip(b"\x00").rstrip(b" "))
            extras = gltf.setdefault("extras", {})
            extras["meshscript_source"] = script
            extras["meshscript_spec"]   = spec
            raw = json.dumps(gltf, separators=(",", ":")).encode("utf-8")
            new_chunks.append((_CHUNK_JSON, _pad(raw, b" ")))
        else:
            new_chunks.append((ctype, cdata))
    return _pack(new_chunks)


def extract_script(glb_bytes: bytes):
    """
    Returns (script: str, spec: str).
    Returns ("", "") if no script is embedded.
    """
    try:
        chunks = _parse_chunks(glb_bytes)
    except AssertionError:
        return "", ""
    for ctype, cdata in chunks:
        if ctype == _CHUNK_JSON:
            gltf   = json.loads(cdata.rstrip(b"\x00").rstrip(b" "))
            extras = gltf.get("extras", {})
            return extras.get("meshscript_source", ""), extras.get("meshscript_spec", "")
    return "", ""
