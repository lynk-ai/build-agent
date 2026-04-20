# Data Modeling

> **Advanced concept.** This page assumes familiarity with entities, features, metrics, and relationships. If you're just getting started, read [Entities](entities.md) first.

Feature chaining is Lynk's mechanism for building features on top of features from other entities. When used across multiple entities, it creates a full data pipeline — values that flow through layers of your semantic graph, each layer building on the one before it.

This page explains how that works and when to use each pattern.

---

## How Feature Chaining Works

Any feature type that sources from another entity is a chain link. That includes:

- **`metric`** — aggregates rows from a related entity (`total_spend_usd` on `player` from `purchase.sum_net_revenue_usd`)
- **`first_last`** — pulls the first or last value from a related entity's rows (`first_purchase_date` on `player` from `purchase`, ordered by `purchase_date`)
- **`field`** — pulls a column from a related entity or source table (`store` on `player` from the player's most recent purchase record)

What makes chaining a pipeline is that a feature on entity B — regardless of type — can be used as input to a metric or formula on entity B, which entity C can then reference. Each layer computes once; downstream entities reference it.

Two components are required at each step:

1. A relationship connecting the two entities
2. A feature on the destination entity that sources from the source entity (`source: <entity_name>`)

**`formula` features don't chain across entities** — they compute from other features on the same entity, so they can't source from a related entity. But they are essential to data modeling: once a `metric` or `first_last` feature has pulled a value onto an entity, a formula can derive new meaning from it. On `player`, after `total_spend_usd` is chained in from `purchase`, a formula can tier each player:

```yaml
- type: formula
  name: player_segment
  data_type: string
  description: Spend-based segment — 'whale', 'dolphin', or 'minnow'
  sql: >
    CASE
      WHEN {total_spend_usd} > 100 THEN 'whale'
      WHEN {total_spend_usd} > 20  THEN 'dolphin'
      ELSE 'minnow'
    END
```

The formula references `total_spend_usd`, which was itself chained in from `purchase`. That's the pattern: chain the raw value in, derive business meaning with a formula.

---

## Example: Three Entities, Two Patterns

Arcadia tracks player behavior through three entities: `purchase`, `player`, and `player_cohort`. Each `player_cohort` row represents a group of players who installed on the same date — pre-calculated in the warehouse.

The example below uses `metric` features to show chaining, since aggregations make the pipeline logic most visible. The same patterns apply to `first_last` and `field` features — any feature that sources from another entity participates in the chain.

The relationships are:
- `player` ↔ `purchase`: one player has many purchases
- `player_cohort` ↔ `player`: one cohort has many players
- `player_cohort` ↔ `purchase`: one cohort's players have many purchases (direct)

The example below shows two chain patterns from these three entities.

### Relationships

```yaml
relationships:
  player-purchase:
    relationship: one_to_many
    description: A player's purchase history
    joins:
      - name: player_to_purchase
        default: true
        join_type: left
        type: sql
        sql: '{source}.{player_id} = {destination}.{player_id}'

  player_cohort-player:
    relationship: one_to_many
    description: All players who belong to a cohort by install date
    joins:
      - name: cohort_to_player
        default: true
        join_type: left
        type: sql
        sql: '{source}.{install_date} = {destination}.{install_date}'

  player_cohort-purchase:
    relationship: one_to_many
    description: All purchases made by players in a cohort — direct path, no player intermediary
    joins:
      - name: cohort_to_purchase
        default: true
        join_type: left
        type: sql
        sql: '{source}.{install_date} = {destination}.{cohort_install_date}'
```

---

### Pattern 1 — Linear Chain (purchase → player → player_cohort)

Use this when the intermediate aggregation matters. Here, you want cohort-level spend, but averaged *per player* — not summed across all purchases directly. You need the player layer to compute the per-player value first.

**Step 1 — `purchase` defines the base metric.**

```yaml
# purchase entity
metrics:
  - name: sum_net_revenue_usd
    description: Total net revenue from purchases, in USD
    sql: SUM({net_revenue_usd})
```

**Step 2 — `player` chains from `purchase` and defines a new metric.**

```yaml
# player entity
features:
  - type: metric
    name: total_spend_usd
    description: Total net revenue from all purchases by this player, in USD
    data_type: number
    source: purchase
    metric: sum_net_revenue_usd

metrics:
  - name: avg_spend_usd
    description: Average spend per player, in USD
    sql: AVG({total_spend_usd})
```

`total_spend_usd` is a metric feature — it pulls from `purchase`. `avg_spend_usd` is an entity metric — it aggregates over players using that feature as input.

**Step 3 — `player_cohort` chains from `player`.**

```yaml
# player_cohort entity
features:
  - type: metric
    name: avg_player_spend_usd
    description: Average spend per player within this cohort, in USD
    data_type: number
    source: player
    metric: avg_spend_usd
```

`avg_player_spend_usd` on `player_cohort` reflects the chain: it averages `avg_spend_usd` across players, which itself averages `total_spend_usd`, which sums from `purchase.net_revenue_usd`. Three entities, one logical pipeline.

---

### Pattern 2 — Direct Chain (purchase → player_cohort)

Use this when you don't need the intermediate layer. Cohort total revenue is a simple sum — no per-player averaging required. Going through `player` would add an unnecessary aggregation step.

```yaml
# player_cohort entity
features:
  - type: metric
    name: cohort_total_revenue_usd
    description: Total net revenue from all purchases made by players in this cohort, in USD
    data_type: number
    source: purchase
    metric: sum_net_revenue_usd
```

Same source metric (`purchase.sum_net_revenue_usd`), different path. The result is different too: `cohort_total_revenue_usd` is a cohort-level sum, not a per-player average.

---

## Linear vs. Direct — Which to Use

| | Linear chain | Direct chain |
|---|---|---|
| **Use when** | The intermediate entity's aggregation is what you need | You need a simple rollup, no intermediate logic |
| **Arcadia example** | Average spend per player, rolled up to cohort | Total revenue for all players in a cohort |
| **Relationships needed** | purchase↔player, player↔player_cohort | player_cohort↔purchase |

Both patterns can coexist on the same entity. `player_cohort` in the example above defines both `avg_player_spend_usd` (linear) and `cohort_total_revenue_usd` (direct) — two different aggregations, two different paths, from the same underlying data.

---

## Related Reference

- [Entities](entities.md) — entity metrics, metric features, and the full feature type reference
- [Relationships YAML Reference](../file-types/relationships-yaml.md) — how to define joins and named join paths
- [Entity YAML Reference](../file-types/entity-yaml.md) — full field reference for defining features and metrics
