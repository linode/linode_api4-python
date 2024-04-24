PYTHON ?= python3

TEST_CASE_COMMAND :=
TEST_SUITE :=

LINODE_SDK_VERSION ?= "0.0.0.dev"
VERSION_MODULE_DOCSTRING ?= \"\"\"\nThe version of this linode_api4 package.\n\"\"\"\n\n
VERSION_FILE := ./linode_api4/version.py

ifdef TEST_CASE
    TEST_CASE_COMMAND = -k $(TEST_CASE)
endif

ifdef TEST_SUITE
    ifneq ($(TEST_SUITE),linode_client)
        TEST_COMMAND = models/$(TEST_SUITE)
    else
        TEST_COMMAND = linode_client
    endif
endif

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

.PHONY: testint
testint:
	$(PYTHON) -m pytest test/integration/${TEST_COMMAND} ${TEST_CASE_COMMAND}

.PHONY: testunit
testunit:
	$(PYTHON) -m pytest test/unit

.PHONY: smoketest
smoketest:
	$(PYTHON) -m pytest -m smoke test/integration