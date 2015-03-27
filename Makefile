all:
	@echo "test         - run test commands"
	@echo "build        - build dist files"
	@echo "build-docs   - build documentation"
	@echo "publish      - publish built files"
	@echo "clean        - get rid of spare files"

test:
	py.test tests ogitm README.rst docs/source/

build: *.tar.gz *.whl

*.tar.gz: $(shell find ogitm)
	python setup.py sdist

*.whl: $(shell find ogitm)
	python setup.py bdist_wheel

build-docs:
	cd docs && make html

publish:
	twine upload dist/*

clean:
	python setup.py clean
	rm -rf dist build *.egg-info
	rm .coverage
	cd docs && rm -rf build

.PHONY: test build-docs publish clean
