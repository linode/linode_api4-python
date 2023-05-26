PYTHON ?= python3

INTEGRATION_TEST_PATH :=

@PHONEY: clean
clean:
	mkdir -p dist
	rm -r dist
	rm -f baked_version

@PHONEY: build
build: clean
	$(PYTHON) setup.py sdist
	$(PYTHON) setup.py bdist_wheel


@PHONEY: release
release: build
	twine upload dist/*


install: clean
	python3 setup.py install


requirements:
	pip install -r requirements.txt -r requirements-dev.txt


black:
	black linode_api4 test


isort:
	isort linode_api4 test


autoflake:
	autoflake linode_api4 test


format: black isort autoflake


lint:
	isort --check-only linode_api4 test
	autoflake --check linode_api4 test
	black --check --verbose linode_api4 test
	pylint linode_api4

@PHONEY: testint
testint:
	python3 -m pytest test/integration/
