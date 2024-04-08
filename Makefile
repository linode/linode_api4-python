PYTHON ?= python3

INTEGRATION_TEST_PATH :=
TEST_CASE_COMMAND :=
MODEL_COMMAND :=

ifdef TEST_CASE
TEST_CASE_COMMAND = -k $(TEST_CASE)
endif

ifdef TEST_MODEL
MODEL_COMMAND = models/$(TEST_MODEL)
endif

@PHONEY: clean
clean:
	mkdir -p dist
	rm -r dist
	rm -f baked_version

@PHONEY: build
build: clean
	$(PYTHON) -m build  --wheel --sdist


@PHONEY: release
release: build
	$(PYTHON) -m twine upload dist/*

@PHONEY: install
install: clean requirements
	$(PYTHON) -m pip install .

@PHONEY: requirements
requirements:
	$(PYTHON) -m pip install -r requirements.txt -r requirements-dev.txt

@PHONEY: black
black:
	$(PYTHON) -m black linode_api4 test

@PHONEY: isort
isort:
	$(PYTHON) -m isort linode_api4 test

@PHONEY: autoflake
autoflake:
	$(PYTHON) -m autoflake linode_api4 test

@PHONEY: format
format: black isort autoflake

@PHONEY: lint
lint: build
	$(PYTHON) -m isort --check-only linode_api4 test
	$(PYTHON) -m autoflake --check linode_api4 test
	$(PYTHON) -m black --check --verbose linode_api4 test
	$(PYTHON) -m pylint linode_api4
	$(PYTHON) -m twine check dist/*

@PHONEY: testint
testint:
	$(PYTHON) -m pytest test/integration/${INTEGRATION_TEST_PATH}${MODEL_COMMAND} ${TEST_CASE_COMMAND}

@PHONEY: testunit
testunit:
	$(PYTHON) -m pytest test/unit

@PHONEY: smoketest
smoketest:
	$(PYTHON) -m pytest -m smoke test/integration