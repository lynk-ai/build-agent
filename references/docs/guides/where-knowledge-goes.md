---
description: How to decide where a piece of knowledge belongs — entity prose, schema, glossary, metric, skill, policy, LYNK.md, or a reference file.
icon: signs-post
---

# Placing knowledge in a layer

Given one piece of knowledge, this guide produces its single home in the layer.

## When you need this

- An analyst just told you something true ("we exclude test accounts", "NDR means...") and you need to record it somewhere.
- You're migrating a wiki, dbt docs, or tribal knowledge into a layer and every page could plausibly go three places.
- Two files already carry the same fact and you have to pick the home before they drift apart.
- A term feels like it could be a glossary entry, a metric, or a skill — and you keep going back and forth.
- You're reviewing a layer and one file has quietly become a catch-all.

## The principle

One concept, one home. Don't ask *where would this be handy* — an agent with a large brain finds it wherever it lives. Ask *what kind of thing is it*: a fact about data, a word, a number, a procedure, a behavior, or orientation. The kind determines the home; everything else points at that home instead of restating it. Duplication is the failure mode — the copy that isn't the home stops being true first, and nothing tells you.

## Patterns

### The placement table

Situation: any piece of knowledge, before you write it anywhere. The move: classify it by kind and place it by row. Deviate only when the row's own page says so — the rows below link to the owning specs.

| You have | It goes in |
|---|---|
| A fact about one thing's data — quirk, convention, gotcha | That entity: prose in [ENTITY.md](../concepts/entity/entity-md.md); a queryable value in [schema.yml](../concepts/entity/schema-yml/README.md) |
| A word or term the team uses | [GLOSSARY.yml](../concepts/glossary.md) |
| A number the layer should compute | A [metric](../concepts/entity/schema-yml/metric.md) — define it; a glossary entry may point at it |
| A multi-step way of reasoning | A [skill](../concepts/skill.md) |
| An eager, always-apply behavioral rule | A [policy](../concepts/policy.md) |
| Who-we-are orientation | [LYNK.md](../concepts/lynk-md.md) — root if every agent benefits, the domain's if one team does |
| Cross-cutting material that fits no primitive | A [reference file](../concepts/reference-files.md), sparingly |

Example: Arcadia's "`is_active` lags 24h — use `last_session_at`" is row one (fact about `player`'s data → its ENTITY.md); Arcadia's `whale` is row two (a word → glossary).

### The noun/verb test

Situation: content that could be entity knowledge or a skill. The move: ask whether it's noun-shaped (*what is true about X*) or verb-shaped (*how to work through Y*). Nouns land on the entity or in the glossary; verbs become skills. Example: Grove's "`first_paid_at` is null for trials" is a noun — `customer`'s ENTITY.md. Grove's "when investigating churn, check usage decline, pending cancellations, then cohort by signup quarter" is a verb — the `churn-investigation` skill.

### The computed-term rule

Situation: a team term that names a number — `ndr`, `arpdau`. The move: if the layer should compute it, define the metric; the glossary entry says what the word means and may point at the metric. Vocabulary points at computation, never carries it. Deviation: a cross-entity ratio like Arcadia's `arpdau` has no entity-local home ([metrics](../concepts/entity/schema-yml/metric.md) are entity-local), so its glossary entry names the two defined metrics to divide (`sum_net_revenue_usd / count_dau`) — still pointing at defined computation, not carrying raw SQL.

### The entity-row rule

Situation: a rule about one entity's rows — "exclude test accounts from customer analyses." The move: it lives on that entity, in `customer`'s ENTITY.md conventions (or as a feature `filter` if it should shape queries). LYNK.md may point at it; it never restates it. Example: Grove's `is_test_account = false` / `is_deleted = false` convention sits in `customer`'s ENTITY.md, and nowhere else.

### The every-agent test

Situation: orientation or vocabulary that could sit at the root or in a domain. The move: ask *would every agent in the project benefit from reading this?* Yes → root; only one team's agent → that domain. Example: Grove's fiscal year (starts February 1) goes in the root LYNK.md — every analysis needs it. Marketing's "we think in funnels and attribution, not contracts" goes in marketing's LYNK.md.

## Anti-patterns

### The glossary shadow metric store

Wrong:

```yaml
# GLOSSARY.yml — wrong
ndr:
  name: NDR
  description: Net Dollar Retention. Compute as (starting ARR + expansion
    - contraction - churn ARR) / starting ARR, using total_arr snapshots.
```

Why it fails: glossary prose is unvalidated and unexecutable, so the agent re-derives the formula from the description — slightly differently per question. Two askers get two NDRs and the build catches neither, because nothing here references schema.

The fix: define the computation where it's validated — a metric (or a skill if it's genuinely multi-step) — and let the `ndr` entry define the *word* and point at it.

### The skill-as-schema-smuggler

Wrong: a SKILL.md step reading "compute at-risk MRR as `SELECT SUM(amount_cents)/100 FROM maindb.public.subscriptions WHERE cancelled_at IS NOT NULL ...`" because no metric exists for it.

Why it fails: raw SQL in prose bypasses build validation entirely — a skill that references an undefined metric fails the build, but embedded SQL sails through, then rots silently when the table changes. See [Skill](../concepts/skill.md): skills use schema, they don't define it.

The fix: add the missing piece to schema — Grove already has `mrr_at_risk` on `subscription` — and have the skill reference `metric(subscription.mrr_at_risk)` by name.

### Policy creep

Wrong: a POLICY.md named `churn-methodology` saying "when investigating churn, always cohort by signup quarter and check NPS detractors first."

Why it fails: policies are eager — this loads into every question in the domain, taxing the many that have nothing to do with churn. And it isn't a behavioral commitment: you can't check an arbitrary answer against it, only churn answers.

The fix: situational, multi-step, verb-shaped — that's a [skill](../concepts/skill.md). It loads only when a churn question arrives. Policies stay for always-apply behavior like output format.

### Orientation dumping

Wrong: Arcadia's root LYNK.md carrying "note: players who installed before 2022-03-01 have `install_date` set to that date."

Why it fails: the quirk now has a duplicated home. The next correction lands on `player`'s ENTITY.md (where anyone analyzing players looks), LYNK.md keeps the stale version, and every agent pays to load a `player` quirk on questions that never touch `player`.

The fix: the quirk lives in `player`'s ENTITY.md — the entity-row rule. LYNK.md may point at it if it truly needs mentioning, but the entity is the single home.

## The bar

- You can name the single home of any fact in the layer — and every other mention points at it rather than restating it.
- No formula lives in glossary prose; every number the layer computes is a defined metric or feature.
- No raw SQL hides in SKILL.md or POLICY.md — skills and policies reference schema by name.
- A good policy is testable from the transcript alone — you can check any answer against it without knowing what was asked.
- Every line of the root LYNK.md passes the every-agent test.
- Reference files are rare; if they're growing, a primitive is being dodged.

## Related

- [Entity](../concepts/entity/README.md) · [ENTITY.md](../concepts/entity/entity-md.md) · [schema.yml](../concepts/entity/schema-yml/README.md) — where facts and definitions live
- [GLOSSARY.yml](../concepts/glossary.md) · [Skill](../concepts/skill.md) · [Policy](../concepts/policy.md) · [LYNK.md](../concepts/lynk-md.md) · [Reference files](../concepts/reference-files.md) — the homes this guide routes to
- [Designing domains](designing-domains.md) — the sibling decision: which domain the home sits in
