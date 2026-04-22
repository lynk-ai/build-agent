# Lynk Validation Rules

Enumerated rules used by the `lynk-validate` skill. Each rule has an ID, severity, and a short "what it checks" line. The skill should treat this as the authoritative checklist — scan every relevant file against every applicable rule group, record findings, and report them in the format prescribed by `SKILL.md`.

Severity levels:
- **ERROR** — causes wrong SQL, runtime failures, or broken loading. Must fix.
- **WARNING** — will confuse the agent and lead to wrong answers, but won't crash. Should fix.
- **NEEDS_CLIENT_INPUT** — contradiction where the correct answer depends on domain knowledge (example follows client's actual behavior vs stated rule). Surface both sides; do not auto-fix.

---

## Entity YAML rules (Y1–Y38)

### Structure & syntax

| Rule | Name | Severity | What it checks |
|---|---|---|---|
| Y1 | YAML syntax | ERROR | Valid YAML, parseable, proper indentation |
| Y2 | Entity required fields | ERROR | Entity has `name`, `key_source` (or `key_table`), and non-empty `keys` array |
| Y25 | Unknown feature type | ERROR | Feature `type` is one of: `field`, `metric`, `formula`, `first_last` |
| Y26 | Broken YAML values | ERROR | Unquoted strings with colons, tabs vs spaces, trailing whitespace, missing space after colon, unclosed quotes |
| Y29 | Entity name ≠ filename | ERROR | `name:` field inside YAML matches filename without `.yml` |
| Y33 | Properties under wrong section | ERROR | Features under `metrics:` or metrics under `features:` — structural confusion |
| Y35 | Unicode / invisible characters | ERROR | Non-ASCII in names/keys (smart quotes, em dashes, zero-width chars) |
| Y38 | Description field presence | ERROR | Every element that supports `description` has the key present. Value can be `''` but the key must exist. Applies to ALL yml files |

### Feature required properties (Y3)

| Feature type | Required properties |
|---|---|
| `field` | `type`, `name`, `description`, `data_type`, `source` (or `asset`), `field`, `join_name` (nullable), `time_field` (nullable), `filters` (can be `[]`) |
| `metric` | `type`, `name`, `description`, `data_type`, `source` (or `asset`), `metric` (or `measure`), `join_name`, `time_field`, `filters` |
| `formula` | `type`, `name`, `description`, `data_type`, `sql` |
| `first_last` | `type`, `name`, `description`, `data_type`, `source` (or `asset`), `join_name`, `time_field`, `filters`, `options` (with `method`, `sort_by`, `field`, `data_type`) |

### SQL correctness

| Rule | Name | Severity | What it checks |
|---|---|---|---|
| Y4 | Missing `{}` in metric SQL | ERROR | `metrics[].sql` references features without `{feature_name}` wrapping |
| Y5 | Missing `{}` in formula SQL | ERROR | Formula `sql` references features without `{feature_name}` wrapping |
| Y6 | METRIC() wrapping | ERROR | No `SUM(METRIC(...))`, `AVG(METRIC(...))`, etc. — METRIC() is standalone. Also check formula SQL and `expected_output` |
| Y18 | Formula aggregate prohibition | ERROR | Formula `sql` does NOT contain aggregates (SUM, AVG, COUNT, MAX, MIN, RATIO_TO_REPORT) |
| Y22 | Circular formula dependencies | ERROR | No cycles in the formula dependency graph |
| Y30 | Metric SQL without aggregation | WARNING | Metric `sql` contains at least one aggregate |
| Y34 | Unbalanced SQL syntax | ERROR | Balanced parentheses, closed quotes, closed CASE/WHEN with END |

### Data types & naming

| Rule | Name | Severity | What it checks |
|---|---|---|---|
| Y9 | data_type validity | ERROR | `data_type` is one of: `string`, `number`, `boolean`, `datetime` |
| Y10 | data_type consistency | WARNING | Metric features → `number`; arithmetic operands → `number`; date functions → `datetime` |
| Y21 | Naming conventions | WARNING | Names are lowercase with underscores |
| Y28 | Empty / null critical fields | ERROR | `name` empty/null, `description` literal `null`, `sql` empty for metrics/formulas, `source` empty |

### References & dependencies

| Rule | Name | Severity | What it checks |
|---|---|---|---|
| Y7 | Feature existence in references | ERROR | Every `{feature_name}` in metric/formula SQL resolves to a feature `name` in the same entity |
| Y8 | Metric existence | ERROR | `metric` features' `metric:` property references a metric in the entity's `metrics:` section |
| Y11 | Duplicate feature names | ERROR | No two features share `name` |
| Y12 | Duplicate metric names | ERROR | No two metrics share `name` |
| Y23 | Duplicate feature SQL | WARNING | Same effective definition (source + field/metric/sql + join_name + filters all identical) |
| Y24 | Duplicate metric SQL | ERROR | Same `sql` expression (after normalizing whitespace) in two metrics |
| Y27 | Orphan features | WARNING | Feature references a `source` entity with no relationship in `entities_relationships.yml` |
| Y31 | Self-referencing source | ERROR | `metric`/`first_last` with `source` equal to own entity name |
| Y32 | Copy-paste contamination | WARNING | Entity `name: A` but features reference `source: A` (self) for field features, or examples use wrong entity name |
| Y36 | Stale feature references | WARNING | Reference doesn't match any feature but a similar name exists (Levenshtein ≤ 2) |

### Sources & relationships

| Rule | Name | Severity | What it checks |
|---|---|---|---|
| Y13 | Source validation | WARNING | Feature `source`/`asset` exists in `key_source`/`key_table`, `related_sources`/`related_assets`, or as another entity name |
| Y14 | Relationship-type vs feature-type | WARNING | `metric`/`first_last` require one-to-many or many-to-many; cross-entity `field` requires many-to-one or one-to-one |
| Y19 | Join name validity | WARNING | If `join_name` is not null, it matches a join name in `entities_relationships.yml` |
| Y20 | time_field validity | WARNING | If `time_field` is not null, it references a `datetime` feature |

### Filters

| Rule | Name | Severity | What it checks |
|---|---|---|---|
| Y15 | Filter structure | ERROR | Valid `type` (`field`/`sql`), valid `operator`, correct `values` count |
| Y16 | Filter field existence | WARNING | Filter `field` exists as feature (entity-sourced) or column (table-sourced) |
| Y17 | first_last options completeness | ERROR | `options` has `method`, `sort_by`, `field`, `data_type`. `offset` is a positive integer |
| Y37 | Filters on wrong feature type | ERROR | `field` feature has entity-feature filters instead of table-column filters, or vice versa |

---

## Relationship rules (R1–R13)

| Rule | Name | Severity | What it checks |
|---|---|---|---|
| R1 | YAML syntax | ERROR | Valid YAML, parseable |
| R2 | Required structure | ERROR | Top-level `relationships` key exists (object, not null) |
| R3 | Relationship type validity | ERROR | `relationship` is one of: `one_to_one`, `one_to_many`, `many_to_one`, `many_to_many` |
| R4 | Joins required | ERROR | Each relationship has a `joins` array with ≥1 join |
| R5 | Join structure | ERROR | Each join has `type` (`fields`, `sql`, or `lookup`) with correct sub-structure |
| R6 | Default join | WARNING | Each relationship has exactly ONE join with `default: true` |
| R7 | Entity existence in keys | WARNING | Both entities in `{entity1}-{entity2}` key exist as YAML files |
| R8 | Join operator validity | ERROR | Operators are: `equal`, `gte`, `lte`, `gt`, `lt` |
| R9 | SQL placeholders | WARNING | SQL-type joins use `{source}` and `{destination}` placeholders |
| R10 | Relationship key naming | WARNING | Keys follow `{entity1}-{entity2}` (lowercase, hyphen-separated) |
| R11 | Duplicate relationship keys | ERROR | Two relationships with the same key name |
| R12 | Duplicate direction | ERROR | Both `entity_a-entity_b` AND `entity_b-entity_a` defined. Relationships are **unidirectional** — each pair defined ONCE |
| R13 | Orphan relationships | WARNING | Relationship exists but no feature in either entity uses it |

---

## Evaluation rules (E1–E9)

| Rule | Name | Severity | What it checks |
|---|---|---|---|
| E1 | YAML syntax | ERROR | Valid YAML, parseable |
| E2 | Test case structure | ERROR | Each test case has `name`, `input`, `expected_output` |
| E3 | METRIC() wrapping | ERROR | Apply Y6 to all `expected_output` SQL |
| E4 | Entity references | WARNING | `entity("name")` references match existing entity names |
| E5 | Metric references | WARNING | `METRIC(name)` references match existing metrics |
| E6 | Feature references | WARNING | `t.feature_name` references match existing features |
| E7 | Tags validity | WARNING | `tags.difficulty` is `EASY`, `MEDIUM`, or `HARD` |
| E8 | Duplicate test names | ERROR | No two test cases share `name` |
| E9 | Stale expected_output | WARNING | References a renamed/deleted metric or feature |

---

## Entity example rules (EX1–EX6)

| Rule | Name | Severity | What it checks |
|---|---|---|---|
| EX1 | Example structure | ERROR | Each example has `input` and `expected_output` |
| EX2 | METRIC() wrapping | ERROR | Apply Y6 to example `expected_output` SQL |
| EX3 | Entity self-reference | WARNING | `entity("name")` matches the entity's own name |
| EX4 | Metric references | WARNING | `METRIC(name)` references match entity's metrics |
| EX5 | Feature references | WARNING | `t.feature_name` references match entity's features |
| EX6 | `{}` syntax in SQL | ERROR | Example SQL does NOT use `{feature_name}` — uses `t.column_name` |

---

## Markdown rules (M1–M8)

| Rule | Name | Severity | What it checks |
|---|---|---|---|
| M1 | Frontmatter exists | ERROR | Every .md file has YAML frontmatter |
| M2 | Type field | ERROR | Frontmatter `type` is one of: `knowledge`, `behavior`, `task-instructions`, `glossary` |
| M3 | Domain field | ERROR | Has `domain` field (`"*"` for global, or domain name) |
| M4 | Entity field (conditional) | ERROR | Entity-level files have `entity:` matching the entity name |
| M5 | Tasks field (conditional) | ERROR | Task instruction files have `tasks:` |
| M6 | Kind field (conditional) | WARNING | Behavior files have `kind` (`clarification_policy`, `output_format`) |
| M7 | Frontmatter YAML syntax | ERROR | Frontmatter is valid YAML between `---` delimiters |
| M8 | Markdown SQL blocks | WARNING | SQL code blocks don't contain `SUM(METRIC(...))` or other anti-patterns |

---

## Cross-file consistency rules

### Glossary (G1–G4)

| Rule | Name | Severity | What it checks |
|---|---|---|---|
| G1 | Glossary ↔ metric SQL | WARNING | Glossary definition doesn't contradict the metric SQL it maps to |
| G2 | Glossary ↔ knowledge files | WARNING | Glossary terms consistent with knowledge file definitions |
| G3 | Glossary ↔ task instructions | WARNING | Glossary terms consistent with task instruction usage |
| G4 | Glossary duplicate / tautological / empty | WARNING | Two entries for the same concept (different slugs), term equals description (`country_code` → `country_code`), description is literally another column name (shifted-paste), placeholder text (`TODO`, `tbd`, `xxx`), or pasted-in fragment from another row |

### Knowledge (K1–K4)

| Rule | Name | Severity | What it checks |
|---|---|---|---|
| K1 | Business ↔ entity knowledge | WARNING | Segment values and terms match across levels |
| K2 | Domain ↔ entity knowledge | WARNING | Entities/metrics mentioned in domain knowledge exist |
| K3 | Entity knowledge ↔ entity YAML | WARNING | Features/metrics described in knowledge exist in YAML |
| K4 | Entity knowledge ↔ task instructions | WARNING | Concept definitions don't contradict |

### Task instructions (T1–T4)

| Rule | Name | Severity | What it checks |
|---|---|---|---|
| T1 | Domain ↔ entity instructions | WARNING | Domain rules not contradicted by entity instructions |
| T2 | Instructions ↔ examples (same file) | WARNING | Rules followed by examples in same file |
| T3 | Instructions ↔ entity YAML examples & evaluations | WARNING | Rules followed by examples in entity YAML and `evaluations.yml` |
| T4 | Anti-pattern enforcement | WARNING | No example violates explicit anti-patterns |

### Behavior (B1–B2)

| Rule | Name | Severity | What it checks |
|---|---|---|---|
| B1 | Output-format ↔ glossary | WARNING | Referenced terms exist in glossary |
| B2 | Clarification ↔ knowledge | WARNING | Referenced concepts exist in entity knowledge |

### Content references (C1–C3)

| Rule | Name | Severity | What it checks |
|---|---|---|---|
| C1 | Feature refs in MD ↔ YAML | WARNING | Feature names in markdown exist in relevant entity YAML |
| C2 | Metric refs in MD ↔ YAML | WARNING | `METRIC(name)` references in markdown match existing metrics |
| C3 | Entity refs in MD ↔ files | WARNING | `entity("name")` references in markdown match existing entity files |

### Missing metric definitions (D1–D3)

| Rule | Name | Severity | What it checks |
|---|---|---|---|
| D1 | Context describes aggregation without metric | WARNING | Knowledge/glossary/task-instructions describe an aggregation (e.g., "total revenue", "avg order value") but no metric exists in any entity's `metrics:` — the agent will write raw aggregation SQL instead of calling `METRIC()` |
| D2 | Task instruction references undefined metric | ERROR | Task instruction references a metric name (backtick or METRIC(name)) that doesn't exist in any entity YAML |
| D3 | Evaluation uses undefined metric | ERROR | Evaluation `expected_output` contains `METRIC(name)` where `name` doesn't exist in any entity's `metrics:` |

### Description quality (Q1–Q5)

Quality-of-description rules — flag these as WARNING so the user sees them even when the YAML is structurally valid.

| Rule | Name | Severity | What it checks |
|---|---|---|---|
| Q1 | Tautological description | WARNING | `description` equals the field/term/metric name (`Bonus Redeemed Amount` → `Bonus Redeemed Amount`) or is just the column name |
| Q2 | Shifted-paste description | WARNING | `description` looks like the name of a different, adjacent field — pattern: matches another field's `name` or `field` in the same file (especially the next row in a table paste) |
| Q3 | Empty description on business-critical element | WARNING | `description: ''` on metrics, formulas, entity top-level, or relationships. Empty descriptions on unnamed bookkeeping fields are fine |
| Q4 | Placeholder text | WARNING | Description contains `TODO`, `tbd`, `xxx`, `FIXME`, `???`, or obvious scaffold text |
| Q5 | Pasted instruction fragment | WARNING | Description contains a clause from a different context (e.g., "Unless stated otherwise, all KPIs are calculated…" in a field description — a spreadsheet paste artifact) |

---

## Engine compatibility (X1)

| Rule | Name | Severity | What it checks |
|---|---|---|---|
| X1 | Engine-unsupported SQL construct | ERROR in entity files, WARNING in `expected_output` | Read `.lynk/config.json` `engine`. Scan every SQL site (entity `metrics[].sql`, `formula.sql`, `first_last.filters[].sql`, relationship `joins[].sql`, evaluation `expected_output`) for constructs the target engine doesn't support. Common flags: `QUALIFY`, `IFF`, `TRY_CAST`, `DATEADD/DATEDIFF`, `SAFE_*`, `LATERAL FLATTEN`, backtick identifiers, `::` casts, `TOP n`, `INTERVAL` string forms, date-literal shape, multi-resultset `expected_output` |

---

## Detection algorithms

### Y4 / Y5 — missing `{}` in SQL

1. Collect all feature `name` values from the entity.
2. For each feature name, check if it appears bare (not inside `{}`) using word-boundary matching.
3. If found, flag with metric/formula name, bare reference, suggest wrapping.

### Y6 — METRIC() wrapping

Regex (case-insensitive):
- `SUM\s*\(\s*METRIC\s*\(`
- `AVG\s*\(\s*METRIC\s*\(`
- `COUNT\s*\(\s*METRIC\s*\(`
- `MAX\s*\(\s*METRIC\s*\(`
- `MIN\s*\(\s*METRIC\s*\(`
- `RATIO_TO_REPORT\s*\(\s*METRIC\s*\(`

### Y18 — aggregates in formula SQL

Regex (case-insensitive, exclude quoted strings):
- `\bSUM\s*\(`
- `\bAVG\s*\(`
- `\bCOUNT\s*\(`
- `\bMAX\s*\(`
- `\bMIN\s*\(`
- `\bRATIO_TO_REPORT\s*\(`

### Y22 — circular dependency detection

1. Build directed graph: formula → each `{feature_name}` it references.
2. Only follow edges to other formula features (non-formulas are leaves).
3. DFS cycle detection.
4. Report full cycle path if found.

### D1 — context describes aggregation without metric

1. Collect all metric names from every entity's `metrics:` section.
2. Scan knowledge, glossary, and task instruction files for aggregation language: "total X", "sum of X", "count of X", "average X", "number of X", "X per Y", and explicit names in backticks or bold.
3. For each aggregation concept found, check if a matching metric exists (normalize to snake_case, compare stems).
4. If no match, flag D1 with file, line, and suggested metric name.

### D2 — task instruction references undefined metric

1. Scan task instruction files for metric references: `` `metric_name` ``, `METRIC(name)`, "use the X metric".
2. Check each name against every entity's `metrics:` section.
3. Flag D2 ERROR if missing.

### D3 — evaluation uses undefined metric

1. For each evaluation in `evaluations.yml`, extract `METRIC(name)` from `expected_output`.
2. Cross-reference each name against every entity's `metrics:` section.
3. Flag D3 ERROR if missing.

### G4 — duplicate / tautological glossary

1. Group glossary entries by normalized term (lowercase, whitespace collapsed, punctuation stripped).
2. If >1 entry per group → duplicate (flag).
3. For each entry, compare description to term — exact match or stem match → tautological.
4. Compare description to every other entry's term in the file — match → shifted-paste.
5. Scan description for placeholder patterns (`TODO`, `tbd`, `xxx`, `???`).

### Q2 — shifted-paste detection

1. Build a set of all field/metric/feature/term names in the file.
2. For each `description` value, normalize (strip punctuation, lowercase).
3. If the normalized description matches the normalized name of ANOTHER element in the same file → shifted-paste.
4. Stronger signal when the matching element is the next row in YAML order (spreadsheet paste artifact).

---

## Mandatory verification gate

Before generating the final report, fill in this checklist. If any row has empty evidence, you have not completed the check — go back and do it. Do NOT write "looks OK" without comparing files.

```
CROSS-FILE VERIFICATION CHECKLIST
==================================
| Rule Group | Files Compared                         | Evidence Summary                    | Finding       |
|------------|----------------------------------------|-------------------------------------|---------------|
| G1         | glossary.md vs entity metrics          | {which terms vs which metrics}      | PASS or ISSUE |
| G2         | glossary.md vs knowledge files         | {which terms vs which definitions}  | PASS or ISSUE |
| G3         | glossary.md vs task instructions       | {which terms vs which rules}        | PASS or ISSUE |
| G4         | glossary.md internal                   | {N entries, N dups, N tautological} | PASS or ISSUE |
| K1         | business_knowledge vs entity knowledge | {which values compared}             | PASS or ISSUE |
| K2         | domain knowledge vs entity YAML        | {which entities/metrics checked}    | PASS or ISSUE |
| K3         | entity knowledge vs entity YAML        | {which features/metrics checked}    | PASS or ISSUE |
| K4         | entity knowledge vs task instructions  | {which definitions compared}        | PASS or ISSUE |
| T1         | domain instr vs entity instr           | {which rules compared}              | PASS or ISSUE |
| T2         | instructions vs examples (same file)   | {which examples vs which rules}     | PASS or ISSUE |
| T3         | instructions vs evals + yaml examples  | {N evals checked, N examples}       | PASS or ISSUE |
| T4         | anti-patterns vs all examples          | {which anti-patterns checked}       | PASS or ISSUE |
| B1         | output_format vs glossary              | {which terms checked}               | PASS or ISSUE |
| B2         | clarification vs knowledge             | {which concepts checked}            | PASS or ISSUE |
| C1         | feature refs in MD vs YAML             | {which files, which features}       | PASS or ISSUE |
| C2         | METRIC() refs in MD vs YAML            | {which files, which metrics}        | PASS or ISSUE |
| C3         | entity() refs in MD vs YAML            | {which files, which entities}       | PASS or ISSUE |
| D1         | context aggregation concepts vs metrics| {which concepts, which entities}    | PASS or ISSUE |
| D2         | task instr metric refs vs YAML         | {which refs, which files}           | PASS or ISSUE |
| D3         | eval METRIC() refs vs YAML             | {which evals, which metrics}        | PASS or ISSUE |
| Q1-Q5      | descriptions across all files          | {N descriptions scanned}            | PASS or ISSUE |
| X1         | engine SQL compatibility               | {engine, N SQL sites checked}       | PASS or ISSUE |
```

For T3 specifically: list the count of evaluations and examples checked. Do not mark PASS without having gone through each one.

---

## Instruction vs example contradictions — NEEDS_CLIENT_INPUT

When an instruction states a rule but an example or evaluation doesn't follow it, the example may reflect the client's actual behavior (which may be the source of truth, not the rule). Do NOT auto-fix these.

- Surface both sides: what the rule says, what the example does.
- Classify as `NEEDS_CLIENT_INPUT` severity.
- Ask the user to confirm the direction with the stakeholder before editing.
