PYTHON ?= python3

LINODE_SDK_VERSION ?= "0.0.0.dev"
VERSION_MODULE_DOCSTRING ?= \"\"\"\nThe version of this linode_api4 package.\n\"\"\"\n\n
VERSION_FILE := ./linode_api4/version.py

.PHONY: clean
clean:
	mkdir -p dist
	rm -r dist
	rm -f baked_version

.PHONY: build
build: clean create-version
	$(PYTHON) -m build  --wheel --sdist

.PHONY: create-version
create-version:
	@printf "${VERSION_MODULE_DOCSTRING}__version__ = \"${LINODE_SDK_VERSION}\"\n" > $(VERSION_FILE)

.PHONY: release
release: build
	$(PYTHON) -m twine upload dist/*

.PHONY: dev-install
dev-install: clean
	$(PYTHON) -m pip install -e ".[dev]"

.PHONY: install
install: clean create-version
	$(PYTHON) -m pip install .

.PHONY: black
black:
	$(PYTHON) -m black linode_api4 test

.PHONY: isort
isort:
	$(PYTHON) -m isort linode_api4 test

.PHONY: autoflake
autoflake:
	$(PYTHON) -m autoflake linode_api4 test

.PHONY: format
format: black isort autoflake

.PHONY: lint
lint: build
	$(PYTHON) -m isort --check-only linode_api4 test
	$(PYTHON) -m autoflake --check linode_api4 test
	$(PYTHON) -m black --check --verbose linode_api4 test
	$(PYTHON) -m pylint linode_api4
	$(PYTHON) -m twine check dist/*

# Integration Test Arguments
# TEST_SUITE: Optional, specify a test suite (e.g. domain), Default to run everything if not set
# TEST_CASE: Optional, specify a test case (e.g. 'test_image_replication')
# TEST_ARGS: Optional, additional arguments for pytest (e.g. '-v' for verbose mode)

TEST_COMMAND = $(if $(TEST_SUITE),$(if $(filter $(TEST_SUITE),linode_client login_client filters),$(TEST_SUITE),models/$(TEST_SUITE)))

.PHONY: test-int
test-int:
	$(PYTHON) -m pytest test/integration/${TEST_COMMAND} $(if $(TEST_CASE),-k $(TEST_CASE)) ${TEST_ARGS}

.PHONY: test-unit
test-unit:
	$(PYTHON) -m pytest test/unit

.PHONY: test-smoke
test-smoke:
	$(PYTHON) -m pytest -m smoke test/integration