PYTHON ?= python
PIP ?= pip
ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST)))/..)

.PHONY: install-deps test lint format check

install-deps:
	$(PIP) install -r requirements.txt
	@if [ -f requirements-dev.txt ]; then \
		$(PIP) install -r requirements-dev.txt; \
	fi

test:
	cd $(ROOT) && PYTHONPATH=. $(PYTHON) -m pytest

lint:
	cd $(ROOT) && ruff check backend tests shared

format:
	cd $(ROOT) && ruff format backend tests shared

check: lint test
