# Exception Handling Demo: ICRL vs Vanilla

This demo showcases ICRL's ability to learn from past precedents when handling unusual situations and edge cases. Unlike standard policy lookups, real exception handling requires institutional memory of what worked before.

## The Problem

Every organization handles exceptions based on unwritten rules and past precedents:
- "Refund requests > 30 days: approve if they're a long-term customer"
- "Enterprise customer asks for custom terms: always loop in legal first"
- "User claims they were charged twice: refund first, investigate later"
- "Competitor is poaching our customer: escalate to VP, offer retention discount"

This knowledge lives in:
- Past decisions made by senior staff
- Slack threads about edge cases
- Tribal knowledge passed down verbally

**It's not in any policy document.**

## How ICRL Solves This

ICRL stores successful exception-handling decisions as trajectories. When a similar situation arises:
1. **Retrieves relevant precedents** based on situation similarity
2. **Applies learned decision patterns** instead of rigid policy
3. **Provides confident, consistent answers** aligned with past decisions

## Demo Structure

```
exception_handling_demo/
├── README.md
├── setup_demo.py              # Seeds trajectory DB with past decisions
├── run_demo.py                # Runs the comparison test
├── evaluate_responses.py      # Detailed analysis
├── scenarios/
│   ├── seed_decisions.json    # Past exception-handling precedents
│   ├── test_scenarios.json    # New edge cases to test
│   └── policies.md            # Official (rigid) policies
└── run_quick_demo.sh
```

## The Trick: Rigid Official Policies

The `policies.md` contains strict, black-and-white rules that don't account for nuance:

```markdown
## Refund Policy
Refunds are only available within 30 days of purchase. No exceptions.

## Contract Terms  
All customers must use standard contract terms. Custom terms are not available.
```

But the **real** handling (from past decisions) includes:
- "Long-term customer (2+ years) asking for late refund → approve with goodwill gesture"
- "Enterprise deal > $500k requesting custom terms → loop in legal, usually approve"
- "Customer threatening to churn to competitor → escalate, offer retention package"

## Running the Demo

```bash
cd examples/exception_handling_demo

# 1. Setup - seeds the trajectory database with past decisions
python setup_demo.py

# 2. Run the comparison test
python run_demo.py

# 3. View detailed evaluation
python evaluate_responses.py
```

## Expected Results

| Scenario | ICRL | Vanilla |
|----------|------|---------|
| Late refund, loyal customer | Approve with goodwill | Deny (policy says 30 days) |
| Enterprise custom terms | Loop in legal, likely approve | Deny (policy says no custom terms) |
| Competitor poaching | Escalate + retention offer | Standard response |
| Billing dispute, high-value | Refund first, investigate later | Investigate first |

**Expected: ICRL matches precedent ~85%+ vs Vanilla ~30%**

## Why This Matters

1. **Consistency**: Similar situations get similar treatment
2. **Customer retention**: Flexible handling keeps valuable customers
3. **Reduced escalations**: Junior staff can handle exceptions confidently
4. **Institutional memory**: Precedents survive employee turnover

## Evaluation Criteria

Each response is scored on:

| Criterion | Points | Description |
|-----------|--------|-------------|
| Correct action | 40 | Matches the precedent-based decision |
| Right escalation | 25 | Knows when/who to escalate to |
| Customer-appropriate | 20 | Tone and framing suitable for situation |
| Confidence | 15 | Doesn't over-hedge on known precedents |

## Key Insight

This demo proves ICRL's value for **judgment-based tasks** where:
- Official policy is too rigid for real situations
- Past precedents define the actual practice
- Consistency matters for fairness and trust
- Knowledge can't be discovered through any tool or API
