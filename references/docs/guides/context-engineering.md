---
description: How to budget the agent's context — deciding @ injection vs a link, splitting a growing ENTITY.md, placing content at root vs domain, and when a rule earns a policy.
icon: gauge-high
---

# Budgeting the agent's context

Decide where a sentence lives — and therefore who pays to load it — before you write it.

## When you need this

- You're deciding whether to `@`-inject a supporting file or just link it.
- An `ENTITY.md` keeps growing and every analysis of that entity is paying for it.
- You're unsure whether a convention belongs in the root `LYNK.md`, a domain `LYNK.md`, or on one entity.
- An entity or skill isn't getting loaded for the questions it should answer — or is loaded for ones it shouldn't.
- You're about to add a policy for a rule that only applies sometimes.

## The principle

Every sentence in the layer has a **load class**:

- **Always** — root and domain `LYNK.md`, `GLOSSARY.yml`, policies. Taxes every question in scope.
- **On activation** — an entity's `ENTITY.md` body plus everything it `@`-injects; a skill's body. Taxes every question touching that primitive.
- **On index** — entity and skill frontmatter descriptions. Read for every routing decision.
- **On demand** — linked supporting files. Free until summoned.

Know the class before you write. The cost of a sentence is set by its class, not its length.

## Patterns

### The three-tier entity split

An entity accumulates knowledge — quirks, procedures, worked examples. Split it into three tiers:

- **Index tier** — the `description`: one line, grain plus use-for. Read on every routing decision.
- **Activation tier** — the `ENTITY.md` body: only what *every* analysis of this entity needs.
- **JIT tier** — supporting files (`instructions/`, `examples/`): linked, not injected. Loaded only when a question summons them.

Grove's `customer` `ENTITY.md` had grown to ~600 words: fiscal-year mechanics, the closing-period procedure, two past-analysis walkthroughs. Every ARR or churn question paid all 600 before a line of SQL was written. After the split:

```markdown
---
name: customer
description: Grove accounts. One row per company. Use for ARR, churn, and plan-tier analysis.
---

# Customer

One row per company that has signed up. "Customer" and "account" are interchangeable.

**Conventions.** Most analyses exclude test and deleted accounts
(`is_test_account = false`, `is_deleted = false`). "Churned" is defined in
@glossary.logo_churn.description.

Fiscal-year mechanics: [fiscal-year](/.lynk/domains/core/entities/customer/instructions/fiscal-year.md).
Past investigations: [examples](/.lynk/domains/core/entities/customer/examples/).
```

Cost: activation drops from ~600 words to ~80. The fiscal-year detail now costs nothing except on the questions that need it. Deviate only when a supporting file is genuinely needed by most loads — then `@`-inject it and accept the cost as part of the activation tier.

### `@` vs link

Inject with `@` when the content is **short and needed by most loads of the host**. Link when it's situational or long. And prefer a **conceptual path** over a whole file: `@glossary.logo_churn.description` injects one sentence that stays in sync with its source; `@/.lynk/...` injects an entire file. Grammar in [Markdown format](../reference/markdown-format.md#references).

Grove's `customer` injects `@glossary.logo_churn.description` — one sentence, relevant to nearly every customer analysis — and *links* the closing-period procedure, which only month-end questions touch.

### Descriptions that route

The `description` is the index tier: it's all the agent sees when deciding whether to load an entity or skill. Write it as **what-it-is + grain + "use for X, Y"** — and make it discriminate against its *siblings*, not just describe its subject. Arcadia has both `player` and `player_cohort`; the description is what routes retention questions to the right one:

```yaml
description: Pre-calculated D1/D7/D30 retention per install cohort. One row per cohort. Use for retention curves — never re-derive retention from sessions.
```

A description can be accurate and still fail — see [the vague description](#the-vague-description) below for the wrong form.

### The placement ladder

Root `LYNK.md` → domain `LYNK.md` → entity → supporting file. Each step down means fewer questions pay for the sentence; promoting a sentence up multiplies who pays. Place at the *lowest* rung whose audience still covers everyone who needs it.

Grove: the fiscal year (starts February 1) is root `LYNK.md` — every domain reports on it. The test-account exclusion is `customer`'s `ENTITY.md` — it's a rule about one entity's rows ([LYNK.md](../concepts/lynk-md.md) is explicit that orientation carries only what no single entity owns). The closing-period procedure is a supporting file — even most customer analyses never need it.

## Anti-patterns

### The encyclopedia ENTITY.md

**Wrong:** a 600-word `ENTITY.md` body — history, edge cases, worked examples, all inline.

**Why it fails:** the body loads as a unit on every activation, so every analysis of the entity pays the full 600 words, including the vast majority that need none of it. The waste is invisible — nothing errors, context just fills.

**Fix:** the [three-tier split](#the-three-tier-entity-split). Body keeps only what every analysis needs; the rest moves to linked supporting files.

### Whole-file @ of another entity

**Wrong:** `@/.lynk/domains/core/entities/subscription/ENTITY.md` inside `customer`'s `ENTITY.md`.

**Why it fails:** `@` is eager — every load of `customer` now drags in all of `subscription`'s prose, plus anything *it* injects, whether or not the question involves subscriptions.

**Fix:** link the file, or inject just the fact you need via a conceptual path — `@subscription.is_pending_cancellation.description`.

### The vague description

**Wrong:** `description: Customer data`.

**Why it fails:** the agent routes on descriptions. This one loads the entity for wrong questions and skips it for right ones — and no build check catches it, because the field is present and non-empty. The failure only shows up as bad answers.

**Fix:** grain + use-for: `Grove accounts. One row per company. Use for ARR, churn, and plan-tier analysis.`

### Policy creep

**Wrong:** a situational rule — "when analyzing refunds, break out by channel" — written as a policy.

**Why it fails:** policies are eager, always-apply commitments ([Policy](../concepts/policy.md)); every question in the domain now carries a rule that applies to one kind of analysis. Each addition seems small; the always-loaded tier only ever grows.

**Fix:** put it where it's lazy — a skill body if it's how to reason through refund analyses, entity prose if it's a fact about `order`.

### Injection chains

**Wrong:** `ENTITY.md` injects `instructions/a.md`, which injects `instructions/b.md`, which injects a third file.

**Why it fails:** injection *cycles* fail the build ([Markdown format](../reference/markdown-format.md#validation)), but chains pass silently — and every activation of the host loads the whole transitive closure. The author of each link sees one small `@`; the agent pays for all of them.

**Fix:** flatten. The host injects at most one level; anything deeper becomes a link the agent follows on demand.

## The bar

- Every entity and skill `description` states grain and use-for, and discriminates against its siblings.
- `ENTITY.md` bodies stay under ~150 words unless you can say why every analysis needs more.
- Nothing is `@`-injected that isn't needed by most loads of its host file.
- For any sentence in the layer, you can name its load class — and it's the cheapest class that still reaches everyone who needs it.

## Related

- [Markdown format](../reference/markdown-format.md) — the `@`/link/bare-path grammar and supporting files
- [ENTITY.md](../concepts/entity/entity-md.md) · [LYNK.md](../concepts/lynk-md.md) · [GLOSSARY.yml](../concepts/glossary.md) · [Skill](../concepts/skill.md) · [Policy](../concepts/policy.md) — the primitives whose load behavior this guide budgets
- [Reference files](../concepts/reference-files.md) — the on-demand tier's home for cross-cutting content
- [Evolving a live layer](./evolving-the-layer.md) — changing what's already loaded without breaking consumers
