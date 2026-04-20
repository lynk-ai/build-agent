# Guide: Adding a Feature

This guide walks through choosing the right feature type and adding it correctly to an entity.

---

## Choose the Feature Type

**Decision tree:**

```
Is the value aggregated from multiple rows?
│
├─ YES → Does the aggregation come from a related entity?
│         ├─ YES → type: metric  (feature chaining)
│         └─ NO  → You need an entity metric first, then type: metric
│
└─ NO  → Is the value derived from other features on this entity?
          ├─ YES → type: formula
          └─ NO  → Does it need first or last row from a source?
                    ├─ YES → type: first_last
                    └─ NO  → type: field
```

**Quick reference:**

| Feature type | When to use |
|---|---|
| `field` | Direct column from a source table, no computation |
| `first_last` | First or last value ordered by a field (e.g., "most recent team") |
| `formula` | Computed from other features on the same entity using SQL |
| `metric` | Aggregated value pulled from a metric on a related entity |

---

## Adding a `field` Feature

**Use when:** You need to expose a column from the entity's `key_source` or a `related_source`.

```yaml
- type: field
  name: {feature_name}
  data_type: {string|number|boolean|datetime}
  source: {warehouse_schema.db.table}
  description: {description}
  field: {actual_column_name_in_table}
  join_name: null         # null = key_source; or a join name from related_sources
  filters: []
```

**Steps:**
1. Verify the column exists in the source table with the exact name in `field:`.
2. If the source is not the `key_source`, verify it exists in `related_sources` and use `join_name` to reference the correct join.
3. Choose a `name` that is clear to business users (it does not have to match the raw column name).
4. Add a `description` that explains what this field means in business terms.

**Example — adding `draft_team_city` to the `player` entity:**
```yaml
- type: field
  name: draft_team_city
  data_type: string
  source: nba.public.player          # or wherever this column actually lives
  description: City of the team that drafted this player
  field: draft_team_city
  join_name: null
  filters: []
```

---

## Adding a `formula` Feature

**Use when:** The value is computed from other features already on this entity.

```yaml
- type: formula
  name: {feature_name}
  data_type: {string|number|boolean}
  description: {description}
  sql: |
    {SQL expression using {feature_name} references}
```

**Steps:**
1. Identify all input features the formula needs. They must already exist on this entity as `field`, `metric`, or other `formula` features.
2. Reference them with `{feature_name}` syntax in the SQL expression.
3. Ensure the SQL produces the correct `data_type` (`boolean` for CASE...TRUE/FALSE, `number` for arithmetic, etc.).

**Example — adding `points_per_minute` to `player_game`:**
```yaml
- type: formula
  name: points_per_minute
  data_type: number
  description: Points scored per minute played in this game
  sql: |
    CASE
      WHEN {num_minutes} > 0 THEN {points} / {num_minutes}
      ELSE NULL
    END
```

**Important:** Formula features can only reference features on the same entity. They cannot reach across entities or join to related sources.

---

## Adding a `first_last` Feature

**Use when:** You need the first or last value from a set of related rows, ordered by a field.

```yaml
- type: first_last
  name: {feature_name}
  description: {description}
  data_type: {string|number|datetime}
  source: {entity_or_source}
  join_name: {join_name_or_null}
  filters: []
  options:
    method: first             # "first" or "last"
    sort_by: {field_to_order_by}
    offset: 1
    field: {field_to_return}
    data_type: {string|number|datetime}
```

**Steps:**
1. Identify the source (can be a raw source table or an entity).
2. Decide `method`: `first` (smallest `sort_by` value) or `last` (largest `sort_by` value).
3. Specify `sort_by`: the field that determines order (e.g., `draft_year`, `start_date`).
4. Specify `field`: the field to return from the selected row.
5. If using a related entity as source, ensure the relationship exists in `entities_relationships.yml`.

**Example — adding `most_recent_team` to `player`:**
```yaml
- type: first_last
  name: most_recent_team
  description: The most recent team this player was affiliated with
  data_type: string
  source: player_team
  join_name: null         # uses default player-player_team relationship
  filters: []
  options:
    method: last
    sort_by: start_date
    offset: 1
    field: team_full_name
    data_type: string
```

---

## Adding a `metric` Feature (Feature Chaining)

**Use when:** You need an aggregated value from a related entity's metrics.

```yaml
- type: metric
  name: {feature_name}
  description: {description}
  data_type: number
  source: {related_entity_name}
  join_name: null               # null = default relationship join
  filters: []                   # optional pre-filters on the related entity
  metric: {metric_name_on_related_entity}
```

**Steps:**

**Step 1: Verify the target metric exists.**
Open the related entity's YAML and confirm the metric name in its `metrics:` section.

```yaml
# In player_game.yml, confirm this exists:
metrics:
  - name: avg_points_per_game
    sql: AVG(COALESCE({points}, 0))
```

**Step 2: Verify the relationship exists.**
In `entities_relationships.yml`, confirm there is a relationship between the current entity and the target entity.

```yaml
# Must exist in entities_relationships.yml:
player-player_game:
  relationship: one_to_many
  ...
```

If the relationship does not exist, add it first. See [Relationships YAML Reference](../file-types/relationships-yaml.md).

**Step 3: Add the metric feature.**
```yaml
# In player.yml:
- type: metric
  name: avg_points_per_game
  description: Average points per game for this player across their career
  data_type: number
  source: player_game           # entity name, not table name
  join_name: null
  filters: []
  metric: avg_points_per_game   # exact name from player_game.metrics
```

**Step 4: Add a filter if needed.**
To aggregate only a subset of the related entity's rows:

```yaml
- type: metric
  name: playoff_points
  description: Total points scored in playoff games
  data_type: number
  source: player_game
  filters:
    - type: sql
      sql: "{source}.{game_type} = 'Playoffs'"
  metric: total_points
```

---

## After Adding a Feature

### Update context files

If the new feature has non-obvious semantics, update the entity knowledge file.

```markdown
## {Feature Name}
- {Explain what it means and how to use it}
- {Note any gotchas — null values, units, edge cases}
```

If the new feature changes how the executor should write SQL for this entity, update the task instructions file.

### Add or update examples

Add at least one example that uses the new feature in `expected_output`. This confirms the feature name is correct and shows the executor how to use it.

### Verify

- [ ] Feature name does not conflict with any existing feature on this entity
- [ ] For `field`: column name in `field:` is verified against the actual warehouse table
- [ ] For `metric`: related entity name and metric name are verified
- [ ] For `metric`: relationship exists in `entities_relationships.yml`
- [ ] For `first_last`: source and join path are valid
- [ ] Description is filled in and accurate
- [ ] At least one example uses the new feature

---

## Common Mistakes

**Using a raw table name as `source` in a metric feature**
```yaml
# WRONG
source: nba.public.player_game_stats

# RIGHT
source: player_game
```

**Formula that references a feature that doesn't exist yet**
Formulas run sequentially. If `scoring_tier` references `avg_points_per_game`, that feature must be defined first (or defined as a metric feature that aggregates it).

**Missing relationship when adding a metric feature**
The most common reason a metric feature fails. Always check `entities_relationships.yml` before adding a metric feature to an entity.

**Adding an entity metric when you need a feature metric**
Entity metrics (in `metrics:`) are how to aggregate this entity's rows. Feature metrics (in `features:` with `type: metric`) pull aggregated values from related entities. They serve different purposes and live in different sections.
