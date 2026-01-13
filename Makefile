
INDEX_URL ?= https://test.pypi.org/legacy/
USERNAME = __token__
PASSWORD ?= dummy

all: build

local_install:
	uv pip install -e '.[test]'

wheel:
	uv build --wheel
	uv build --sdist

build: wheel

publish:
	@USERNAME=$(USERNAME) PASSWORD=$(PASSWORD) INDEX_URL=$(INDEX_URL) uv publish --index $(INDEX_URL) --username $(USERNAME) --password $(PASSWORD)

test: local_install
	tox

clean:
	rm -rf dist .pytest_cache build .eggs fylearn.egg-info htmlcov .tox *.whl *~
