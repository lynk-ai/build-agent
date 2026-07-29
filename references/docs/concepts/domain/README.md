---
description: A domain is an agent — one team's analytical surface, with its own vocabulary, entities, skills, and policies. A user talks to one at a time.
icon: users
---

# Domain

A domain is an agent. Each domain is one team's analytical agent — marketing's agent, sales' agent, finance's agent — with its own vocabulary, its own data of interest, and its own way of reasoning.

## What it is

When a user picks a domain, they are picking which agent answers their question. A user always talks to one agent at a time. Designing a domain *is* designing an agent — every choice about what entities to include, what to call them, what skills to write, and what policies to set is a choice about how that team's agent thinks and answers.

The triple **domain + branch + build** addresses one queryable agent. See [Project](../project.md) for how builds and branches scope a query.

**Isolation is the definition, not a constraint.** Each domain's agent sees only its own world — sales' agent doesn't know marketing's definitions unless sales pulled them in. When a question can't be answered in the active agent's world, the moves are: ask a different agent, expand this agent's world, or promote shared content to a domain multiple agents can pull from (typically `core`). Cross-domain reasoning is never a runtime mode — it's a modeling decision. Whether a domain may *reference* another is governed by the project [topology](../lynk-yml.md#topology), declared once in `lynk.yml` — under medallion a domain reaches its own files, the root reference files, and the configured shared domain; peers never reach each other.

Create a new domain when a new *audience* arrives whose vocabulary or definitions would be hurt by another team's bleeding in — not per entity. When and how to split, size, and share is [Designing domains](../../guides/designing-domains.md).

## Where it lives

One folder per domain under `domains/`. The folder name is the domain's name — the domain is derived from the path, with no `domain:` field anywhere.

```
.lynk/domains/<domain>/
├── LYNK.md
├── GLOSSARY.yml
├── entities/
├── skills/
└── policies/
```

Folder names are lowercase alphanumeric with underscores (`marketing`, `core`, `customer_success`) — a domain name can appear in a cross-domain reference (`core.customer` in an [`identity:`/`imports:`](../entity/schema-yml/identity-and-imports.md)). `core` is the conventional shared domain under medallion but is not a reserved name. See [Layout and naming](../../reference/layout-and-naming.md).

## Format

A domain is a container, so its format is the folder contract — everything its agent needs to answer questions in its team's language:

- [Entities](../entity/README.md) the team thinks about — some native to this domain, some pulled in from elsewhere.
- [Skills](../skill.md) for the team's recurring analytical reasoning.
- [Policies](../policy.md) for how the team wants the agent to communicate.
- The team's [`GLOSSARY.yml`](glossary.md) and [`LYNK.md`](lynk-md.md).

What goes in is the team's choice. Marketing's agent might pull in `deals` (a sales concept) because attribution requires it; sales' agent might not. The structure provides the primitives; each team composes their agent.

## Examples

**A single domain.** The whole project is one agent.

```
.lynk/domains/core/
└── entities/
    └── customer/
        ├── ENTITY.md
        └── schema.yml
```

**A team domain building on `core`.** Marketing reuses `core.customer` and adds its own skill.

```
.lynk/domains/marketing/
├── LYNK.md
├── GLOSSARY.yml
├── entities/
│   └── customer/        # identity: core.customer
│       ├── ENTITY.md
│       └── schema.yml
└── skills/
    └── attribution-analysis/
        └── SKILL.md
```

## Validation

- A domain folder name is lowercase alphanumeric with underscores.
- A domain with no entities passes with a **warning** — an agent with no entities can't answer anything.
- Cross-domain references that violate the declared topology are build errors.

## Related

- [LYNK.md](lynk-md.md) · [GLOSSARY.yml](glossary.md) — the domain's orientation and vocabulary
- [Entity](../entity/README.md) · [Skill](../skill.md) · [Policy](../policy.md) — what a domain holds
- [lynk.yml → topology](../lynk-yml.md#topology) — where the reference pattern is declared
- [Project](../project.md) — how domain + branch + build address an agent
- Guides: [Designing domains](../../guides/designing-domains.md)
