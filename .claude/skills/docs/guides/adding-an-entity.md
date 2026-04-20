# Guide: Adding an Entity

This guide walks through every step of adding a new entity to the semantic layer — from the YAML definition through context files, relationships, and verification.

---

## Before You Start

Ask yourself:
- **Is this a real business concept or a warehouse table?** Entities model business concepts. If you are tempted to name it after a table (e.g., `player_game_stats`), rename it to the concept it represents (`player_game`).
- **Does this entity already exist under a different name?** Check `default/entities/` for existing entities before adding a duplicate.
- **What grain does this entity have?** One row per what? (Per player? Per game? Per player per game?) The grain determines the keys and drives everything else.

---

## Checklist

### 1. Create the Entity YAML

**File:** `.lynk/default/entities/{entity}.yml`

Minimum viable entity YAML:

```yaml
name: {entity}
description: {one or two sentence description}

key_source: {warehouse_schema.db.table}

keys:
  - {primary_key_field}

features:
  - type: field
    name: {field_name}
    data_type: {string|number|boolean|datetime}
    source: {warehouse_schema.db.table}
    description: {description}
    field: {column_name_in_source}
    join_name: null
    filters: []

metrics:
  - name: {metric_name}
    description: {description}
    sql: {aggregation_sql}
```

**Checklist for the YAML:**
- [ ] `name` matches the entity folder name
- [ ] `key_source` points to a real warehouse table
- [ ] `keys` correctly identifies the grain (can be composite)
- [ ] At least one identifying `field` feature (name, id, or key)
- [ ] At least one `metric` if this entity will be used as a source for metric features on other entities
- [ ] `description` on the entity and every feature is filled in
- [ ] Field names in the `field:` key are verified against the actual warehouse table

→ See [Entity YAML Reference](../file-types/entity-yaml.md) for full field documentation.

---

### 2. Add Relationships

**File:** `.lynk/default/entities_relationships.yml`

Add a relationship entry for every entity this new entity connects to.

```yaml
{new_entity}-{existing_entity}:
  relationship: {one_to_many|many_to_one|many_to_many|one_to_one}
  description: {description}
  joins:
  - name: {join_name}
    default: true
    join_type: left
    type: sql
    sql: '{source}.{key_field} = {destination}.{foreign_key_field}'
```

**Checklist for relationships:**
- [ ] One entry per entity pair this new entity relates to
- [ ] Relationship direction (one_to_many, etc.) matches the actual cardinality
- [ ] Join SQL uses `{source}` and `{destination}` placeholders
- [ ] Join SQL references **feature names**, not raw column names
- [ ] `default: true` is set on the primary join for each relationship

→ See [Relationships YAML Reference](../file-types/relationships-yaml.md) for full documentation.

---

### 3. Create the Entity Knowledge File

**File:** `.lynk/default/entities/{entity}/{entity}__knowledge.md`

Create the entity subfolder first, then the knowledge file.

```markdown
---
type: knowledge
domain: "default"
entity: {entity}
---

## What This Entity Represents
{One paragraph describing what a row in this entity represents.}

## Key Business Rules
- {Rule 1}
- {Rule 2}

## Data Quality Notes
- {Any known gaps, caveats, or quirks in the data}
```

**Checklist for knowledge:**
- [ ] Entity subfolder exists at `entities/{entity}/`
- [ ] Frontmatter is correct (`type: knowledge`, correct `domain`)
- [ ] Explains what one row represents (the grain)
- [ ] Calls out any non-obvious field semantics
- [ ] Notes any known data quality issues

→ See [Knowledge File Reference](../file-types/knowledge-md.md) for writing guidance.

---

### 4. Create the Entity Task Instructions File

**File:** `.lynk/default/entities/{entity}/{entity}__task_inst__text_to_sql.md`

```markdown
---
type: task-instructions
domain: "default"
entity: {entity}
tasks: "text-to-sql"
---

## {Entity} Query Patterns
- {Guidance specific to writing SQL for this entity}
- {Which fields to use for display vs. filtering}
- {Common query patterns}
```

**Checklist for task instructions:**
- [ ] Frontmatter is correct (`type: task-instructions`, `tasks: "text-to-sql"`)
- [ ] Covers which fields to use for display (usually `full_name`, `id`)
- [ ] Notes any tricky fields or join paths
- [ ] Includes guidance for queries that span to other entities

→ See [Task Instructions Reference](../file-types/task-instructions-md.md) for guidance on what to include.

---

### 5. Add Evaluations

Add at least two evaluation test cases to `evaluations.yml` — one easy, one medium difficulty.

**File:** `.lynk/default/evaluations.yml`

```yaml
test_cases:
  - type: SQL
    name: {snake_case_name}
    description: |-
      {what this evaluation tests}
      Evaluation:
      - {which rule or context is being verified}
    input: {natural language question as a user would ask it}
    expected_output: |-
      SELECT ...
      FROM entity('{entity}')
      ...
    tags:
      difficulty: EASY
      domain: default
      eval: entity_knowledge
```

**Checklist for evaluations:**
- [ ] Input is written in natural business language — not field names or SQL
- [ ] Expected output uses `FROM entity('{entity}')` and `metric()` function
- [ ] SQL is verified to match actual feature and metric names in the entity YAML
- [ ] At least one easy evaluation (simple attribute lookup or count)
- [ ] At least one medium evaluation (filtering, grouping, or a metric that requires the right join)
- [ ] Default filters are applied in `expected_output` if your task instructions require them

→ See [Evaluations YAML Reference](../file-types/evaluations-yaml.md) for full field documentation.

---

### 6. Verify

Before considering the entity complete:
- [ ] Entity YAML has no syntax errors (validate YAML structure)
- [ ] All `source` values in `field` features point to either the `key_source` or a declared `related_source`
- [ ] All `source` values in `metric` features are entity names with matching relationship entries
- [ ] All `join_name` values in features match join names defined in `entities_relationships.yml` or `related_sources`
- [ ] Run at least one of the example queries and confirm it executes without errors
- [ ] Confirm the entity appears correctly in the semantic layer catalog

---

## Quick Reference

| Step | File | Reference |
|---|---|---|
| 1. Entity YAML | `default/entities/{entity}.yml` | [Entity YAML](../file-types/entity-yaml.md) |
| 2. Relationships | `default/entities_relationships.yml` | [Relationships YAML](../file-types/relationships-yaml.md) |
| 3. Knowledge | `default/entities/{entity}/{entity}__knowledge.md` | [Knowledge](../file-types/knowledge-md.md) |
| 4. Task Instructions | `default/entities/{entity}/{entity}__task_inst__text_to_sql.md` | [Task Instructions](../file-types/task-instructions-md.md) |
| 5. Evaluations | `default/evaluations.yml` | [Evaluations](../file-types/evaluations-yaml.md) |
