"""Security policy errors."""

from __future__ import annotations


class PolicyViolationError(Exception):
    """Raised when a runtime policy blocks an operation."""
