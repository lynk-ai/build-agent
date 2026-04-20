# Domains

Domains let you scope context to a specific audience. Different teams use different terminology, ask different questions, and need different agent behavior. Domains are how you manage that without duplicating your entire semantic layer.

---

{% hint style="warning" %}
**Common mistake:** `domain: "default"` does NOT mean "applies everywhere by default." It scopes content to the main domain only. Use `domain: "*"` for content that should apply to all domains, including custom ones like `marketing` or `finance`. Getting this wrong produces silent errors — the agent simply won't load the content in other domains.
{% endhint %}

---

## The Domain Model

Every context file has a `domain` field in its frontmatter. This controls which audience the file's content applies to.

`domain: "*"` is the base — content defined here applies to every domain. Named domains (e.g., `domain: "marketing"`, `domain: "finance"`) inherit everything from `domain: "*"` and can extend or override it for their specific audience.

The main domain is `default`. Content scoped to `domain: "default"` applies only to queries in the main domain — not to other named domains. Use `domain: "*"` for content that should apply everywhere, including `default`.

```yaml
# Applies to all domains
---
type: glossary
domain: "*"
---

# Applies only to the marketing domain
---
type: glossary
domain: "marketing"
---
```

---

## How Domains Are Activated

Users are assigned to domains on the Users management page in the Lynk UI. Each user has a default domain — for example, marketing team members are assigned the `marketing` domain. When they open Lynk, the agent operates in that domain automatically.

Users can switch to another domain in the UI if they have access to it. Access is also configured per user on the Users management page.

If a user has no domain assigned, they operate in the main domain (`default`).

---

## Inheritance

When the agent answers a question in a named domain, it loads context from two places:

1. All files scoped to `domain: "*"`
2. All files scoped to that specific named domain

The named domain's content takes precedence. A named domain can:

- **Expand** — add new terms, rules, or instructions that don't exist in `domain: "*"`
- **Override** — redefine a term or rule from `domain: "*"` with a different version for this audience
- **Exclude** — explicitly remove a term or rule from `domain: "*"` so it doesn't apply to this domain

**Example — override:** The marketing team uses "conversion" to mean a form submission, not a paid upgrade.

```yaml
---
type: glossary
domain: "marketing"
---

conversion:
  term: Conversion
  description: A visitor who submitted a lead form. That means a marketing conversion is not a paid upgrade — that is tracked separately as a sales conversion.
```

The marketing domain uses this definition. All other domains still use the `domain: "*"` definition. All other `domain: "*"` terms still apply to the marketing domain unchanged.

---

## Excluding Terms

To prevent a `domain: "*"` term from applying in a named domain, redefine the term in that domain with a definition that overrides the global one. The named domain's version takes precedence.

---

## Scoping a File to Multiple Domains

To apply a context file to a specific set of domains — but not all domains — pass a list to the `domain` field:

```yaml
---
type: knowledge
domain: ["marketing", "sales"]
---
```

This file loads only when the active domain is `marketing` or `sales`. It does not load in `default`, `finance`, or any other domain.

Use this when context is shared between two audiences but irrelevant to the rest. For content that applies everywhere, use `domain: "*"`. For content scoped to a single domain, use the domain name directly.

---

## Multiple Files Per Domain

You can have multiple files with the same domain value — including multiple files scoped to `domain: "*"`. All files with the same domain are merged and loaded to context together.

If two files in the same domain define the same key, both definitions are visible to the agent. This is a conflict — the agent will see the ambiguity.

Keep one file per domain per file type where possible to avoid conflicts.

---

## Conflict Handling

Avoid defining the same term or rule in multiple files within the same domain. 

The safest practice: one file per domain per file type. If you need to split a large file, ensure the two files do not define the same key.

In a team environment where multiple engineers edit context files, conflicts can appear silently. Before merging a context branch to `main`, review all files in the affected domain for duplicate keys. Running evaluations before merge will surface conflicts that cause incorrect SQL — which is another reason to keep a comprehensive evaluation suite.

---

## Which File Types Support Domains

The `domain` frontmatter field is supported across all context file types:

| File type | Scoping effect |
|---|---|
| `glossary` | Terms apply to queries in the specified domain |
| `knowledge` | Context applies to queries in the specified domain |
| `task-instructions` | SQL rules apply to queries in the specified domain |
| `clarification-policy` | Clarification behavior applies to queries in the specified domain |
| `output-format` | Response structure applies to queries in the specified domain |

Entity YAML files are scoped by entity, not domain. Domain-level context (knowledge, task instructions) that references a specific entity is loaded when that entity is queried within the domain.
