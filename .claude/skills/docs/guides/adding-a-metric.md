# Guide: Adding a Metric

This guide covers adding an entity metric — an aggregation defined on an entity that the agent uses to answer questions like "total revenue," "order count," or "average session length."

Entity metrics live in the `metrics:` section of the entity YAML. They are written in SQL using `{feature_name}` references, which means **a metric can only reference features that already exist on that entity**. Before writing a metric, you need to know what features are available.

---

## Before You Start

**Check the entity's existing features.**
Open the entity YAML and read through the `features:` section. Metrics can only reference features defined there — you cannot reference raw column names or features from other entities. If a field you need isn't a feature yet, add it first. See [Adding a Feature](adding-a-feature.md).

**Check the entity's existing metrics.**
Two rules apply:

1. **No duplicate names.** Each metric on an entity must have a unique `name`. Adding a metric with a name that already exists will conflict.
2. **No duplicate definitions.** Two metrics with different names but identical SQL are ambiguous — the agent cannot distinguish them and will produce inconsistent results. If you want a variant (e.g., filtered), create it as a distinct metric with a clearly different definition and name.

---

## Step 1: Identify the Features You Need

Open the entity YAML and list every feature referenced in your metric's SQL. For each:

- [ ] Confirm the feature exists in `features:`
- [ ] Confirm the feature name matches exactly (case-sensitive)
- [ ] Confirm the feature's `data_type` is appropriate for the aggregation (e.g., `number` for `SUM`, any type for `COUNT`)

**Example — checking features before writing a metric on `order`:**
```yaml
# In order.yml — verify these features exist before referencing them:
features:
  - type: field
    name: order_id        # ✓ can use in COUNT
    ...
  - type: field
    name: net_amount      # ✓ can use in SUM / AVG
    ...
  - type: field
    name: status          # ✓ can use in a CASE filter
    ...
```

If a field you need is not in `features:`, add it first. Do not reference raw warehouse column names directly in metric SQL.

---

## Step 2: Check for Existing Metrics

Open the `metrics:` section of the entity YAML and scan for:

1. **Name conflict** — is the name you want already taken?
2. **Definition conflict** — does the SQL you're about to write already exist under a different name?

```yaml
# In order.yml — check what already exists:
metrics:
  - name: sum_net_revenue
    sql: SUM({net_amount})

  - name: count_orders
    sql: COUNT({order_id})
```

If your intended metric is `SUM({net_amount})` and `sum_net_revenue` already exists, **use the existing metric** — don't add a duplicate. If you need a filtered variant (e.g., revenue for a specific currency), make sure the SQL is meaningfully different and give it a distinct, descriptive name.

---

## Step 3: Write the Metric

Add the new metric to the `metrics:` section of the entity YAML:

```yaml
metrics:
  - name: {metric_name}
    description: {what it measures, units, any caveats}
    sql: {aggregation SQL using {feature_name} references}
```

| Field | Requirement |
|---|---|
| `name` | Unique on this entity. Lowercase, underscore-separated. Referenced by `metric(name)` in queries. |
| `description` | Required. Explains what the metric measures, the unit (e.g., USD, count), and any non-obvious scope. |
| `sql` | Aggregation expression. Reference entity features with `{feature_name}`. Standard SQL aggregation functions: `SUM`, `COUNT`, `AVG`, `MIN`, `MAX`, `COUNT DISTINCT`. |

**Example — adding a revenue metric to `order`:**
```yaml
metrics:
  - name: sum_net_revenue
    description: Total net revenue across orders, after discounts, in USD
    sql: SUM({net_amount})

  - name: count_orders
    description: Number of orders
    sql: COUNT({order_id})

  - name: count_distinct_customers
    description: Number of unique customers who placed an order
    sql: COUNT(DISTINCT {customer_id})
```

**Example — a conditional metric using a feature in a CASE expression:**
```yaml
  - name: sum_completed_revenue
    description: Total revenue from completed orders only, in USD
    sql: SUM(CASE WHEN {status} = 'completed' THEN {net_amount} ELSE 0 END)
```

---

## Step 4: Expose the Metric on Other Entities (if needed)

Once an entity metric exists, other entities can pull it as a metric feature via feature chaining. For example, a `customer` entity can expose `total_revenue` by chaining from `order.sum_net_revenue`.

This is a separate step — adding a metric feature on a related entity. If you need this, see [Adding a Feature → metric feature](adding-a-feature.md#adding-a-metric-feature-feature-chaining).

---

## Step 5: Update Context Files

If the new metric has non-obvious semantics — units, scope, exclusions, or naming that could be confused with another metric — document it in the entity knowledge file:

```markdown
## {Metric Name}
- {What it measures and in what unit}
- {Any rows excluded from the aggregation}
- {Differences from similar-sounding metrics on this entity}
```

If there are rules about when to use this metric vs. another (e.g., "use `sum_net_revenue`, not `sum_gross_revenue`, for margin analysis"), add those to the task instructions file for this entity.

---

## Step 6: Add an Evaluation

Add at least one evaluation case that exercises the new metric. This confirms the name is correct, the SQL compiles, and the agent selects it for the right questions.

→ See [Writing Evaluations](writing-evaluations.md) for format and examples.

---

## Verify

- [ ] All `{feature_name}` references in the metric SQL exist in `features:` on this entity
- [ ] The metric `name` is unique on this entity
- [ ] The metric SQL is not a duplicate of an existing metric's SQL on this entity
- [ ] The `description` is filled in with units and any relevant caveats
- [ ] If the metric should be exposed on related entities, metric features have been added where needed
- [ ] Context files are updated if the metric's semantics could be ambiguous
- [ ] At least one evaluation covers the new metric

---

## Common Mistakes

**Referencing a raw column name instead of a feature name**
```yaml
# WRONG — references a warehouse column directly
sql: SUM(net_amount)

# RIGHT — references the entity feature
sql: SUM({net_amount})
```

**Adding a metric that duplicates an existing one**
```yaml
# WRONG — sum_revenue already exists as sum_net_revenue with identical SQL
- name: sum_revenue
  sql: SUM({net_amount})   # duplicate of sum_net_revenue

# RIGHT — use the existing metric, or define a genuinely distinct variant
- name: sum_gross_revenue
  sql: SUM({gross_amount})  # different field, different meaning
```

**Referencing a feature from a related entity**
```yaml
# WRONG — order_count lives on the order entity, not on customer
- name: total_orders
  sql: COUNT({order_count})  # order_count is not a feature on this entity

# RIGHT — add a metric feature on customer that chains from order
- type: metric
  name: total_orders
  source: order
  metric: count_orders
```

**Writing a metric where a metric feature is needed**
Entity metrics (in `metrics:`) aggregate rows *of this entity*. If you want an aggregated value from a *related* entity (e.g., total orders per customer), that is a metric feature in `features:`, not an entity metric. See [Adding a Feature](adding-a-feature.md).

---

## Quick Reference

| Step | What to do | Where |
|---|---|---|
| 1 | Check available features | `features:` section of the entity YAML |
| 2 | Check for duplicate names and definitions | `metrics:` section of the entity YAML |
| 3 | Write the metric | `metrics:` section of the entity YAML |
| 4 | Expose on related entities (optional) | Related entity `features:` — metric feature type |
| 5 | Document semantics | Entity knowledge file + task instructions |
| 6 | Add evaluation | `evaluations.yml` |

→ See [Entity YAML Reference](../file-types/entity-yaml.md#entity-metrics) for full field-level syntax\
→ See [Adding a Feature](adding-a-feature.md) for metric features (feature chaining)\
→ See [Data Modeling](../concepts/data-modeling.md) for aggregation patterns across entities
