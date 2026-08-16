.DEFAULT_GOAL := help

.PHONY: help lint test types mutation compat contract package live pr targeted

help:
	@printf '%s\n' 'make lint|test|types|mutation|compat|contract|package|live|pr'

lint:
	uv run ruff format --check .
	uv run ruff check .

test:
	uv run pytest -o addopts="" -v --tb=short --strict-markers \
		-m "not live and not serial" -n auto --dist loadscope \
		--cov=multica_py --cov-branch --cov-report=
	uv run pytest -o addopts="" -v --tb=short --strict-markers \
		-m "serial and not live" --cov=multica_py --cov-branch --cov-append \
		--cov-report=term-missing --cov-report=xml --cov-report=json
	uv run python scripts/check_coverage.py --coverage-json coverage.json

types:
	uv run mypy --namespace-packages --explicit-package-bases -p multica_py
	uv run mypy tests scripts --ignore-missing-imports --follow-imports=silent --check-untyped-defs
	uv run mypy tools --ignore-missing-imports --follow-imports=silent --disable-error-code misc

mutation:
	mkdir -p .artifacts/mutation
	NO_COLOR=1 uv run mutmut run
	NO_COLOR=1 uv run mutmut results | tee .artifacts/mutation/results.txt

compat:
	@collected=$$(uv run pytest --collect-only -q -m compat 2>&1 | tail -1); \
	echo "$$collected"; \
	selected=$$(echo "$$collected" | sed -n 's/.* \([0-9][0-9]*\)\/[0-9][0-9]* tests collected.*/\1/p'); \
	if [ -z "$$selected" ]; then \
		if echo "$$collected" | grep -Eq 'no tests collected|^0 tests collected'; then selected=0; \
		else echo "compat contract: could not parse pytest collect summary: $$collected" >&2; exit 1; fi; \
	fi; \
	[ "$$selected" -ge 4 ] || { echo "compat contract requires at least four collected items; got $$selected" >&2; exit 1; }; \
	uv run pytest -q -m compat

contract:
	uv run python scripts/upstream_contract.py check --approved contracts/sdk-contract.json

package:
	uv build
	@test "$$(find dist -maxdepth 1 -name '*.whl' | wc -l | tr -d ' ')" -eq 1
	@test "$$(find dist -maxdepth 1 -name '*.tar.gz' | wc -l | tr -d ' ')" -eq 1
	uv run pytest tests/packaging/ -v -o addopts="" -m packaging

live:
	uv run pytest -o addopts="" -q -m live_smoke tests/live/test_smoke.py

pr: lint types test mutation compat contract package

targeted:
	uv run ruff format --check .
	uv run ruff check .
	uv run mypy src tests scripts
	uv run pytest -q $(PYTEST_ARGS)
