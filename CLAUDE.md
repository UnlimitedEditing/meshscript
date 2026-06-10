# MeshScript — Project Context (D:\tripostl\meshscript)

This file orients a fresh conversation picking up mid-stream. For the long-term
phase plan see `ROADMAP.md`. For the language/op reference see `docs/`.

## Current status (as of 2026-06-10)

**The Graydient pipeline is LIVE and renders end-to-end:**

- `gen_meshscript_txt2mesh_v1.py` → `GraydientWorkflow-meshscript-txt2mesh-v2.json`
- `gen_meshscript_mesh2mesh_v1.py` → `GraydientWorkflow-meshscript-mesh2mesh-v2.json`

Both deployed via Graydient backup/restore. Pipeline:
`MeshScriptLLMLoader (Qwen2.5-Coder-7B, transformers, GPU device_map=auto)
 → MeshScriptLLMGen/Revise → MeshScriptExecute → SaveMeshWithScript
 → MeshSmuggleGate(enable=1) → SmuggleMeshAsImage`

The `SmuggleMeshAsImage` tail (from `github.com/UnlimitedEditing/Meshsmuggler`) was
just added to fix `success:false / timed_out:true / assets:[]` — Graydient only
collects IMAGE-type WebSocket outputs, and the GLB now travels home as a
steganographic PNG. This part is working — first real end-to-end render succeeded
(GPU, ~48s, GLB saved, PNG returned).

## ACTIVE BUG — translation quality (the real work starts here)

**Symptom:** Prompt `"32 tooth gear 1:6 width to height profile /xray"` produced a
single long plain cylinder — not a gear, no teeth, no profile shaping. Repeat
prompts show the same pattern: output looks like only the *first build step* of
a typical multi-step `.ms` file (compare to `examples/*.ms`, which all have
5-15 `show()` checkpoints).

**Two competing hypotheses, not yet distinguished:**

1. **Prompt contamination** — the `prompt` field Graydient sends to
   `MeshScriptLLMGen` may be the *raw bot command string*
   (`/wf /run:build-mesh 32 tooth gear 1:6 width to height profile /xray`)
   rather than a cleaned design spec. A 7B model fed bot-command syntax
   (`/wf`, `/run:build-mesh`, `/xray`) as part of "Design spec: ..." could
   plausibly degrade to a minimal fallback script. **Cheapest thing to check
   first** — log the raw `prompt` value `MeshScriptLLMGen.generate()` actually
   receives.

2. **Generation quality** — Qwen2.5-Coder-7B with `context_level="base"`
   (just `prompt/system-prompt.md`, no patterns/reference) and
   `max_tokens=2048` may simply be producing a short, minimal script regardless
   of spec quality — either because the system prompt (155 lines) leaves little
   budget/attention for a long multi-step response, or `max_tokens` truncates a
   longer script before its closing ` ``` ` fence (in which case
   `_extract_script` would currently fail entirely — but since *something*
   rendered, the fence did close, meaning the model *chose* to stop early).

**Debugging plan (not yet implemented):**

- Add full I/O logging to `nodes_llm.py`:
  - `_chat_complete`: print the exact rendered chat-template string (or at least
    the user message) and the full raw decoded output (char count + content),
    not just the post-extraction script.
  - `MeshScriptLLMGen.generate` / `MeshScriptLLMRevise.revise`: print the
    `prompt` / `edit_prompt` argument verbatim as received from Graydient,
    before any processing — this directly tests hypothesis 1.
- Add compiler/executor feedback to `nodes.py` `MeshScriptExecute.execute()`:
  - Print the full generated script (with line numbers) to stdout before
    executing, so Graydient logs show exactly what ran.
  - On exception, print the full traceback to stdout (currently only returned
    on the `error` output pin, which nothing downstream surfaces in this
    workflow — it's invisible in the Graydient log).
  - Print a one-line summary: number of `show()` checkpoints vs. expected
    (sanity signal for "only first build step" pattern).
- Once logs are visible, do one more Graydient run with the same gear prompt
  and read back: raw prompt in → raw LLM output → extracted script → execution
  trace. That will tell us which hypothesis (or both) is correct.

**Likely follow-on fixes once root-caused:**
- If hypothesis 1: strip bot command syntax before it reaches `prompt` (either
  in the bot/wrapper layer, or defensively in `MeshScriptLLMGen`).
- If hypothesis 2: bump `max_tokens` (e.g. 2048 → 4096), consider few-shot
  example(s) in the generation user-message (one full `.ms` example with
  5+ `show()` steps), or raise `context_level` default to `+patterns`.
- Either way, this bug is exactly the gap **Phase 3 (critique loop)** and
  **Phase 4 (designer agent)** in `ROADMAP.md` are designed to close — a
  single LLM shot with no feedback loop will always be fragile for anything
  beyond trivial primitives. The `critique/` and `agent/` scaffolding already
  exists locally (per Phase 3/4 status) but is not wired into the Graydient
  workflow yet — that's the longer-term direction once the immediate
  generation bug is understood.

## Key files for this debugging session

- `D:\ComfyUI-MeshScript\nodes_llm.py` — `_chat_complete`, `MeshScriptLLMGen`,
  `MeshScriptLLMRevise` — where prompt/response logging needs to be added.
- `D:\ComfyUI-MeshScript\nodes.py` — `MeshScriptExecute.execute()` — where
  compiler/execution feedback needs to be added.
- `D:\tripostl\meshscript\sandbox\executor.py` — `run()` already prints
  `[show:label] N verts M faces watertight=...` per checkpoint; traceback is
  in `result["error"]` but not printed.
- `D:\tripostl\meshscript\examples\*.ms` — reference scripts showing expected
  multi-step structure (mug.ms, toy_car.ms, ops_test.ms).
- `D:\tripostl\meshscript\prompt\system-prompt.md` — current system prompt
  (base context level).

## Repos (all under github.com/UnlimitedEditing/)

| Repo | Local path | Role |
|---|---|---|
| `meshscript` | `D:\tripostl\meshscript` | DSL library (ops, sandbox, docs, roadmap) |
| `ComfyUI-MeshScript` | `D:\ComfyUI-MeshScript` | ComfyUI node package (LLM + execute/save/load nodes) |
| `Meshsmuggler` | `D:\Meshsmuggler` | GLB↔PNG steganography (asset-collection workaround) |

`.env` in `D:\tripostl\meshscript\.env` holds `OPENROUTER_API_KEY` — gitignored,
never commit.
