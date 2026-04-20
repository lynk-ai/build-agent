# File-Types Reference

**The complete field-by-field reference for every file type in Lynk.**

This section documents the exact structure, required fields, allowed values, and behavior of every file you write in a Lynk semantic layer project. Use these pages when you need to know precisely what a field does, what values it accepts, or how a file is loaded.

---

## What's in this section

### YAML Files

| Page | What it covers |
|---|---|
| [Entity YAML](entity-yaml.md) | Features (field, first_last, formula, metric), entity metrics, related_sources, examples, common pitfalls |
| [Relationships YAML](relationships-yaml.md) | Relationship types, join definitions (sql / lookup), multiple named joins, feature chaining dependencies |
| [Evaluations YAML](evaluations-yaml.md) | Test case structure, eval tags, difficulty levels, common pitfalls |

### Markdown Context Files

| Page | What it covers |
|---|---|
| [Knowledge Files](knowledge-md.md) | Business definitions, data quality notes, domain and entity scoping, what belongs here vs. other file types |
| [Task Instructions](task-instructions-md.md) | SQL patterns, default filters, field choices, domain-level vs. entity-level instructions |
| [Glossary Files](glossary-md.md) | Entry format, what terms belong in the glossary vs. knowledge files or entity YAML |
| [Output Format Files](output-format-md.md) | Table structure, tone, insights, data notes, domain-specific formatting |
| [Clarification Policy Files](clarification-policy-md.md) | When to ask vs. when to proceed, default assumptions, response tone |

---

## Frontmatter Quick Reference

Every Markdown context file starts with a YAML frontmatter block that controls its scope.

**Knowledge file:**
```yaml
---
type: knowledge
domain: "default"        # or "*" for all domains, or a specific domain name
entity: customer         # optional — omit for domain-wide knowledge
---
```

**Task instructions file:**
```yaml
---
type: task-instructions
domain: "default"        # or "*" for all domains, or a specific domain name
tasks: "text-to-sql"     # which task this applies to
entity: customer         # optional — omit for domain-wide instructions
---
```

**Glossary file:**
```yaml
---
type: glossary
domain: "*"              # or a specific domain name
---
```

**Behavior file:**
```yaml
---
type: behavior
kind: output_format      # one of: output_format, clarification_policy
domain: "*"              # or a specific domain name
---
```

---

## Key Distinctions

**Knowledge vs. Task Instructions** — Use knowledge files for definitions, business rules, and data context — things the agent needs to understand the question. Use task instructions for SQL-specific guidance — filters, field choices, query patterns — things the agent needs when executing the task.

**Knowledge vs. Glossary** — Use the glossary for quick term lookups (one or two sentences). Use knowledge files for multi-paragraph explanations, data quality caveats, governance rules, and business context that requires interpretation.

**Behavior vs. Everything Else** — Behavior files control how the agent communicates with users — output format and clarification policy. SQL guidance and business definitions do not belong in behavior files.

---

## What you can do with this

Use this section to:
- Look up the exact fields and syntax for a file you're writing
- Understand what goes in each file type vs. the others (when to use knowledge vs. glossary vs. task instructions)
- See annotated full examples for three different company types (B2B SaaS, e-commerce, mobile gaming)
- Debug a file that isn't behaving as expected — the common pitfalls sections cover the most frequent mistakes

**Where to go next:**
- Want step-by-step guidance for adding a new entity or feature? → [Guides](../guides/README.md)
- Want to understand how these file types interact as a system? → [Concepts](../concepts/README.md)
