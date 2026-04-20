# Guide: Writing Evaluations

Evaluations are test cases that verify the agent generates correct SQL before you push context changes to production. Each test case is a natural language question paired with the SQL you expect the agent to produce.

---

## Before You Start

- **Do you have verified SQL for the question?** The `expected_output` must be correct Lynk SQL — feature and metric names from the entity YAML, not raw warehouse columns. Verify the field names before writing.
- **Is this question non-trivial to answer?** Good evaluations test the things most likely to break — default filters, glossary terms, metric selection, edge cases. A question with an obvious answer tests nothing.
- **Do you know which domain this test runs in?** The `tags.domain` field determines which context the agent loads. Make sure it matches the domain where the question would actually be asked.

---

## Steps

### 1. Identify the questions to cover

Start from what can go wrong. Write test cases that cover:

- Questions using company-specific terms that require glossary interpretation
- Queries where a default filter must always apply (`is_test_account = false`, `status = 'active'`)
- Metric selection where two similar fields exist and the agent must choose the right one
- Any question the agent has previously answered incorrectly

**Minimum per entity:** one EASY case (simple lookup or count) and one MEDIUM case (filtering, grouping, or a metric that requires a join).

---

### 2. Write the test case

**File:** `.lynk/default/evaluations.yml`

```yaml
test_cases:
  - type: SQL
    name: {snake_case_name}
    description: |-
      {What this test verifies, in one or two sentences.}
      Evaluation:
      - {The specific rule or context being tested}
    input: {Natural language question as a real user would ask it}
    expected_output: |-
      SELECT
        {feature_name},
        metric({metric_name}) AS {alias}
      FROM entity('{entity}')
      WHERE {default_filter_1} = {value}
        AND {default_filter_2} = {value}
      GROUP BY 1
      ORDER BY 2 DESC
    tags:
      difficulty: {EASY|MEDIUM|HARD}
      domain: {domain_name}
      eval: {eval_tag}
```

**Checklist:**
- [ ] `input` is written in business language — not field names or SQL fragments
- [ ] `expected_output` uses `FROM entity('{entity}')` and `metric()` — not raw table names
- [ ] All feature and metric names are verified against the entity YAML
- [ ] All default filters your task instructions require are present in `expected_output`
- [ ] `tags.domain` matches the domain where the question would be asked
- [ ] `name` is unique within the file

→ See [Evaluations YAML Reference](../file-types/evaluations-yaml.md) for full field documentation and eval tag options.

---

### 3. Run evaluations in the UI

Before merging a context change to `main`:

1. Push your branch to Git
2. Open the Lynk UI and navigate to **Evaluations**
3. Select the branch you want to test
4. Run the relevant test cases — either the full suite or filtered to the entity you changed
5. Check the similarity score for each case. A score of 1.0 is exact. Scores below the passing threshold mean the agent produced meaningfully different SQL.

**Checklist:**
- [ ] Branch is pushed and visible in the UI
- [ ] Evaluated against the correct branch, not `main`
- [ ] All previously passing cases still pass
- [ ] New test cases pass

→ See [Evaluations](../concepts/evaluations.md) for how semantic similarity scoring works.

---

### 4. Iterate

If a test case fails:

- Check the agent's generated SQL in the **Conversations** log (run the question as a real query to see what the agent produces)
- Compare it to your `expected_output` — identify which rule was missing or wrong
- Update the relevant context (task instructions, glossary, knowledge file) and re-run

If your `expected_output` was wrong — feature name typo, missing filter, incorrect metric — fix it and re-run.

---

## Quick Reference

| Step | File | Reference |
|---|---|---|
| 1. Identify questions | — | [Evaluations concepts](../concepts/evaluations.md) |
| 2. Write test cases | `default/evaluations.yml` | [Evaluations YAML](../file-types/evaluations-yaml.md) |
| 3. Run in UI | Lynk UI → Evaluations | [Evaluations concepts](../concepts/evaluations.md) |
| 4. Debug failures | Lynk UI → Conversations | [Troubleshooting](troubleshooting.md) |
