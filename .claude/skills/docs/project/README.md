# Project Walkthrough

**Build a complete Lynk semantic layer from scratch.**

This walkthrough takes you from a blank project to a working, queryable, accurate semantic layer. It follows a recommended top-down approach: start with the big picture — what the business is and what its terms mean — then work down to the technical details of entity YAML. Every file is complete and uses a real running example — no placeholders.

---

## What's in this section

| Page | What you do | Time |
|---|---|---|
| [Step 1: Business Context](01-business-context.md) | Write domain knowledge and glossary | 10–15 min |
| [Step 2: Domains](02-domains.md) | Define audiences and when to create custom domains | 5 min |
| [Step 3: Domain Context](03-domain-context.md) | Write domain-wide SQL rules (task instructions), clarification policy, and output format | 10 min |
| [Step 4: Entities](04-entities.md) | Model a dimension entity, a fact entity, relationships, and feature chaining | 20–25 min |
| [Step 5: Examples and Evaluations](05-examples.md) | Add evaluation test cases to validate accuracy before going to production | 5–10 min |

Read these pages in order.

---

## What you can do with this

The running example is **Grove** — a B2B SaaS company. By the end you will have built:
- A knowledge file and glossary defining what Grove is and what its terms mean
- Two domains with domain-specific context
- Two entities (`customer` and `subscription`) connected by a relationship with feature chaining
- Evaluation test cases that validate agent accuracy before going live


**Where to go next:**
- Adding to an existing project instead of starting fresh? → [Guides](../guides/README.md)
- Need to understand how a specific concept works? → [Concepts](../concepts/README.md)
- Need exact field documentation? → [File-Types Reference](../file-types/README.md)

---

## Project Structure

The canonical folder layout for a Lynk semantic layer project.

```
.lynk/
├── default/                              # Main domain — all entity definitions live here
│   ├── entities/
│   │   ├── {entity}.yml                  # Entity definition (features, metrics, related_sources)
│   │   └── {entity}/                     # Context files for this entity
│   │       ├── {entity}__knowledge.md
│   │       └── {entity}__task_inst__text_to_sql.md
│   ├── domain_context/
│   │   ├── {domain}_knowledge.md         # Domain-wide business context
│   │   └── {domain}__task_inst__text_to_sql.md
│   ├── agent/
│   │   ├── clarification_policy.md
│   │   └── output_format.md
│   ├── {domain}_glossary.md
│   ├── entities_relationships.yml
│   └── evaluations.yml
│
└── {custom_domain}/                      # Custom domain — overrides only
    ├── entities/
    │   ├── {entity}.yml                  # Only if feature definitions differ from default
    │   └── {entity}/
    │       └── {entity}__knowledge.md
    └── evaluations.yml
```

### Naming Conventions

Lynk does not enforce file names — scoping is controlled by frontmatter fields, not paths or names. The patterns below are a recommended convention to keep context files predictable and easy to navigate. You can use different names as long as the frontmatter is correct.

We recommend using double underscore (`__`) as the delimiter in context file names.

| Pattern | Meaning |
|---|---|
| `{entity}__knowledge.md` | Knowledge file scoped to this entity |
| `{entity}__task_inst__text_to_sql.md` | Task instructions for text-to-sql, scoped to this entity |
| `{domain}__task_inst__text_to_sql.md` | Task instructions for text-to-sql, scoped to the domain |
| `{domain}_glossary.md` | Glossary file for the domain (single underscore — standalone file) |

### What Goes Where

| File type | Location | Scope | Read by |
|---|---|---|---|
| Entity YAML | `default/entities/{entity}.yml` | Entity | Agent + Tasks |
| Entity knowledge | `default/entities/{entity}/{entity}__knowledge.md` | Entity + domain | Agent + Tasks |
| Entity task instructions | `default/entities/{entity}/{entity}__task_inst__text_to_sql.md` | Entity + domain | Tasks only |
| Domain knowledge | `default/domain_context/{domain}_knowledge.md` | Domain-wide | Agent + Tasks |
| Domain task instructions | `default/domain_context/{domain}__task_inst__text_to_sql.md` | Domain-wide | Tasks only |
| Glossary | `default/{domain}_glossary.md` | Domain-wide | Agent + Tasks |
| Behavior files | `default/agent/{kind}.md` | Domain-wide | Agent only |
| Relationships | `default/entities_relationships.yml` | All entities | Agent + Tasks |
| Evaluations | `default/evaluations.yml` | Domain | Evals only |

### The Entity Subfolder Pattern

Every entity YAML file has a sibling subfolder with the same name. Context files for that entity live inside it.

```
entities/
├── customer.yml              ← entity definition
└── customer/                 ← context files for customer
    ├── customer__knowledge.md
    └── customer__task_inst__text_to_sql.md
```

When adding a new entity, create both the YAML file and the subfolder.

### Custom Domain Rules

Custom domains override the default — they don't replace it.

1. **Entity YAML files always live in `default/entities/`.** If a custom domain only needs different context, add context files only — not a new entity YAML.
2. **Create a custom domain entity YAML only if feature definitions must differ.** For example, if `finance` defines `is_active` differently than `default`, create `.lynk/finance/entities/customer.yml` with just the changed features.
3. **Custom domain context files shadow the default.** If `marketing/entities/customer/customer__knowledge.md` exists, it takes precedence over the `default` version for queries in the `marketing` domain.

### Domain Feature Resolution

When the agent queries an entity in a specific domain, features resolve in this priority order:

1. Domain-specific feature (in the custom domain's entity YAML) — highest priority
2. Multi-domain feature (matched by `domain: ["marketing", "sales"]` in the feature)
3. Wildcard feature (matched by `domain: "*"`)
4. Default feature (in `default/entities/{entity}.yml`) — lowest priority, the fallback
