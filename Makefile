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
