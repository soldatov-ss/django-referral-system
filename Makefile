VERSION := $(shell grep -m1 '^version' pyproject.toml | sed -E 's/version = "(.*)"/\1/')

.PHONY: list qa testall test pdb coverage build version publish tag \
        clean clean-build clean-pyc clean-test

# Show available commands
list:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'

# Run all the formatting, linting, and testing commands
qa: ## Run formatting, linting, and tests
	uv run --python=3.12 --extra test ruff format .
	uv run --python=3.12 --extra test ruff check . --fix
	uv run --python=3.12 --extra test ruff check --select I --fix .
	uv run --python=3.12 --extra test pytest .

# Run all the tests for all the supported Python versions
testall: ## Run tests on all supported Python versions
	uv run --python=3.9  --extra test pytest
	uv run --python=3.10 --extra test pytest
	uv run --python=3.11 --extra test pytest
	uv run --python=3.12 --extra test pytest
	uv run --python=3.13 --extra test pytest

# Run tests, pass extra args via ARGS="..." (e.g. make test ARGS="-k test_foo")
test: ## Run tests (ARGS=... to pass pytest arguments)
	@echo "Running with args: $(ARGS)"
	uv run --python=3.12 --extra test pytest $(ARGS)

# Drop into IPython debugger on first failure
pdb: ## Run tests with IPython pdb on failure (ARGS=... supported)
	@echo "Running with args: $(ARGS)"
	uv run --python=3.12 --extra test pytest --pdb --maxfail=10 --pdbcls=IPython.terminal.debugger:TerminalPdb $(ARGS)

# Run coverage and build HTML report
coverage: ## Run coverage and generate HTML report
	uv run --python=3.12 --extra test coverage run -m pytest .
	uv run --python=3.12 --extra test coverage report -m
	uv run --python=3.12 --extra test coverage html

# Build the distribution
build: clean-build ## Build source and wheel distributions
	uv build

# Print current version
version: ## Print current project version
	@echo "Current version is $(VERSION)"

# Publish to PyPI (usage: make publish TOKEN=pypi-...)
publish: ## Publish to PyPI (TOKEN=<your-token>)
	uv publish --token $(TOKEN)

# Tag the current version and push to GitHub
tag: ## Tag current version and push to GitHub
	@echo "Tagging version v$(VERSION)"
	git tag -a v$(VERSION) -m "Creating version v$(VERSION)"
	git push origin v$(VERSION)

# Remove all build, test, coverage and Python artifacts
clean: clean-build clean-pyc clean-test ## Remove all build, test, and Python artifacts

# Remove build artifacts
clean-build: ## Remove build artifacts
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

# Remove Python file artifacts
clean-pyc: ## Remove Python file artifacts
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

# Remove test and coverage artifacts
clean-test: ## Remove test and coverage artifacts
	rm -f .coverage
	rm -fr htmlcov/
	rm -fr .pytest_cache
