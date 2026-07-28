---
description: LYNK.md is the agent's orientation and identity — who the business is, who a team is, and how they think. Always loaded.
icon: compass
---

# LYNK.md

The agent's orientation and identity — who the business is, who a team is, how they think, what makes their voice their voice. Always loaded, before any specific reasoning happens.

## What it is

`LYNK.md` is the closest thing in Lynk to what `CLAUDE.md` or `AGENTS.md` is in agent-IDE ecosystems: always loaded, prepended to the agent's context before it reasons about anything. It carries orientation, system-prompt-level personality, and identity — the business at the root level, the team at the [domain](domain/README.md) level.

It is what an agent reads to know *who it is and where it's working*, before it knows anything else. It is deliberately **not**:

- protocol — output format and clarification behavior live in [policies](policy.md);
- vocabulary lookups — terms live in [`GLOSSARY.yml`](glossary.md);
- facts about specific entities — those live in [`ENTITY.md`](entity/entity-md.md).

## Where it lives

One `LYNK.md` at the project root, and optionally one inside each domain:

```
.lynk/LYNK.md                       # the business
.lynk/domains/marketing/LYNK.md     # the marketing team
```

It is always loaded, eagerly, in scope order: root first, then the domain's, appended.

## Format

A single Markdown file of pure prose — no structure is imposed. Unlike the other primitives, `LYNK.md` requires no frontmatter contract; it is orientation, not an indexed primitive. It may use the [`@` operator](../reference/markdown-format.md#references) to inject glossary terms, entity descriptions, or shared files.

**Composition is additive.** The agent's effective orientation is the root `LYNK.md` followed by the domain's `LYNK.md` when present. Domain content *extends* root content; it never replaces it.

**What goes where:**

| File | Carries |
|---|---|
| Root `LYNK.md` | Who the company is — the business, fiscal year, top-level conventions every agent should know. |
| Domain `LYNK.md` | Who this team is — their analytical lens, their voice, vocabulary nuances that differ from the root. |

The test for placement: *would every agent in the project benefit from reading this?* If yes, root. If only this team's agent, the [domain's LYNK.md](domain/lynk-md.md).

One more boundary: a rule about **one entity's rows** — "exclude test accounts from customer analyses" — lives on that entity's [`ENTITY.md`](entity/entity-md.md), not here. `LYNK.md` may point at it, but the entity is its single home; orientation carries only what no single entity owns.

Lynk ships no default — the file is empty until you author it.

## Examples

**A root `LYNK.md`.**

```markdown
# Grove

Grove sells subscription-based business software to other companies. Revenue is
recurring; ARR is the headline metric. The fiscal year starts February 1
(Q1 = Feb–Apr). All revenue reporting is in USD.
```

**A domain `LYNK.md` that extends the root.**

```markdown
# Marketing

This is the marketing team's agent. We think in funnels and attribution, not
contracts. When someone says "lead," they mean a marketing-qualified lead —
the sales team uses the word differently.

Lead with conversion and pipeline contribution. The team's working definition
of "qualified" is in @glossary.mql.description.
```

## Validation

- `LYNK.md` is optional at both levels but recommended at the root — a project with no root orientation passes with a **warning** (see the [project minimum](project.md#the-minimum-project)).

## Related

- [Domain → LYNK.md](domain/lynk-md.md) — the domain-scoped orientation that extends this file
- [GLOSSARY.yml](glossary.md) — vocabulary, which `LYNK.md` is not
- [Policy](policy.md) — operational protocol, which `LYNK.md` is not
- [Markdown format](../reference/markdown-format.md) — the `@` operator
- Guides: [Budgeting the agent's context](../guides/context-engineering.md) · [Placing knowledge in a layer](../guides/where-knowledge-goes.md)
