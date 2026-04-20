# Agent

The agent is the reasoning layer that turns a business question into a trusted answer. It reads your semantic graph, assembles the context it needs, and executes the right task — all in a single interaction.

---

## How the Agent Works

When a question arrives, the agent follows a consistent sequence from question to answer.

**1. Start with business context.**
Every interaction begins with business knowledge, glossary, domain knowledge, and the clarification policy already loaded. The agent knows who is asking and what domain they operate in — this scope is established before any question is processed.

**2. Understand the question and set goals.**
The agent reads the question and determines what it needs to answer it. For a question like "what's the revenue by region this quarter?", the agent identifies the goal: find revenue data, apply the right date range, and break it down by region.

**3. Load the relevant entities.**
The agent reads entity names and descriptions to identify which entities apply to this question — then loads only those entities and their context. Entity descriptions are the primary signal here: they tell the agent what each entity represents and when it's relevant.

**4. Choose the task and load task instructions.**
The agent selects the right tool for the job. For data questions, that's `text-to-sql`. It then loads the task instructions for that task at both the domain level and the entity level — specific guidance on how to write the query correctly for this context.

**5. Execute the tasks.**
The agent writes the SQL query, runs it against your warehouse, and retrieves the result.

**6. Finalize and respond.**
The agent applies your output format rules to structure and present the result — what to include, how to phrase it, and whether to add context or caveats.

---

## Dynamic Context Loading

The agent does not load your entire semantic graph for every question. It loads context selectively — each layer at the moment it becomes relevant.

Business knowledge, the glossary, and the clarification policy load with every interaction. They define the scope the agent operates within. Entity context loads only for the entities relevant to the specific question at hand. Task instructions load only after the agent has determined which task to run, and only for the entities involved.

This means the agent works with a focused, relevant picture of your data — not everything at once. A question about orders doesn't load player context. Output format rules don't load during query execution. The agent receives exactly what it needs for each step, and no more.

The practical effect: context you add to the semantic graph reaches the agent at the right moment. A glossary term the agent needed last week will be there next week. A task instruction you add today applies to every future question on that entity. The more complete and precise your context is, the better the agent performs at the step where that context matters.

---

## Tools

### text-to-sql

`text-to-sql` is the tool the agent uses to answer data questions. Given a natural language question and the relevant entity context, it produces a SQL query, executes it against your warehouse, and returns the result.

The agent reads three inputs before generating SQL:

1. **The entity YAML** — which features and metrics are available, what the source tables are, how entities relate
2. **The task instructions** — SQL patterns, default filters, date field conventions, grouping rules. This is what directly shapes the SQL output.
3. **The glossary and knowledge files** — what terms mean, which values are valid, what caveats apply. These inform interpretation, not SQL patterns. SQL rules belong in task instructions.

Configuring `text-to-sql` is done through task instruction files scoped to the relevant entity:

```markdown
---
type: task-instructions
domain: "default"
entity: order
tasks: "text-to-sql"
---

## Default Filters
Always apply: status = 'completed' AND is_test_order = false
Never omit these unless the user explicitly asks for all order statuses.
```

For the full field reference, SQL guidance patterns, and examples, see [Task Instructions Reference](../file-types/task-instructions-md.md).

---

## Evaluations

As your business evolves and your data changes, the agent's accuracy needs to be measured and maintained. Evaluations are test cases — a natural language question paired with an expected result — that you run before pushing context changes to production.

Evaluations give you confidence that a change you made to the semantic graph improved answers without breaking others. They are the mechanism that keeps the agent accurate over time, as your context grows and your business questions shift.

See [Evaluations Reference](../file-types/evaluations-yaml.md) for how to write evaluations and what fields they support.

---

## Transparency

The agent does not operate as a black box. You can see what it did.

**Conversations** — every production question and its answer is logged. You can see the user's question, the entity the agent selected, the SQL it generated, and the result it returned.

These logs are where you learn what your users actually ask. Real production questions are the best source for new evaluation cases and for identifying gaps in your context.

---

## When Answers Are Wrong

When the agent returns a wrong or unexpected result, the Conversations log is the starting point. It shows which entity the agent selected and what SQL it generated — those two facts narrow down the cause.

**1. Wrong entity selected.**
The agent picked an entity that doesn't match the question. Fix: open the entity's YAML and update its `description` to be more specific about what questions it answers. If two entities have similar descriptions, the one that doesn't apply should explicitly say what it does *not* cover.

**2. Correct entity, wrong SQL.**
The agent selected the right entity but generated incorrect SQL — wrong filter, wrong field, wrong date range. Fix: check the task instructions for that entity. Add a rule that covers the case that failed. Task instructions are the only context that shapes SQL generation — if a rule isn't there, the agent can't follow it.

**3. Wrong term interpretation.**
The agent misread a business term in the question. Fix: add or update the glossary entry for that term. A precise definition prevents the agent from guessing.

If the same issue recurs across multiple questions, add an evaluation test case so it can't regress.

---

## Related Reference

- [Context](./context.md) — the full teaching framework the agent reads
- [Domains](./domains.md) — how domain scoping controls what the agent sees
- [Entities](./entities.md) — how entity descriptions affect agent selection
- [Task Instructions Reference](../file-types/task-instructions-md.md) — how to configure text-to-sql behavior per entity
- [Evaluations Reference](../file-types/evaluations-yaml.md) — writing evaluations and test case structure
