---
description: Reference files — user-organized files outside the domain primitives, the escape hatch for cross-cutting content, reached by absolute /.lynk/ references.
icon: folder-open
---

# Reference Files

User-organized files that sit outside the domain primitives — the escape hatch for cross-cutting content that doesn't fit an entity, skill, policy, or glossary.

## What it is

Most knowledge has an obvious home: facts go on an [entity](entity/README.md), vocabulary in the [glossary](glossary.md), reasoning in a [skill](skill.md), behavior in a [policy](policy.md). Reference files are for the rare content that fits none of them — onboarding notes, internal documentation, a shared data dictionary — that an author wants to point at without inventing a primitive.

They are any files or folders outside the domain primitives (a `docs/` folder is the usual convention, but the name and layout are yours), kept at one of two scopes:

- **At the `.lynk/` root** (outside `domains/`) — shared content that belongs to no domain. The project [topology](lynk-yml.md#topology) makes these reachable from every domain.
- **Inside a domain** — a domain's own docs or references, scoped to that domain like the rest of its content.

Use the root for cross-domain material; a domain folder for material only that domain needs.

The escape hatch is deliberately low-status. Heavy use is a signal the primitives are wrong — something that should be an entity, skill, or policy is being parked here. Reach for it sparingly.

## Where it lives

At the `.lynk/` root for shared content, or inside a domain for domain-scoped content:

```
.lynk/
├── docs/                         # root: shared, reachable from every domain
│   └── onboarding.md
├── reference/
│   └── data-dictionary.md
└── domains/
    └── marketing/
        └── docs/                 # domain: scoped to marketing
            └── channel-taxonomy.md
```

## Format

Plain files — no frontmatter contract, no required structure (these aren't primitives). A reference file never loads on its own; it enters context only when something points at it, via an absolute [`/.lynk/` reference](../reference/markdown-format.md#references) — `@` injection to pull its content in, or a markdown link / bare path to navigate to it.

## Examples

**A root onboarding note injected into the root `LYNK.md`.**

```markdown
# In /.lynk/LYNK.md

New to this project? Start here: @/.lynk/docs/onboarding.md
```

**A shared data dictionary linked from an entity (navigation, not injection).**

```markdown
# In /.lynk/domains/core/entities/customer/ENTITY.md

Column lineage and source notes: [data dictionary](/.lynk/reference/data-dictionary.md)
```

## Validation

- A reference file nothing points at is unreachable — it never loads. Not an error, but it earns its keep only when referenced.
- References to it are absolute (`/.lynk/…`) and resolve to a real file.
- Root reference files (outside `domains/`) are reachable from every domain (they belong to none); reference files inside a domain are scoped to that domain. See [topology](lynk-yml.md#topology).

## Related

- [Markdown format](../reference/markdown-format.md) — the reference grammar (`@` injection, markdown links, bare paths)
- [lynk.yml → topology](lynk-yml.md#topology) — what each domain may reach
- [Entity](entity/README.md) · [Skill](skill.md) · [Policy](policy.md) — the primitives reference files are a last resort behind
