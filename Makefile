PYTHON ?= python3

@PHONEY: clean
clean:
	mkdir -p dist
	rm dist/*

@PHONEY: build
build: clean
	$(PYTHON) setup.py sdist
	$(PYTHON) setup.py bdist_wheel


@PHONEY: release
release: build
	twine upload dist/*

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