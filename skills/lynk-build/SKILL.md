---
name: lynk-build
description: >
  Build and edit the Lynk semantic layer — add or modify entities, metrics, features,
  relationships, knowledge files, glossary, task instructions, clarification policy,
  output format, and domains in `.lynk/`.

  Use this skill whenever the user asks to add, create, edit, update, define, review,
  improve, enhance, fix or optimize any semantic layer artifact. Trigger even when "semantic
  layer" isn't mentioned — phrases like "add an entity", "edit a metric", "update the
  glossary", "write task instructions", "change the clarification policy", "add a feature
  to X", "model this table", "help me define Y", "improve the knowledge file",
  "enhance the player entity", "optimize the glossary", or any request to improve/fix a
  file in the `.lynk/` directory mean this skill should run. Use it also when the user complains about the ask agent not working properly — the issue might be in the semantic layer and this skill can fix it.
---

# lynk-build-semantics

## Steps

### 1. Detect the customer's SQL engine

The SQL engine is:
```
! bash skills/lynk-build/references/get_engine.sh
```
Keep it in mind throughout all subsequent steps — it informs how you write SQL expressions (e.g. date functions, quoting style, dialect-specific syntax).

#### If the engine is not detected, ask the user to provide it
- If the engine is `unknown`, ask the user: **"Which SQL engine are you using? (e.g. Snowflake, BigQuery, Redshift, DuckDB, etc.)"**
- Once the user answers, make sure the answer makes sense and its a known engine, then write or update `.lynk/config.json` with the value:
  ```json
  {
    "engine": "<user-provided engine>"
  }
  ```
  If the file already exists with other keys, merge — do not overwrite the whole file.

### 2. Ground yourself in the docs

Learn about Lynk's Semantic Graph concepts:
- Fetch `https://docs.getlynk.ai/concepts/` to refresh the Core Vocabulary — what Lynk primitives exist: Entity, Feature, Metric, Relationship, Glossary, Domain, Context (knowledge / task-instructions / clarification policy / output format).

### 3. Ground yourself in the user's existing semantic graph located in `.lynk/`

The current semantic graph files:
```
! find ./.lynk -type f | sort
```

### 4. Connect the user's request to the relevant concepts and files
From the user's request, determine:
- **Concept type** — which primitive are they asking about? An Entity? A Metric? A Relationship? Glossary? Domain? Context (knowledge, task instructions, clarification policy, output format)?
- **Artifact name** — which specific one, based on the files existing in `.lynk/`?
- **Domain** — default to `default` unless stated otherwise

### 5. Read the relevant docs

- Fetch the docs index at `https://docs.getlynk.ai/llms.txt` to see what pages are available.
- Navigate to the relevant page(s) based on the concept type and artifact name you identified in step 4 and read the relevant docs carefully. Only fetch what you need accoreding to the infornation you gathered so far.

### 6. Read the relevant semantic graph files

Identify which file(s) own the artifact the user mentioned by scanning the actual filenames and folder structure.
If the user is asking about metrics or features, find which entity owns them. If they're asking about a relationship, find which entities are involved.

- **Domain**: always read the domain-level knowledge files and task instructions based on the domain you identified. If no domain was identified, default to `default` domain files.

Read the narrowest set of files that gives you enough context to act:
- **Entity**: (or its features / metrics): the entity's YAML file, and its associated knowledge and task-instructions files
- **Metric**: metrics live inside entity YAMLs — find which entity owns it, then read that entity's YAML and context files
- **Relationship**: the relationships file, plus the two entity YAMLs if you need field context
- **Glossary**: only the matching glossary file
- **Clarification policy**: only the clarification policy file
- **Output format**: only the output format file

If the focused files aren't enough (e.g. a metric feature requires seeing the related entity, or a join issue spans two entities), expand to those related files.

### 7. Use user-provided files

If the user attached or pasted CSV, text, or document files, use them as source data to derive field names, values, definitions, or examples for the semantic layer.

### 8. Plan and confirm

Create an action plan based on all the information you've gathered:
- Which files will you create or edit?
- What are the key decisions you made based on the docs and the user's existing semantic graph?

In case there is any missing information that is critical to the plan, ask the user to provide it before you start writing or editing files.

Share a concise plan: which files you'll create or edit and the key decisions. Wait for the user to confirm before making any changes.

### 9. Execute step by step

Write or edit one file at a time. Show the user what was written before moving to the next.

## Output Format

Always respond clearly with the recommendations as bullet points, and use code blocks to show any file content.
Give references from the docs to justify your decisions. If you make assumptions, state them explicitly.
