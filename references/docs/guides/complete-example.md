---
description: A complete, annotated .lynk/ project for Grove (B2B SaaS) — every file of a small correct layer, end to end, with the reasoning behind each choice. Read when you want the whole shape at once instead of per-concept fragments.
icon: layer-group
---

# Reading a complete layer

What a small, correct `.lynk/` project looks like end to end — every file of Grove's layer, and why each choice was made.

## When you need this

The concept pages each explain one file type in isolation. This page shows them fitting together: one project, one domain, two entities, a skill, and a policy — small enough to read in one sitting, complete enough that every cross-reference resolves. Read it when you're building your first layer or reviewing someone else's.

## The layer at a glance

Two entities carry Grove's model — `customer` (the account) and `subscription` (the billing object) — in a single `core` domain.

```
.lynk/
├── lynk.yml
├── LYNK.md
├── GLOSSARY.yml
└── domains/
    └── core/
        ├── entities/
        │   ├── customer/
        │   │   ├── ENTITY.md
        │   │   └── schema.yml
        │   └── subscription/
        │       ├── ENTITY.md
        │       └── schema.yml
        ├── skills/
        │   └── churn-investigation/
        │       └── SKILL.md
        └── policies/
            └── output-format/
                └── POLICY.md
```

## File by file

### `lynk.yml`

```yaml
schema_version: "v2"
name: Grove
```

No `topology` block: with one domain there is nothing to compose across, and the default (medallion, no shared domain) already says "each domain references only itself and the root files." Adding `shared_domain: core` becomes worthwhile only when a second domain appears. See [lynk.yml](../concepts/lynk-yml.md).

### `LYNK.md`

```markdown
# Grove

Grove sells subscription-based business software to other companies. Revenue is
recurring; ARR is the headline metric. The fiscal year starts February 1
(Q1 = Feb–Apr). All revenue reporting is in USD.
```

Orientation only — facts no single entity owns. Notice what is *not* here: the test-account exclusion is a rule about `customer` rows, so it lives on that entity's `ENTITY.md`, not in orientation. See [LYNK.md](../concepts/lynk-md.md).

### `GLOSSARY.yml`

```yaml
expansion:
  name: Expansion
  description: Additional recurring revenue from an existing customer — upsells, seat growth, or plan upgrades. Counted separately from new-logo revenue.
logo_churn:
  name: Logo Churn
  description: A customer fully cancelling, counted as one lost logo regardless of contract size. Distinct from revenue churn, which weights by ARR.
```

Vocabulary only — each entry is `key → name / description`, no formulas, no pointers to entities. The keys are stable `@` addresses: the skill below injects `@glossary.logo_churn.description`. See [GLOSSARY.yml](../concepts/glossary.md).

### `domains/core/entities/customer/ENTITY.md`

```markdown
---
name: customer
description: Grove accounts. One row per company. Use for ARR, churn, and plan-tier analysis.
---

# Customer

One row per company that has signed up. The team uses "customer" and "account"
interchangeably.

**Convention.** Most analyses exclude test accounts (`is_test_account = false`). This entity is that rule's single home — other files may point here, never restate it.

**Quirk.** `first_paid_at` is null for trials — filter it out when measuring time-to-paid, or the cohort skews.
```

The `description` states the grain and what the entity is *for* — that line is what the agent reads at index time to decide whether to load the entity. The body carries only what every analysis of this entity needs. See [ENTITY.md](../concepts/entity/entity-md.md).

### `domains/core/entities/customer/schema.yml`

```yaml
identity: maindb.public.customers
keys:
  - id

features:
  # keys are not features — id is declared because customer_to_subscription joins on it
  - name: id
    description: Unique customer identifier
    sql: maindb.public.customers.id
    data_type: number
  - name: company_name
    description: The customer's company name
    sql: maindb.public.customers.company_name
    data_type: string
  - name: status
    description: Lifecycle status — 'active', 'churned', or 'trial'
    sql: maindb.public.customers.status
    data_type: string
  - name: arr
    description: Annual recurring revenue for this customer, in USD
    sql: maindb.public.customers.arr
    data_type: number
  - name: is_test_account
    description: True for internal test accounts, which most analyses exclude
    sql: maindb.public.customers.is_test_account
    data_type: boolean
  # derived — a sql expression over the entity's own features
  - name: customer_tier
    description: Size tier from ARR — 'Enterprise' (>= 250k USD), 'Mid-Market' (>= 25k), else 'SMB'
    sql: CASE WHEN customer.arr >= 250000 THEN 'Enterprise' WHEN customer.arr >= 25000 THEN 'Mid-Market' ELSE 'SMB' END
    data_type: string
  # cross-entity aggregate — a feature wrapping a metric on subscription, bound by join_name
  - name: total_mrr
    description: Total normalized monthly recurring revenue across this customer's subscriptions, in USD
    sql: metric(subscription.total_mrr)
    data_type: number
    join_name: customer_to_subscription

metrics:
  - name: count_customers
    description: Count of customers
    sql: COUNT(*)
    data_type: number
  - name: total_arr
    description: Total ARR across customers, in USD
    sql: SUM(customer.arr)
    data_type: number
  - name: churned_customers
    description: Count of customers who have churned
    sql: SUM(CASE WHEN customer.status = 'churned' THEN 1 ELSE 0 END)
    data_type: number

entity_relationships:
  - name: customer_to_subscription
    description: Subscriptions belonging to this customer
    entity: subscription
    cardinality: one_to_many
    steps:
      - target: subscription
        join_type: left
        sql: customer.id = subscription.customer_id
```

Three feature shapes in one file: direct column reads, a derived `sql` expression (`customer_tier`), and a cross-entity aggregate (`total_mrr`) — which is a *feature*, not a metric, because the rows it aggregates belong to `subscription`. Every feature has exactly the fields `name` / `description` / `sql` / `data_type`, plus `join_name` only where the expression crosses the relationship. The relationship step joins on `customer.id` and `subscription.customer_id`, so both are declared features on their entities. See [schema.yml](../concepts/entity/schema-yml/README.md).

### `domains/core/entities/subscription/ENTITY.md`

```markdown
---
name: subscription
description: Active and historical subscriptions. One row per subscription. Use for MRR, billing cycle, and cancellation analysis.
enabled: true
---
```

Frontmatter only — this entity has no quirks worth a body, and the body is optional. The `description` alone makes it loadable.

### `domains/core/entities/subscription/schema.yml`

```yaml
identity: maindb.public.subscriptions
keys:
  - subscription_id

features:
  # joined on by both relationships — so it must be a declared feature
  - name: customer_id
    description: The customer this subscription belongs to
    sql: maindb.public.subscriptions.customer_id
    data_type: number
  - name: status
    description: Subscription status — 'active' or 'cancelled'
    sql: maindb.public.subscriptions.status
    data_type: string
  - name: billing_cycle
    description: Billing cycle — 'monthly' or 'annual'
    sql: maindb.public.subscriptions.billing_cycle
    data_type: string
  - name: amount_cents
    description: Billed amount per cycle, in US cents
    sql: maindb.public.subscriptions.amount_cents
    data_type: number
  - name: mrr
    description: Normalized monthly recurring revenue for this subscription, in USD
    sql: CASE WHEN subscription.billing_cycle = 'annual' THEN subscription.amount_cents / 100.0 / 12 ELSE subscription.amount_cents / 100.0 END
    data_type: number
  - name: is_pending_cancellation
    description: True when the subscription is active but a cancellation takes effect at period end
    sql: subscription.status = 'active' AND maindb.public.subscriptions.cancelled_at IS NOT NULL AND maindb.public.subscriptions.current_period_end > CURRENT_DATE
    data_type: boolean

metrics:
  - name: count_subscriptions
    description: Count of subscriptions
    sql: COUNT(*)
    data_type: number
  - name: total_mrr
    description: Total normalized monthly recurring revenue across subscriptions, in USD
    sql: SUM(subscription.mrr)
    data_type: number

entity_relationships:
  - name: subscription_to_customer
    description: The customer this subscription belongs to
    entity: customer
    cardinality: many_to_one
    steps:
      - target: customer
        join_type: left
        sql: subscription.customer_id = customer.id
```

`customer_id` is declared because a relationship step joins on it; the key `subscription_id` is *not* declared, because nothing references it — keys are not features, and only touched columns earn a declaration. `total_mrr` lives here, on the entity whose rows it sums; `customer` exposes it across the boundary as a feature. The relationship is `customer_to_subscription` seen from the other side: its own name, its own `many_to_one` cardinality, its own `sql`. See [relationships](../concepts/entity/schema-yml/relationships.md).

### `domains/core/skills/churn-investigation/SKILL.md`

```markdown
---
name: churn-investigation
description: How to investigate customer churn — quantify lost logos and ARR, then surface early signals
---

# Churn Investigation

The team counts churn in logos — see @glossary.logo_churn.description.

1. Quantify: lost logos via `metric(customer.churned_customers)`; lost ARR — see @customer.arr.description.
2. Early signals still in the base — see @subscription.is_pending_cancellation.description.
3. Segment by tier — see @customer.customer_tier.description. Enterprise and SMB churn are different problems.
```

A skill uses the schema, it never defines it — every `@` reference here resolves to a feature or glossary entry that already exists, and no value is computed inside the prose. The `description` is what the agent reads to decide whether to load the skill. See [Skill](../concepts/skill.md).

### `domains/core/policies/output-format/POLICY.md`

```markdown
---
name: output-format
description: How the agent presents query results to the user
---

# Output Format

- Lead with the answer, then the numbers behind it.
- Label ARR and MRR explicitly — never a bare "revenue". All figures in USD.
- For period comparisons, use Grove's fiscal calendar (Q1 = Feb–Apr) and say so.
```

The folder is named after the Lynk policy type `output-format`, so this file fully replaces Lynk's shipped default. It carries operating behavior, not data facts or reasoning procedures. See [Policy](../concepts/policy.md).

## What to notice

- **Keys are not features — touched columns are.** `customer.id` and `subscription.customer_id` are declared because a relationship step joins on them; `subscription_id` is not, because nothing references it. [Relationships](../concepts/entity/schema-yml/relationships.md)
- **Metrics are entity-local and take no arguments.** `total_mrr` is defined once, on `subscription`; `customer` reaches it as a feature whose `sql` wraps `metric()` with a `join_name`. [Metric](../concepts/entity/schema-yml/metric.md)
- **Feature fields are exactly six.** `name` / `description` / `sql` / `data_type`, plus optional `join_name` and `filter` — no types, no templating. And every `description` states what the value is (grain, units, enums), because the agent reasons from it. [Feature](../concepts/entity/schema-yml/feature.md)
- **Each rule has one home.** The test-account exclusion lives on `customer`'s `ENTITY.md`; `LYNK.md` carries only what no entity owns. [ENTITY.md](../concepts/entity/entity-md.md) · [LYNK.md](../concepts/lynk-md.md)
- **The glossary is vocabulary, not computation.** `key → name / description` only; anything formula-shaped belongs in schema or a skill. [GLOSSARY.yml](../concepts/glossary.md)
- **Names match folders, everywhere.** `customer`, `churn-investigation`, `output-format` — frontmatter `name` equals folder name, and the domain is the folder under `domains/`. [Layout and naming](../reference/layout-and-naming.md)

## Related

- [Layout and naming](../reference/layout-and-naming.md) — the tree and naming rules this layer follows
- [Entity](../concepts/entity/README.md) — the `ENTITY.md` / `schema.yml` split
- [Skill](../concepts/skill.md) · [Policy](../concepts/policy.md) — reasoning versus operating behavior
- [SQL expressions](../reference/sql-expressions.md) — the grammar every `sql:` above follows
