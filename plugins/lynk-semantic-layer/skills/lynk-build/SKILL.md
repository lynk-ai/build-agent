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

## Guardrails

Apply these to every edit in `.lynk/`:

- **Suggest, then confirm.** When a required input is missing (descriptions, primary key, relationship cardinality, metric SQL), propose 1–2 concrete options based on the field name, related context, and docs — and offer "or provide your own." Don't write content until the user picks or supplies one. For primary keys, `keys: []` is an acceptable placeholder if the user is unsure.
- **Quality over presence.** A value isn't good just because it's non-empty. Reject and re-ask for: missing or empty descriptions, descriptions that restate the field name (`country_code` → `country_code`), descriptions that are actually another column name (shifted-paste), placeholder text (`TODO`, `tbd`, `xxx`), pasted-in instruction fragments, one-word labels with no usage meaning.
- **Engine-aware SQL.** Read `.lynk/config.json` for the `engine`. Every SQL expression you author (entity metrics, formula features, metric / first_last filters, relationship joins) must be valid for that engine. If `config.json` is missing or `engine` is unset, ask the user.
- **Scope to the request.** Only create the sections the user asked for. "Add entity" means the entity YAML (with its requested features/metrics/first-last) — not unrelated knowledge files, relationships, glossary entries, or other domains.

## Steps

### 1. Identify the Lynk concept type

The Lynk docs live at `https://docs.getlynk.ai`. Ground yourself before acting:

- Fetch the docs tree with `WebFetch https://docs.getlynk.ai/llms.txt` (fallback: `https://docs.getlynk.ai/`) to see what pages exist.
- Fetch `https://docs.getlynk.ai/concepts/` — the Concepts README. Navigate from there to only the pages this task needs. Don't enumerate docs upfront.

From the user's request, determine:
- **Concept type** — which primitive are they asking about?
- **Artifact name** — which specific one (e.g. "player entity", "points_per_game metric", "NBA glossary")?
- **Domain** — default to `default` unless stated otherwise
- Whether the user provided source files (CSV, text, docs) to inform the content

### 2. Locate the artifact in `.lynk/`

The current semantic layer:
```
! find ./.lynk -type f | sort
```

Identify which file(s) own the artifact the user mentioned by scanning the actual filenames and folder structure.

### 3. Read only the files that are relevant

Read the narrowest set of files that gives you enough context to act:

- **Entity** (or its features / metrics): the entity's YAML file first, then its associated knowledge and task-instructions files
- **Metric**: metrics live inside entity YAMLs — find which entity owns it, then read that entity's YAML and context files
- **Relationship**: the relationships file, plus the two entity YAMLs if you need field context
- **Glossary**: only the matching glossary file
- **Clarification policy / output format**: only that single file
- **Domain knowledge / task instructions**: only the domain-level files that match the topic

If the focused files aren't enough (e.g. a metric feature requires seeing the related entity, or a join issue spans two entities), expand to those related files.

### 4. Read the relevant docs (only if needed)

Consult the live Lynk docs via `WebFetch` — navigate from the Concepts README (Step 1) to only the concept page, file-type spec, or guide this task needs. Skip what you already know.

### 5. Use user-provided files

If the user attached or pasted CSV, text, or document files, use them as source data to derive field names, values, definitions, or examples for the semantic layer.

### 6. Warehouse pre-flight (only when creating a new entity from a warehouse table, or when a source table was modified)

Follow `references/scaffold-from-warehouse.md` §Pre-flight + §Fetch. Bring the fetched schema into the plan in Step 7.

### 7. Plan and confirm

Share a concise plan: which files you'll create or edit and the key decisions. Wait for the user to confirm before making any changes.

### 8. Execute step by step

Write or edit one file at a time. Show the user what was written before moving to the next. For warehouse scaffolds, follow `references/scaffold-from-warehouse.md` §Write YAML.

## Output Format

Always respond clearly with the recommendations as bullet points, and use code blocks to show any file content.
Give references from the docs to justify your decisions. If you make assumptions, state them explicitly.
