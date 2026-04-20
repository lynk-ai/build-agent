# Step 1: Business Context

Before touching any entity YAML, write down what the business is and what language it uses.

This step produces two files: a knowledge file that describes the business and its data, and a glossary that defines the terms users will type when asking questions.

---

## Why Start with Business Context?

Starting here is a recommended best practice — not a requirement. Think of it the same way you would onboard a new analyst: you would not start by walking them through database tables and column names. You would first explain what the business does, what the key terms mean, and what the numbers represent. The same logic applies here. Start with the big picture — what the business is, what language it uses — and the entity YAML you write later will be grounded in that context from the beginning.

---

## 1a: Domain Knowledge File

**Location:** `.lynk/default/domain_context/grove_knowledge.md`

This file answers: *What is this business? What data does the semantic layer cover? What rules always apply?*

```markdown
---
type: knowledge
domain: "*"
---

## What Grove Is

Grove sells subscription-based business software to companies. Customers are B2B organizations ranging from early-stage startups to large enterprise accounts. The primary business model is annual recurring revenue (ARR) from software subscriptions, with expansion revenue from upgrades and seat additions.

## Data Scope

This semantic layer covers customer accounts and subscription data. Marketing attribution, product usage events, and support tickets are not included — those are separate domains planned for future phases.

## Temporal Scope

- Data starts from 2019-01-01 (earliest customer records)
- Data is current through yesterday — the pipeline refreshes nightly
- `first_paid_at` is the canonical start date for a paying relationship, not the account creation date

## Data Governance

- Test accounts (`is_test_account = true`) must be excluded from all analysis by default
- Deleted accounts (`is_deleted = true`) must be excluded from all analysis by default
- `arr` is the single source of truth for revenue. Do not use `total_paid` — it includes one-time professional services fees that inflate revenue figures
- The fiscal year starts February 1. Q1 = Feb–Apr, Q2 = May–Jul, Q3 = Aug–Oct, Q4 = Nov–Jan
```

**What to include:**
- What the company does in one paragraph — the business model and primary revenue driver
- What the semantic layer covers and what is explicitly out of scope
- Temporal scope — when data starts, how fresh it is, which date field is canonical for cohort analysis
- Data governance rules that apply to every query (test account exclusion, deleted records, the canonical revenue metric)
- Fiscal year calendar if it differs from the calendar year

**What to leave out:**
- SQL instructions — those go in domain task instructions
- Term definitions — those go in the glossary
- Entity-specific rules — those go in entity knowledge files

---

## 1b: Glossary File

**Location:** `.lynk/default/grove_glossary.md`

This file answers: *What do these terms mean when a user types them?*

The glossary is a dictionary, not an encyclopedia. Each entry is a key with a term and a short definition — one to two sentences maximum. Anything requiring more explanation belongs in a knowledge file.

```markdown
---
type: glossary
domain: "*"
---

arr:
  term: Annual Recurring Revenue (ARR)
  description: The normalized annual value of all active subscription contracts. Excludes one-time fees and professional services. The default revenue metric at Grove.

mrr:
  term: Monthly Recurring Revenue (MRR)
  description: ARR divided by 12. Used for month-over-month revenue tracking.

logo_churn:
  term: Logo Churn
  description: The percentage of customer accounts that cancelled in a given period, regardless of their ARR value. Count-based, not revenue-based.

revenue_churn:
  term: Revenue Churn
  description: The percentage of ARR lost from cancellations and downgrades in a given period. A large account churning has more revenue impact than a small one — that is the distinction from logo churn.

expansion:
  term: Expansion
  description: Revenue growth from existing customers through upgrades, seat additions, or plan changes that increase ARR.

ndr:
  term: Net Dollar Retention (NDR)
  description: The percentage of ARR retained and expanded from the existing customer base over a 12-month period. NDR above 100% means expansion revenue exceeds churn.

at_risk:
  term: At-Risk
  description: A customer flagged as likely to churn. At Grove, at-risk means NPS score below 6, or no login activity in the past 60 days.

power_user:
  term: Power User
  description: A user who logs in 20 or more days per month and has engaged with 3 or more core product features.

plan_type:
  term: Plan Type
  description: The subscription tier — one of starter, growth, or enterprise. Enterprise plans are always billed annually.
```

**What to include:**
- Abbreviations users will type (ARR, MRR, NDR, NPS)
- Business-specific terms where your definition differs from the industry default — especially thresholds that define a term (at-risk is NPS < 6 OR no login in 60 days)
- Any "same word, different meanings" distinctions (logo churn vs. revenue churn)

**What to leave out:**
- Anything requiring more than two sentences — use a knowledge file instead
- Technical SQL field names — those live in entity YAML
- Terms that are unambiguous in plain English

---

## Key Point

The glossary is what prevents the agent from guessing. Without it, a question like "show me at-risk customers" requires the agent to infer what "at-risk" means from schema and column names alone. With a glossary entry that defines the threshold precisely — NPS below 6 or no login in 60 days — the agent applies your definition every time, consistently.

Writing these two files before touching entity YAML is the recommended starting point. If you find it difficult to describe what the business is and what its terms mean, that is a signal to work through the knowledge file and glossary first before modeling entities.
