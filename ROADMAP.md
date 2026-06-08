# MeshScript — Living Roadmap

> **How to use this doc:** Work top-to-bottom. Each phase has a clear blocker note.  
> Update the status column as things land. Open a fresh conversation per phase.

---

## Current position

```
Phase 1 ████████████████ DONE
Phase 2 ████████████████ DONE  (expanded beyond original scope — see notes)
Phase 3 ░░░░░░░░░░░░░░░░ unblocked  ← you are here
Phase 4 ░░░░░░░░░░░░░░░░ blocked on 3
Phase 5 ░░░░░░░░░░░░░░░░ open-ended / parallel
```

---

## Phase 1 — Language foundation ✅ DONE

Everything the executor and downstream tools run on.

| Component | Status | Notes |
|---|---|---|
| Op library (~63 exported ops) | ✅ | primitives, booleans, transforms, SDF, sweep/loft, profiles, spatial, hull |
| Sandbox executor | ✅ | `exec()` with controlled namespace, `show()` checkpoint |
| Viewer | ✅ | file:// compatible, base64 GLBs, inline JSON |
| Y-up export fix | ✅ | glTF coordinate correction on export |
| Multi-view renderer | ✅ | `render.py` — pyrender, 8 azimuths, EGL on Linux |
| Domain knowledge index | ✅ | `domains/index.md` — 9 disciplines, v1 scope identified |

---

## Phase 2 — The Dictionary ✅ DONE

**What:** A machine-readable + human-readable reference that tells an LLM exactly what MeshScript contains — every op, its signature, its parameters, idiomatic usage, spatial conventions, and compositional recipes.

**Why this must come before the designer agent:** Without it, the LLM hallucinates op names, invents parameter orders, and ignores spatial idioms. The critique loop can flag that a result is wrong; it cannot teach the LLM what `fillet()` takes. The dictionary is the LLM's vocabulary.

### Deliverables — as built

| File | Description | Status |
|---|---|---|
| `docs/op-reference.md` | All 63 ops: exact signature, all params, one working example each. 9 groups. | ✅ |
| `docs/conventions.md` | Z-up system; `ground()` convention; spatial idioms; `show()` discipline; loft vertex-count constraint; SDF resolution table; boolean vs SDF decision guide; rotation-orbit and polar_array gotchas. | ✅ |
| `docs/patterns.md` | **41 micro-patterns + 4 macro stubs** across 6 strategy families (see below). Domain-tagged for cross-referencing. | ✅ expanded |
| `prompt/system-prompt.md` | Tight LLM injection context: all op signatures in quick-reference form, 4 critical rules, common pattern one-liners, workflow template. Full reference docs available for retrieval. | ✅ |

### Pattern library — what was built and why it expanded

The original scope called for a flat list of ~15 named recipes. During this session the pattern library was restructured and significantly expanded based on a key insight: **patterns should be organised by construction strategy, not by domain**. The same profile-revolution pattern appears in architecture, manufacturing, natural form, and ceramics — organising by domain would duplicate it and obscure the relationship.

**Final structure:**

| Family | Count | Covers |
|---|---|---|
| Profile-Driven | 9 | extrude, revolve, sweep, loft — shapes defined by a cross-section moving through space |
| Boolean Composition | 6 | union, subtract, intersect — combining and carving solids |
| Surface Quality | 5 | fillet, blend, offset — edge and surface character |
| Spatial Arrangement | 7 | array, mirror — repetition and symmetry |
| Interior & Void | 7 | hollow, hole, pocket, channel, bore, groove |
| Positional Assembly | 7 | stack, center, flush-mount, orbital placement, proportion-locked sizing |
| **Macro-patterns (stubs)** | 4 | Doric column, turned part with bore, flanged pipe, arch in wall |

**Tag vocabulary** (`math`, `mech`, `arch`, `natural`, `product`, `game`, `craft`, `struct`, `art`) enables cross-domain lookup and reveals structural relationships — e.g. `natural` appears only in P1.2 (revolution), P1.7 (helical sweep), and P3.2 (smooth join), which correctly maps the three construction strategies nature uses most.

**Macro-patterns are the Phase 2↔5 bridge.** The 4 stubs preview what Phase 5 domain modules will implement as named functions (`doric_column()`, `flanged_pipe()`, etc.). They reference their constituent micro-patterns explicitly, so Phase 5 development has a clear composition spec to implement against.

### What the dictionary is NOT

- Not domain vocabulary (that's Phase 5)
- Not a training corpus (that's the Decompiler, Phase 6+)
- Not a tutorial for humans — optimised for LLM consumption

### Open questions resolved this phase

- **Dictionary token budget:** Resolved. `prompt/system-prompt.md` is the tight injection (all signatures + critical rules + pattern one-liners). Full op-reference and patterns docs are retrieval targets, not always-on context.
- **Pattern organisation:** Resolved. Strategy-first taxonomy with domain tags. Not domain-organised.

---

## Phase 3 — Critique loop ⬜ UNBLOCKED

**What:** Wire `render.py` → image grid → VLM (Claude) → structured critique → back to caller.

**Status:** Unblocked. Dictionary exists, so the critique prompt can reference specific ops and patterns by name ("try `fillet()` on that edge", "use `blend_union` for the handle join"). This is significantly richer than a critique that can only describe visual problems.

### Deliverables

| Deliverable | Description |
|---|---|
| `critique/grid.py` | Assembles N render frames into a single image grid (PIL). Labels each panel with azimuth. |
| `critique/prompt.py` | Builds the structured critique prompt: embeds the image grid, injects the goal spec, asks for pass/fail + specific issues + suggested revision. References op and pattern names from the dictionary. |
| `critique/loop.py` | Entry point: `critique(mesh, spec) -> CritiqueResult`. Calls renderer, assembles grid, calls VLM, parses response. |
| `CritiqueResult` schema | `{ passed: bool, issues: [str], suggestions: [str], raw: str }` |

### Key design decisions to resolve in that session

- **How many views?** 8 is generous; 4 (front/back/left/top) may be enough for first loop. Start with 4, add if the critique misses geometry.
- **VLM model:** Claude Sonnet 4.6 (`claude-sonnet-4-6`) — current best vision/cost balance for a tight loop. Re-evaluate when Opus 4.8 vision quality is needed for ambiguous geometry.
- **Critique response format:** JSON schema (`{ passed, issues, suggestions }`) is parseable and feeds the agent loop cleanly. Free-text is more flexible but harder to act on programmatically. Prefer JSON with a `raw` fallback field.
- **Pattern feedback:** The critique should optionally suggest a specific micro-pattern by ID (e.g. "P3.2 — Smooth Join") when a known pattern addresses the issue. This creates a direct feedback channel from critique → pattern library gaps.

### New consideration: pattern gap surfacing

The critique loop is the first mechanism that can surface **missing patterns** at runtime. When the VLM consistently identifies an issue that has no named pattern to fix it, that's a pattern gap. Log critique suggestions that don't map to an existing pattern ID — these are candidates for the next patterns.md expansion.

---

## Phase 4 — LLM designer agent ⬜ BLOCKED ON: Phase 3

**What:** The model that writes MeshScript given a natural-language spec, receives critique from Phase 3, and iterates until the critique passes or a revision budget is exhausted.

### Deliverables

| Deliverable | Description |
|---|---|
| `agent/designer.py` | `design(spec: str, max_revisions=3) -> DesignResult`. Calls LLM with system prompt, runs executor, calls critique loop, feeds result back to LLM. |
| `agent/prompts.py` | Turn-by-turn prompt templates: initial design prompt, revision prompt (includes prior script + critique + suggested pattern IDs). |
| `DesignResult` schema | `{ script: str, mesh: Trimesh, checkpoints: [...], critique_history: [...], converged: bool }` |

### What this phase will surface

- Which ops the LLM reaches for most vs. misuses → informs dictionary gaps
- Which patterns the LLM uses vs. ignores → informs pattern injection strategy (always-on vs retrieval)
- Where the LLM hits structural limits of CSG → informs whether new morphologies are needed
- Which specs the critique loop can't evaluate → informs critique prompt refinement
- Which macro-pattern stubs get reached for → signals which Phase 5 domain modules to build first

---

## Phase 5 — Domain vocabularies ⬜ OPEN / PARALLEL

**What:** Higher-level named ops for each v1 domain that compile down to base ops.
This is **not blocking** Phase 3/4, but enriches the dictionary and gives the designer agent better building blocks.

**Relationship to patterns:** Macro-patterns in `docs/patterns.md` are the spec for what Phase 5 modules implement. `doric_column()` is M1 fully parameterised. `flanged_pipe()` is M3. Build the function, then promote the macro-pattern stub to a real op entry in `docs/op-reference.md`.

### v1 domains

| Domain | Example vocabulary | Macro-pattern stub | Notes |
|---|---|---|---|
| **Mathematical solids** | Already covered by `solids.py` | — | Minimal work needed |
| **Mechanical parts** | `spur_gear(module, teeth, thickness)`, `hex_bolt(size, length)`, `flanged_pipe(r, h, flange_r)` | M3 | Gear geometry is well-specified; good early test |
| **Classical architecture** | `doric_column(height, base_r)`, `arch(span, rise, thickness)`, `barrel_vault(span, h, depth)` | M1, M4 | Vitruvian proportions compile to ratios — very testable |

### When to tackle

Build a domain module when a designer agent session hits a wall — i.e., when the LLM needs a concept the base op library can't express cleanly. Don't pre-build; let usage surface the need. The macro-pattern stubs give enough scaffold to start quickly when the trigger comes.

### The "other morphologies" question

The base op library is fundamentally CSG (AutoCAD paradigm). As domain work matures, new morphologies may be needed:

| Morphology | Trigger domain | What it enables |
|---|---|---|
| L-systems / grammar rules | Natural form, architecture | Branching, growth, recursive tiling |
| Subdivision surfaces | Game assets, organic | Smooth organic forms without SDF |
| Noise / displacement | Terrain, natural texture | Surface detail beyond geometry |
| Voronoi / lattice | Jewelry, structural engineering | Lightweight infill, cellular forms |
| Parametric curves (NURBS) | Industrial design, automotive | Smooth compound surfaces |

**Rule:** don't add a morphology until a domain explicitly demands it and CSG can't approximate it adequately.

---

## Phase 6 — Decompiler (Inverse Procedural Modeling) ⬜ FUTURE

**What:** Takes a finished mesh and reverse-engineers a MeshScript that would produce it.
**Purpose:** Generate SFT training data at scale from open-source CAD libraries.
**Status:** Logged. Do not start until Phase 4 is working — you need a functional designer agent to know what the training data should teach.

---

## Phase 7 — 3D VLM critic ⬜ LONG-TERM RESEARCH

The novel piece. A model trained on `(mesh, spec, critique, correction)` tuples that understands geometry as geometry — not just appearance.
Requires: a working critique loop (Phase 3) running long enough to collect tuples.
Do not scope this until Phase 4 is producing consistent output.

---

## Dependency graph

```
Phase 1 (ops + renderer)
    │
    ├──► Phase 2 (dictionary + pattern library)
    │         │
    │         ├──► Phase 4 (designer agent) ◄──────────────┐
    │         │                                             │
    │         └──► Phase 5 (domain vocabularies) ──────────┤
    │                   ↑ macro-pattern stubs feed here     │
    └──► Phase 3 (critique loop) ──────────────────────────┘
              │
              └── pattern gap log → feeds back into Phase 2
```

---

## Open questions

| Question | Resolve at | Current thinking |
|---|---|---|
| **Critique response format** | Phase 3 | JSON schema preferred; `raw` fallback field for flexibility |
| **How many render views** | Phase 3 | Start with 4 (front/back/left/top); expand to 8 if geometry is missed |
| **Pattern injection strategy** | Phase 4 | Unknown until we see which patterns the LLM reaches for. Hypothesis: always inject Family 6 (positional assembly) + Family 5 (void/interior); retrieve others by keyword match on spec. |
| **Revision budget** | Phase 4 | Start with 3, tune from usage |
| **Domain build order** | Phase 5 | Let Phase 4 agent failures decide. Current guess: mechanical first (clearer ground truth), architecture second (richer composition). |
| **Macro-pattern trigger** | Phase 5 | Build a domain module when the agent reaches for a macro-pattern stub more than 3 times in a session without a satisfying result. |
| **New morphology triggers** | Phase 5+ | Don't decide in advance — let designer agent failure modes surface them |
