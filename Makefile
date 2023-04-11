PYTHON ?= python3

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
