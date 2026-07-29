---
description: A domain's LYNK.md — who this team is. Appended to the root LYNK.md; extends it, never replaces it.
icon: compass
---

# Domain LYNK.md

A domain's orientation file — who this team is, their analytical lens and voice. It extends the [root `LYNK.md`](../lynk-md.md) rather than standing alone.

## What it is

The shared definition of what `LYNK.md` is — its role, what belongs in it, and what doesn't — lives on the [root `LYNK.md`](../lynk-md.md) page. This page covers only the **scope behavior** at the domain level.

A domain `LYNK.md` describes who *this team* is: their analytical lens, their voice, and the vocabulary nuances that differ from the company-wide root. It is what makes a [domain's](README.md) agent *theirs*.

## Where it lives

Optionally, one per domain:

```
.lynk/domains/<domain>/LYNK.md
```

## Format

Pure prose, same as the root file — see [LYNK.md → Format](../lynk-md.md#format).

**Composition is additive.** The agent's effective orientation is the root `LYNK.md` followed by the domain's, appended in scope order. The domain file *extends* the root; it never replaces it. Put content here only when it is specific to this team — if every agent in the project would benefit, it belongs in the root.

## Examples

**A domain voice note.**

```markdown
# Finance

This is the finance team's agent. Default to GAAP definitions and the fiscal
calendar. When a number could be cash or accrual, say which.
```

**A domain that redefines a shared term for its audience.**

```markdown
# Marketing

This is the marketing team's agent. We think in funnels and attribution.
"Lead" here means a marketing-qualified lead — narrower than the company-wide
usage in the root. The team's definition is in @glossary.mql.description.

Lead answers with conversion and pipeline contribution, not contract value.
```

## Validation

- Optional; a domain with no `LYNK.md` simply inherits the root orientation.

## Related

- [LYNK.md](../lynk-md.md) — the root concept and the shared definition
- [Domain](README.md) — the agent this orientation belongs to
- [Domain GLOSSARY.yml](glossary.md) — the team's vocabulary
