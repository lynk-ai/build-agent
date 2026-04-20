# Step 5: Examples and Evaluations

With entities modeled and context in place, add evaluation test cases to validate agent accuracy before going to production.

---

## Why Add Examples?

Examples serve two purposes.

**Validation:** Before merging a context branch to `main`, run evaluations to verify the agent generates the correct SQL. If a context change breaks something, evaluations catch it before users see wrong results. This is the equivalent of running tests before deploying code.

**Signal:** Writing examples forces you to think about what correct looks like. If you cannot write a clear expected SQL for a question, the context is probably incomplete — either the glossary is missing a term, the knowledge file is ambiguous, or the task instructions do not cover that query pattern.

Write examples before going live, not after.

---

## 5a: Writing Evaluation Test Cases

**Location:** `.lynk/default/evaluations.yml`

Each test case pairs a natural language question with the Lynk SQL the agent should generate to answer it correctly. Run evaluations before merging any context branch to `main` — the agent generates SQL from your context and Lynk compares it to the expected SQL in each test case.

```yaml
test_cases:

  - type: SQL
    name: active_customer_count
    description: |-
      Count of active Grove customers.
      Evaluation:
      - entity knowledge to filter status = 'active'
      - task instructions to exclude test accounts (is_test_account = false) and deleted accounts (is_deleted = false)
    input: How many active customers do we have?
    expected_output: |-
      SELECT
        metric(count_customers) AS customer_count
      FROM entity('customer')
      WHERE status = 'active'
        AND is_test_account = false
        AND is_deleted = false
    tags:
      difficulty: EASY
      domain: default
      eval: entity_knowledge

  - type: SQL
    name: arr_by_plan_type
    description: |-
      Total ARR grouped by plan type for active customers.
      Evaluation:
      - task instructions to use arr field, not total_paid
      - task instructions to exclude test and deleted accounts
    input: What is our ARR breakdown by plan type?
    expected_output: |-
      SELECT
        plan_type,
        metric(total_arr) AS arr,
        metric(count_customers) AS customers
      FROM entity('customer')
      WHERE status = 'active'
        AND is_test_account = false
        AND is_deleted = false
      GROUP BY 1
      ORDER BY 2 DESC
    tags:
      difficulty: EASY
      domain: default
      eval: task_instructions

  - type: SQL
    name: logo_churn_this_quarter
    description: |-
      Logo churn rate for the current fiscal quarter.
      Evaluation:
      - domain knowledge for fiscal quarter definition (Q1 = Feb–Apr)
      - glossary: logo_churn = count of churned accounts, not revenue
      - task instructions to exclude test and deleted accounts
    input: What is our logo churn rate this quarter?
    expected_output: |-
      SELECT
        metric(churn_rate) AS logo_churn_rate
      FROM entity('customer')
      WHERE churn_date >= '2026-02-01'
        AND churn_date < '2026-05-01'
        AND is_test_account = false
        AND is_deleted = false
    tags:
      difficulty: MEDIUM
      domain: default
      eval: domain_knowledge

  - type: SQL
    name: mrr_at_risk_pending_cancellations
    description: |-
      Total MRR at risk from active subscriptions with a scheduled cancellation before renewal.
      Evaluation:
      - feature chaining: mrr_at_risk metric pulled from subscription entity
      - entity knowledge: is_pending_cancellation flag defined on subscription
    input: How much MRR is at risk from pending cancellations?
    expected_output: |-
      SELECT
        metric(mrr_at_risk) AS mrr_at_risk
      FROM entity('subscription')
      WHERE status = 'active'
        AND is_pending_cancellation = true
    tags:
      difficulty: MEDIUM
      domain: default
      eval: feature_chaining
```

**What makes a good test case:**
- `input` is a question a real user would type — business language, not field names
- `expected_output` uses `FROM entity()` and `metric()` — never raw warehouse table names
- The `description` field names what the evaluation is testing — which rule, which field, which definition from the glossary
- Cover the questions most likely to produce wrong answers: multi-condition definitions, metric selection (arr vs total_paid), fiscal calendar edge cases, and filters that must always apply

**What to avoid:**
- Questions so vague that any answer would score as correct
- Expected SQL you wrote from memory without verifying against the entity YAML — field names must match the feature names you defined
- Trivial examples that would pass even with no context at all

---

## 5b: Running Evaluations

After adding test cases to `evaluations.yml`, run evaluations from the Lynk UI before merging your branch to `main`. Select the test cases you want to run and the branch to evaluate against. The agent generates SQL from your context on that branch and Lynk compares it to the expected SQL in each test case.

**If a test case fails:** the agent generated different SQL than expected. Check whether the problem is entity selection (wrong entity picked), SQL logic (correct entity but wrong filter or metric), or term interpretation (glossary entry missing or ambiguous). The agent.md debugging guide covers these cases in detail.

**If a previously passing test case fails after a context change:** a new rule may be conflicting with existing logic. Review what changed and whether it introduces ambiguity.

All test cases should pass before you merge to `main`. `main` is what live users query against — treat it as production.

See [Evaluations](../concepts/evaluations.md) for how the evaluation system works end to end.

---

## Key Point

Evaluations are regression tests for your semantic layer. Write them before going to production. Run them before every merge to `main`. A failing test case means something in your context is ambiguous, missing, or conflicting — not a bug in the agent. The agent generates SQL from the context you give it; the quality of the output reflects the quality of the context.
