.PHONY: lint test offline-integration integration

lint:
	ruff check .

test:
	pytest -q

offline-integration:
	pytest -m "integration and not internet" -q || true

integration:
	pytest -m "integration and internet" -q || true
