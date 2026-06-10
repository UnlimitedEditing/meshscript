# MeshScript

LLM-driven procedural design via imperative "compiler" scripts — deterministic
geometry and graphics instead of diffusion from noise.

## Architecture

```
ops/            — 3D geometric operation library (primitives, booleans, transforms, modifiers)
sandbox/        — restricted Python executor for MeshScript; show() as render/critique checkpoint
canvas_ops/     — 2D graphic design operation library (CanvasScript): shapes, text, images, layout
canvas_sandbox/ — restricted Python executor for CanvasScript; show() captures the composited canvas
critique/       — multi-view headless renderer + VLM feedback loop (3D)
domains/        — knowledge index and rule books per discipline
examples/       — sample MeshScript (.ms) and CanvasScript (.cnv) programs
```

## How it works

1. LLM writes a script (constrained Python using the ops / canvas_ops library)
2. Sandbox executor runs it step-by-step; show() renders/captures intermediate state
3. (3D) Critique loop renders from multiple angles, passes to VLM, returns structured feedback
4. LLM revises and reruns

## MeshScript (3D) v1 scope

Three domains: mathematical solids, mechanical parts, classical architecture.
See `domains/index.md` for the full discipline map.

## CanvasScript (2D)

A sibling "compiler" for 2D graphics — exact, seed-independent text and layout.
Build documents, posters, UI/game cards, and overlays on existing images by
composing shapes, text, and loaded images via `canvas_ops`. See
`prompt/canvas-system-prompt.md` for the LLM-facing op reference and
`examples/canvas/` for sample `.cnv` scripts. ComfyUI nodes
(`CanvasScriptExecute`, `SaveCanvasWithScript`, `LoadCanvasWithScript`) live in
`D:\ComfyUI-MeshScript\nodes_canvas.py`.
