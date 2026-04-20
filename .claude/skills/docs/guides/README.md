# Guides

**Task-focused how-to guides for extending an existing Lynk project.**

Use this section when you already have a working semantic layer and need to add something new — a new entity, a new feature — without rebuilding from scratch. Each guide is a focused checklist that walks through every required step in the right order.

---

## What's in this section

| Page | When to use it |
|---|---|
| [Adding an Entity](adding-an-entity.md) | You're modeling a new business concept the agent should be able to query — from YAML through relationships, context files, and evaluations |
| [Adding a Feature](adding-a-feature.md) | You're adding a new attribute to an existing entity — includes a decision tree to pick the right feature type (field / first_last / formula / metric) |
| [Adding a Metric](adding-a-metric.md) | You're adding a new aggregation to an entity — covers checking available features, avoiding duplicate metrics, and writing the SQL |
| [Writing Evaluations](writing-evaluations.md) | You need to write regression test cases — covers what to test, how to write `expected_output`, and how to run evaluations in the UI |
| [Writing Task Instructions](writing-task-instructions.md) | The agent is generating wrong SQL — covers how to identify the right rule, choose the right scope, and verify the fix |
| [Troubleshooting](troubleshooting.md) | Agent returned a wrong answer, an evaluation failed, or context isn't loading — diagnostic steps for the most common problems |

---

## What you can do with this

Use these guides to:
- Add a new entity correctly — without missing steps that cause the agent to fail (missing relationships, missing context files)
- Choose the right feature type for what you're trying to express — and understand why the wrong choice produces wrong results
- Follow a verified checklist so nothing is skipped before you run evaluations and push to production

**Before using these guides:**
- If you're building a project from scratch, start with the [Project Walkthrough](../project/README.md) instead — it covers the right build order for a new project
- If you need the exact field-level syntax for a file you're writing, see [File-Types Reference](../file-types/README.md)
