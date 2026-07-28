---
description: A domain's GLOSSARY.yml — the team's vocabulary, merged over the root glossary with the domain winning on a key collision.
icon: book-a
---

# Domain GLOSSARY.yml

A domain's vocabulary file. It merges with the [root `GLOSSARY.yml`](../glossary.md), with the domain winning when a term collides.

## What it is

The shared definition of what `GLOSSARY.yml` is — its role, its entry format, and when a term should be a [skill](../skill.md) instead — lives on the [root `GLOSSARY.yml`](../glossary.md) page. This page covers only the **scope behavior** at the domain level.

A domain glossary holds the terms this team uses, and overrides any root term whose meaning differs for this audience.

## Where it lives

Optionally, one per domain:

```
.lynk/domains/<domain>/GLOSSARY.yml
```

## Format

Same entry format as the root — key → `name` / `description`. See [GLOSSARY.yml → Format](../glossary.md#format).

**Composition merges across scopes.** The effective glossary in a domain is the root glossary merged with the domain's. On a key collision, the **domain entry wins** — this is how a team gives a company-wide term its own meaning. Terms the domain doesn't redefine are inherited from the root unchanged.

## Examples

**One domain-specific term.**

```yaml
mql:
  name: MQL
  description: Marketing Qualified Lead. A lead that has met the marketing team's engagement-score threshold and is ready to pass to sales.
```

**Overriding a shared term for this audience.** The root defines `lead` broadly; marketing narrows it.

```yaml
lead:
  name: Lead
  description: A marketing-qualified lead — narrower than the company-wide definition. Excludes self-serve signups, which marketing does not source.

cac:
  name: CAC
  description: Customer Acquisition Cost. Total marketing and sales spend in a period divided by new customers acquired in that period.
```

## Validation

- Optional; a domain with no glossary inherits the root vocabulary.
- Each entry declares `name` and `description`.
- A root/domain key collision resolves to the domain entry (expected, not an error).

## Related

- [GLOSSARY.yml](../glossary.md) — the root concept and the shared definition
- [Domain](README.md) — the agent this vocabulary belongs to
- [Domain LYNK.md](lynk-md.md) — the team's orientation
