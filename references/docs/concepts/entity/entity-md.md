---
description: ENTITY.md is the prose side of an entity — quirks, conventions, and business context the agent reads. Short by design, frontmatter required.
icon: file-lines
---

# ENTITY.md

The prose side of an [entity](README.md) — what the agent reads to understand the entity's character: quirks, conventions, gotchas, business context. The kind of thing a senior teammate tells a new hire.

## What it is

Where [`schema.yml`](schema-yml/README.md) defines structure, `ENTITY.md` carries prose. It's the orientation an analyst needs before running any analysis on this thing — not exhaustive documentation, just the few things every analysis must know.

It is **not** the place for:

- definitions of features or metrics — those are in [`schema.yml`](schema-yml/README.md);
- domain-wide context — that's [`LYNK.md`](../lynk-md.md);
- vocabulary — that's [`GLOSSARY.yml`](../glossary.md);
- operational behavior like output format — that's a [policy](../policy.md).

## Where it lives

One per entity, alongside `schema.yml`:

```
.lynk/domains/<domain>/entities/<entity>/ENTITY.md
```

## Format

Frontmatter (the shared [contract](../../reference/markdown-format.md#frontmatter-contract)) over an optional prose body.

**Frontmatter is required.** Lazy loading depends on it: the agent reads each entity's `name` and `description` at index time to decide whether to load the entity for a given question. Write the `description` to signal what the entity is *for* — what kinds of questions it answers.

**`enabled: false` disables the whole entity.** The flag lives on `ENTITY.md`, but it governs the entire entity — `schema.yml` included. A disabled entity can't be queried, referenced, or imported; it's as if it weren't there, so a reference to it fails the build like a reference to a missing entity. See [Markdown format](../../reference/markdown-format.md#frontmatter-contract).

**The body should be short.** `ENTITY.md` loads as a unit whenever the entity is activated, so a long body taxes every analysis that touches the entity. A typical body covers:

- a brief framing of what the entity represents;
- conventions the team uses (vocabulary nuances, how they talk about this thing);
- quirks or gotchas in the data that affect most analyses;
- pointers to deeper content via [`@` injection](../../reference/markdown-format.md#references).

The body is optional — an entity with no quirks worth flagging can have an empty body; the frontmatter alone makes it loadable. Keep `ENTITY.md` lean and inject only what every analysis needs; leave deeper content un-injected so the load cost stays honest.

## Examples

**Frontmatter only.**

```markdown
---
name: subscription
description: Active and historical subscriptions. One row per subscription. Use for MRR, billing cycle, and cancellation analysis.
enabled: true
---
```

**Grove's `customer`, with conventions, a quirk, and an injected file.**

```markdown
---
name: customer
description: Grove accounts. One row per company. Use for ARR, churn, and plan-tier analysis.
enabled: true
---

# Customer

One row per company that has signed up. The team uses "customer" and "account"
interchangeably.

**Conventions.** Most analyses exclude test and deleted accounts
(`is_test_account = false`, `is_deleted = false`). "Churned" is defined in
@glossary.logo_churn.description.

**Quirk.** `first_paid_at` is null for trials — filter it out when measuring
time-to-paid, or the cohort skews.

@/.lynk/domains/core/entities/customer/instructions/fiscal-year.md
```

## Validation

- `ENTITY.md` exists and carries valid frontmatter — `name` (matching the folder) and `description`. A missing required field fails the build.

## Related

- [Entity](README.md) — the entity folder and the two-file split
- [schema.yml](schema-yml/README.md) — the structured side, where definitions live
- [Markdown format](../../reference/markdown-format.md) — the frontmatter contract and `@` injection
- Guides: [Budgeting the agent's context](../../guides/context-engineering.md)
