---
name: lynk-build
description: >
  Build and edit the Lynk semantic layer — add or modify entities, metrics, features,
  relationships, knowledge files, glossary, task instructions, clarification policy,
  output format, and domains in `.lynk/`.

  Use this skill whenever the user asks to add, create, edit, update, define, review,
  improve, enhance, or optimize any semantic layer artifact. Trigger even when "semantic
  layer" isn't mentioned — phrases like "add an entity", "edit a metric", "update the
  glossary", "write task instructions", "change the clarification policy", "add a feature
  to X", "model this table", "help me define Y in Lynk", "improve the knowledge file",
  "enhance the player entity", "optimize the glossary", or any request to improve/fix a
  file inside `.lynk/` all mean this skill should run.
---

# lynk-build-semantics

## Steps

**Never run a "lean" version of this skill.** Every step below is mandatory regardless of how mechanical, repetitive, or large the edit appears. Bulk pass-through edits (e.g. "add 30 fields from this source") feel mechanical but are exactly the situations where skipped doc reads or substituted sub-skill flows produce silently wrong artifacts — the user has no way to tell until something breaks. If you believe a step can be safely skipped in a given case, **tell the user before the work** which step, why, and what's lost by skipping; wait for explicit opt-in. Never confess the shortcut after the fact.

### 1. Read the basic Lynk docs to ground yourself

**Mandatory — do not skip even for bulk pass-through edits.** The vocabulary and primitive list below is what every later step assumes you know.

- Fetch `https://docs.getlynk.ai/concepts.md` to understand the Core Vocabulary and Semantic Layer structure — what Lynk primitives exist: Entity, Feature, Metric, Relationship, Glossary, Domain, Context (knowledge / task-instructions / clarification policy / output format).

For how to navigate the docs (the two anchor pages and walking from the index to leaf pages), see `references/lynk-docs.md`.

### 2. Understand the user's request

From the user's request, determine:
- **Concept type** — which primitive are they asking about?
- **Artifact name** — which specific one (e.g. "player entity", "points_per_game metric", "NBA glossary")?
- **Domain** — default to `default` unless stated otherwise
- Whether the user provided source files (CSV, text, docs) to inform the content

### 3. Locate the artifact in `.lynk/`

The current semantic layer:
```
! find ./.lynk -type f | sort
```

Identify which file(s) own the artifact the user mentioned by scanning the actual filenames and folder structure.

### 4. Read the relevant docs and detect the SQL engine

**Mandatory — do not skip the docs index fetch or the entity-file reads below, even for bulk pass-through edits.** A 30-field "just add these columns" request is exactly where re-reading the entity's knowledge file and task-instructions catches naming conventions, field-visibility rules, and existing groupings that the agent would otherwise miss.

**Always fetch the docs index** with `https://docs.getlynk.ai/llms.txt` to see what pages are available. This is the index of all Lynk docs that you can fetch. It also gives you a sense of how the docs are structured, so you can make informed decisions about which files to read for the most relevant context.

Consult the live Lynk docs via `WebFetch` — only fetch what you need.
Read the narrowest set of files that gives you enough context to act:

#### Entity
Users can ask to build or edit an entity, or ask about an entity's features, metrics, relationships, knowledge, task instructions, clarification policy, or output format. In all cases, the core files to read are:
- the entity's YAML file
- the entity's knowledge files
- the entity's task-instructions files
- the domain-level files for that entity (knowledge, task instructions, clarification policy, output format)

In case the user request is referring multiple entities, read all of them, but avoid reading unrelated entities.

#### Non Entity
- If the user does not ask about an entity or its sub-primitives (metrics, features, relationships or context), and it is clear that they are asking about (might be agent behavior, a glossary term, or a domain-level context file), then read only the relevant file(s). 
If it is not clear, check with the user before moving forward.

#### Detect the SQL engine
Read `.lynk/config.json` for an `engine`, `dialect`, or `warehouse` field (common values: `bigquery`, `snowflake`, `postgres`, `redshift`, `databricks`). If the field is missing, empty, or the file doesn't exist, ask the user via `AskUserQuestion` — do not guess. The dialect drives Rule 7 of `references/content-rules.md`: every SQL snippet you write must be valid in that engine.

### 5. Ground the model in the real source — fields first, then the key

When the user wants to add or extend an entity, model against the source's **actual** columns, description, and keys — never guesses. The catalog already holds all of this, so the default is to go get it, not to ask the user how. Open an `AskUserQuestion` about *how* to obtain columns only when the catalog genuinely can't answer (table still not found after a sync) or the user has said they'd rather paste — not as the opening move.

#### Fetch and read the source

Delegate to `lynk-sources` to pull the source's `description`, `keys`, column count, and column list. Do this before planning — it's the grounding pass.

- **Table name resolves** → surface the table `description` (if any) and the column types/descriptions, so the model reflects what the data *means*, not just column names.
- **Table name doesn't resolve** → don't punt to the user yet. Recommend the closest-matching catalog table name, or offer to run a `sync` (a table added since the last sync won't appear until then). Fall back to asking the user to paste columns only if it still can't be found.
- **Wide table (roughly ≥40 columns)** → don't dump every column or ask the user how to proceed. Lead with a recommended next step: model the core subset the entity's questions actually need first, or group the columns by theme and confirm the grouping. Recommend; don't offload the whole decision.
- **User-provided files** — if the user attached or pasted CSV/text/docs, use those as the column source instead of (or alongside) the catalog.

If the user says "I added fields to X" or "columns of X changed", delegate to `lynk-sources` to sync, refetch fields, and reconcile any field features whose source columns no longer exist.

**Announce the source-fetch step for multi-field adds (≥5 fields).** Before delegating to `lynk-sources`, tell the user explicitly: *"Fetching current source columns via `lynk-sources` first — grounding against the live catalog so we don't model fields that no longer exist or miss ones that were just added."* The user should see the workflow happen, not have to ask afterwards whether the skill grounded itself.

#### Choose the entity key

A `keys` is mandatory and must *uniquely identify a row* — see Rule 11 in `references/content-rules.md` for why a non-unique column is worse than none. Source it from real data, never fabricate it:

1. **Catalog reports `keys`** → use them as-is.
2. **Catalog `keys` is empty** → derive a candidate (a single id-like column, or a composite for the grain) and verify it via `lynk-sources`: `SELECT COUNT(*) AS rows, COUNT(DISTINCT <candidate>) AS distinct_rows FROM <table>` (composite → count the distinct concatenation). Unique iff `rows == distinct_rows` and non-null. **Narrate each attempt** so the user sees the reasoning, not just a verdict.
3. **At most 3 candidates.** One verifies → use it, and say it was *verified*. All 3 fail → stop and escalate via `AskUserQuestion` with the real options (a composite the user knows is unique, an upstream surrogate, or reconsidering the grain).

### 6. Plan and confirm

Share a concise plan: which files you'll create or edit and the key decisions. Wait for the user to confirm before making any changes.

Before drafting the plan, apply every applicable rule in `references/content-rules.md` (the rule index is at the top) to the proposed change, and call out in the plan which rules bear on it and what each requires — build enforces the same rulebook evaluate audits. A few need action *inside the plan*, not just a mental check:
- **Rule 3** — if you noticed misplaced content while reading, offer relocation here, even if it's outside the original request.
- **Rule 8** — fetch the SQL docs Rule 8 lists *before* writing any SQL; don't rely on memory.
- **Rules 10 & 11** — if you're adding an `examples:` entry / `evaluations.yml` case / SQL example, or setting an entity's `keys:`, that rule's procedure is binding (key verification runs in Step 5). State in the plan that you applied it.
- **Rule 12** — before adding a `related_source`, confirm the table is not (and won't become) its own entity and that you won't aggregate it; if either holds, model it as an entity + relationship instead. **When you create a *new* entity, reconcile in the same edit:** grep `.lynk/` for that table used as a `related_source` elsewhere (`! grep -rn "<table>" .lynk/`) and convert any hit to a relationship + entity-sourced feature. Phased modeling is exactly where a table becomes an entity *after* another entity already bolted it on as a related_source — that drift is the failure Rule 12 catches.

### 7. Execute step by step

Write or edit one file at a time. Show the user what was written before moving to the next.

After each file is saved, run the **per-file quick check** (questions 1, 2, 4, 6, 7, 8, 10 from the bottom of `references/content-rules.md` — right place / clear / internally consistent / engine-compatible SQL / Lynk SQL syntax / domain on-topic / keys real). After all files in the edit are saved, run the **cross-file pass** (questions 3, 5, 9, 11 — appears once / references resolve / examples & evaluations valid / related-sources legit), since those checks need every edited file to be on disk first.

Fix or escalate to the user before considering the edit done. Don't silently advance past a failure: if a check fails because of a question only the user can answer (naming, contradicting definitions), surface it before continuing.

**After-action summary (mandatory before Step 8).** Once all files are saved and the cross-file pass is clean, produce a single structured recap so the user can see what happened without reconstructing it from per-file messages. Three sections, in this order, even if a section is empty (in which case say "none"):

- **Done** — what was added, changed, or removed. For bulk edits, lead with counts and grouped highlights (mirror the grouping you used during the edit — e.g., *"Added 28 features to `inventory.yml`: Product condition (5), Packaging condition (5), Bin/location flags (18)"*). Cite file paths.
- **Skipped / deferred + reason** — anything you didn't do that the user might have expected: source columns with no obvious mapping, fields whose type you couldn't confidently infer, naming choices you punted on, content that would have belonged in a file outside the edit's scope, etc. Each item gets an explicit reason.
- **Needs your input** — items you can't decide unilaterally: contradictory definitions, ambiguous naming, fields that may be PII / internal-only and need a visibility call, etc. Phrase each as a concrete question.

This recap is the user's record of the work and the bridge into Step 8. Never skip it for "small" or "obvious" edits.

### 8. Evaluate what you built

**Announce the handoff explicitly before starting.** Open this step with a sentence like *"Now chaining into `lynk-evaluate` to surface content-quality issues beyond schema validity — description quality, cross-file consistency, placement, and Lynk SQL syntax."* The user should see the phase change, not have to ask afterwards whether evaluate ran.

Once all edits are saved, run the `lynk-evaluate` flow targeted at the artifact you just edited (the entity, glossary, or domain file from Step 7) — not the full graph. Evaluate already chains the backend `lynk-validate` call **and** owns the fix-offer + re-evaluation loop (capped at 3 attempts). Just present whatever evaluate returns; **do not** run a parallel fix loop here.

**Never substitute a raw API call for the full `lynk-evaluate` flow.** Calling `POST /semantics/validate` directly (or via `lynk-validate` alone) only runs the backend schema check — it skips the content-rules layer (description quality, cross-file consistency, placement, Lynk SQL syntax, domain coherence) that `lynk-evaluate` adds on top. A "the edit was mechanical enough" reason is not sufficient grounds to substitute; the content-rules layer catches naming and placement issues that have nothing to do with how mechanical the change felt.

Skip this step only if the user **explicitly** opted out ("just add the field, don't evaluate it"). Inferring discretion from the size or apparent simplicity of the edit is not opting out.

## Output Format

Always respond clearly with the recommendations as bullet points, and use code blocks to show any file content.
Give references from the docs to justify your decisions. If you make assumptions, state them explicitly.

## Best Practices
- Always look for conflicts and ambiguities in the context files. Always flag them to the user and ask for clarification before proceeding.
- Never change files before getting user confirmation on the plan. Always be transparent about what you're changing and why.
- Apply `references/content-rules.md` on every edit. Surface out-of-scope misplacements or duplications you notice (Rule 3) — don't silently accept them.
