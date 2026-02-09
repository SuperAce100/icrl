# Preference Learning Demo: ICRL Adapts to Your Style

This demo showcases ICRL's ability to learn and adapt to individual user preferences, communication styles, and working patterns over time.

## The Problem

Every user has different preferences:
- **Verbosity**: Some want detailed explanations, others want terse commands
- **Format**: Some prefer bullet points, others want prose
- **Depth**: Some want "just tell me what to do", others want "explain why"
- **Tone**: Some prefer formal, others casual
- **Examples**: Some learn from examples, others find them redundant

Vanilla LLMs treat every user the same. You end up repeatedly saying:
- *"Be more concise"*
- *"Give me the command, not the explanation"*
- *"I need more context"*
- *"Stop using bullet points"*

## How ICRL Solves This

ICRL stores successful interactions that reflect your preferences. Over time:
1. **Learns your style** from past interactions you approved
2. **Retrieves preference-matched examples** for similar requests
3. **Adapts responses automatically** without re-prompting

## Demo Structure

```
preference_learning_demo/
├── README.md
├── setup_demo.py              # Seeds DB with user-specific trajectories
├── run_demo.py                # Runs comparison across user profiles
├── evaluate_responses.py      # Analyzes preference matching
├── user_profiles/
│   ├── expert_terse.json      # Senior dev: "just the code"
│   ├── learner_detailed.json  # Junior dev: "explain everything"
│   └── manager_summary.json   # Manager: "high-level overview"
└── scenarios/
    ├── seed_interactions.json # Past interactions per user type
    └── test_requests.json     # New requests to test
```

## User Profiles

### 1. Expert Terse (Senior Developer)
- **Style**: Minimal explanation, maximum efficiency
- **Wants**: Commands, code snippets, no hand-holding
- **Hates**: Obvious explanations, verbose responses
- **Example**: "How do I rebase?" → `git rebase -i HEAD~3`

### 2. Learner Detailed (Junior Developer)
- **Style**: Thorough explanations with context
- **Wants**: Why things work, potential pitfalls, examples
- **Hates**: Unexplained commands, assumed knowledge
- **Example**: "How do I rebase?" → Full explanation with diagrams

### 3. Manager Summary (Technical Manager)
- **Style**: High-level overview with business context
- **Wants**: Impact, timeline, risks, decisions needed
- **Hates**: Implementation details, code snippets
- **Example**: "How do I rebase?" → "Rebasing reorganizes commit history..."

## Running the Demo

```bash
cd examples/preference_learning_demo

# 1. Setup - seeds trajectories for each user profile
python setup_demo.py

# 2. Run the comparison test
python run_demo.py

# 3. View detailed evaluation
python evaluate_responses.py
```

## What to Observe

### Same Question, Different Answers

**Request**: "How do I fix a merge conflict?"

**Expert Terse (with ICRL)**:
```
git status  # see conflicted files
# edit files, remove <<<< ==== >>>> markers
git add .
git commit
```

**Learner Detailed (with ICRL)**:
```
A merge conflict happens when Git can't automatically combine changes...

Here's how to resolve it step by step:

1. First, identify the conflicted files:
   $ git status
   
   You'll see files marked as "both modified"

2. Open each conflicted file. You'll see markers like:
   <<<<<<< HEAD
   your changes
   =======
   their changes
   >>>>>>> branch-name
   
   The part above ======= is your version...
   [continues with full explanation]
```

**Manager Summary (with ICRL)**:
```
Merge conflicts occur when two branches modify the same code.

**Impact**: Blocks the merge until resolved
**Time to fix**: Usually 5-30 minutes depending on complexity
**Risk**: Low if handled carefully; changes could be lost if done wrong
**Who should handle**: The developer who made the conflicting changes

Let me know if you need the technical details or if the team should handle this.
```

### Vanilla (No Preference Learning)

Without ICRL, all three users get the same generic response - probably a medium-verbosity explanation that's:
- Too verbose for the expert
- Not detailed enough for the learner
- Too technical for the manager

## Evaluation Criteria

Responses are scored on preference matching:

| Criterion | Points | Description |
|-----------|--------|-------------|
| Length match | 25 | Response length matches user preference |
| Format match | 25 | Bullet points vs prose vs code-only |
| Depth match | 25 | Explanation level appropriate |
| Tone match | 25 | Formal/casual/technical as preferred |

## Expected Results

| User Profile | ICRL Score | Vanilla Score | Improvement |
|--------------|------------|---------------|-------------|
| Expert Terse | ~90% | ~40% | +50% |
| Learner Detailed | ~85% | ~50% | +35% |
| Manager Summary | ~85% | ~30% | +55% |

## Why This Matters

1. **Reduced friction**: No more "be more concise" corrections
2. **Faster workflows**: Responses match your mental model
3. **Team scalability**: Each team member gets personalized assistance
4. **Onboarding**: New users benefit from similar users' preferences

## Key Insight

This demo proves ICRL's value for **personalization** where:
- One size doesn't fit all
- User preferences are implicit in past interactions
- Adaptation happens automatically without explicit configuration
- The same question should have different "right" answers for different users
