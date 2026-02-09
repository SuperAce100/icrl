# IT Support Demo: ICRL vs Vanilla

This demo showcases ICRL's ability to learn from past support interactions and apply that knowledge to new tickets. Unlike coding demos where patterns can be discovered by searching the codebase, this demo tests **pure memory** - the knowledge exists only in past trajectories.

## The Problem

Every IT support team accumulates tribal knowledge:
- "VPN fails on macOS Sonoma? Disable IPv6 first."
- "Email not syncing on mobile? MFA token probably expired."
- "Can't reach production DB? Check if you're on guest WiFi."

This knowledge lives in:
- Past ticket resolutions
- Slack threads
- Senior engineers' heads

**It's not in any searchable documentation.**

## How ICRL Solves This

ICRL stores successful support interactions as trajectories. When a similar issue comes in:
1. **Retrieves relevant past tickets** based on semantic similarity
2. **Applies learned solutions** instead of generic troubleshooting
3. **Provides confident, specific answers** for known issues

## Demo Structure

```
it_support_demo/
├── README.md
├── setup_demo.py              # Seeds trajectory DB with past tickets
├── run_demo.py                # Runs the comparison test
├── evaluate_responses.py      # Scores responses
├── scenarios/
│   ├── seed_tickets.json      # Past resolved tickets (ICRL's memory)
│   └── test_tickets.json      # New tickets to test
└── knowledge_base/
    └── official_docs.md       # Intentionally incomplete docs
```

## The Trick: Incomplete Official Docs

The `knowledge_base/official_docs.md` contains generic, outdated information - exactly like real corporate wikis. The **real** knowledge comes from past ticket resolutions.

## Running the Demo

```bash
cd examples/it_support_demo

# 1. Setup - seeds the trajectory database with past tickets
python setup_demo.py

# 2. Run the comparison test
python run_demo.py

# 3. View detailed evaluation
python evaluate_responses.py
```

## Expected Results

| Test Case | ICRL (with examples) | Vanilla (no examples) |
|-----------|---------------------|----------------------|
| VPN + macOS Sonoma | "Disable IPv6" ✅ | "Reinstall VPN client" ❌ |
| Email sync mobile | "MFA token expired" ✅ | "Check internet connection" ❌ |
| DB access issue | "Check guest WiFi" ✅ | "Is the database up?" ❌ |
| Git push rejected | "Use Personal Access Token" ✅ | "Reset your password" ❌ |

**Expected: ICRL ~90%+ accuracy vs Vanilla ~25% accuracy**

## Why This Matters

1. **Faster resolution**: Known issues get solved in minutes, not hours
2. **Consistent quality**: Junior support staff perform like seniors
3. **Knowledge preservation**: Tribal knowledge survives employee turnover
4. **Reduced escalations**: Fewer tickets need senior engineer involvement

## Evaluation Criteria

Each response is scored on:

| Criterion | Points | Description |
|-----------|--------|-------------|
| Correct root cause | 40 | Identifies the actual issue |
| Actionable fix | 30 | Provides specific steps that work |
| Efficiency | 20 | Doesn't waste time on wrong paths |
| Confidence | 10 | Appropriate certainty level |

## Key Insight

This demo proves ICRL's value for **non-coding tasks** where:
- Knowledge can't be discovered by searching files
- Experience matters more than documentation
- Pattern recognition from past cases is critical
