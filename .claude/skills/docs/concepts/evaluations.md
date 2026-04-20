# Evaluations

Evaluations are test cases that validate agent accuracy before you merge context changes to production. Each test case is an English question paired with the SQL you expect the agent to generate. Run evaluations after any context change — new entities, updated task instructions, glossary additions — to confirm the change improves accuracy without breaking something that already worked.

---

## How Evaluations Work

A test case has two parts:

- **Input** — a natural language question, written the way a real user would ask it
- **Expected output** — the SQL the agent should generate to answer it correctly

When you run an evaluation, Lynk provides the agent with the semantics version you're testing (a specific branch and its latest commit) and the input question. The agent goes through its normal flow: it identifies the relevant entities, loads their knowledge and task instructions, and runs text-to-sql to generate SQL. Lynk then compares the generated SQL to the expected output using semantic similarity scoring.

Semantic similarity scoring checks for equivalent meaning, not character-for-character identity. Two queries that produce the same result using different aliases, different column ordering, or minor SQL variations will score close to 1.0. A score of 1.0 is exact. Scores below a passing threshold indicate the agent generated meaningfully different SQL — wrong entity, missing filter, wrong metric — and the test case fails.

The result tells you whether the agent, working from the context in that branch, produces SQL with the same meaning as what you intended.

---

## Running Evaluations

Evaluations run from the Lynk UI. Select the test cases you want to run and the branch to evaluate against. You can run a full suite or a targeted subset — for example, only the test cases tagged to the entity you just modified.

Run evaluations before merging any context branch into `main`. Passing evaluations means your context change produces the intended SQL and has not broken any previously correct cases.

---

## Writing Good Test Cases

**What makes a useful test case:**

- The input is a question a real user would type — not a query you constructed to test a specific field
- The expected SQL uses the correct entity, the right filters, and the metric or feature you intended
- The question targets something non-obvious — a glossary term with a precise threshold, a default filter that must always apply, a metric that uses a specific formula

**What to cover:**

Write test cases for the patterns most likely to produce wrong answers:
- Questions that use company-specific terms (the agent must interpret from the glossary)
- Queries with default filters that must always apply (`is_test_account = false`, `status = 'active'`)
- Metric selection where two similar fields exist (`arr` vs `total_paid`, `mrr` vs `amount_cents`)
- Fiscal calendar edge cases if your fiscal year differs from the calendar year

**Minimum per entity:** one easy case (a simple lookup or count) and one medium case (filtering, grouping, or a metric that requires the right join).

For full test case structure and field reference, see [Evaluations YAML Reference](../file-types/evaluations-yaml.md).

---

## Evaluations and the Production Workflow

The production workflow is:

1. **Create a branch** in your Git repository for the context change you're making
2. **Make your changes** — add an entity, update task instructions, refine the glossary
3. **Run evaluations** against the branch in the Lynk UI — confirm your change produces the expected SQL and hasn't broken other test cases
4. **Merge to main** — `main` is your production semantics. The agent queries live users against whatever is on `main`.

{% hint style="warning" %}
Never merge a context change to `main` without running evaluations first.
{% endhint %} A broken task instruction or a conflicting glossary entry won't fail loudly — the agent will just produce wrong answers quietly. Evaluations catch this before users see it.

---

## Building Your Evaluation Suite Over Time

Start with the questions you know should work correctly. Add a test case whenever:

- You add a new entity or a significant new feature
- You find a question the agent answered incorrectly — write the test case so it can't regress
- You see a question pattern in production (via Conversations) that you want to protect going forward

The more test cases you have, the more confident you can be before each merge. A well-maintained evaluation suite means context changes are low-risk — you know exactly what's covered and what would break.

---

## Related Reference

- [Evaluations YAML Reference](../file-types/evaluations-yaml.md) — test case structure and field reference
- [Agent](./agent.md) — how the agent selects entities and generates SQL
- [Conversations](./agent.md#transparency) — where production questions appear
