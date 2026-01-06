"""Harbor integration for ICICL.

This module provides Harbor-compatible agents that enable running ICICL
on real-world benchmarks (SWE-bench, Terminal-Bench) via the Harbor CLI.

Example usage with Harbor CLI:

    # Training run (fills trajectory database)
    harbor run -d "swebench-verified@1.0.0" \
        --agent-import-path icicl.harbor.agents:ICICLTrainAgent \
        --limit 50

    # Evaluation run (uses frozen database)
    harbor run -d "swebench-verified@1.0.0" \
        --agent-import-path icicl.harbor.agents:ICICLTestAgent \
        --limit 50
"""

from icicl.harbor.adapter import HarborEnvironmentAdapter
from icicl.harbor.agents import ICICLTestAgent, ICICLTrainAgent

__all__ = [
    "HarborEnvironmentAdapter",
    "ICICLTrainAgent",
    "ICICLTestAgent",
]


