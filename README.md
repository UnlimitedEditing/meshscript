# MeshScript

LLM-driven procedural 3D modeling via imperative construction scripts.

## Architecture

```
ops/        — geometric operation library (primitives, booleans, transforms, modifiers)
sandbox/    — restricted Python executor; show() as render/critique checkpoint
critique/   — multi-view headless renderer + VLM feedback loop
domains/    — knowledge index and rule books per discipline
examples/   — sample MeshScript programs
```

## How it works

1. LLM writes a MeshScript program (constrained Python using the ops library)
2. Sandbox executor runs it step-by-step; show() renders intermediate state
3. Critique loop renders from multiple angles, passes to VLM, returns structured feedback
4. LLM revises and reruns

## v1 scope

Three domains: mathematical solids, mechanical parts, classical architecture.
See `domains/index.md` for the full discipline map.

## Status

The full pipeline (LLM → MeshScript → mesh → GLB) is deployed end-to-end on
Graydient as `meshscript-txt2mesh` and `meshscript-mesh2mesh` (gen scripts in
`D:\tripostl\`). It renders successfully, but **translation quality is the
current focus** — the LLM is producing oversimplified scripts (single
primitive, single `show()`) that ignore most of the spec. See `CLAUDE.md` for
the active debugging plan and `ROADMAP.md` for the longer-term phase plan
(critique loop / designer agent, Phases 3-4, are the structural fix for this
class of issue).
