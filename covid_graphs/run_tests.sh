#!/bin/bash -euo pipefail

if [[ "${VIRTUAL_ENV:-}" == "" ]]
then
    echo "⚠️  Running outside of a virtual environment."
fi

echo "🏃 Running tests..."
pytest

echo "✅ Great success!"
