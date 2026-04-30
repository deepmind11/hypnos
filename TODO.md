# TODO

Tracks what to build, in order. Each phase = a separate commit.

## Phase 0 — Decisions (resolved)

- [x] **Story structure** — bedtime-tuned three-act: gentle setup → mild conflict → soothing resolution.
- [x] **Output schemas** — Validator/Censor: `{"pass": bool, "feedback": str}`. Judge: `{"approved": bool, "feedback": str}`. Use OpenAI JSON mode.
- [x] **Per-agent temperatures** — Writer 0.7; Judge 0.3; Censor 0.0; Validator 0.0.
- [x] **Writer → Judge payload** — full current draft each round (diffs deferred).
- [x] **Iteration cap** — 3 per Writer↔Judge session. Counter resets on censor rejection or user revision.

## Phase 0.5 — Decisions

- [x] **Tracing** — stdout + JSONL trace file. Zero cloud. Langfuse deferred.
- [x] **Eval** — pytest suite under `tests/`.
- [x] **Schema validation** — OpenAI JSON mode only for now. Parse with `json.loads`. Pydantic deferred (see deferred section).
- [x] **Per-session token budget** — 50,000 tokens (cumulative across all agent calls in one user request). ~3× worst-case headroom.
- [x] **Counter-reset semantics** — Writer→Judge round = +1. Reset to 0 only on Censor rejection or user revision. Cap = 3 → abort.

## Phase 1 — Foundation (one commit)

- [ ] Add a small `Agent` abstraction: wraps the OpenAI call, takes `system_prompt`, `temperature`, `model`. Replace the inline `call_model` in `main.py`.

## Phase 2 — Single-shot agents (one commit each)

- [ ] **Validator** — input → `{pass, message}`. Wire at input.
- [ ] **Censor** — input → `{pass, reason}`. Wire after Validator on input. (Reuse for output later.)
- [ ] **Writer** — prompt → story. Single shot, no Judge yet. Verify quality of single-shot output before adding the loop.

## Phase 3 — Writer ↔ Judge loop

- [ ] **Judge** — `(original prompt, current draft, prior feedback) → {approved, feedback}`. Single shot.
- [ ] Wire Writer ↔ Judge with iteration cap + "could not generate" fallback.
- [ ] Add Censor as the final gate on the approved story. On failure, re-enter the Writer ↔ Judge loop (known limitation; deferred).

## Phase 4 — Story state & user revision

- [ ] Add the `Current Story State` shared object + a `user_prompt_history` list.
- [ ] Allow the user to ask for changes after delivery → kick off another W↔J round (counter resets).
- [ ] Pass the full `user_prompt_history` to the Judge alongside the current draft so it can evaluate against every request the user has made.

## Phase 5 — Iteration

- [ ] Test with a handful of real prompts; observe output quality.
- [ ] Tune system prompts (length, vocabulary, structure adherence, calming ending).
- [ ] Tune temperatures.

## Deferred (notes only — do not build now)

- Context compaction for Judge & Writer when histories grow.
- Diff-only payloads from Writer to Judge.
- What to retain when summarising a Judge-approved block.
- Token / cost / wall-clock budget guards beyond the iteration cap.
- Logging / observability layer for the multi-agent flow (during dev: just print each agent's I/O).
- Evaluation harness with a fixed set of test prompts.
- External data sources (none planned).
- Pydantic schema validation for agent responses (currently raw `json.loads`).

## Notes — story structure for ages 5–10

From research:

- **Three-act** (Setup → Confrontation → Resolution) and **Hero's Journey** (Departure → Initiation → Return) are the dominant frameworks. Both work for kids' fiction.
- **For bedtime specifically**, sources are consistent: gentle beginning, mild and easily-resolved conflict (no high-stakes drama or fear), and a **soothing resolution** that returns the character to comfort and safety. Cozy wind-down language ("safe", "cozy", "snuggled", "dream") at the end.
- Recommendation for v1: use a **bedtime-tuned three-act**: opening calm → small adventure or problem → gentle resolution that lands on a sleepy / cozy note. Hero's Journey is usable but its resolution beat must be tamed; three-act is the simpler primary.
- The Judge's rubric should explicitly check: structure present, age-appropriate vocabulary, sentence simplicity, calming ending, length ~500–600 words.

## Notes — components flagged as missing from baseline plan

1. **Structured outputs.** Validator / Censor / Judge responses need to be machine-parseable for the loop to act on them reliably. Without it, control flow gets fragile (regex on prose).
2. **Logging.** Debugging a multi-agent pipeline is painful without per-turn traces. At minimum, print each agent's input + output during development.
3. **Termination budgets** beyond the iteration cap — token spend or wall-clock cap, in case an agent gets verbose.
4. **Error handling.** API failures, rate limits, malformed agent responses. Even a basic retry-once-then-abort.
5. **Evaluation.** Without a small bank of test prompts, prompt-tuning is guesswork.

