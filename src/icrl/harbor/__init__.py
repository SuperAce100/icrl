"""Harbor integration for ICRL.

This module provides Harbor-compatible agents that enable running ICRL
on real-world benchmarks (SWE-bench, Terminal-Bench) via the Harbor CLI.

Example usage with Harbor CLI:

    # Training run (fills trajectory database)
    uv run harbor run -d "swebench-verified@1.0" \
        --agent-import-path icrl.harbor.agents:ICRLTrainAgent \
        -t "*django*"

    # Evaluation run (uses frozen database)
    uv run harbor run -d "swebench-verified@1.0" \
        --agent-import-path icrl.harbor.agents:ICRLTestAgent \
        -t "*django*"
"""

from icrl.harbor.adapter import HarborEnvironmentAdapter
from icrl.harbor.agents import ICRLTestAgent, ICRLTrainAgent, ICRLZeroShotAgent

__all__ = [
    "HarborEnvironmentAdapter",
    "ICRLTrainAgent",
    "ICRLTestAgent",
    "ICRLZeroShotAgent",
]


