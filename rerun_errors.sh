#!/bin/bash
set -e

# Wait for baseline to finish
echo "Waiting for baseline experiment to finish..."
while true; do
  finished=$(python3 -c "import json; r=json.load(open('jobs/baseline-zeroshot/result.json')); print('yes' if r.get('finished_at') else 'no')" 2>/dev/null)
  if [ "$finished" = "yes" ]; then
    echo "Baseline experiment finished!"
    break
  fi
  sleep 30
done

# Source environment
source .env
export MODEL GOOGLE_APPLICATION_CREDENTIALS VERTEXAI_PROJECT VERTEXAI_LOCATION

# Resume ICRL with error filter (retry errors)
echo "Re-running ICRL errors..."
uv run harbor jobs resume -p jobs/icrl-50steps \
  -f AddTestsDirError \
  -f RuntimeError \
  -f AgentTimeoutError

# Resume baseline with error filter (retry errors)
echo "Re-running baseline errors..."
uv run harbor jobs resume -p jobs/baseline-zeroshot \
  -f AddTestsDirError \
  -f RuntimeError \
  -f AgentTimeoutError \
  -f ContentPolicyViolationError

echo "All error retries complete!"
