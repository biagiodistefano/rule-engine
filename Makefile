.PHONY: format
format:
	ruff format .

.PHONY: lint
lint:
	ruff check . --fix

.PHONY: mypy
mypy:
	mypy --strict --extra-checks --warn-unreachable --warn-unused-ignores src

.PHONY: test
test:
	pytest --cov=src --cov-report=term --cov-report=html --cov-branch -v src/ && coverage html --skip-covered

.PHONY: test-failed
test-failed:
	pytest --cov=src --cov-report=term --cov-report=html --cov-branch -v --last-failed src/ && coverage html --skip-covered

.PHONY: test-pipeline
test-pipeline:
	pytest --cov=src --cov-report=term --cov-report=html --cov-branch --cov-fail-under=100 -v src

# Combined command: Runs format, lint, and mypy in sequence
.PHONY: check
check: format lint mypy
