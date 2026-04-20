# Troubleshooting

Common problems and how to fix them.

---

## The agent returned a wrong answer

Open the **Conversations** log in the Lynk UI. It shows which entity the agent selected and what SQL it generated. Those two facts identify the cause.

---

**The agent picked the wrong entity.**

The agent selected an entity that doesn't match the question.

Fix: Open the entity's YAML and update its `description`. Make it more specific about what questions it answers. If two entities have similar descriptions, the one that doesn't apply should explicitly state what it does *not* cover.

→ See [Entities](../concepts/entities.md) for how entity descriptions affect agent selection.

---

**The agent selected the right entity but generated wrong SQL.**

Wrong filter, wrong field, wrong date range — the entity was correct but the query wasn't.

Fix: Check the task instructions file for that entity. Add a rule that covers the case that failed. Task instructions are the only context that shapes SQL generation — if a rule isn't there, the agent cannot follow it.

→ See [Task Instructions Reference](../file-types/task-instructions-md.md).

---

**The agent misread a business term.**

The agent misinterpreted a word or phrase in the question — it guessed instead of knowing.

Fix: Add or update the glossary entry for that term. A precise definition prevents guessing.

→ See [Glossary Files Reference](../file-types/glossary-md.md).

---

**The same wrong answer keeps recurring.**

Add an evaluation test case that covers this question. Evaluations are the mechanism that prevents regressions — once a correct answer is captured as a test case, it stays correct as your context evolves.

→ See [Evaluations YAML Reference](../file-types/evaluations-yaml.md).

---

## An evaluation failed

**The SQL in `expected_output` doesn't match the entity's feature or metric names.**

Evaluations use Lynk SQL — feature and metric names must exactly match what's defined in the entity YAML. A renamed feature or metric will break existing evaluations.

Fix: Check the failing evaluation's `expected_output` against the entity YAML. Update whichever is out of date.

→ See [Lynk SQL](../api/lynk-sql.md) for syntax reference.

---

**The evaluation passes in isolation but fails after a context change.**

A change to task instructions, glossary, or a knowledge file altered how the agent interprets the question — the expected output is still correct but the agent now takes a different path to it.

Fix: Review what changed in the semantic graph since the evaluation last passed. Update the evaluation's `expected_output` if your business rules changed, or revert the context change if it introduced a regression.

---

**The evaluation input is too close to a SQL field name.**

If the `input` field in an evaluation reads like a query rather than a natural language question, the agent may interpret it differently from how a real user would phrase it.

Fix: Rewrite `input` in plain business language — the way a user would actually ask the question, not using technical field names.

---

## Context doesn't seem to be loading

**A knowledge file or task instruction isn't affecting agent behavior.**

Check the frontmatter on the file. The two most common causes:

1. `domain` value doesn't match the domain the query runs in — a file scoped to `domain: "marketing"` won't load for queries in `domain: "default"`.
2. `entity` value doesn't match the entity name exactly — a typo in the `entity` field means the file never loads.

→ See [Context](../concepts/context.md) for how scoping and compounding work.

---

**A task instructions file isn't shaping SQL output.**

Task instructions only load during task execution — they require `tasks: "text-to-sql"` in frontmatter. Without it, the file is ignored during SQL generation.

Fix: Confirm the file has `type: task-instructions` and `tasks: "text-to-sql"` in its frontmatter.

---

## Related Reference

- [Agent](../concepts/agent.md) — the full question-to-answer lifecycle and debugging workflow
- [Context](../concepts/context.md) — how scoping and context compounding work
- [Evaluations YAML Reference](../file-types/evaluations-yaml.md) — test case structure and fields
