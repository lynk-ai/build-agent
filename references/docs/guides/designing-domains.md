---
description: How to decide how many domains to create, what belongs in the shared domain, and when to promote, extend, split, or merge.
icon: sitemap
---

# Designing domains

This guide produces a domain layout: how many domains, what sits in the shared one, and how a definition moves between them.

## When you need this

- You're starting a layer and don't know whether to make one domain or five.
- A second team wants to use the layer and their vocabulary doesn't match the first team's.
- Two teams define the same term — ARR, lead, active — differently, and both are "right."
- You're tempted to copy an entity's YAML from one domain into another.
- A domain feels wrong-sized: bloated and contradictory, or empty and pointless.

## The principle

A [domain is an agent](../concepts/domain/README.md) — one audience's analytical surface. So domains map to audiences, never to data, dashboards, or org charts you merely anticipate. The shared domain holds only what multiple audiences consume *and* describe the same way; a contested definition stays in the leaf that owns it until the teams reconcile. Everything else follows: when to create a domain (a new audience), what to promote (agreed, twice-consumed), when to split (one audience turns out to be two).

## Patterns

### Start with one domain

Situation: a new layer, one team asking questions. The move: one domain, until the second *audience* arrives — not the second entity. `customer` and `subscription` in one domain is normal; a second domain with nobody behind it is not. Deviate only when two teams are onboarding on day one — then start with the shared domain plus two leaves. Example: Grove's arc — a `core`-only layer serving everyone; finance arrives with its own collections vocabulary → `core` + `finance`; marketing follows → `core` + `finance` + `marketing`.

### What lives in the shared domain

Situation: deciding whether a definition belongs in `core` or a leaf. The move: promote only what passes the two-consumers-AND-one-agreed-description test — at least two domains consume it, and both sign off on a single description. Contested definitions stay in leaves until reconciled. Example: Grove's finance defines ARR as contract value; marketing computes a run-rate ARR from current MRR. Those stay split — `finance.customer` and `marketing.customer` each carry their own — until the company reconciles on one description. The reconciled one moves to `core`; the leaf-specific variant that survives keeps a distinct name.

### The promotion protocol

Situation: a leaf definition just found its second consumer. The move, in order:

1. It was defined in the leaf (say, finance's `customer` with `total_arr`).
2. A second team needs it — marketing wants ARR for segmentation.
3. Reconcile the description: one sentence both teams accept. This is the slow step; don't skip it.
4. Move the entity (or the definition) to `core`.
5. The leaf re-declares itself as an extension — `identity: core.customer` plus explicit `imports` of what it uses (see [identity and imports](../concepts/entity/schema-yml/identity-and-imports.md)).
6. **Imports can't be renamed** — so if the leaf's old local name differed, keep a deprecated local feature whose `sql` references the import (the alias is how old queries keep working while they migrate), and delete it after a stated window.

### Extend vs duplicate

Situation: a leaf needs an entity that exists elsewhere. The move: if it's the same conceptual thing — same grain, same meaning — extend it: `identity: core.customer` + imports, which share definitions by reference. If the grain or meaning genuinely differs, define an independent entity rooted in its own table. Never copy-paste YAML between peer domains — sameness must be declared, not implied by similar columns. Example: Grove marketing's `customer` is the same company as core's → extension. Grove's `subscription` is a different grain from `customer` → its own entity, no relation to extension.

### Vocabulary layering

Situation: deciding where a term's glossary entry lives. The move: company-wide terms in the root [GLOSSARY.yml](../concepts/glossary.md); a [domain glossary](../concepts/domain/glossary.md) entry only for a genuine meaning shift for that audience. Collision-domain-wins is the feature: marketing overrides `lead` to mean a marketing-qualified lead, narrower than the company-wide root definition, and marketing's agent resolves the word marketing's way. Deviate when the "override" is really a correction — then fix the root entry so every agent benefits.

### Sizing signals

Situation: a domain feels wrong-sized. The move — read the signals: **split** when sub-teams inside one domain disagree on what a term means (that's two audiences sharing one agent); **merge** when a domain is more than ~90% imports — it's a filtered view of `core`, not an agent with its own vocabulary or reasoning; and treat a one-entity, no-skill domain as a placeholder, not an agent — fold it back until its audience shows up. Example: a Grove `marketing` domain that only imports `core.customer` and adds nothing has no reason to exist yet.

## Anti-patterns

### Core as dumping ground

Wrong: at Grove, every new definition is promoted to `core` "so it's there if anyone needs it" — marketing's `mql`, finance's collections aging, all of it.

Why it fails: `core` is what every agent can see, so its vocabulary decays to the lowest common denominator, and every definition change now needs every team's sign-off — each definition fight becomes a core fight. Leaves lose the room to mean things their own way.

The fix: the two-consumer test. Nothing enters `core` without two named consumers and one agreed description; everything else stays in its leaf.

### Copy-paste peer coupling

Wrong: Grove's marketing needs finance's `customer` definitions; peers can't reference each other under [topology](../concepts/lynk-yml.md#topology), so someone pastes finance's `schema.yml` into `marketing/entities/customer/`.

Why it fails: the copies fork at the first correction. Finance fixes `total_arr`; marketing's paste doesn't move; two agents now report different ARR and no build error fires — they are, by definition, independent entities.

The fix: the peer barrier is a prompt to promote. Move the shared definition to `core`, and have both leaves extend it via `identity` + `imports` — imports are by reference, so corrections propagate.

### Domain-per-dashboard

Wrong: a `board_deck` domain at Grove holding whatever the quarterly deck needs.

Why it fails: a domain is an audience's agent, and "the board deck" isn't an audience — it's a set of questions. The dashboard domain has no vocabulary or reasoning of its own, duplicates entities that already have homes, and users picking an agent are now picking a report.

The fix: the questions belong to an existing audience's domain; if walking through them is a recurring procedure, that's a [skill](../concepts/skill.md) there — not a domain.

### The ghost domain

Wrong: an `operations` domain created "for when ops onboards" — one entity, no skills, no glossary, no LYNK.md, no one asking it anything.

Why it fails: it appears in the domain list as a pickable agent but can't answer like one, and whatever gets parked there is invisible to every real agent — peers can't reach into it, so the content is worse than homeless.

The fix: don't create a domain before its audience exists. Put the entity in the domain that actually consumes it (or `core`, once two do), and create `operations` the day ops shows up with questions.

## The bar

- Each domain names its audience — you can say whose agent it is in one sentence.
- Every `core` entry has two consumers you can name today, and one description both accepted.
- No two domains define the same term with silently different meanings — every glossary collision is a deliberate, documented domain override.
- No YAML is duplicated between peers; every "same thing" is declared with `identity` + `imports`.
- No domain is >90% imports, and none is a one-entity, no-skill placeholder.

## Related

- [Domain](../concepts/domain/README.md) — the primitive this guide shapes
- [lynk.yml → topology](../concepts/lynk-yml.md#topology) — the reference rules that make promotion the sharing mechanism
- [Identity and imports](../concepts/entity/schema-yml/identity-and-imports.md) — the extension mechanics the promotion protocol lands on
- [GLOSSARY.yml](../concepts/glossary.md) · [Domain GLOSSARY.yml](../concepts/domain/glossary.md) — the vocabulary layering pattern's owners
- [Placing knowledge in a layer](where-knowledge-goes.md) — the sibling decision: which primitive, before which domain
