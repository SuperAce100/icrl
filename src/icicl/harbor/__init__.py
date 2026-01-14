"""Harbor integration for ICICL.

This module provides Harbor-compatible agents that enable running ICICL
on real-world benchmarks (SWE-bench, Terminal-Bench) via the Harbor CLI.

Example usage with Harbor CLI:

    # Training run (fills trajectory database)
    uv run harbor run -d "swebench-verified@1.0" \
        --agent-import-path icicl.harbor.agents:ICICLTrainAgent \
        -t "*django*"

    # Evaluation run (uses frozen database)
    uv run harbor run -d "swebench-verified@1.0" \
        --agent-import-path icicl.harbor.agents:ICICLTestAgent \
        -t "*django*"
"""

from icicl.harbor.adapter import HarborEnvironmentAdapter
from icicl.harbor.agents import ICICLTestAgent, ICICLTrainAgent, ICICLZeroShotAgent

__all__ = [
    "HarborEnvironmentAdapter",
    "ICICLTrainAgent",
    "ICICLTestAgent",
    "ICICLZeroShotAgent",
]


