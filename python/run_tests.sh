#!/bin/bash
set -euo pipefail

if [[ "${VIRTUAL_ENV:-}" == "" ]]
then
    echo "⚠️  Running outside of a virtual environment."
fi

PYTHON_PACKAGES=(covid_graphs covid_web)

echo "📝 Checking order of imports..."
isort --check-only --recursive --diff $PYTHON_PACKAGES

echo "⚫ Checking code format..."
black --diff --check $PYTHON_PACKAGES

echo "👮 Type checking..."
mypy $PYTHON_PACKAGES

echo "🧶 Linting..."
flake8 --config setup.cfg --jobs auto $PYTHON_PACKAGES

echo "🏃 Running tests..."
pytest

echo "✅ Great success!"
