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
	twine upload dist/*

@PHONEY: install
install: clean
	python3 -m pip install .

@PHONEY: requirements
requirements:
	pip install -r requirements.txt -r requirements-dev.txt

@PHONEY: black
black:
	black linode_api4 test

@PHONEY: isort
isort:
	isort linode_api4 test

@PHONEY: autoflake
autoflake:
	autoflake linode_api4 test

@PHONEY: format
format: black isort autoflake

@PHONEY: lint
lint: build
	isort --check-only linode_api4 test
	autoflake --check linode_api4 test
	black --check --verbose linode_api4 test
	pylint linode_api4
	twine check dist/*

@PHONEY: testint
testint:
	python3 -m pytest test/integration/${INTEGRATION_TEST_PATH}${MODEL_COMMAND} ${TEST_CASE_COMMAND}

@PHONEY: testunit
testunit:
	python3 -m python test/unit

@PHONEY: smoketest
smoketest:
	pytest -m smoke test/integration --disable-warnings