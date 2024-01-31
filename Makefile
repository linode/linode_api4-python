PYTHON ?= python3

INTEGRATION_TEST_PATH :=
TEST_CASE_COMMAND :=
MODEL_COMMAND :=

LINODE_SDK_VERSION ?= "0.0.0.dev"
VERSION_MODULE_DOCSTRING ?= \"\"\"\nThe version of this linode_api4 package.\n\"\"\"\n\n
VERSION_FILE := ./linode_api4/version.py

ifdef TEST_CASE
TEST_CASE_COMMAND = -k $(TEST_CASE)
endif

ifdef TEST_MODEL
MODEL_COMMAND = models/$(TEST_MODEL)
endif

.PHONY: clean
clean:
	mkdir -p dist
	rm -r dist
	rm -f baked_version

.PHONY: build
build: clean
	$(PYTHON) -m build  --wheel --sdist

.PHONY: create-version
create-version:
	@echo "${VERSION_MODULE_DOCSTRING}__version__ = \"${LINODE_PYTHON_SDK_VERSION}\"" > $(VERSION_FILE)

.PHONY: release
release: build
	$(PYTHON) -m twine upload dist/*

.PHONY: dev-install
dev-install: clean
	$(PYTHON) -m pip install -e ".[dev]"

.PHONY: install
install: clean
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

.PHONY: testint
testint:
	$(PYTHON) -m pytest test/integration/${INTEGRATION_TEST_PATH}${MODEL_COMMAND} ${TEST_CASE_COMMAND}

.PHONY: testunit
testunit:
	$(PYTHON) -m pytest test/unit

.PHONY: smoketest
smoketest:
	$(PYTHON) -m pytest -m smoke test/integration --disable-warnings