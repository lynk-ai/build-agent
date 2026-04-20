# Guide: Writing Task Instructions

Task instructions tell the agent how to generate SQL for a specific entity or domain. They are the primary lever for fixing wrong SQL — wrong filters, wrong field choices, wrong date patterns.

---

## Before You Start

- **Is the problem SQL generation or question interpretation?** Task instructions only affect SQL. If the agent misread a business term, fix the glossary instead. If it selected the wrong entity, fix the entity's `description`. Only use task instructions when the right entity was selected but the generated SQL was wrong.
- **Which scope does the rule belong to?** A rule that applies to all entities (e.g., always exclude deleted records) goes in a domain-level file. A rule specific to one entity (e.g., always filter `order` to `status = 'completed'` for revenue questions) goes in an entity-level file.
- **Does an entity-level task instructions file already exist?** Check `.lynk/default/entities/{entity}/` before creating a new file.

---

## Steps

### 1. Identify the rule

Before writing, be precise about what the rule is:

- What question triggered the wrong SQL?
- What was wrong about the generated SQL?
- What rule, if stated explicitly, would have produced the correct SQL?

Write the rule as a clear instruction: *"Always filter `is_test_order = false` on all order queries"*, not *"handle test orders correctly."*

---

### 2. Determine scope

| Rule applies to... | Use |
|---|---|
| All entities across all domains | Domain-level file with `domain: "*"` |
| All entities in one domain | Domain-level file with `domain: "default"` (or named domain) |
| One specific entity | Entity-level file with `domain: "default"` + `entity: {name}` |

When in doubt, start at entity scope — it's easier to widen later than to narrow after a domain-wide rule causes unexpected behavior on other entities.

---

### 3. Create or update the task instructions file

**Domain-level file:** `.lynk/default/domain_context/{domain}__task_inst__text_to_sql.md`

```markdown
---
type: task-instructions
domain: "default"
tasks: "text-to-sql"
---

## Always Do
- {Rule 1 — what to always include}
- {Rule 2 — what to always include}

## Never Do
- {Anti-pattern 1}

## Date Conventions
- {How to interpret "this month", "last quarter", "YTD"}
```

**Entity-level file:** `.lynk/default/entities/{entity}/{entity}__task_inst__text_to_sql.md`

```markdown
---
type: task-instructions
domain: "default"
entity: {entity}
tasks: "text-to-sql"
---

## Default Filters
Always apply: {filter_condition}
Never omit unless the user explicitly asks for all {entities}.

## Field Choices
- Use `{field_a}` for display; use `{field_b}` for filtering
- {When two similar fields exist, specify which to use and when}

## Query Patterns
- {Common pattern and how to handle it}
```

**Checklist:**
- [ ] `type: task-instructions` (hyphen, not underscore)
- [ ] `tasks: "text-to-sql"` is present
- [ ] `domain` matches the target domain
- [ ] `entity` is present and spelled exactly as the entity name (entity-level only)
- [ ] Rules are written as instructions, not descriptions — "Always filter X" not "X is filtered"
- [ ] SQL field names in rules match actual feature names in the entity YAML

→ See [Task Instructions Reference](../file-types/task-instructions-md.md) for full frontmatter reference and content guidelines.

---

### 4. Add an evaluation to verify

Write at least one evaluation test case that confirms the new rule is followed. The `expected_output` should reflect the rule — if you added a default filter, it must appear in the expected SQL.

**File:** `.lynk/default/evaluations.yml`

```yaml
test_cases:
  - type: SQL
    name: {rule_name_test}
    description: |-
      Verifies that {rule description}.
      Evaluation:
      - task_instructions: {the specific rule being tested}
    input: {A question where the rule must apply}
    expected_output: |-
      SELECT ...
      FROM entity('{entity}')
      WHERE {filter_from_your_new_rule}
    tags:
      difficulty: EASY
      domain: {domain}
      eval: task_instructions
```

**Checklist:**
- [ ] `input` is a real user question — not a technical spec
- [ ] `expected_output` includes the filter or field choice the new rule requires
- [ ] Evaluation passes after the new file is pushed to your branch

→ See [Writing Evaluations](writing-evaluations.md) for the full evaluation workflow.

---

## Quick Reference

| Step | File | Reference |
|---|---|---|
| 1. Identify the rule | — | [Troubleshooting](troubleshooting.md) |
| 2. Determine scope | — | [Task Instructions Reference](../file-types/task-instructions-md.md) |
| 3. Domain-level file | `default/domain_context/{domain}__task_inst__text_to_sql.md` | [Task Instructions Reference](../file-types/task-instructions-md.md) |
| 3. Entity-level file | `default/entities/{entity}/{entity}__task_inst__text_to_sql.md` | [Task Instructions Reference](../file-types/task-instructions-md.md) |
| 4. Add evaluation | `default/evaluations.yml` | [Evaluations YAML](../file-types/evaluations-yaml.md) |
