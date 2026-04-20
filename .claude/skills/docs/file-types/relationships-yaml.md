# Relationships YAML Reference

`entities_relationships.yml` defines all entity-to-entity connections. It is the map that enables feature chaining and cross-entity joins.

---

## Top-Level Structure

```yaml
relationships:
  {entity_a}-{entity_b}:        # relationship key — format: "entity1-entity2"
    relationship: {type}
    description: {description}
    joins:
      - name: {join_name}
        default: true
        description: {description}
        join_type: left
        type: {join_type}       # sql or lookup
        sql: {expression}       # for type: sql
        # or: lookup            # for type: lookup
```

---

## Relationship Types

| Type | Meaning | Example |
|---|---|---|
| `one_to_many` | One row on the left, many rows on the right | `customer` → `order` |
| `many_to_one` | Many rows on the left, one row on the right | `order` → `customer` |
| `one_to_one` | Unique match on both sides | `customer` → `customer_details` |
| `many_to_many` | Multiple matches on both sides (requires bridge) | `customer` ↔ `product` |

---

## Relationship Keys

The relationship key is `{source}-{destination}`. Order is meaningful: the first entity is the source (left side of the join), the second is the destination (right side). This determines which entity maps to `{source}` and which maps to `{destination}` in join SQL expressions.

```yaml
relationships:
  customer-order:
    # {source} = customer, {destination} = order
    # join sql: '{source}.{id} = {destination}.{customer_id}'
    relationship: one_to_many
    ...
```

One entry covers traversal in both directions — you do not need to define `order-customer` separately. When a metric feature on `customer` specifies `source: order`, the system looks up the `customer-order` relationship and applies the join with customer as source and order as destination.

---

## Join Definition

Each relationship has one or more joins. Multiple joins allow different join paths for different use cases.

In join expressions, `{source}` refers to the left entity in the relationship key (e.g. `customer` in `customer-order`) and `{destination}` refers to the right entity. Field names inside `{...}` are feature names on that entity, not raw column names.

```yaml
joins:
  - name: customer_to_order
    default: true
    description: Join from customer to their orders using customer id
    join_type: left
    type: sql
    sql: '{source}.{id} = {destination}.{customer_id}'
```

**Fields:**

| Field | Description |
|---|---|
| `name` | Referenced by `join_name` in metric and first_last features |
| `default` | `true` = used when `join_name` is omitted in a feature |
| `join_type` | SQL join type: `left`, `inner`, `right`, `full` |
| `type` | Join implementation type: `sql` or `lookup` |

---

## Join Types

### `sql` — Explicit SQL Condition

The join condition is an explicit SQL expression. Use `{source}` for the left entity and `{destination}` for the right entity.

```yaml
type: sql
sql: '{source}.{id} = {destination}.{customer_id}'
```

Field names must match feature names on the entity — not raw column names from the warehouse table.

---

### `lookup` — Multi-Hop Join

A chain of joins through intermediate tables or entities. Each step specifies the destination and the join condition to reach it.

```yaml
type: lookup
lookup:
  - destination: db_prod.core.order_items    # intermediate raw table
    type: sql
    sql: '{source}.{order_id} = {destination}.{order_id}'
  - destination: product                      # final entity
    type: sql
    sql: '{source}.{product_id} = {destination}.{id}'
```

Lookup joins are used for `many_to_many` relationships where there is no direct foreign key between the two entities. The chain navigates through a bridge table (which may be a raw source table, not an entity).

**Example — `customer-product` relationship:**

A customer can buy many products; a product can be bought by many customers. There is no direct foreign key — the connection goes through `order_items`.

```yaml
customer-product:
  relationship: many_to_many
  description: Customers are related to products through their order history
  joins:
    - name: customer_to_product_via_orders
      default: true
      join_type: left
      type: lookup
      lookup:
        - destination: db_prod.core.orders
          type: sql
          sql: '{source}.{id} = {destination}.{customer_id}'
        - destination: db_prod.core.order_items
          type: sql
          sql: '{source}.{order_id} = {destination}.{order_id}'
        - destination: product
          type: sql
          sql: '{source}.{product_id} = {destination}.{id}'
```

The bridge tables (`orders`, `order_items`) are raw sources navigated through to reach the `product` entity.

---

## Multiple Joins on One Relationship

A relationship can define multiple joins. Only one can be `default: true`. Others are referenced explicitly by `join_name` in a feature.

A common case: the same two entities can be joined in different ways depending on context.

```yaml
customer-order:
  relationship: one_to_many
  description: Customer to their orders
  joins:
    - name: customer_to_order
      default: true
      join_type: left
      type: sql
      sql: '{source}.{id} = {destination}.{customer_id}'
    - name: customer_to_billing_order
      default: false
      join_type: left
      type: sql
      sql: '{source}.{id} = {destination}.{billing_customer_id}'
```

A metric feature that needs to aggregate orders by billing customer (rather than the placing customer) would specify `join_name: customer_to_billing_order`.

---

## Feature Chaining via Relationships

The relationship file is what makes metric features work. When `customer` defines:

```yaml
- type: metric
  name: total_revenue
  source: order
  metric: sum_net_amount
```

The system:
1. Looks up the `customer-order` relationship.
2. Uses the join with `default: true` (`customer_to_order`).
3. Applies `{source}.{id} = {destination}.{customer_id}`.
4. Computes `SUM({net_amount})` from `order`, grouped by the customer key.

Without the relationship entry, the metric feature cannot be resolved.

---

## When to Add a New Relationship

Add a relationship when:
- You want to define a metric feature that aggregates from a different entity.
- You want to use a `first_last` feature that reaches across entities.
- You need to join two entities in a query that would otherwise require manual SQL.

Do not add a relationship:
- Between an entity and a raw source table (use `related_sources` in the entity YAML instead).
- Between two entities that have no meaningful join path.
- Speculatively — only add relationships you will actually use.

---

## Full Examples

### Example 1 — Grove (B2B SaaS)

Three relationships: `customer-subscription` (direct FK — enables the `active_subscription_count` and `total_mrr` metric features on the `customer` entity), `subscription-invoice` (direct FK — for invoice-level billing data), and `customer-event` via a users lookup bridge (the events table is keyed by `user_id`, not `customer_id`).

```yaml
relationships:

  customer-subscription:
    relationship: one_to_many
    description: >
      A Grove customer has many subscriptions over their lifetime. This relationship enables
      the active_subscription_count and total_mrr metric features on the customer entity.
    joins:
      - name: customer_to_subscription
        default: true
        join_type: left
        type: sql
        sql: '{source}.{id} = {destination}.{customer_id}'

  subscription-invoice:
    relationship: one_to_many
    description: >
      A subscription generates many invoices over its lifetime. Used for invoice count and
      total billed metric features on the subscription entity.
    joins:
      - name: subscription_to_invoice
        default: true
        join_type: left
        type: sql
        sql: '{source}.{subscription_id} = {destination}.{subscription_id}'

  customer-event:
    relationship: one_to_many
    description: >
      A customer has many product events. Events are keyed by user_id, not customer_id —
      the join goes through the db_prod.identity.users bridge table to resolve the mapping.
    joins:
      - name: customer_to_event_via_users
        default: true
        join_type: left
        type: lookup
        lookup:
          - destination: db_prod.identity.users
            type: sql
            sql: '{source}.{id} = {destination}.{account_id}'
          - destination: event
            type: sql
            sql: '{source}.{user_id} = {destination}.{user_id}'
```

---

### Example 2 — Bly (E-commerce)

Three relationships: `customer-order` (direct FK — enables order count and revenue metric features on `customer`), `order-product` (many-to-many via `order_items`), and `customer-product` (many-to-many via both orders and order_items — enables "which products does this customer buy?" queries).

```yaml
relationships:

  customer-order:
    relationship: one_to_many
    description: >
      A Bly customer places many orders. Used for order count and net revenue
      metric features on the customer entity.
    joins:
      - name: customer_to_order
        default: true
        join_type: left
        type: sql
        sql: '{source}.{id} = {destination}.{customer_id}'

  order-product:
    relationship: many_to_many
    description: >
      An order contains many products; a product can appear in many orders.
      The join navigates through db_prod.core.order_items — there is no direct FK
      between the order and product entities.
    joins:
      - name: order_to_product_via_items
        default: true
        join_type: left
        type: lookup
        lookup:
          - destination: db_prod.core.order_items
            type: sql
            sql: '{source}.{order_id} = {destination}.{order_id}'
          - destination: product
            type: sql
            sql: '{source}.{product_id} = {destination}.{product_id}'

  customer-product:
    relationship: many_to_many
    description: >
      Customers are related to products through their full order history. No direct FK —
      the join navigates through both orders and order_items to reach the product entity.
      Enables "which products does customer X buy?" queries.
    joins:
      - name: customer_to_product_via_orders
        default: true
        join_type: left
        type: lookup
        lookup:
          - destination: db_prod.core.orders
            type: sql
            sql: '{source}.{id} = {destination}.{customer_id}'
          - destination: db_prod.core.order_items
            type: sql
            sql: '{source}.{order_id} = {destination}.{order_id}'
          - destination: product
            type: sql
            sql: '{source}.{product_id} = {destination}.{product_id}'
```

---

### Example 3 — Arcadia (Mobile gaming)

Three relationships: `player-session` (one-to-many with two named joins — default includes all sessions, non-default filters to meaningful sessions only), `player-purchase` (one-to-many — enables the `total_spend_usd` and `spend_last_30_days_usd` metric features on `player`), and `player-achievement` (many-to-many via the `player_achievements` bridge table).

```yaml
relationships:

  player-session:
    relationship: one_to_many
    description: >
      An Arcadia player has many sessions. Two named joins are defined: the default
      (player_to_session) includes all sessions and is used for DAU and session count.
      The second (player_to_meaningful_session) filters to sessions with duration > 5 seconds
      to exclude crashed or immediately-abandoned loads from engagement metrics.
    joins:
      - name: player_to_session
        default: true
        join_type: left
        type: sql
        sql: '{source}.{player_id} = {destination}.{player_id}'

      - name: player_to_meaningful_session
        default: false
        join_type: left
        type: sql
        sql: >
          {source}.{player_id} = {destination}.{player_id}
          AND {destination}.{duration_seconds} > 5

  player-purchase:
    relationship: one_to_many
    description: >
      A player makes many in-app purchases. This relationship enables the total_spend_usd
      and spend_last_30_days_usd metric features on the player entity.
    joins:
      - name: player_to_purchase
        default: true
        join_type: left
        type: sql
        sql: '{source}.{player_id} = {destination}.{player_id}'

  player-achievement:
    relationship: many_to_many
    description: >
      Players unlock many achievements; achievements can be unlocked by many players.
      The relationship is resolved through the db_prod.game.player_achievements bridge table.
    joins:
      - name: player_to_achievement_via_bridge
        default: true
        join_type: left
        type: lookup
        lookup:
          - destination: db_prod.game.player_achievements
            type: sql
            sql: '{source}.{player_id} = {destination}.{player_id}'
          - destination: achievement
            type: sql
            sql: '{source}.{achievement_id} = {destination}.{achievement_id}'
```

---

## When to Use This File

Add or update a relationship when a situation meets one of these conditions:
1. Two entities need to be joined to answer a question but no relationship is defined between them
2. The agent fails to resolve a metric that pulls data from another entity
3. There are multiple valid ways to join two entities and different metric features need different joins

**Examples:**
- "I added a `total_revenue` metric feature on `customer` that pulls from `order`, but it fails to resolve" → missing `customer-order` relationship
- "The agent can answer questions about customers and orders separately, but not 'which customers placed the most orders'" → add the `customer-order` relationship
- "We need to answer 'which products does each customer buy?' but `customer` and `product` have no direct FK — orders are in between" → add a `customer-product` lookup relationship through the orders bridge table
- "There are two ways to join `customer` to `order` — by the placing customer and by the billing customer — and different metric features need different joins" → add a second named join to the existing relationship

---

## Best Practices

**Define relationships before adding metric or `first_last` features that depend on them.** The entity YAML references the relationship by name — if it doesn't exist, the feature fails to resolve.

**One entry per entity pair.** The system resolves join direction automatically. Define `customer-order` once — it covers both `customer→order` and `order→customer` traversals.

**Name joins descriptively.** `customer_to_order` is clear; `join1` is not. Names appear in `join_name` references across entity YAML files — they need to be self-explanatory.

**Set `default: true` on the most commonly used join.** Features that omit `join_name` use the default. Only one join per relationship can be the default.

**Use `lookup` only when there is no direct foreign key.** If two entities can be joined directly, use `sql`. Reserve `lookup` for genuine many-to-many relationships that require a bridge table.

**Only define relationships between entities.** Raw source tables belong in `related_sources` inside the entity YAML, not in `entities_relationships.yml`.

---

## Common Pitfalls

{% hint style="danger" %}
Avoid these common pitfalls when defining entity relationships.
{% endhint %}

**Wrong key order for `{source}` and `{destination}`**

The first entity in the key is always `{source}`, the second is always `{destination}`. If you write `order-customer` when you meant `customer-order`, `{source}` will resolve to `order` and `{destination}` to `customer` — the join condition will be backwards.

Write the key with the entity you're joining *from* first. For a metric feature on `customer` that aggregates from `order`, define `customer-order` so that `{source}.{id} = {destination}.{customer_id}` resolves correctly.

**Missing relationship for a metric feature**

If `customer` has a metric feature with `source: order` but no `customer-order` relationship exists, the feature will fail to resolve. Always add the relationship entry before adding the metric feature.

**Using a raw table name as a relationship key**

Relationship keys must be entity names, not raw table names. `db_prod.core.orders` is a source table; `order` is the entity. The relationship is `customer-order`, not `customer-db_prod.core.orders`.
