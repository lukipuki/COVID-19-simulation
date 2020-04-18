#!/bin/bash
set -euo pipefail

if [[ "${VIRTUAL_ENV:-}" == "" ]]
then
    echo "⚠️  Must run within a virtual environment, please activate it first."
    exit 1
fi

echo "🏃 Running tests..."
pytest

echo "✅ Great success!"
