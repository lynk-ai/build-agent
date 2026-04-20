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

### 1. Identify the Lynk concept type

The available docs:
```
! find .claude/skills/docs -type f | sort
```

Read `.claude/skills/docs/concepts/README.md` (the Core Vocabulary section) to ground yourself in what Lynk primitives exist: Entity, Feature, Metric, Relationship, Glossary, Domain, Context (knowledge / task-instructions / clarification policy / output format).

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

From the docs file tree injected in step 1, identify and read the files most relevant to the artifact type and task — guides, file-type references, or concept pages. Read only what you need; skip what you already know.

### 5. Use user-provided files

If the user attached or pasted CSV, text, or document files, use them as source data to derive field names, values, definitions, or examples for the semantic layer.

### 6. Plan and confirm

Share a concise plan: which files you'll create or edit and the key decisions. Wait for the user to confirm before making any changes.

### 7. Execute step by step

Write or edit one file at a time. Show the user what was written before moving to the next.

## Output Format

Always respond clearly with the recommendations as bullet points, and use code blocks to show any file content.
Give references from the docs to justify your decisions. If you make assumptions, state them explicitly.
