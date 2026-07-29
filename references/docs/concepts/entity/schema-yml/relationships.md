---
description: Relationships declare a path from an entity to a physical table or another entity — directional, per-step joins with cardinality.
icon: share-nodes
---

# Relationships

A relationship declares a path from an [entity](../README.md) to a target — either a physical table or another entity. Features use them to pull values across boundaries; the agent uses them to navigate between entities.

## What it is

Two kinds of relationships exist, distinguished by what they target:

- **Table relationships** target a physical table. Used only at build time, only by the entity that declares them — invisible to the agent. If two entities pull from the same physical table, each declares its own.
- **Entity relationships** target another entity. Used at build time (pulling features or metrics) and at query time (the agent navigating between entities) — visible to the agent.

Both share the same interface shape. The split into two sections reflects the agent's view — entities are the source of truth it reasons in; physical tables are scaffolding below its vision.

Three properties shape how relationships are written:

- **Each relationship is flat.** Two ways to connect the same pair of things means two relationships, not one with branching joins. The `name` is the relationship's full identity, and multiple relationships between the same pair are allowed.
- **Relationships are directional.** Each side declares its own relationship in its own vocabulary — `player_to_session` from the player's perspective, `session_to_player` from the session's. The SQL is direction-specific. AI descriptions matter, so each direction gets its own.
- **Cardinality is per-direction.** Going from `player` to `session` is `one_to_many`; the reverse, `session` to `player`, is `many_to_one`. Each side states what it sees; there is no symmetric cardinality.

Features reference a relationship by its `name` through their [`join_name`](feature.md) — the single namespace means the name resolves whether it's a table or entity relationship.

## Where it lives

`.lynk/domains/<domain>/entities/<entity>/schema.yml`, under `table_relationships:` and `entity_relationships:`.

## Format

| Field | Required | Type | Notes |
|---|---|---|---|
| `name` | ✓ | string | Unique within the entity across all relationships, features, and metrics. Convention: `{source}_to_{target}`. |
| `description` | ✓ | string | What this relationship represents, from this entity's perspective. Load-bearing for the agent. |
| `table` / `entity` | ✓ | path | `table:` in `table_relationships`; `entity:` in `entity_relationships`. The target. |
| `cardinality` | ✓ | enum | `one_to_one`, `one_to_many`, `many_to_one`, or `many_to_many` — from this entity to the target. |
| `steps` | ✓ | list | Ordered hops along the path. Single-step relationships have one entry. |
| `default` | – | `true` | Marks one relationship as the default when several share the same target. |

The `default` flag is a query-time navigation hint — it tells the agent which relationship to use when an entity pair has several. It has no build-time consumer, since every feature names its relationship explicitly through `join_name`.

### Per step

| Field | Required | Notes |
|---|---|---|
| `target` | ✓ | The table or entity reached by this hop. In a **table relationship**, every step (intermediates and the endpoint) is a physical table. In an **entity relationship**, every step is an entity — a multi-hop path models its bridges as entities, never as raw physical tables. The final step's target matches the relationship's `table:` / `entity:`. |
| `join_type` | – | `left` (default), `inner`, or `full_outer`. Per-step, so multi-hop paths can mix join types. |
| `sql` | ✓ | The join condition — qualified references, no templating. **Entity-relationship** steps use `entity.feature` paths (`player.player_id`, never a physical table); **table-relationship** steps use physical columns. See [Validation](#validation) for the full source/target rule. |

Per-step `join_type` is where the LEFT-default is expressed. The entity's grain is still preserved by construction — `one_to_many` and `many_to_many` targets are consumed through aggregation or row-selection in [features](feature.md) and [metrics](metric.md), never through references that multiply rows.

**Join columns must be declared features.** An entity-relationship step's `sql` references only declared features — and [keys are not features](identity-and-imports.md#identity-and-keys). If a step joins on `player.player_id`, both `player` and the entity on the other side must declare that column as a feature.

**When a pair has several relationships, mark exactly one `default: true`.** A bare `JOIN` with no default to resolve it is ambiguous — the agent must fall back to naming the relationship with `USING('<join_name>')`, and near-identical descriptions make that choice a coin flip.

## Examples

**A single-step entity relationship.** On Arcadia's `player`, the purchases a player has made.

```yaml
entity_relationships:
  - name: player_to_purchase
    description: Purchases this player has made
    entity: purchase
    cardinality: one_to_many
    steps:
      - target: purchase
        join_type: left
        sql: player.player_id = purchase.player_id
```

**Two relationships to the same target, plus a multi-step relationship through a bridge entity.** All declared on `player`, so all sit in one entity's `entity_relationships:`. `player_to_session` is the default; `player_to_meaningful_session` narrows the join to real play sessions; `player_to_achievement` hops through `player_achievement`, a bridge modeled as its own entity (the join table `maindb.public.player_achievements` is its identity).

```yaml
entity_relationships:
  - name: player_to_session
    description: All sessions this player has played
    entity: session
    cardinality: one_to_many
    default: true
    steps:
      - target: session
        join_type: left
        sql: player.player_id = session.player_id

  - name: player_to_meaningful_session
    description: Sessions longer than 5 seconds (excludes crash and load sessions)
    entity: session
    cardinality: one_to_many
    steps:
      - target: session
        join_type: left
        sql: player.player_id = session.player_id AND session.duration_seconds > 5

  - name: player_to_achievement
    description: Achievements this player has unlocked
    entity: achievement
    cardinality: many_to_many
    steps:
      - target: player_achievement       # bridge modeled as an entity
        join_type: left
        sql: player.player_id = player_achievement.player_id
      - target: achievement
        join_type: left
        sql: player_achievement.achievement_id = achievement.id
```

A table relationship looks the same, with `table:` instead of `entity:` — here Bly's `order` reaching its line-item rows:

```yaml
table_relationships:
  - name: order_to_items
    description: Per-line-item rows backing this order
    table: maindb.public.order_items
    cardinality: one_to_many
    steps:
      - target: maindb.public.order_items
        join_type: left
        sql: maindb.public.orders.order_id = maindb.public.order_items.order_id
```

## Validation

- `name` is unique within the entity (relationships, features, and metrics share one namespace).
- In an `entity_relationship`, **every step target is an entity** — a physical-table intermediate fails the build (model the bridge as its own entity). In a `table_relationship`, every step target is a physical table.
- An **entity-relationship** step's `sql` references only entities and their features (the owning entity by name, e.g. `player.player_id`) — a physical-table column (`db.schema.table.col`) in an entity relationship fails the build. A **table-relationship** step references physical table columns. In both, the first step's source is the owning entity (resolved from [`identity`](identity-and-imports.md)) — its features in an entity relationship, its identity-table columns in a table relationship; each subsequent step's source is the previous step's target; the final step's target matches the relationship's `table:` / `entity:`.
- All referenced columns exist on their respective tables/entities. In an entity relationship this means **declared features** — a step that joins on an undeclared key column fails (see [identity and imports](identity-and-imports.md#identity-and-keys)).
- At most one relationship per target pair is marked `default: true`.

## Related

- Parent: [schema.yml](README.md) · [Entity](../README.md)
- Siblings: [Feature](feature.md) — references relationships via `join_name` · [Metric](metric.md)
- [identity and imports](identity-and-imports.md) — the base table a relationship's first step anchors to
- [Lynk SQL](../../../api/lynk-sql.md) — `USING('<join_name>')` at query time
- Guides: [Choosing and shaping entities](../../../guides/designing-entities.md)
