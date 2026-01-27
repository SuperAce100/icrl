#!/bin/bash
# Quick-start script for the codebase patterns demo

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🎯 ICRL Codebase Patterns Demo"
echo "=============================="
echo ""

# Check if icrl is installed
if ! command -v icrl &> /dev/null; then
    echo "❌ 'icrl' command not found. Please install icrl first:"
    echo "   pip install -e ."
    exit 1
fi

# Setup the demo
echo "📦 Setting up demo environment..."
python setup_demo.py

echo ""
echo "🚀 Starting ICRL chat in mock_codebase directory..."
echo ""
echo "Try these prompts:"
echo "  1. 'Add a GET /orders endpoint that returns a list of orders. Follow the existing patterns.'"
echo "  2. 'Add a GET /categories endpoint with CRUD operations'"
echo ""
echo "Press Ctrl+C to exit"
echo ""

cd mock_codebase
exec icrl chat
