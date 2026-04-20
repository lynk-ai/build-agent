# Entities

An entity is a modeled business concept — the authoritative, curated definition of a real-world thing your business cares about. An entity is not a database table. A table is raw storage; an entity is governed meaning.

When you model an `order` entity, you're not just pointing to `db_prod.core.orders`. You're defining what an order *is* to your business: which fields matter, how revenue is calculated, what filters should always apply, and how orders relate to customers and products. That governed definition is what the agent reads and reasons about.

---

## What an Entity Contains

An entity is defined in a YAML file and optionally enriched with Markdown context files.

**The YAML file** defines the data model:
- The primary warehouse table (`key_source`) and the field(s) that uniquely identify a row (`keys`)
- **Features** — the attributes the agent can select, filter, and group by
- **Metrics** — aggregation expressions for rolling up rows
- **Related sources** — secondary warehouse tables enriching the entity with additional fields

**Markdown context files** define the business layer:
- Knowledge files carry definitions, data quality notes, and business rules
- Task instruction files tell the agent how to write SQL for this entity

These two layers load together. When the agent identifies that a question is about `customer`, it reads both the entity YAML and all context files scoped to that entity. See [Context](./context.md) for how the layers connect.

---

## Entity Identity

Every entity has a `name` and a `description`. These are the two fields the agent reads first — before looking at features or metrics.

**`name`** is the entity identifier. It appears in queries (`entity('order')`), in relationship keys (`customer-order`), and in metric feature references. Keep it short, lowercase, and unambiguous.

**`description`** is what the agent uses to decide whether this entity is relevant to a question. Vague descriptions cause the agent to miss the entity or pick the wrong one.

```yaml
# Too vague — the agent has no signal for when to use this
name: order
description: Order data

# Useful — the agent knows what this entity answers
name: order
description: >
  A completed purchase transaction. Use this entity for questions about
  revenue, order volume, average order value, and channel performance.
  For product-level questions, use the product entity joined through order_items.
```

If your project has two entities that could answer similar questions, the description is how the agent chooses between them. Be explicit about what the entity represents and which questions it answers.

---

## Key Source and Keys

`key_source` is the primary warehouse table — the table that defines the entity's grain. One row in `key_source` equals one instance of the entity.

`keys` are the fields that uniquely identify a row. They are used in joins and in feature resolution.

```yaml
key_source: db_prod.core.orders
keys:
  - order_id
```

Enrichment from secondary tables belongs in `related_sources`, not in `key_source`. The key source defines entity identity; related sources extend it with additional data.

---

## Sources vs. Entities

A **source** is a raw warehouse table or view. Sources have columns. Entities have features, metrics, descriptions, and relationships — concepts the agent can reason about.

The distinction matters for metric features. When `customer` defines a `total_revenue` feature that aggregates from orders, the `source` must reference the `order` entity — not `db_prod.core.orders`. Metric features depend on the entity's `metrics:` section, which raw tables don't have.

```yaml
# Wrong — points to a raw table
- type: metric
  source: db_prod.core.orders
  metric: sum_amount

# Correct — points to the entity
- type: metric
  source: order
  metric: sum_amount
```

For context files, the entity scope works the same way: you reference the entity by name (`entity: order`), not by table name.

---

## Features

Features are the attributes of an entity — the fields the agent can select, filter, and group by in a query. Features are defined in the entity YAML file, under the `features:` section.

There are four feature types. The type determines where the data comes from and how it is computed.

### The Four Feature Types

| Type | What it does | Use it when |
|---|---|---|
| `field` | Pulls a column directly from a source table | You want a raw attribute — name, status, amount |
| `first_last` | Gets the first or last value from a set of rows, ordered by a field | You need "most recent plan", "first order date", "highest-value item" |
| `formula` | Derives a value from other features on the same entity | You need a ratio, tier, or days-since calculation |
| `metric` | Aggregates from a metric defined on a related entity | You need a per-entity total from another entity — total revenue, order count |

The agent selects which features to use based on the question and the feature descriptions.

### Feature Descriptions Drive Selection

Every feature has a `description` field. This is not just documentation — it is what the agent reads to decide whether a feature is relevant to a question.

A vague description produces wrong selections. A precise description helps the agent pick the right field, especially when two fields look similar.

```yaml
# Too vague — the agent doesn't know when to use this vs. gross_amount
- type: field
  name: net_amount
  description: Net order value

# Precise — the agent knows this is the default revenue field
- type: field
  name: net_amount
  description: Order total after discounts and refunds, in USD. Default revenue field.
```

The description should answer: what does this feature represent, and when should the agent use it instead of a similar field?

### `field` — Direct Column

Pulls a column from a source table without transformation. The column name in the warehouse (`field`) may differ from the feature `name`.

```yaml
- type: field
  name: status
  data_type: string
  source: db_prod.public.customers
  description: Account status — 'active', 'churned', or 'trial'
  field: account_status
```

When two date fields exist on an entity (e.g., `created_at` and `completed_at`), make the description explicit about which one to use for date filtering. The agent selects date fields based on feature descriptions.

### `first_last` — First or Last Value

Retrieves a single value from a set of rows ordered by another field. Use it when you need a scalar attribute derived from a one-to-many relationship — most recent plan, first order date, highest-value item.

```yaml
- type: first_last
  name: first_order_date
  description: Date of the customer's first completed order
  data_type: datetime
  source: order
  join_name: customer_to_order
  options:
    method: first
    sort_by: order_date
    offset: 1
    field: order_date
    data_type: datetime
```

`method: first` returns the row with the smallest `sort_by` value; `method: last` returns the largest. `field` is the column to return from that row — it can differ from `sort_by`. When `source` is an entity, the relationship must be defined in `entities_relationships.yml`.

### `formula` — Derived Value

Computes a value from other features on the same entity. Uses `{feature_name}` syntax to reference other features.

```yaml
- type: formula
  name: days_since_signup
  data_type: number
  description: Number of days since this customer signed up
  sql: DATEDIFF('day', {first_paid_at}, CURRENT_DATE)
```

Formula features have no `source` field — they operate entirely on the entity's own feature set. They can reference any feature on the same entity — `field`, `first_last`, `formula`, or `metric` — but cannot reference features on other entities. Use a `metric` feature for cross-entity aggregation.

### `metric` — Aggregated Value from a Related Entity

Pulls an aggregated value from a metric defined on a different entity. This is **feature chaining** — the mechanism that makes cross-entity totals available as attributes on a dimension entity.

```yaml
- type: metric
  name: total_revenue
  description: Total net revenue from all completed orders placed by this customer
  data_type: number
  source: order
  metric: sum_net_amount
```

`source` must be an entity name — not a raw table name. The relationship between the two entities must be defined in `entities_relationships.yml`. Without it, the metric feature cannot be resolved.

### The `source` Field

`source` tells the agent where to get the data. What it accepts depends on the feature type:

| Feature type | `source` accepts | Format |
|---|---|---|
| `field` | A warehouse table or an entity | `schema.db.table` or entity name |
| `first_last` | A warehouse table or an entity | `schema.db.table` or entity name |
| `metric` | An entity only | entity name |
| `formula` | — | No `source` — references other features on this entity |

`metric` features require an entity as `source` because aggregation logic only exists on entities, not on raw tables.

For the full feature field reference and examples, see [Entity YAML Reference](../file-types/entity-yaml.md).

---

## Metrics

Metrics are how the agent aggregates data. There are two kinds: **entity metrics**, which define aggregation logic on a fact entity, and **metric features**, which surface that aggregated value as an attribute of a related entity. The two work together through feature chaining.

### Entity Metrics

Entity metrics are defined in the `metrics:` section of an entity YAML. Each metric is an aggregation expression — a SQL aggregate function over the entity's features.

```yaml
metrics:
  - name: count_orders
    description: Total number of orders
    sql: COUNT({order_id})

  - name: sum_net_revenue
    description: Total net revenue across orders, in USD
    sql: SUM({net_amount})

  - name: avg_order_value
    description: Average net order value, in USD
    sql: AVG({net_amount})
```

`sql` is a SQL aggregate expression. Feature names inside `{...}` reference features defined on the same entity.

Entity metrics define *how* to aggregate — not which rows to aggregate. Filtering happens at query time, not in the metric definition.

Entity metrics exist on fact entities — `order`, `session`, `purchase`. They are the aggregation primitives that metric features reference from other entities.

### Metric Features

A metric feature is a feature of type `metric` on one entity that pulls an aggregated value from a metric on a related entity.

The `customer` entity below surfaces revenue from the `order` entity:

```yaml
# On the customer entity
features:
  - type: metric
    name: total_revenue
    description: Total net revenue from all completed orders placed by this customer
    data_type: number
    source: order
    metric: sum_net_revenue
```

The `source` field points to the entity whose metrics you want to use. The `metric` field names the specific metric on that entity.

This makes `total_revenue` queryable as an attribute of every customer — without duplicating the aggregation logic. The SQL for `SUM({net_amount})` lives once, on the `order` entity. Any entity that relates to `order` can surface it via a metric feature.

### How Feature Chaining Works

Feature chaining requires three parts:

1. **A fact entity** defines a metric. `order` defines `sum_net_revenue` as `SUM({net_amount})`.
2. **A relationship** connects the two entities. `customer-order` is defined in `entities_relationships.yml`.
3. **A metric feature** on the dimension entity references the fact entity's metric. `customer` defines `total_revenue` pointing to `order.sum_net_revenue`.

When the agent resolves `total_revenue` on `customer`, it:
1. Looks up the `customer-order` relationship
2. Uses the default join (`customer_to_order`)
3. Aggregates `SUM({net_amount})` from `order`, grouped by the customer key

All three parts are required. If the relationship does not exist, the metric feature fails to resolve.

### Filtered Metric Features

Metric features can include filters that narrow the rows before aggregating. This lets you define multiple scoped metrics from the same fact entity without creating separate entity metrics for each.

```yaml
- type: metric
  name: spend_last_30_days_usd
  description: Net revenue from purchases in the last 30 days, in USD
  data_type: number
  source: purchase
  filters:
    - type: sql
      sql: >
        {source}.{purchase_currency} = 'USD'
        AND {source}.{purchase_date} >= CURRENT_DATE - INTERVAL '30 days'
  metric: sum_net_revenue_usd
```

`{source}` in filter expressions refers to the source entity, and `{feature_name}` references features defined on that entity. Filters are applied before aggregation.

Filtered metric features are how you express business-specific aggregations — revenue in a fiscal quarter, active subscriptions, spend from a specific channel — without modifying the underlying entity metric.

### Which Join is Used

By default, metric features use the default join on the relationship between the two entities. To use a non-default join, specify `join_name` on the metric feature. Multiple named joins on a relationship let you compute different metrics through different join paths.

For how joins are defined and named, see [Relationships YAML Reference](../file-types/relationships-yaml.md).

---

## Entities Are the Source of Truth

Raw warehouse tables are inputs. Entities are the source of truth.

When the agent needs to answer a question, it queries entities — not raw tables. The entity defines which columns are exposed as features, how they're labeled, what they mean, and how to aggregate them. The warehouse table is just where the data lives.

This means all metric logic lives on entities. If you need to aggregate from a table that has no entity, you have two options:

1. **Create a new entity** from that table, define its features, and add the metric to the entity.
2. **Enrich an existing entity** using `related_sources`, bring the relevant fields in as features, and define the metric as an aggregation over those features.

Either way, the metric ends up on an entity — the only place the agent can find and use it.

---

## How Context Compounds on Entities

For a query about the `customer` entity in the `finance` domain, the agent loads:

1. Domain-wide knowledge for `domain: "*"` (global conventions, fiscal year)
2. Domain-wide knowledge for `domain: "finance"` (finance-specific definitions)
3. Entity knowledge for `entity: customer` (customer-specific business rules, data quality notes)
4. Task instructions scoped to `entity: customer` (SQL patterns for customer queries)

The entity YAML provides the data model. The context files fill in the business meaning. Both are needed for the agent to answer correctly.

For the full context loading model, see [Context](./context.md). For how domains affect scoping, see [Domains](./domains.md).

---

## Related Reference

- [Entity YAML Reference](../file-types/entity-yaml.md) — full field reference for entity YAML files
- [Relationships YAML Reference](../file-types/relationships-yaml.md) — how to connect entities and define joins
- [Context](./context.md) — the five context file types and how they load on entities
- [Context](./context.md) — how entity YAML and context files connect into the full teaching framework
