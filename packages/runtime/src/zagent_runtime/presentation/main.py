"""Runtime process entrypoint."""

from __future__ import annotations

from zagent_runtime.presentation.cli import app


def main() -> None:
    """Run the runtime CLI."""
    app()


if __name__ == "__main__":
    main()
