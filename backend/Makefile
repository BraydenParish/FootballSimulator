.PHONY: test lint format run coverage-branch-check seed run-backend

TEST_TARGET?=.
LINT_PATHS=app ../tests/backend

lint:
	black --check $(LINT_PATHS)
	isort --check-only $(LINT_PATHS)
	flake8 $(LINT_PATHS)
	mypy --config-file mypy.ini app

format:
	black $(LINT_PATHS)
	isort $(LINT_PATHS)

test:
	python -m coverage erase
	python -m coverage run -m pytest -q ${TEST_TARGET}
	python -m coverage xml
	python -m coverage report --fail-under=70
	python -m coverage json
	$(MAKE) coverage-branch-check

coverage-branch-check:
	python -c "import json, sys; from pathlib import Path; data_path = Path('coverage.json'); payload = json.loads(data_path.read_text()) if data_path.exists() else (_ for _ in ()).throw(SystemExit('coverage.json was not generated')); totals = payload.get('totals', {}); branches_total = totals.get('num_branches') or 0; branches_covered = totals.get('covered_branches') or 0; branch_pct = 100.0 if not branches_total else (branches_covered / branches_total) * 100; minimum = 60.0; (branch_pct + 1e-9 >= minimum) or (_ for _ in ()).throw(SystemExit(f'Branch coverage {branch_pct:.1f}% is below the {minimum:.0f}% minimum'))"

run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

run-backend: run

seed:
	PYTHONPATH=.. python -m database.load_data
