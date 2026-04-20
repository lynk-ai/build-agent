# Step 2: Domains

With business context written, decide who the audiences are.

---

## Why Define Domains Now?

Domains determine where context files live and who they apply to. Knowing the audiences before writing task instructions and behavior files means you write them for the right audience from the start — rather than writing generic files and retrofitting them later.

At Grove, two audiences ask questions: the analytics team and the customer success team. They care about different things, use different language, and sometimes need different definitions of the same concept.

---

## What Is a Domain?

A domain is a named audience or business unit with its own view of the data. Different domains can have different context files, different examples, and — when necessary — different feature definitions.

**The key rule:** Entities are always defined in the main domain (`default`). Domains customize how context is presented, not the entity structure itself. If two audiences need different feature definitions for the same entity, that is when a custom domain gets its own entity YAML.

---

## The Main Domain (`default`)

Every Lynk project has a main domain called `default`. It contains:
- All entity YAML files
- The canonical feature definitions
- Business-wide knowledge, glossary, and behavior files

Every other domain is an overlay on top of `default`. If a custom domain does not define something, the agent falls back to `default`.

---

## When to Create a Custom Domain

Create a custom domain when an audience needs:

- **Different context** — the customer success team needs guidance about at-risk flags, renewal dates, and escalation signals that the analytics team does not need
- **Different examples** — CSM questions focus on individual account risk; analytics questions focus on aggregate metrics
- **Different feature definitions** — only when the same feature means something genuinely different to this audience (rare)

Do not create a domain to organize files. If the definitions and context are the same, one domain is enough.

---

## Grove Example: Two Domains

| Domain | Audience | What it has |
|---|---|---|
| `default` | Analytics and data engineering | All entity definitions, business-wide knowledge, glossary, SQL rules, output format |
| `cs` | Customer success team | CS-specific knowledge about at-risk accounts, renewal focus, CSM question examples |

The `cs` domain does not need its own `customer.yml` — it uses the same feature definitions. It gets a `cs_knowledge.md` with CS-specific context and its own `evaluations.yml` with CSM-oriented test cases. No entity YAML overrides needed.

---

## Domain Folder Structure

```
.lynk/
├── default/                                       # All entity definitions live here
│   ├── entities/
│   │   ├── customer.yml
│   │   ├── customer/
│   │   │   ├── customer__knowledge.md
│   │   │   └── customer__task_inst__text_to_sql.md
│   │   ├── subscription.yml
│   │   └── subscription/
│   │       ├── subscription__knowledge.md
│   │       └── subscription__task_inst__text_to_sql.md
│   ├── entities_relationships.yml
│   ├── domain_context/
│   │   ├── grove_knowledge.md
│   │   └── default__task_inst__text_to_sql.md
│   ├── grove_glossary.md
│   ├── evaluations.yml
│   └── agent/
│       ├── clarification_policy.md
│       └── output_format.md
└── cs/                                            # Only what differs from default
    ├── domain_context/
    │   └── cs_knowledge.md
    └── evaluations.yml
```

**Rules for custom domain folders:**
- Only add entity YAML in a custom domain if feature definitions must differ from `default`
- Context files in a custom domain apply only to that domain and shadow their `default` equivalents
- `entities_relationships.yml` lives only in `default` — relationships are shared across domains
- Glossary and behavior files scoped to `domain: "*"` apply to all domains

---

## The `cs` Domain Knowledge File

**Location:** `.lynk/cs/domain_context/cs_knowledge.md`

```markdown
---
type: knowledge
domain: "cs"
---

## Who Uses This Domain

Customer success managers (CSMs) at Grove use this view to monitor account health, prioritize outreach, and manage renewal conversations. Typical questions: which accounts are at risk, which renewals are coming up, which customers have low NPS.

## What CSMs Care About

- At-risk flags: NPS below 6 or no login in 60 days
- Pending cancellations: subscriptions with a scheduled cancellation before renewal
- Renewal timeline: `current_period_end` on the subscription entity is the renewal date
- Plan type: enterprise accounts get priority CSM attention

## How CSMs Count "Active"

For CSM purposes, "active" means the account has status = 'active' AND has logged in within the past 30 days. This is more restrictive than the analytics definition (status = 'active' alone). When a CSM asks for active accounts, apply both conditions.
```

This behavioral rule belongs in the knowledge file, not in task instructions. The agent reads the knowledge file when planning a query in the `cs` domain and applies this definition automatically. Task instructions are the right place when you need a specific SQL pattern — here, the plain-English definition is enough.

---

## Key Point

Entities are defined once in `default` and shared. Domains are the mechanism for customization without duplication. Before creating a custom domain entity YAML, ask: does this audience need a different *definition* of this feature, or just different *context* about it?

If the answer is "different context" — add a context file to the custom domain folder. If the answer is "different definition" — then a custom entity YAML in that domain is warranted.
