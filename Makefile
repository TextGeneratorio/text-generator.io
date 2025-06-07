.PHONY: lint test offline-integration integration coverage install ruff-fix download-punkt

lint:
	ruff check .

test:
	pytest -q

offline-integration:
	pytest -m "integration and not internet" -q || true

integration:
	pytest -m "integration and internet" -q || true

coverage:
	pytest --cov=questions --cov-report=term-missing -q

install:
	pip install uv
	uv pip install --system -r requirements.txt -r requirements-test.txt

ruff-fix:
	ruff check --fix .

download-punkt:
	python -m nltk.downloader punkt
