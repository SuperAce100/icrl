# ICICL

**Self-Generated In-Context Learning for LLM Agents**

ICICL implements the Self-Generated In-Context Learning algorithm, enabling LLM agents to bootstrap their own performance by learning from successful trajectories. The agent accumulates successful experiences and retrieves relevant examples at each decision point to improve future task completion.

## Installation

```bash
pip install icicl
# or with uv
uv add icicl
```

**Dependencies**: `pydantic`, `litellm`, `sentence-transformers`, `faiss-cpu`, `aiofiles`, `rich`, `python-dotenv`

## Quick Start

```python
import asyncio
from icicl import Agent, LiteLLMProvider

# Create the agent
agent = Agent(
    llm=LiteLLMProvider(model="gpt-4o-mini"),
    db_path="./trajectories",
    plan_prompt="Goal: {goal}\n\nExamples:\n{examples}\n\nCreate a plan:",
    reason_prompt="Goal: {goal}\nPlan: {plan}\nObservation: {observation}\nThink step by step:",
    act_prompt="Goal: {goal}\nPlan: {plan}\nReasoning: {reasoning}\nNext action:",
    k=3,           # number of examples to retrieve
    max_steps=30,  # max steps per episode
)

# Training: successful trajectories are stored for future use
trajectory = asyncio.run(agent.train(env, goal="Complete the task"))

# Inference: uses stored examples but doesn't add new ones
trajectory = asyncio.run(agent.run(env, goal="Complete another task"))
```

## Core Concepts

### The SGICL Algorithm

1. **Bootstrap Phase**: The agent attempts tasks, storing successful trajectories
2. **Retrieval**: At each decision point, semantically similar examples are retrieved
3. **Generation**: The LLM generates plans/reasoning/actions informed by examples
4. **Curation**: Low-utility trajectories are automatically pruned over time

### ReAct Loop

Each episode follows a **Plan → Reason → Act** loop:

```
┌─────────────────────────────────────────────────────────┐
│  1. PLAN: Generate high-level strategy using examples   │
├─────────────────────────────────────────────────────────┤
│  2. REASON: Analyze observation with retrieved context  │
├─────────────────────────────────────────────────────────┤
│  3. ACT: Execute action based on reasoning              │
├─────────────────────────────────────────────────────────┤
│  4. OBSERVE: Get environment feedback                   │
│     └─→ Loop back to REASON until done                  │
└─────────────────────────────────────────────────────────┘
```

## API Reference

### `Agent`

The main class for training and running the ICICL agent.

```python
from icicl import Agent

agent = Agent(
    llm: LLMProvider,              # LLM for generating completions
    db_path: str,                  # Path to trajectory database
    plan_prompt: str,              # Template with {goal}, {examples}
    reason_prompt: str,            # Template with {goal}, {plan}, {observation}, {history}, {examples}
    act_prompt: str,               # Template with {goal}, {plan}, {reasoning}, {history}, {examples}
    k: int = 3,                    # Number of examples to retrieve
    max_steps: int = 30,           # Maximum steps per episode
    seed_trajectories: list[Trajectory] | None = None,  # Initial examples
    on_step: Callable[[Step, StepContext], None] | None = None,  # Step callback
    curation_threshold: float = 0.3,      # Utility threshold for pruning
    curation_min_retrievals: int = 5,     # Min retrievals before pruning
)
```

#### Methods

| Method | Description |
|--------|-------------|
| `await agent.train(env, goal)` | Run training episode, store successful trajectories |
| `await agent.run(env, goal)` | Run inference episode (database frozen) |
| `agent.train_sync(env, goal)` | Synchronous wrapper for `train` |
| `agent.run_sync(env, goal)` | Synchronous wrapper for `run` |
| `await agent.train_batch(env_factory, goals)` | Train on multiple goals |
| `await agent.run_batch(env_factory, goals)` | Run inference on multiple goals |
| `agent.get_stats()` | Get database statistics |
| `agent.database` | Access the underlying `TrajectoryDatabase` |

### `LiteLLMProvider`

Built-in LLM provider supporting 100+ models via [LiteLLM](https://github.com/BerriAI/litellm).

```python
from icicl import LiteLLMProvider

llm = LiteLLMProvider(
    model: str = "gpt-4o-mini",    # Model identifier
    temperature: float = 0.7,      # Sampling temperature
    max_tokens: int | None = None, # Max tokens (None for model default)
    **kwargs,                      # Additional LiteLLM arguments
)
```

**Supported models include:**
- OpenAI: `gpt-4o`, `gpt-4o-mini`, `gpt-4-turbo`, `gpt-3.5-turbo`
- Anthropic: `claude-3-5-sonnet-20241022`, `claude-3-opus-20240229`
- Google: `gemini/gemini-pro`, `gemini/gemini-1.5-pro`
- Azure, Cohere, Replicate, and [many more](https://docs.litellm.ai/docs/providers)

### `Environment` Protocol

Implement this protocol for your custom environment:

```python
from icicl import Environment

class MyEnvironment:
    def reset(self, goal: str) -> str:
        """Reset environment and return initial observation.
        
        Args:
            goal: The goal description for this episode.
        
        Returns:
            Initial observation as a string.
        """
        self._goal = goal  # Store for use in step()
        return "Initial state description"

    def step(self, action: str) -> tuple[str, bool, bool]:
        """Execute an action.
        
        Args:
            action: The action string to execute.
        
        Returns:
            Tuple of (observation, done, success):
            - observation: Result of the action
            - done: Whether episode has ended
            - success: Whether goal was achieved
        """
        # Execute action and check if goal is met
        observation = execute(action)
        success = check_goal(self._goal)
        done = success or max_steps_reached
        return observation, done, success
```

### `LLMProvider` Protocol

Implement for custom LLM integrations:

```python
from icicl import LLMProvider, Message

class MyLLMProvider:
    async def complete(self, messages: list[Message]) -> str:
        """Generate completion from messages.
        
        Args:
            messages: List of Message(role, content) objects.
        
        Returns:
            Generated text as a string.
        """
        # Call your LLM
        return await my_llm_call(messages)
```

### Data Models

All models are Pydantic `BaseModel` classes for type safety and serialization.

#### `Trajectory`

A complete episode trajectory:

```python
from icicl import Trajectory, Step

trajectory = Trajectory(
    id: str,                    # Auto-generated UUID
    goal: str,                  # Goal description
    plan: str,                  # Generated plan
    steps: list[Step],          # List of steps taken
    success: bool,              # Whether goal was achieved
    metadata: dict[str, Any],   # Custom metadata
)

# Convert to example string for prompts
example_str = trajectory.to_example_string()
```

#### `Step`

A single step in a trajectory:

```python
from icicl import Step

step = Step(
    observation: str,  # What the agent observed
    reasoning: str,    # Agent's reasoning
    action: str,       # Action taken
)
```

#### `StepContext`

Context available during prompt formatting:

```python
from icicl import StepContext

context = StepContext(
    goal: str,
    plan: str,
    observation: str,
    reasoning: str = "",
    history: list[Step] = [],
    examples: list[Trajectory] = [],
)

# Format for prompts
context.format_examples()  # → "Goal: ...\nPlan: ...\nSteps: ..."
context.format_history()   # → "Step 1: action -> observation\n..."
```

#### `Message`

A chat message:

```python
from icicl import Message

message = Message(role="user", content="Hello")
```

## Prompt Templates

Prompts use Python format strings with these placeholders:

| Placeholder | Available In | Description |
|-------------|--------------|-------------|
| `{goal}` | All prompts | The current goal |
| `{examples}` | All prompts | Formatted retrieved trajectories |
| `{plan}` | reason, act | The generated plan |
| `{observation}` | reason, act | Current observation |
| `{reasoning}` | act | Generated reasoning |
| `{history}` | reason, act | Previous steps in episode |

### Example Prompts

```python
PLAN_PROMPT = """You are a helpful agent.

Goal: {goal}

Here are examples of similar tasks that were completed successfully:
{examples}

Create a step-by-step plan to accomplish the goal."""

REASON_PROMPT = """Goal: {goal}
Plan: {plan}

Previous steps:
{history}

Current observation:
{observation}

Examples of similar situations:
{examples}

Think step by step about what you observe and what to do next."""

ACT_PROMPT = """Goal: {goal}
Plan: {plan}

Steps so far:
{history}

Current observation: {observation}
Your reasoning: {reasoning}

What is the next action? Respond with only the action."""
```

## Step Callbacks

Monitor agent progress with step callbacks:

```python
from icicl import Step, StepContext

def my_callback(step: Step, context: StepContext) -> None:
    print(f"Observation: {step.observation[:100]}...")
    print(f"Reasoning: {step.reasoning}")
    print(f"Action: {step.action}")
    print(f"Using {len(context.examples)} examples")

agent = Agent(
    ...,
    on_step=my_callback,
)
```

## Trajectory Database

The agent stores trajectories on disk with FAISS-based semantic search.

```python
# Access the database directly
db = agent.database

# Search for similar trajectories
similar = db.search("find config files", k=3)

# Get all trajectories
all_trajs = db.get_all()

# Get a specific trajectory
traj = db.get("trajectory-id")

# Remove a trajectory
db.remove("trajectory-id")
```

### Database Structure

```
./trajectories/
├── trajectories/
│   ├── <uuid-1>.json
│   ├── <uuid-2>.json
│   └── ...
├── index.faiss         # FAISS vector index
├── index_ids.json      # ID mapping
└── curation.json       # Utility tracking
```

## Curation

The agent automatically prunes low-utility trajectories. A trajectory is pruned when:

1. It has been retrieved at least `min_retrievals` times
2. Its utility score (success rate when used) falls below `threshold`

```python
agent = Agent(
    ...,
    curation_threshold=0.3,       # Prune if utility < 30%
    curation_min_retrievals=5,    # After at least 5 retrievals
)
```

## Advanced Usage

### Seed Trajectories

Initialize with pre-existing examples:

```python
from icicl import Trajectory, Step

seed = Trajectory(
    goal="Example task",
    plan="1. Do A\n2. Do B",
    steps=[
        Step(observation="Started", reasoning="Need to do A", action="do_a"),
        Step(observation="A done", reasoning="Now do B", action="do_b"),
    ],
    success=True,
)

agent = Agent(
    ...,
    seed_trajectories=[seed],
)
```

### Batch Training

Train on multiple tasks efficiently:

```python
def make_env():
    return MyEnvironment()

goals = ["Task 1", "Task 2", "Task 3"]

# Training mode - learns from each successful episode
trajectories = await agent.train_batch(make_env, goals)

# Inference mode - frozen database
trajectories = await agent.run_batch(make_env, goals)
```

### Custom Embeddings

The database uses `sentence-transformers` with `all-MiniLM-L6-v2` by default (as used in the paper). For custom embeddings, subclass the database:

```python
from icicl.embedder import SentenceTransformerEmbedder
from icicl.database import TrajectoryDatabase

embedder = SentenceTransformerEmbedder(model_name="your-model")
db = TrajectoryDatabase(path="./trajectories", embedder=embedder)
```

## Examples

### File System Navigation Agent

See `examples/demo_with_real_llm.py` for a complete example of an agent that navigates a virtual file system:

```bash
# Set your API key
export OPENAI_API_KEY=your-key

# Run the demo
uv run python examples/demo_with_real_llm.py
```

### Mock LLM for Testing

Use the mock provider for fast iteration without API calls:

```python
from examples.mock_llm import MockLLMProvider

llm = MockLLMProvider(success_rate=1.0)
agent = Agent(llm=llm, ...)
```

### Harbor Coding Agent (Terminal-Bench 2.0 Compatible)

See `examples/harbor_coding_agent.py` for a coding agent example compatible with [Harbor](https://harborframework.com) and Terminal-Bench 2.0. This demonstrates:

- A sandboxed coding environment with shell commands (ls, cat, grep, sed, etc.)
- Realistic software engineering tasks (debugging, refactoring, testing)
- Performance improvement tracking before/after ICICL training

```bash
export OPENAI_API_KEY=your-key
uv run python examples/harbor_coding_agent.py
```

The Harbor example shows how ICICL improves agent performance on coding tasks:

1. **Baseline Evaluation**: Agent attempts tasks without learned examples
2. **Training Phase**: Agent learns from successful coding task trajectories
3. **Improved Evaluation**: Re-test shows performance gains from trajectory learning

This pattern integrates with Harbor's agent evaluation framework, allowing you to:
- Benchmark coding agents on Terminal-Bench 2.0 tasks
- Use ICICL's self-generated examples to improve agent performance
- Track improvements across training iterations

## Architecture

```
icicl/
├── agent.py        # Main Agent class
├── loop.py         # ReAct loop implementation
├── database.py     # FAISS-backed trajectory storage
├── retriever.py    # Semantic example retrieval
├── curation.py     # Automatic trajectory pruning
├── embedder.py     # Sentence transformer embeddings
├── models.py       # Pydantic data models
├── protocols.py    # Environment and LLMProvider protocols
└── providers/
    └── litellm.py  # LiteLLM integration
```

## Reference

This implementation is based on the algorithm described in:

> **Self-Generated In-Context Examples Improve LLM Agents for Sequential Decision-Making Tasks**

The key insight is that LLM agents can bootstrap their own performance by:
1. Attempting tasks and recording successful trajectories
2. Using semantic retrieval to find relevant examples at each decision point
3. Automatically curating the example database to retain high-utility examples

## License

MIT

