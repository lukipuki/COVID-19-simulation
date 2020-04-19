#!/bin/bash
set -euo pipefail

if [[ "${VIRTUAL_ENV:-}" == "" ]]
then
    echo "⚠️  Running outside of a virtual environment."
fi

echo "📝 Checking order of imports..."
isort covid_graphs/ --check-only --recursive --diff

echo "⚫ Checking code format..."
black covid_graphs/ --diff --check

echo "👮 Type checking..."
mypy covid_graphs/

echo "🧶 Linting..."
flake8 --config setup.cfg --jobs auto covid_graphs/

echo "🏃 Running tests..."
pytest

echo "✅ Great success!"
