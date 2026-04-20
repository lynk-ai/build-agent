# Concepts

**Deep-dive reference for how specific systems behave.**

This section explains the cross-cutting concepts that affect multiple parts of the semantic layer. These pages are not tied to a single file type — they cover how domains, entities, context, and the agent work as a system.

Read these when you already understand the basics and want to understand *why* something works the way it does, or when you need to troubleshoot unexpected behavior.

---

## Core Vocabulary

These are the terms used throughout the product and these docs.

**Semantic Graph** — The full set of YAML and Markdown files in your project. Entity YAML files form the data layer (what tables exist, what fields mean, how to aggregate). Context Markdown files form the knowledge layer (what your terms mean, how the agent should behave, what SQL rules apply). Together, they are what the agent reads to answer questions.

**Domain** — A business unit or audience with its own view of the data. Domains let you present different feature definitions, context, and language to different consumers without duplicating the underlying entity model. Examples: `finance`, `marketing`, `customer_success`. Entities always live in the main domain (`default`) — custom domains override only what differs.

**Entity** — A modeled business concept. Not a database table — the governed, curated representation of what the business knows about that concept. Has a `key_source` (primary warehouse table), `keys` (fields that uniquely identify a row), `features` (attributes you can query), and `metrics` (aggregation logic). Examples: `customer`, `order`, `session`.

**Source** — A raw warehouse table or view used to enrich an entity with additional fields. Sources have no metrics, no relationships, and no independent existence in the model. Used for `field` and `first_last` features only.

**Feature** — An attribute of an entity — something you can select, filter, or group by. Four types:

| Type | What it does | Example |
|---|---|---|
| `field` | Pulls a column directly from a source table | `email` from `db.public.customers` |
| `metric` | Pulls an aggregated value from a metric on a related entity | `total_revenue` from `order.sum_amount` |
| `first_last` | Retrieves the first or last value from a source, ordered by a field | `first_order_date` (first by `created_at`) |
| `formula` | A derived value computed from other features on the same entity | `days_since_signup` from `signup_date` |

**Metric** — An aggregation expression defined on a fact entity (e.g., `SUM({amount})` on `order`). Metrics are a central concept in the semantic graph — the primary mechanism for computing quantities across rows. All aggregation logic lives on the entity that owns the data: revenue totals, order counts, averages, and ratios are all defined as entity metrics. The agent uses metrics to answer any question that requires aggregation.

**Metric Feature** — A feature of type `metric` on a dimension entity that pulls an aggregated value from a metric on a related entity. A `customer` entity can define a `total_revenue` feature pointing to `order.sum_net_revenue` — surfacing the aggregated value as a queryable attribute of each customer. Aggregation logic lives once, on the fact entity, and is reused by any entity that relates to it.

**Relationship** — A connection between two entities that enables joins and feature chaining. Defined in `entities_relationships.yml`. Defined once, works in both directions.

**Context** — The collection of Markdown files that teach the agent what things mean and how to work with your data. Five types: `knowledge`, `task-instructions`, `glossary`, `output_format` behavior, and `clarification_policy` behavior. Context compounds — the agent loads all applicable files together, from broadest to most specific scope.

**Agent and Tasks** — The agent is the reasoning layer. It reads the user's request, selects relevant context, and decides what to do. When it needs to produce output it performs a task (e.g., `text-to-sql`). Each task has its own task instructions file that tells the agent how to execute that task correctly.

---

## Advanced Data Modeling

These capabilities build on the core vocabulary above. They are not required to get started, but they unlock more expressive models as your semantic layer matures.

**Feature Chaining** — The mechanism that lets you build features on top of metrics from the same or a different entity. A `customer` entity defines `total_revenue` by pointing to `order.sum_net_revenue`. A `player` entity defines `spend_last_30_days_usd` by pointing to `purchase.sum_net_revenue_usd` with a date filter applied. The aggregation logic stays on the fact entity; the dimension entity just references it.

Because these chains can span entity relationships — and because metric features can themselves be inputs to formula features — feature chaining enables building a full data pipeline inside Lynk. Derived features depend on other derived features, across entities, without duplicating SQL. The semantic graph stays the single source of truth.

All three parts are required for feature chaining to work: a metric defined on the fact entity, a relationship connecting the two entities, and a metric feature on the dimension entity referencing that metric. See [Entities](entities.md) for the full mechanics, and [Data Modeling](data-modeling.md) for a worked multi-entity example.

---

## What's in this section

| Page | What it covers |
|---|---|
| [Domains](domains.md) | How domains scope context to specific audiences — inheritance, overrides, `domain: "*"` vs named domains, conflict handling |
| [Entities](entities.md) | Entity anatomy — key_source, keys, the four feature types, entity metrics, feature chaining, how context compounds |
| [Context](context.md) | The semantic graph — how YAML (data model) and Markdown (context) work together, the five context file types, scoping, compounding |
| [Agent](agent.md) | How the agent works — the 6-step question-to-answer lifecycle, dynamic context loading, text-to-sql, debugging wrong answers |
| [Evaluations](evaluations.md) | How evaluations work — test case structure, running evaluations in the UI, the branch-to-main workflow |
| [Data Modeling](data-modeling.md) | **Advanced.** Feature chaining across multiple entities — linear chains, direct chains, and how to build a data pipeline in the semantic graph |

---

## What you can do with this

After reading this section, you will understand:
- Why `domain: "*"` and `domain: "default"` behave differently — and when to use each
- How entity metrics work — and why they are the central aggregation primitive in the semantic graph
- How metric features surface those aggregations on dimension entities, and how feature chaining extends that into a full data pipeline
- How context compounding works — which files load when, and in what order
- What the agent does step-by-step when it receives a question
**Where to go next:**
- Need exact field-by-field documentation for a specific file? → [File-Types Reference](../file-types/README.md)
- Need the Lynk SQL query syntax? → [API Reference](../api/README.md)
- Want to see a complete working example? → [Project Walkthrough](../project/README.md)
