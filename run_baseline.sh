#!/bin/bash
set -e

# Wait for ICRL to finish
echo "Waiting for ICRL experiment to finish..."
while true; do
  finished=$(python3 -c "import json; r=json.load(open('jobs/icrl-50steps/result.json')); print('yes' if r.get('finished_at') else 'no')" 2>/dev/null)
  if [ "$finished" = "yes" ]; then
    echo "ICRL experiment finished!"
    break
  fi
  sleep 30
done

# Source environment
source .env
export MODEL GOOGLE_APPLICATION_CREDENTIALS VERTEXAI_PROJECT VERTEXAI_LOCATION

# Run baseline (zero-shot) experiment with same conditions
echo "Starting baseline (zero-shot) experiment..."
uv run harbor run \
  -d terminal-bench@2.0 \
  --agent-import-path icrl.harbor.agents:ICRLZeroShotAgent \
  --job-name baseline-zeroshot \
  --timeout-multiplier 3.0 \
  --max-retries 3 \
  --retry-include RuntimeError \
  --retry-include InternalServerError \
  --retry-include APIConnectionError \
  --retry-include Timeout \
  -n 4

echo "Baseline experiment complete!"
