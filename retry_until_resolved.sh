#!/bin/bash
set -e

cd /Users/asanshaygupta/Documents/Codes/Stanford/Research/sgicl
source .env
export MODEL GOOGLE_APPLICATION_CREDENTIALS VERTEXAI_PROJECT VERTEXAI_LOCATION

MAX_RETRIES=10
retry_count=0

while [ $retry_count -lt $MAX_RETRIES ]; do
    # Wait for current run to finish
    echo "Waiting for current run to finish..."
    while true; do
        finished=$(python3 -c "import json; r=json.load(open('jobs/icrl-50steps/result.json')); print('yes' if r.get('finished_at') else 'no')" 2>/dev/null)
        if [ "$finished" = "yes" ]; then
            break
        fi
        sleep 30
    done
    
    # Check error count
    errors=$(python3 -c "import json; r=json.load(open('jobs/icrl-50steps/result.json')); print(r['stats']['n_errors'])" 2>/dev/null)
    echo "Current errors: $errors"
    
    if [ "$errors" -eq 0 ]; then
        echo "All errors resolved!"
        exit 0
    fi
    
    retry_count=$((retry_count + 1))
    echo "Retry attempt $retry_count of $MAX_RETRIES..."
    
    # Resume with error filters
    uv run harbor jobs resume -p jobs/icrl-50steps \
        -f AuthenticationError \
        -f RuntimeError \
        -f AgentTimeoutError \
        -f AddTestsDirError
done

echo "Max retries reached. Some errors may remain."
