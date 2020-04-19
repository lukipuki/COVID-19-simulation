#!/bin/bash
set -euo pipefail

if [[ "${VIRTUAL_ENV:-}" == "" ]]
then
    echo "⚠️  Running outside of a virtual environment."
fi

echo "👮 Type checking.."
mypy covid_graphs/

echo "🏃 Running tests..."
pytest

echo "✅ Great success!"
