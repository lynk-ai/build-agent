# Context

The agent reads two things to answer a question: the data model (entity YAML files defining features, metrics, and relationships) and context (Markdown files carrying business knowledge, terminology, and behavioral rules). Together, these form the semantic graph — the complete framework you build to teach the agent about your company.

Context is the layer you build and refine most. A data model without context produces technically valid but business-ignorant answers. Context is how you close the gap between "the agent can query your data" and "the agent answers like your best analyst would."

---

## The Semantic Graph

The semantic graph has two layers:

**The data layer** — YAML files that define your data model. Entity definitions, features, metrics, relationships. This is the agent's understanding of what your data *is*: what tables exist, what they mean, how they relate, and how to aggregate them.

**The context layer** — Markdown files that carry your business knowledge. Glossaries, knowledge files, task instructions, clarification policies, output formats. This is the agent's understanding of how to *work* — your terminology, your rules, your preferences, your data quirks.

| Layer | File types | What it teaches |
|---|---|---|
| Data | Entity YAML, `entities_relationships.yml` | Which tables to use, which fields matter, how to calculate KPIs, how entities relate |
| Context | `knowledge`, `glossary`, `task-instructions`, `clarification-policy`, `output-format` | What your terms mean, how to behave with different audiences, what to filter by default, how to answer when uncertain |

The connection between the two layers happens through entities and domains. Entity YAML files define the data model for a specific concept — say, `customer`. Context files scoped to that entity enrich the data model with business meaning. When the agent identifies that a question is about customers, it loads both the entity YAML and all context files scoped to that entity. The data model and the context arrive together.

Everything in the semantic graph lives in your Git repository — version-controlled, editable in any IDE or in the Lynk UI, and yours entirely.

---

## The Five Context File Types

| Type | Frontmatter | What it carries |
|---|---|---|
| `knowledge` | `type: knowledge` | Business definitions, data quality notes, metric conventions, domain rules |
| `glossary` | `type: glossary` | Company-specific terms and abbreviations — 1–2 sentences each |
| `task-instructions` | `type: task-instructions` | How to perform a specific task — SQL patterns, filter defaults, naming rules |
| `clarification-policy` | `type: behavior` / `kind: clarification_policy` | When the agent asks follow-up questions vs. when it proceeds |
| `output-format` | `type: behavior` / `kind: output_format` | How answers are structured and presented |

Each file type loads at a different point. Task instructions only load when the agent is performing that specific task. Clarification policy loads when the agent is deciding whether to ask a follow-up. Knowledge and glossary load when the scoped domain or entity is active.

---

## How Context is Scoped

Every context file has a `domain` field and optionally an `entity` field in its frontmatter. These determine when the file loads.

**Domain scope** — `domain: "*"` applies to all queries across all domains. A named domain (e.g., `domain: "finance"`) applies only when that domain is active.

**Entity scope** — adding `entity: customer` narrows the file further: it only loads when the `customer` entity is identified as relevant to the question. Omit the `entity` field for domain-wide files.

```yaml
---
type: knowledge
domain: "*"
---
# Loads on every query in every domain

---
type: knowledge
domain: "finance"
---
# Loads on every query in the finance domain

---
type: knowledge
domain: "default"
entity: customer
---
# Loads when a customer query runs in the main domain
```

For the full inheritance and override model, see [Domains](./domains.md).

---

## Context Compounding

Context loads at multiple levels simultaneously. For a query about the `customer` entity in the `finance` domain, the agent assembles:

1. All files scoped to `domain: "*"` (global conventions)
2. All files scoped to `domain: "finance"` (finance-specific rules)
3. All files scoped to `entity: customer` in the applicable domains (customer-specific knowledge)
4. Task instructions for the current task (e.g., `type: task-instructions` for `text-to-sql`)

All of this loads together. The agent does not pick one level and ignore the others — it reads all applicable context for the question at hand.

Named domain content takes precedence over `domain: "*"` content when the same concept is defined in both. See [Domains](./domains.md) for override and exclusion rules.

---

## Knowledge Files

Knowledge files carry business context that shapes how the agent interprets questions. They answer: what do things mean here, what rules apply, what are the quirks of this data?

**At the `domain: "*"` level** — global conventions that apply everywhere: currency, fiscal year, exclusion rules, data refresh schedule.

**At the domain level** — audience-specific context: who uses this domain, what they care about, what terms mean to them.

**At the entity level** — entity-specific knowledge: what this entity represents, data quality caveats, which fields to prefer, what filters always apply.

For structure, field reference, and full examples, see [Knowledge File Reference](../file-types/knowledge-md.md).

---

## Glossary Files

Glossary files define company-specific terms. The agent reads the glossary to interpret questions that use internal terminology — terms that would be ambiguous or meaningless without company context.

Each entry is a term and a 1–2 sentence definition. Without a glossary entry, the agent has to guess what company-specific terms mean.

For structure, field reference, and full examples, see [Glossary File Reference](../file-types/glossary-md.md).

---

## Task Instruction Files

Task instruction files tell the agent how to perform a specific task correctly. The primary task is `text-to-sql`. Task instructions answer: for this entity and this task, what SQL patterns apply? What should always be filtered? What should never be done?

{% hint style="info" %}
Task instructions are the only context that directly shapes SQL generation. Knowledge files and glossary files inform how the agent interprets the question — what a term means, what the business rules are — but they do not produce SQL patterns. If you want the agent to apply a specific filter, use a specific field, or follow a specific query convention when writing SQL, it must be in a task instructions file, not a knowledge file.
{% endhint %}

Task instructions are loaded only when the agent is performing that specific task — they do not add overhead to queries where they are irrelevant.

For structure, field reference, and full examples, see [Task Instructions Reference](../file-types/task-instructions-md.md).

---

## Clarification Policy Files

Clarification policy files control when the agent asks a follow-up question before answering. This is behavioral guidance: given an ambiguous request, should the agent ask for clarification or make a reasonable assumption and proceed?

For structure, field reference, and full examples, see [Clarification Policy Reference](../file-types/clarification-policy-md.md).

---

## Output Format Files

Output format files control how the agent structures and presents its answers. They carry formatting preferences, tone rules, and presentation conventions specific to the domain or audience.

For structure, field reference, and full examples, see [Output Format Reference](../file-types/output-format-md.md).

---

## Related Reference

- [Knowledge File Reference](../file-types/knowledge-md.md) — field reference and examples
- [Glossary File Reference](../file-types/glossary-md.md) — structure and examples
- [Task Instructions Reference](../file-types/task-instructions-md.md) — SQL guidance patterns
- [Clarification Policy Reference](../file-types/clarification-policy-md.md) — when and how to configure
- [Domains](./domains.md) — how domain scoping and inheritance work
