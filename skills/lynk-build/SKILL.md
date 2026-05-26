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

### 1. Read the basic Lynk docs to ground yourself

- Fetch `https://docs.getlynk.ai/concepts.md` to understand the Core Vocabulary and Semantic Layer structure — what Lynk primitives exist: Entity, Feature, Metric, Relationship, Glossary, Domain, Context (knowledge / task-instructions / clarification policy / output format).

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

### 5. Get source-table fields when modeling entities

When the user wants to add or extend an entity, you need the source table's actual columns to ground the model in real data. Three ways to get them, in order of preference:

- **From the Lynk catalog (preferred)** — delegate to `lynk-sources` to fetch the source's columns. If the source isn't in the catalog yet, lynk-sources will run `POST /api/data-catalog/sources/sync` to pick it up.
- **From user-provided files** — if the user attached or pasted CSV, text, or document files, use those instead.
- **Ask the user** — as a last resort, ask the user to paste the source table's column list (`AskUserQuestion`). Do not guess column names.

If the user says "I added fields to X" or "columns of X changed", delegate to `lynk-sources` to sync, refetch fields, and reconcile any field features whose source columns no longer exist.

### 6. Plan and confirm

Share a concise plan: which files you'll create or edit and the key decisions. Wait for the user to confirm before making any changes.

Before drafting the plan, apply `references/content-rules.md` to the proposed change:
- **Rule 2 (placement)** — confirm the target file is the right place. Use the file-type spec you already fetched in Step 4; fetch now only if you skipped it for this artifact.
- **Rule 1 (single source)** — check that equivalent content doesn't already exist elsewhere in `.lynk/`.
- **Rule 3 (misplaced content)** — surface any misplaced content you noticed during reading; offer relocation in this same plan, even if it's outside the original request.
- **Rule 8 (Lynk SQL syntax)** — fetch the docs listed in Rule 8 of `references/content-rules.md` before writing SQL and follow their spec for the relevant context (feature-definition `sql:` vs `expected_output` / task-instruction / knowledge SQL). Do not rely on memory.
- **Rule 9 (domain coherence)** — when editing a file scoped to a named domain (not `*`), confirm the file has a domain description and the new content fits it. Missing description or off-topic content → offer to draft / relocate in this same plan, per Rule 9.

### 7. Execute step by step

Write or edit one file at a time. Show the user what was written before moving to the next.

After each file is saved, run the **per-file quick check** (questions 1, 2, 4, 6 from the bottom of `references/content-rules.md` — right place / clear / internally consistent / engine-compatible SQL). After all files in the edit are saved, run the **cross-file pass** (questions 3 and 5 — appears once / references resolve), since those checks need every edited file to be on disk first.

Fix or escalate to the user before considering the edit done. Don't silently advance past a failure: if a check fails because of a question only the user can answer (naming, contradicting definitions), surface it before continuing.

### 8. Evaluate what you built

Once all edits are saved, run the `lynk-evaluate` flow targeted at the artifact you just edited (the entity, glossary, or domain file from Step 7) — not the full graph. Evaluate already chains the backend `lynk-validate` call **and** owns the fix-offer + re-evaluation loop (capped at 3 attempts). Just present whatever evaluate returns; **do not** run a parallel fix loop here.

Skip this step only if the user explicitly opted out ("just add the field, don't evaluate it").

## Output Format

Always respond clearly with the recommendations as bullet points, and use code blocks to show any file content.
Give references from the docs to justify your decisions. If you make assumptions, state them explicitly.

## Best Practices
- Always look for conflicts and ambiguities in the context files. Always flag them to the user and ask for clarification before proceeding.
- Never change files before getting user confirmation on the plan. Always be transparent about what you're changing and why.
- Apply `references/content-rules.md` on every edit. Surface out-of-scope misplacements or duplications you notice (Rule 3) — don't silently accept them.
