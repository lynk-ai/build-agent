---
description: An entity is a lazy, encapsulated representation of a thing in the business — a folder holding an ENTITY.md prose file and a schema.yml definition.
icon: cube
---

# Entity

A lazy, encapsulated representation of a thing in the business — customers, orders, campaigns, games. Each entity owns everything true about itself.

## What it is

An entity is a concept in the business, not a database table. Everything true about orders — its definitions, its quirks, its conventions, its metrics — lives in the orders entity. That is the core of Lynk's "one concept, one home" model: a quirk in the orders table goes in the orders entity, not in a separate knowledge file or in [`LYNK.md`](../lynk-md.md).

Entities are **lazy**. The agent reads an index of entity names and descriptions, decides which entities a question touches, and loads only those. This keeps the brain large while the agent's working memory stays focused — which is why an entity's `description` is load-bearing.

An entity is two files in a folder:

- [`ENTITY.md`](entity-md.md) — the prose side: quirks, conventions, business context the agent reads to understand the entity's character.
- [`schema.yml`](schema-yml/README.md) — the structured side: the [features](schema-yml/feature.md), [metrics](schema-yml/metric.md), and [relationships](schema-yml/relationships.md) the agent queries to compose SQL.

## Where it lives

A folder per entity inside a [domain](../domain/README.md):

```
.lynk/domains/<domain>/entities/<entity>/
├── ENTITY.md          # prose (required frontmatter; body optional)
├── schema.yml         # structure
└── ...                # optional supporting files
```

The two named files are required; the folder may hold any [supporting files](../../reference/markdown-format.md#supporting-files) the prose injects.

## Format

The split is consistent across every entity:

| File | Carries | Page |
|---|---|---|
| `ENTITY.md` | Frontmatter (`name`, `description`) + prose: framing, conventions, quirks. | [ENTITY.md](entity-md.md) |
| `schema.yml` | `identity`, `keys`, `imports`, `features`, `metrics`, `table_relationships`, `entity_relationships`. | [schema.yml](schema-yml/README.md) |

An entity is rooted in its [`identity`](schema-yml/identity-and-imports.md) — either a physical warehouse table (the standalone case) or another entity (the extending case, which shares grain and imports definitions). See [identity and imports](schema-yml/identity-and-imports.md).

## Examples

**A standalone entity.**

```
.lynk/domains/core/entities/customer/
├── ENTITY.md
└── schema.yml
```

```yaml
# schema.yml
identity: maindb.public.customers
keys:
  - id

features:
  - name: company_name
    description: The customer's company name
    sql: maindb.public.customers.company_name
    data_type: string

metrics:
  - name: count_customers
    description: Count of customers
    sql: COUNT(*)
    data_type: number
```

**An entity folder with supporting content.** Grove's `customer`, with prose injecting a fiscal-year note.

```
.lynk/domains/core/entities/customer/
├── ENTITY.md
├── schema.yml
└── instructions/
    └── fiscal-year.md
```

## Validation

- Both `ENTITY.md` and `schema.yml` are present, and `ENTITY.md` carries valid [frontmatter](../../reference/markdown-format.md#frontmatter-contract).
- `schema.yml` declares a valid `identity` (see [identity and imports](schema-yml/identity-and-imports.md#validation)).
- If `ENTITY.md` is marked `enabled: false`, the whole entity is disabled — `schema.yml` included — and can't be queried, referenced, or imported; a reference to it fails the build like a reference to a missing entity.
- **One concept, one home.** A fact lives on the entity it belongs to and nowhere else — a quirk about orders is not also restated in [`LYNK.md`](../lynk-md.md), a policy, or another entity; everything else points to that single home.
- A domain with no entities passes with a [warning](../domain/README.md#validation).

## Related

- [ENTITY.md](entity-md.md) — the prose side
- [schema.yml](schema-yml/README.md) — the structured side
- [Domain](../domain/README.md) — what entities belong to
- [Skill](../skill.md) — reasoning that *uses* entities, versus facts that live *on* them
- Guides: [Choosing and shaping entities](../../guides/designing-entities.md) · [Reading a complete layer](../../guides/complete-example.md)
