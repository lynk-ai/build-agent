---
name: lynk-evaluate
description: >
  Judge the *quality* of the Lynk semantic layer's context in `.lynk/` — not its
  validity (that's `lynk-validate`). Read-only: reads the files and the docs and
  assesses placement, description clarity, completeness, cross-file coherence,
  example quality, and modeling correctness the build can't see. Never calls the
  backend or the warehouse.

  Use when the user wants to evaluate, audit, review, or assess how good the
  layer is for the agent. Triggers: "evaluate the semantics", "is this good
  enough for the agent", "audit my entities", "check description quality", "any
  contradictions in my context", "review the glossary". For validity, schema, or
  engine errors, use `lynk-validate`.
---

# lynk-evaluate

Judge whether the semantic layer is *good enough for the agent to use* — well-placed, clearly written, complete, coherent, correctly modeled. **Read-only:** read the `.lynk/` files and the v2 docs; never edit, never call the backend or the warehouse. Validity — schema, references resolving, SQL running on the engine — is `lynk-validate`'s job, not this skill's.

The rulebook is `references/content-rules.md`. The file-type specs the layer is judged against are under `references/docs/concepts/`.

## 1. Decide what to evaluate

If the user didn't say, ask with `AskUserQuestion`. Surface recent work first — include added *and* modified files:

```
! git log --oneline --name-only -20 -- .lynk/ | head -40
```

Offer the 3 most-recently-touched artifacts (an entity / skill / policy folder, or `GLOSSARY.yml` / `LYNK.md`) plus "the whole layer." Collapse each path to its owning artifact and show a clean name (`player entity`, `core glossary`).

## 2. Read the target and its context

| Target | Read |
|---|---|
| An entity | its `schema.yml` + `ENTITY.md` (+ what its prose `@`-injects); if it extends another (`identity: <domain>.<entity>`), also the **parent** entity so `imports:` can be checked; its domain's `LYNK.md` + `GLOSSARY.yml`, and the root's |
| Entity + related | the above for the seed and every entity in its `entity_relationships:` |
| Glossary | root `GLOSSARY.yml` + the domain's (they merge; domain wins) |
| Skill / policy | the `SKILL.md` / `POLICY.md` + every definition it references |
| Whole layer | everything under `.lynk/` — `lynk.yml`, root files, every domain |

Read only what the target needs. **For a large whole-layer eval (many entities), sample rather than read all:** read every top-level / cross-cutting file in full (`lynk.yml`, root + domain `LYNK.md`, every `GLOSSARY.yml`, all skills and policies), then one entity of each distinct *type* plus one full variant group — enough to judge the patterns with evidence. State what you sampled.

## 3. Read the specs it's judged against

Start at `references/docs/SUMMARY.md`, then read only the spec pages (`references/docs/concepts/…`) for the file types in scope. Each spec's body is the standard for what that file *should* contain and how — the authority on "what good looks like." Don't judge from memory. (Navigation: `references/docs/CLAUDE.md`.)

## 4. Evaluate — Phase A: each file against its spec

For every file in scope, identify its type and judge it against its spec and the applicable content rules:

- **Belongs here** — the file holds only what its type is for: SQL/formulas or hardcoded data values kept out of prose (Rules 10, 17); agent *behavior* in a policy/skill and not a knowledge file, reasoning in a skill and not smuggled schema (Rule 2); no legacy/misplaced/unreachable file (Rule 15).
- **Complete** — carries what the spec requires: an entity's grain first, a metric's scale, a physical-identity entity's `keys`; and **`lynk.yml` declares `localization.start_of_week_day`** — mandatory; if absent, flag `needs-client-input` (Rule 18).
- **Clear** — every description is the load decision: concise, says when it applies, discriminates from its siblings, with depth pushed to knowledge (Rule 4).
- **Well-budgeted** — nothing loads eagerly that only some questions need; the glossary carries team vocabulary, not common knowledge; examples teach and are lazy (Rule 14).
- **Right SQL surface & correctly modeled** (what the build can't see) — definitions use the authoring grammar, not query-only constructs (`first()`/`last()`, a physical table where an entity belongs, any templating) (Rule 8); ratios are ratio-of-sums (Rule 12); stock/snapshot measures aren't blindly summed across time (Rule 13); time-varying dimension fields state as-of-vs-current and are used correctly (Rule 16); keys look real — flag a fabricated-key suspicion read-only and point the user to `lynk-sources` to confirm uniqueness; never query here (Rule 11).

Record each finding as: **severity** (error / warning / needs-client-input / suggestion) · **location** (file + field/feature) · what's wrong · how to fix · the `local/content-rules-<N>` tag.

If the layer's own prose already acknowledges an issue (e.g. an `ENTITY.md` that says "assumed key — confirm uniqueness"), still report it, but note the author's caveat as mitigation and you may drop it one severity step.

## 5. Evaluate — Phase B: across files

Only after every in-scope file has a per-file verdict:

- **No contradictions** — definitions that disagree in *meaning* across files → `needs-client-input`; don't pick a side (Rule 5).
- **One home** — the same concept defined twice, or a shared convention (e.g. the fiscal year) restated per-entity instead of stated once in the root `LYNK.md` and referenced (Rules 1, 9).
- **Routing coherent** — when several entities answer the same question class, their when-to-use lines deconflict and no two silently claim the same default (Rule 9).
- **References resolve** — every `@`-injection, cross-entity feature/metric name, and cross-domain import/topology hop resolves (Rule 6a), and every concept the prose implies has a backing definition (Rule 6b).
- **Nothing is orphaned** — every reference/supporting file has an inbound `@`-injection or link; an unreferenced one never loads and is dead content (Rule 15).

The full checklist is the **Quick check** at the bottom of `references/content-rules.md`: Phase A is its per-file questions, Phase B its cross-file ones. Run every item **except engine compatibility (item 6 / Rule 7)** — that's validity, `lynk-validate`'s job. Skip nothing else.

## 6. Report

Lead with the verdict, then findings by severity. If the user asked about one metric/feature/relationship, lead with a focused section on it.

```
## Evaluation — [Target] · [n errors, m warnings, k suggestions]

### Summary
[1–2 sentences: overall health, counts by severity, the single biggest issue]

### Errors (must fix)
- **[location]** [local/content-rules-<N>]: [what's wrong] → [fix]

### Warnings (should fix)
- ...

### Needs client input
- **[location]**: [the contradiction / unresolvable intent] → [what you need from the user]

### Suggestions
- ...

### What looks good
- [specific, well-modeled things — cite them, don't just say "looks good"]
```

Omit any empty section. For a whole-layer evaluation, keep the severity tiers but lead every finding with its file path (and, if the layer is large, add a short per-entity index at the top) so the user can work one artifact at a time. Close with one line: *for structural / engine validity, run `lynk-validate`.*

## 7. Offer fixes and re-evaluate (bounded, hard cap 3)

If there are errors or warnings, this skill owns the fix loop — `lynk-build`'s Step 8 and `lynk-validate` defer here; never run a parallel one.

Each iteration (max 3):

1. **Offer via `AskUserQuestion`.** If errors exist: one option `Fix all <N> errors, then ask about warnings` + `Stop`. If only warnings: present them `multiSelect: true` + `Stop`. Never auto-fix suggestions — mention them, don't offer them.
2. **On opt-in,** delegate the edits to `lynk-build`'s plan-and-confirm and execute steps **only** — not its final evaluate step (this skill is already running the loop; a nested evaluate would recurse). It re-reads the docs, so fixes stay grounded.
3. **Re-check locally:** re-run Steps 2, 4, 5 on the edited files.
4. **Repeat** with the count in the prompt (`Attempt 2 of 3 — <N> remain. Fix? Stop?`). After attempt 3, stop unconditionally: *"Reached the 3-attempt cap; <N> remain — fix manually, or re-run to start a fresh loop."*
5. On `Stop`, exit immediately and leave the remaining issues in the report.

## Output Format

- Reference exact file paths and field/feature names so the user can navigate straight to each finding — say `player/schema.yml → feature: career_points → sql references metric(game.nonexistent_metric)`, not "a feature has an issue."
- Use code blocks for YAML, SQL, and paths.
- Lead with the most important findings; never bury an error at the bottom.
- Offer fixes only after the full report (Step 7).
