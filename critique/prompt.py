"""
Builds the structured critique messages for VLMClient.chat().

build_messages(grid_bytes, spec, script=None) -> list[dict]
"""

SYSTEM = """\
You are a 3D geometry critic reviewing multi-view renders of a procedurally constructed solid mesh.
Your job: decide whether the mesh matches the goal spec and identify specific geometric problems.

You know the MeshScript op vocabulary:
  Primitives:    box, sphere, cylinder, cone, torus, capsule, wedge
  Booleans:      union, subtract, intersect
  SDF (smooth):  blend_union, blend_subtract, fillet, offset
  Sweep/Loft:    extrude, revolve, sweep, pipe, loft
  Transforms:    translate, rotate, scale, mirror, linear_array, polar_array
  Profiles:      circle_profile, rect_profile, ngon_profile, ring_profile, star_profile
  Assembly:      ground, place_on, place_at, center_on, align_to

When identifying issues, name the specific op that would fix them.
When referencing patterns, use IDs from the pattern library (P1.1–P6.7, M1–M4).

Respond ONLY with this JSON schema — no prose outside the JSON:
{
  "passed": <bool>,
  "issues": ["<specific geometric problem observed>", ...],
  "suggestions": ["<op-level fix referencing MeshScript ops/patterns>", ...],
  "pattern_gaps": ["<issue with no existing pattern to fix it>", ...]
}

"passed" = true only when the mesh clearly matches the spec with no significant geometric problems.
"issues" = problems in the renders; reference views by azimuth angle when helpful (e.g. "at 90°, the handle is too thin").
"suggestions" = concrete fixes: op name, parameters, pattern ID.
"pattern_gaps" = issues that cannot be addressed by any named op or pattern — these surface gaps in the library.
"""


def build_messages(grid_bytes: bytes, spec: str, script: str = None) -> list:
    """
    grid_bytes: PNG bytes from make_grid()
    spec:       natural-language goal description
    script:     optional MeshScript source — adds op-level context to the critique
    """
    from .client import image_content

    user_parts = [
        {"type": "text", "text": f"Goal spec: {spec}\n\nRenders (labelled by azimuth angle):"},
        image_content(grid_bytes),
    ]

    if script:
        user_parts.append({
            "type": "text",
            "text": f"\nMeshScript that produced this mesh:\n```python\n{script}\n```",
        })

    user_parts.append({
        "type": "text",
        "text": "\nEvaluate the renders. Respond with the JSON critique schema only.",
    })

    return [
        {"role": "system",  "content": SYSTEM},
        {"role": "user",    "content": user_parts},
    ]
