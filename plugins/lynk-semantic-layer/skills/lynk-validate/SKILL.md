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

## Guardrails

Apply these when judging correctness and quality:

- **Rule taxonomy is authoritative.** The full list of validation rules (IDs, severities, detection algorithms, cross-file checks, description-quality rules, and the mandatory verification gate) lives in `references/validation-rules.md`. Read it before you validate — every finding in your report should cite a rule ID from that file.
- **Quality over presence.** A value isn't good just because it's non-empty. Surface as **warnings**: missing or empty descriptions (Q3), descriptions that restate the field name (Q1 — `country_code` → `country_code`), descriptions that are actually another column name (Q2, shifted-paste), placeholder text like `TODO`/`tbd`/`xxx` (Q4), pasted-in instruction fragments (Q5), one-word labels with no usage meaning.
- **Duplicates matter.** Explicitly check for: duplicate feature names (Y11), duplicate metric names (Y12), duplicate metric SQL (Y24), duplicate relationship keys (R11), duplicate direction in relationships (R12, `a-b` AND `b-a`), duplicate evaluation names (E8), and duplicate / tautological glossary entries (G4).
- **Cross-file contradictions matter.** Glossary vs metric SQL (G1), knowledge vs YAML (K3), task instructions vs examples and evaluations (T3). A well-formed YAML with wrong cross-file alignment will still produce wrong answers.
- **Engine-aware SQL.** See Step 5a — mandatory engine-compatibility pass against `.lynk/config.json` (rule X1).

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

- Fetch the docs tree with `WebFetch https://docs.getlynk.ai/llms.txt` (fallback: `https://docs.getlynk.ai/`) to see what pages exist.
- Fetch `https://docs.getlynk.ai/concepts/` — the Concepts README — and navigate from there to the file-type spec, concept page, or guide the target actually needs. Don't enumerate docs upfront.

---

### 5. Validate

Apply the rule groups from `references/validation-rules.md` that match the target type. For each issue found, record: **severity** (error / warning / suggestion), **location** (file + field or feature name), **rule ID**, and **what's wrong + how to fix it**.

Rule groups by target:

| Target | Apply rule groups |
|---|---|
| Specific entity | Y1–Y38, EX1–EX6, X1 on that file; C1–C3, G1–G3, G4, K3, K4, T3 on related MD files |
| Glossary | M1–M8 on the glossary file; G1–G4 against metrics, knowledge, task instructions |
| Relationships | R1–R13 |
| Evaluations | E1–E9, plus T3 against task instructions and D3 |
| Full graph | ALL rule groups; fill the mandatory verification gate at the end of `references/validation-rules.md` before writing the report |

#### 5a. Engine-compatibility pass (mandatory) — rule X1

Read `.lynk/config.json` for the `engine`; if missing or unset, ask the user. Scan every SQL site (entity `metrics[].sql`, `formula.sql`, `first_last.filters[].sql`, relationship `joins[].sql`, and every evaluation `expected_output`) for constructs the target engine doesn't support. Common flags: `QUALIFY`, `IFF`, `TRY_CAST`, `DATEADD/DATEDIFF`, `SAFE_*`, `LATERAL FLATTEN`, backtick identifiers, `::` casts, `TOP n`, `INTERVAL` string forms, date-literal shape, multi-resultset `expected_output`. Engine issues inside entity files are **errors**; inside `expected_output` they're **warnings** unless the runner executes the SQL — ask if unclear.

#### 5b. Cross-file verification gate (mandatory for multi-file or full-graph targets)

Before drafting the report, fill the `CROSS-FILE VERIFICATION CHECKLIST` in `references/validation-rules.md`. Every row must have concrete evidence (e.g., "compared glossary term `bet_vertical` to metric `bet_vertical_share` — no contradiction") and a PASS or ISSUE finding. Empty evidence = check not done; go do it before writing the report.

Then proceed with the semantic checks below.

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
- **[Location]** [Rule ID]: [What's wrong] → [How to fix]

### Warnings (should fix)
- **[Location]** [Rule ID]: [What's wrong] → [How to fix]

### Needs client input
- **[Location]** [Rule ID]: [What the rule says] vs [what the example does] → ask the stakeholder which is source of truth

### Suggestions (nice to have)
- **[Location]** [Rule ID]: [What could be improved] → [Suggested improvement]

### What looks good
- [Bullet list of things that are well-modeled — be specific]
```

Always cite the rule ID (from `references/validation-rules.md`) alongside each finding so the user can look up the rule and the detection algorithm.

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
