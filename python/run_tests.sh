#!/bin/bash
set -euo pipefail

if [[ "${VIRTUAL_ENV:-}" == "" ]]
then
    echo "⚠️  Running outside of a virtual environment."
fi

PYTHON_PACKAGES=(covid_graphs covid_web)
for PYTHON_PACKAGE in "${PYTHON_PACKAGES[@]}"
do
    echo "☞  Running on ${PYTHON_PACKAGE}"
    echo "📝 Checking order of imports..."
    isort --check-only --recursive --diff $PYTHON_PACKAGE
    
    echo "⚫ Checking code format..."
    black --diff --check $PYTHON_PACKAGE
    
    echo "👮 Type checking..."
    mypy $PYTHON_PACKAGE
    
    echo "🧶 Linting..."
    flake8 --config setup.cfg --jobs auto $PYTHON_PACKAGE
    
    echo "🏃 Running tests..."
    pytest
done

echo "✅ Great success!"
