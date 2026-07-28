---
description: How to decide what becomes an entity and how to shape it — the entity test, grain, promoting table relationships to entities, the upstream boundary, and base-row hygiene. Reach for it before adding or restructuring entities.
icon: cubes
---

# Choosing and shaping entities

Whether a concept becomes an entity, what its grain is, and what stays a table relationship or moves upstream.

## When you need this

- A new source table landed and someone wants it "added to Lynk."
- You can't decide whether line items, raw events, or a join table deserve entities.
- An entity's feature list has grown past what anyone can scan.
- Analyses disagree because some queries include test rows and some don't.
- You're wishing `identity:` could take a SELECT statement.

## The principle

An entity is a concept the business asks questions *of* directly: it has a stable identity, a grain you can state in one sentence, and people argue about it in meetings. Model those, and only those. Everything else is scaffolding — reached through a relationship, or reshaped upstream before Lynk sees it. Lynk owns meaning; the warehouse pipeline owns shape.

## Patterns

### Apply the entity test

Ask: does anyone address questions *to* this thing? "How many customers churned this quarter" makes Grove's `customer` an entity. Nobody asks questions of `maindb.public.order_items` — questions about items are really questions about orders or products — so at Bly it is not an entity; it's a table that `order` reaches through a relationship. A table you happen to have is not a concept the business owns. When in doubt, start it as a table relationship and let the promotion ladder below decide.

### State the grain in the first line

One row per *what*? Say it in the first line of every entity description: "Active and historical subscriptions. One row per subscription." An entity whose grain you can't state in one sentence isn't an entity yet — it's a table that still needs shaping. The description is what the agent reads at index time to decide whether to load the entity, so grain-first descriptions are also what make lazy loading work ([ENTITY.md](../concepts/entity/entity-md.md)).

### Climb the promotion ladder deliberately

Start every supporting table as a `table_relationship` on the entity that uses it — Bly's `order_to_items` feeds the `primary_category` feature with `last(...)` and never appears in the agent's view. Promote it to an entity when any of these holds:

1. **Users ask questions of it directly.** "Which categories have the highest margin" is a question *of* products — so Bly's `product` is an entity even while `order_items` stays a table.
2. **Two or more entities need paths through it.** Entity-relationship steps must be entities, so a shared bridge must be one — Arcadia's `player_achievement`, whose identity is the physical join table, exists so `player_to_achievement` can step through it ([Relationships](../concepts/entity/schema-yml/relationships.md)).
3. **It needs its own features or metrics.** The moment the thing carries definitions, it needs a `schema.yml` to put them in.

Event streams get the same treatment: raw events stay a table relationship under `player`; the entity is `session` — materialized upstream, one row per session. Raw events are never an entity (see the anti-pattern below).

### Keep shaping upstream of the identity

An entity's `identity` is one physical table or another entity — never a query ([identity and imports](../concepts/entity/schema-yml/identity-and-imports.md)). So identity stitching, dedup, SCD flattening, and snapshot building happen upstream, in the pipeline that produces the table the entity roots in. If the rows aren't yet one-per-instance of the concept, that's warehouse work, not schema work.

### Enforce base-row hygiene structurally

Grove excludes `is_test_account` and `is_deleted` rows from most analyses. The convention's single home is the entity's [ENTITY.md](../concepts/entity/entity-md.md) — written once, as prose. Enforcement is structural: preferred, an upstream filtered view that `identity` points at, so test rows never enter the entity; otherwise a `filter:` on each definition that must exclude them. A prose reminder alone is probabilistic — followed on most queries, missed on some (see the anti-pattern below).

## Anti-patterns

### The god entity

```yaml
# wrong — customer as the home of every number in the company
features:
  - name: refund_rate_paid_search
    description: Refund rate of this customer's paid-search orders, 0–1
    sql: metric(order.refund_rate)
    data_type: number
    join_name: customer_to_order
    filter: order.channel = 'paid_search'
  # …plus refund_rate_email, refund_rate_direct, avg_margin_of_items_bought,
  # and 190 more — one per question anyone ever asked
```

Every feature is individually legal; the pile is the failure. The entity loads as a unit, so every customer question pays for all 200 definitions; the descriptions of near-duplicates blur together; retrieval degrades until the agent picks the wrong variant. Keep each value on the entity that owns it — the agent reaches `order.refund_rate` through the relationship at query time — and promote onto `customer` only what customer-grain questions consume repeatedly.

### Entity-per-table strip-mining

The wrong form: `entities/` as a mirror of the warehouse — `order_items`, `order_status_history`, `currency_rates`, each dutifully wrapped as an entity. Their descriptions can only say "the X table", which answers no question — so the index the agent scans fills with entries that never help it choose, and every pseudo-entity still needs keys, features, and maintenance. Apply the entity test; supporting tables are table relationships on the entities that use them.

### The raw-events entity

```yaml
# wrong — one row per client event
identity: maindb.public.events
keys:
  - event_id
```

"One row per click-or-pageview-or-heartbeat" is not a grain anyone reasons at, and every real question — activity, engagement, retention — needs sessionization, which `schema.yml` cannot express: Lynk cannot create a grain that doesn't exist. Materialize `session` upstream (Arcadia: one row per session, with `duration_seconds`, `level_reached`) and model that; keep raw events reachable as a table relationship if some feature needs them.

### The table-relationship reach-around

```yaml
# wrong — order reads customer's data raw to skip the entity path
- name: customer_email
  description: Email of the customer who placed this order
  sql: maindb.public.customers.email
  data_type: string
  join_name: order_to_customers_table   # a table relationship aimed at customer's identity table
```

It builds — table relationships legitimately expose physical columns. But the value bypasses `customer`, the entity that owns it: the definition is duplicated into every consumer, drifts when `customer` changes, and the table relationship is invisible to the agent, hiding cross-entity structure it navigates by. Another entity's value has one form — its declared feature: `sql: customer.email` with `join_name: order_to_customer` ([Feature](../concepts/entity/schema-yml/feature.md)).

### Correctness by prose reminder

```markdown
<!-- wrong — an ENTITY.md line as the only enforcement -->
**Convention.** Always remember to exclude test accounts.
```

Prose is advisory. Most queries comply; some don't; the same question returns different counts depending on whether the reminder was heeded on that run — and nothing errors, because rows with `is_test_account = true` are valid rows. Enforce structurally (upstream filtered view, or `filter:` on the affected definitions) and keep the ENTITY.md line as documentation of *why*, pointing at the enforcement.

## The bar

- The grain is stated in the first line of the entity description: "one row per …".
- The description says what the entity is *for* — the questions it answers.
- Every column a relationship step joins on or a query selects is a declared feature, keys included.
- Quirks that affect most analyses are in ENTITY.md — and restated nowhere else.
- Conventions that must always hold are enforced structurally, not by prose alone.
- Nothing on this entity restates a fact whose home is another entity.

## Related

- [Entity](../concepts/entity/README.md) · [ENTITY.md](../concepts/entity/entity-md.md) · [schema.yml](../concepts/entity/schema-yml/README.md)
- [Relationships](../concepts/entity/schema-yml/relationships.md) — table vs entity relationships, bridges, defaults
- [Identity and imports](../concepts/entity/schema-yml/identity-and-imports.md) — what an entity roots in; keys are not features
- Sibling: [Modeling metrics, time, and state](metrics-time-and-state.md)
