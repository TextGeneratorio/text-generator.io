.PHONY: lint test test-main test-inference offline-integration integration coverage install ruff-fix download-punkt

lint:
	ruff check .

test:
	pytest -q

test-main:
	pytest -q -m "not inference"

test-inference:
	pytest -q -m "inference"

offline-integration:
	pytest -m "integration and not internet and not inference" -q || true

integration:
	pytest -m "integration and internet and not inference" -q || true

coverage:
	pytest --cov=questions --cov-report=term-missing -q

install:
	pip install uv
	uv pip install --system -r requirements.txt -r requirements-test.txt

ruff-fix:
	ruff check --fix .

download-punkt:
	python -m nltk.downloader punkt
