#!/bin/bash
# Quick-start script for the IT Support demo

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🎯 IT Support Demo - ICRL vs Vanilla Comparison"
echo "================================================"
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
