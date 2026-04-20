# Overview

Data teams carry a lot of knowledge that lives nowhere in the database: what a "churned customer" actually means, which revenue column to trust, why the orders table has duplicates before a certain date, what "monthly active user" counts vs. excludes. When an AI agent queries your data without that context, it makes assumptions — and those assumptions produce wrong answers.

Lynk is a semantic layer for AI. It gives data teams a structured way to encode their data model and institutional knowledge into files the agent reads before every query. The agent learns your entities, your metrics, your business rules, your vocabulary — and uses them to generate accurate SQL and reliable answers.

The result: an AI analyst that works the way your best analyst does, because you taught it everything your best analyst knows.

---

## Product Philosophy

Lynk is built on a few core ideas that shape how everything works:

**You define everything in files.** The agent knows only what you've written. Nothing is inferred from table names or column patterns. If a rule isn't in a file, the agent doesn't know it — which means you can trust what it does know.

**Files live in your Git repository.** Your semantic layer is version-controlled, reviewable, and editable in any IDE. It's not locked inside a SaaS UI. Teams treat it like code.

**Two file types, two jobs.** YAML files define the structure of your data — what entities exist, what fields mean, how metrics are calculated. Markdown files teach the agent how to think — business definitions, vocabulary, SQL rules, behavior. YAML tells the agent *what your data is*. Markdown tells the agent *how to reason about it*.

**Context compounds.** The agent loads all applicable context together at query time — domain-level rules, entity-specific knowledge, task-specific instructions. More context means more accuracy. Start with the basics and add depth over time.

**One agent, one reasoning layer.** There is one agent. It reads context and produces output — text-to-SQL, answers, analysis. All agent behavior is driven by the files you define. No black boxes.

---

## Two File Types

There are two types of files you manage in Lynk:

| Type | Format | What it does |
|---|---|---|
| **Data model** | YAML | Defines your data schema — entities (each entity is a level of granularity) and its features, metrics and relationships |
| **Context** | Markdown | Teaches the agent about your tribal knowledge — knowledge, glossary, task instructions, behavior |

---

## What Connects to Lynk

Lynk connects to your data warehouse with read-only access. Supported warehouses: **Snowflake**, **BigQuery**, **Postgres**, **Clickhouse** and **Trino**. New data warehouse connections are being  added constantly.

Entity `key_source` fields point to any table or view in your warehouse — including dbt models. If a dbt model is materialized as a table or view, you can use it as an entity source directly.

---

## Your Data Model — YAML Files

These files define the structure of your data. The agent uses them to know what tables exist, what fields mean, and how to calculate metrics.

**Entity YAML** (`<entity>.yml`)
An entity represents a level of granularity in your data — a real-world thing like `player`, `order`, or `customer`. Each entity has one definition as the source of truth. It defines features (columns), metrics (aggregations), and which source tables to pull from.

**Relationships YAML** (`entities_relationships.yml`)
Defines how entities connect to each other. Enables the agent to join across entities without guessing.

---

## Your Context — Markdown Files

These files teach the agent how to behave and interpret your data. They live alongside your YAML files and are loaded at query time.

Each markdown file has frontmatter that controls its scope — how broadly it applies:

```yaml
---
type: knowledge
domain: "*"           # applies to every domain — default, marketing, finance, all of them
# or
domain: "default"    # applies ONLY to the main domain — does NOT apply to custom domains like "marketing"
# optionally add:
entity: player        # scopes further to a single entity within the domain
---
```

{% hint style="warning" %}
`domain: "default"` does **not** mean "applies everywhere by default." It scopes content to the main domain only. Use `domain: "*"` for content that should apply across all domains. See [Domains](concepts/domains.md) for the full model.
{% endhint %}

The same file type can exist at multiple levels. Context compounds — the agent loads all applicable levels together. There are two independent dimensions that control when a file loads.

**Domain and entity scope** — applies to all context file types:

| Frontmatter | When the agent loads it |
|---|---|
| `domain: "*"` | Every query in every domain |
| `domain: "default"` | Every query in the main domain |
| `domain: "marketing"` | Every query in the marketing domain |
| `domain: "default"` + `entity: player` | When the `player` entity is relevant in the main domain |

**Task scope** — applies only to task-instructions files:

| Frontmatter | When the agent loads it |
|---|---|
| `tasks: "text-to-sql"` | Only when the agent is generating SQL |

A task-instructions file uses both: it has a `domain` (or `domain` + `entity`) to control which queries it applies to, and a `tasks` field to ensure it only loads during SQL generation.

---

**Knowledge**
What something *is*. Business definitions, data rules, caveats, context. Can be scoped to all domains, to a specific domain, or to a specific entity within a domain. Context compounds — when a query involves the `player` entity, the agent loads domain-level knowledge AND entity-level knowledge together.

**Glossary**
Your company's vocabulary. Terms, abbreviations, KPI names that only make sense inside your organization. 1–2 sentences per entry. Scoped to a domain.

**Task Instructions**
Instructions for a specific task. For text-to-SQL: which filters to always apply, edge cases, naming rules. Loaded only when the agent performs that task. Can be scoped to a domain (applies to all entities) or to a specific entity within a domain.

**Behavior**
How the agent interacts with users. Two types, set via the `kind` field:

- `kind: output_format` — tone, table formatting, insights, data disclaimers, analysis best practices
- `kind: clarification_policy` — when to ask clarifying questions and how to phrase them

---

## What Goes Where

| I want to teach her... | Type | Frontmatter |
|---|---|---|
| What the `order` entity is and which tables it uses | Entity YAML | *(YAML file — no frontmatter)* |
| How `player` and `game` relate to each other | Relationships YAML | *(YAML file — no frontmatter)* |
| Context that applies across all domains | Knowledge | `type: knowledge` / `domain: "*"` |
| Context specific to the default domain | Knowledge | `type: knowledge` / `domain: "default"` |
| Everything about the `player` entity specifically | Knowledge | `type: knowledge` / `domain: "default"` / `entity: player` |
| What "monthly active user" means in our company | Glossary | `type: glossary` / `domain: "default"` |
| Always filter inactive accounts when querying orders | Task Instructions | `type: task-instructions` / `domain: "default"` / `entity: order` / `tasks: "text-to-sql"` |
| Always filter inactive accounts across all entities | Task Instructions | `type: task-instructions` / `domain: "default"` / `tasks: "text-to-sql"` |
| Always ask for a date range when it's not specified | Behavior | `type: behavior` / `kind: clarification_policy` / `domain: "*"` |
| Control how the agent formats tables and insights | Behavior | `type: behavior` / `kind: output_format` / `domain: "*"` |

---

## How It Works

A user asks: *"Which customers spent more than $10k last quarter?"*

1. **Agent reads context** — loads domain knowledge, the `customer` entity YAML, glossary, behavior files
2. **Agent reasons** — identifies the right entity, metric, and time filter based on the question
3. **Agent performs text-to-SQL** — loads entity YAML and task instructions, generates the query
4. **SQL is generated** — the agent writes a query using Lynk's entity syntax, executed against your warehouse
5. **Agent formats the response** — applies output format rules, returns the answer

Every step is driven by context you defined. Nothing is guessed. That's the control.

→ See [Agent](concepts/agent.md) for the full step-by-step lifecycle and how to debug wrong answers.

---

## Getting Started

**What you need:**
- A Git repository (GitHub, GitLab, Bitbucket, or any hosted Git service)
- Read-only credentials for the database schemas you want to connect — Snowflake, BigQuery, Postgres, Clickhouse, or Trino

No local installation required.

**Setup:**

1. Go to [app.getlynk.ai](https://app.getlynk.ai) and create your account.
2. Run the onboarding flow at [app.getlynk.ai/onboarding](https://app.getlynk.ai/onboarding) — it walks through connecting your Git repository and data warehouse in one flow.

**Connecting your Git repository:** Provide your repository URL and grant Lynk access. Lynk creates a `.lynk/` folder at the root of your repo. This is where your entire semantic layer lives — entity definitions, context files, relationships, evaluations. You can edit files in the Lynk UI or directly in your editor (VS Code, Cursor, or any IDE). Both write to the same repository.

**Connecting your data warehouse:** Provide read-only credentials to the schemas you want Lynk to query. Lynk never writes to your warehouse.

**After setup:** Your repo has a `.lynk/default/` folder — your main domain, where all entity definitions live. The agent can answer questions immediately, but accuracy depends on context. The more you teach it — entity definitions, business rules, glossary terms, SQL patterns — the better it performs. Most teams reach their first trusted production answers within 1–2 days.

{% hint style="info" %}
**Note on query syntax:** Throughout the docs, examples show queries like `FROM entity('customer')` and `metric(count_orders)`. This is Lynk SQL — the syntax the agent uses when querying your semantic layer, and the syntax you write when authoring evaluation test cases. See [Lynk SQL](api/lynk-sql.md) for the full reference.
{% endhint %}

---

## Next Steps

| If you want to... | Go to |
|---|---|
| Understand the vocabulary (Entity, Feature, Metric, etc.) | [Concepts](concepts/README.md) |
| See every file type and what it does | [File-Types Reference](file-types/README.md) |
| Query the semantic layer via SQL or REST | [API Reference](api/README.md) |
| Build a project from scratch | [Project Walkthrough](project/README.md) |
| Add a new entity to an existing project | [Adding an Entity](guides/adding-an-entity.md) |
