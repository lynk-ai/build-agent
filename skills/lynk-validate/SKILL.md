---
name: lynk-validate
description: >
  Validate the Lynk semantic layer in `.lynk/` for correctness, completeness, and consistency.

  Use this skill whenever the user asks to validate, check, audit, review, verify, inspect,
  or diagnose the semantic layer or any part of it. Trigger on phrases like "validate the
  semantics", "check the entity", "audit the glossary", "review the evaluations", "is this
  correct", "validate player", "check my metrics", "verify the relationships", "is the semantic
  layer well structured", or any request to assess quality of files inside `.lynk/`.
---

# lynk-validate-semantics

## Steps

### 1. Determine what to validate

If the user has **not** specified what to validate, use the `AskUserQuestion` tool to ask them. Before presenting options, check git history to surface recently edited artifacts:

```
! git log --oneline --diff-filter=M --name-only -20 -- .lynk/ | head -40
```

Use that output to identify the last 3 distinct `.lynk/` artifacts that were modified (entity YAML, knowledge file, task instructions, glossary, evaluations, etc.). Strip the domain path and file extension to present a clean artifact name (e.g., `player entity`, `nba_glossary`, `evaluations`).

Present these options to the user:
- **Option 1** — Last edited artifact (e.g., `player entity`)
- **Option 2** — Second-to-last edited artifact
- **Option 3** — Third-to-last edited artifact
- **Option 4** — Validate the entire semantic graph end-to-end

If git history doesn't yield 3 distinct artifacts, fill remaining slots with sensible defaults (e.g., the glossary, evaluations, or the largest entity in the domain).

Once the user selects, continue to Step 2 with the chosen target.

---

### 2. Locate the target files

Scan the semantic layer file tree to understand what's available:

```
! find ./.lynk -type f | sort
```

Based on the user's selection, identify the relevant files:

| Validation target | Files to read |
|---|---|
| Specific entity | Entity YAML + its knowledge file + its task instructions file + domain knowledge + domain task instructions + glossary |
| Entity + related entities | Same as above, but for the seed entity AND every entity it is related to (via `entities_relationships.yml`) |
| Glossary | The glossary file only |
| Full semantic graph | All entity YAMLs + all knowledge/task instruction files + glossary + domain context + evaluations + relationships |
| Evaluations | `evaluations.yml` + all entity YAMLs (to verify references) |

If the user asked about a **specific metric, feature, or relationship** on an entity, still validate the full entity context — but lead your response output with the specific item they asked about.

---

### 3. Read the target files

Read only the files identified in Step 2. For entity validation, read in this order:
1. Entity YAML
2. Entity knowledge file
3. Entity task instructions file
4. Domain knowledge + domain task instructions
5. Glossary

For multi-entity validation (seed + related), read `entities_relationships.yml` first to determine the related entity set, then read each entity's files.

---

### 4. Read the relevant docs

Check rules or best practices during validation by consulting the live Lynk docs — only fetch what you actually need:

- Start with `WebFetch https://docs.getlynk.ai/` (or `https://docs.getlynk.ai/llms.txt` if present) to discover available pages.
- Concept pages: `https://docs.getlynk.ai/concepts/<concept>` (entity, feature, metric, relationship, glossary, domain, context, data-modeling, evaluations, agent).
- File-type specs: `https://docs.getlynk.ai/file-types/<type>` (entity, relationships, glossary, evaluations, task-instructions, clarification-policy, output-format, knowledge).
- Guides: `https://docs.getlynk.ai/guides/<topic>`.

---

### 5. Validate

Apply the checklist that matches the target type. For each issue found, record: **severity** (error / warning / suggestion), **location** (file + field or feature name), and **what's wrong + how to fix it**.

per file you validate, create a checklist of potential issues to look for based on the relevant docs files.

---

### 6. Produce the validation report

Structure your output as follows:

**If the user asked about a specific metric / feature / relationship:** Lead with a focused section on that specific item — its validation result, any issues, and suggested fixes — before the broader entity report.

**Report structure:**

```
## Validation Report — [Target Name]

### Summary
[1-2 sentences: overall health, number of issues by severity]

### Errors (must fix)
- **[Location]**: [What's wrong] → [How to fix]

### Warnings (should fix)
- **[Location]**: [What's wrong] → [How to fix]

### Suggestions (nice to have)
- **[Location]**: [What could be improved] → [Suggested improvement]

### What looks good
- [Bullet list of things that are well-modeled — be specific]
```

If no issues are found in a severity tier, omit that section entirely.

For **full graph validation**, group findings by entity/file rather than by severity tier, so the user can focus on one entity at a time.

For **evaluations validation**, group findings by evaluation name and add a coverage summary at the top showing entity distribution.

---

## Output Format

- Use code blocks when quoting YAML field names, feature names, or SQL snippets
- Reference exact file paths so the user can navigate directly
- Be specific about locations — say `player.yml → feature: career_points → metric: nonexistent_metric` not just "a feature has an issue"
- Lead with the most important findings; don't bury critical errors at the bottom
- If you find issues in the files, offer to fix them — but only after completing the full report
