.PHONY: sync lint test

sync:
	uv sync --all-packages --group dev

lint:
	uv run --all-packages ruff check .
	uv run --all-packages mypy packages/runtime/src packages/launcher/src

test:
	uv run --all-packages pytest
