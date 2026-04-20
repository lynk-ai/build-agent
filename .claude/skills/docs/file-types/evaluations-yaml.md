# Evaluations YAML Reference

`evaluations.yml` contains test cases for regression testing. Each case pairs a natural language question with the expected Lynk SQL output. Run evaluations before pushing context changes to production to catch breaks before they affect users.

---

## Structure

```yaml
test_cases:
  - type: SQL
    name: active_customers_by_country
    description: |-
      Count active customers grouped by country.
      Evaluation:
      - entity knowledge to correctly filter by status = 'active'
    input: How many active customers do we have per country?
    expected_output: |-
      SELECT
        country,
        metric(count_customers) AS customer_count
      FROM entity('customer')
      WHERE status = 'active'
      GROUP BY 1
      ORDER BY 2 DESC
    tags:
      difficulty: EASY
      domain: default
      eval: entity_knowledge
```

---

## Fields

| Field | Description |
|---|---|
| `type` | `SQL` — the only supported type |
| `name` | Unique identifier for this test case |
| `description` | What this test verifies — written for a human reviewer |
| `input` | The natural language question as a user would ask it |
| `expected_output` | The Lynk SQL that correctly answers the question |
| `tags.difficulty` | `EASY`, `MEDIUM`, or `HARD` |
| `tags.domain` | Which domain this test case runs in |
| `tags.eval` | What is being tested — see eval tags below |

---

## Eval Tags

| Tag | Tests |
|---|---|
| `entity_knowledge` | Agent correctly uses entity-specific knowledge (field selection, naming) |
| `domain_knowledge` | Agent applies domain-wide rules (filters, conventions) |
| `task_instructions` | Agent follows SQL-specific guidance |
| `behavior` | Agent follows communication style rules |
| `feature_chaining` | Metric features and cross-entity aggregation work correctly |

---

## When to Use This File

Add or update evaluations when a situation meets one of these conditions:
1. You're about to push a context change and need to verify it doesn't break existing behavior
2. You've modeled a new entity and need regression coverage for its key question patterns
3. There's a known failure area you want to lock in correct behavior for

**Examples:**
- "I just updated the task instructions on the `customer` entity — run evaluations to make sure nothing broke before deploying" → run existing evaluations before pushing
- "We added a new entity for `session` — write evaluations to verify the agent can answer basic engagement questions" → add new test cases for the entity
- "The agent keeps getting churn queries wrong — write a set of test cases that cover the different churn scenarios" → add targeted test cases for a known failure area
- "I want confidence that the `is_test_account = false` filter is always applied correctly" → add a test case that verifies the filter appears in expected output
- "We're onboarding a new customer — create a set of evaluations from their 20 sample questions before the first demo" → add domain-scoped test cases from real user questions

---

## Best Practices

**Write `input` as a real user would ask it** — business language, not field names.

```yaml
# GOOD
input: How many active customers do we have per country?

# TOO TECHNICAL
input: Query customer entity grouped by country where status = active
```

**Write `expected_output` as clean Lynk SQL.** Use entity references and metric functions — never raw table names.

```yaml
expected_output: |-
  SELECT
    country,
    metric(count_customers) AS customer_count
  FROM entity('customer')
  WHERE status = 'active'
  GROUP BY 1
  ORDER BY 2 DESC
```

**Apply the domain's default filters** in the expected output — season type exclusions, soft-delete filters, etc. The evaluation tests whether the agent applies them correctly.

**Use verified feature names** from the entity YAML. Do not guess.

---

## Common Pitfalls

**Using raw table names in `expected_output`.** Evaluations test Lynk SQL — always use `FROM entity('customer')` and `metric(count_customers)`, not raw warehouse tables or SQL aggregations. Raw SQL will fail the evaluation even if logically correct.

**Writing `input` as a technical query.** The input should sound like a business user asking a question, not an engineer writing a spec. `"Query customer entity grouped by country where status = active"` is not how users ask questions.

**Not applying domain default filters.** If your task instructions say "always exclude test accounts", the `expected_output` must include that filter. Evaluations test whether the agent follows the rules — if the expected output doesn't reflect the rules, the evaluation is testing the wrong thing.

**Too few test cases for important entities.** Aim to cover the common question patterns for each entity — simple counts, time-filtered queries, groupings, and any known edge cases. A single test case per entity is not enough to catch regressions.

**Letting test cases go stale.** When you rename a feature, update a metric, or change a default filter, update the evaluations. Stale expected output causes false failures that erode confidence in the evaluation suite.

---

## Difficulty Guidelines

| Level | Characteristics |
|---|---|
| `EASY` | Single entity, few features, no joins, straightforward question |
| `MEDIUM` | Multiple features, time filtering, or implicit business logic required |
| `HARD` | Feature chaining, multi-entity reasoning, complex filters, or ambiguous input |

---

## Full Examples

### Example 1 — Grove (B2B SaaS)

Three test cases for the Grove `customer` entity: simple active customer count, ARR broken down by customer tier, and enterprise customers at risk of churning. Progresses from EASY to MEDIUM — the at-risk query requires combining NPS, plan type, and the `arr` feature with correct default filters.

```yaml
test_cases:

  - type: SQL
    name: active_customer_count
    description: |-
      Count of active Grove customers.
      Evaluation:
      - entity knowledge to filter by status = 'active'
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
    name: arr_by_customer_tier
    description: |-
      Total ARR grouped by customer_tier (Enterprise / Mid-Market / SMB) for active customers.
      Evaluation:
      - entity knowledge to use the customer_tier formula feature and the arr feature
      - task instructions to exclude test and deleted accounts
    input: What is our ARR by customer tier?
    expected_output: |-
      SELECT
        customer_tier,
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
      eval: entity_knowledge

  - type: SQL
    name: at_risk_enterprise_customers
    description: |-
      Active enterprise customers with NPS below 6, ordered by ARR descending.
      Evaluation:
      - task instructions: "Enterprise" means plan_type = 'enterprise', not customer_tier = 'Enterprise'
      - entity knowledge: nps_score < 6 signals churn risk
      - task instructions to exclude test and deleted accounts
    input: Which enterprise customers are at risk of churning this quarter?
    expected_output: |-
      SELECT
        company_name,
        customer_tier,
        arr,
        nps_score,
        active_subscription_count,
        total_mrr
      FROM entity('customer')
      WHERE status = 'active'
        AND plan_type = 'enterprise'
        AND nps_score < 6
        AND is_test_account = false
        AND is_deleted = false
      ORDER BY arr DESC
    tags:
      difficulty: MEDIUM
      domain: default
      eval: task_instructions
```

---

### Example 2 — Bly (E-commerce)

Three test cases for the Bly `order` entity: net revenue this month, top channels by order volume, and refund rate by product category. Progresses from EASY to MEDIUM — the refund rate test requires joining through `order_item` to reach product category, which is feature chaining.

```yaml
test_cases:

  - type: SQL
    name: net_revenue_this_month
    description: |-
      Total net revenue for the current calendar month, completed orders only.
      Evaluation:
      - task instructions to filter to status = 'completed' for revenue questions
      - task instructions to use net_amount, not gross_amount
      - task instructions to filter order_date, not created_at
    input: What is our net revenue this month?
    expected_output: |-
      SELECT
        metric(sum_net_revenue) AS net_revenue
      FROM entity('order')
      WHERE status = 'completed'
        AND is_test_order = false
        AND order_date >= DATE_TRUNC('month', CURRENT_DATE)
    tags:
      difficulty: EASY
      domain: default
      eval: task_instructions

  - type: SQL
    name: orders_by_channel
    description: |-
      Order count and net revenue by acquisition channel, completed orders only.
      Evaluation:
      - entity knowledge to use the channel feature for grouping
      - task instructions to exclude test orders and filter to completed
    input: Which channels drive the most orders?
    expected_output: |-
      SELECT
        channel,
        metric(count_orders) AS order_count,
        metric(sum_net_revenue) AS net_revenue
      FROM entity('order')
      WHERE status = 'completed'
        AND is_test_order = false
      GROUP BY 1
      ORDER BY 2 DESC
    tags:
      difficulty: EASY
      domain: default
      eval: entity_knowledge

  - type: SQL
    name: refund_rate_by_product_category
    description: |-
      Refund rate grouped by primary product category.
      Evaluation:
      - entity knowledge: primary_category is a first_last feature on the order entity (not a raw column)
      - task instructions to exclude test orders (refund rate skews heavily with test data)
      - MEDIUM: agent must know to use the primary_category feature, not attempt a manual join to order_items
    input: What is our refund rate by product category?
    expected_output: |-
      SELECT
        primary_category,
        metric(refund_rate) AS refund_rate_pct,
        metric(count_orders) AS total_orders
      FROM entity('order')
      WHERE is_test_order = false
      GROUP BY 1
      ORDER BY 2 DESC
    tags:
      difficulty: MEDIUM
      domain: default
      eval: entity_knowledge
```

---

### Example 3 — Arcadia (Mobile gaming)

Three test cases for the Arcadia `player` entity: DAU count for today, ARPDAU for the last 7 days, and whale players with no recent session. The ARPDAU test is MEDIUM (requires combining `sum_net_revenue_usd` from `purchase` with a DAU count and filtering to USD); the whale lapse test is HARD (feature chaining on `player_segment`, filtering on `last_session_at`, plus domain knowledge that `player_segment` must not be recalculated manually).

```yaml
test_cases:

  - type: SQL
    name: dau_today
    description: |-
      Count of daily active players for today — players with a session since UTC midnight.
      Evaluation:
      - task instructions to use last_session_at for activity, not is_active (lags 24h)
      - domain knowledge for UTC midnight day boundary
    input: How many players were active today?
    expected_output: |-
      SELECT
        metric(count_players) AS dau
      FROM entity('player')
      WHERE last_session_at >= CURRENT_DATE
    tags:
      difficulty: EASY
      domain: default
      eval: task_instructions

  - type: SQL
    name: arpdau_last_7_days
    description: |-
      ARPDAU for the last 7 days — total net revenue from purchases divided by DAU.
      Tests that the agent uses metric features for cross-entity aggregation (not raw JOINs),
      applies the active player filter via last_session_at, and uses the correct revenue metric.
      Evaluation:
      - feature_chaining: revenue accessed via metric feature on player entity chaining to purchase
      - task_instructions: use last_session_at for DAU filter, not is_active
      - domain_knowledge: use net_revenue_usd; USD purchases only
    input: What is our ARPDAU for the last 7 days?
    expected_output: |-
      SELECT
        metric(sum_net_revenue_usd) / NULLIF(metric(count_players), 0) AS arpdau
      FROM entity('player')
      WHERE last_session_at >= CURRENT_DATE - INTERVAL '7 days'
    tags:
      difficulty: MEDIUM
      domain: default
      eval: feature_chaining, domain_knowledge

  - type: SQL
    name: whale_players_no_recent_session
    description: |-
      Whale players with no session in the last 14 days — highest-value lapse risk segment.
      Tests that the agent uses the player_segment feature (not a manual recalculation from
      total_spend_usd) and filters on last_session_at.
      Evaluation:
      - feature_chaining: player_segment is a formula derived from spend_last_30_days_usd metric
      - domain_knowledge: never recalculate player_segment manually; always use the feature
      - task_instructions: use last_session_at for activity; UTC day boundaries
    input: Show me whale players who haven't played in 14 days
    expected_output: |-
      SELECT
        player_id,
        username,
        country,
        total_spend_usd,
        spend_last_30_days_usd,
        last_session_at
      FROM entity('player')
      WHERE player_segment = 'whale'
        AND last_session_at < CURRENT_DATE - INTERVAL '14 days'
      ORDER BY total_spend_usd DESC
    tags:
      difficulty: HARD
      domain: default
      eval: feature_chaining, domain_knowledge
```
