#!/bin/bash
# Quick-start script for the Exception Handling demo

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🎯 Exception Handling Demo - ICRL vs Vanilla Comparison"
echo "========================================================"
echo ""
echo "This demo shows how ICRL learns from past exception-handling"
echo "decisions to make nuanced judgment calls that go beyond rigid policy."
echo ""

# Setup the demo
echo "📦 Setting up demo environment..."
python setup_demo.py

echo ""
echo "🚀 Running comparison test..."
echo ""

# Run the demo
python run_demo.py

echo ""
echo "📊 Running detailed evaluation..."
echo ""

# Show detailed evaluation
python evaluate_responses.py
