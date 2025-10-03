.PHONY: test lint format

TEST_TARGET?=.
LINT_PATHS=app ../tests/backend

lint:
black --check $(LINT_PATHS)
isort --check-only $(LINT_PATHS)
flake8 $(LINT_PATHS)
mypy app

format:
black $(LINT_PATHS)
isort $(LINT_PATHS)

test:
pytest -q ${TEST_TARGET}
