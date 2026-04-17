"""MCP server specification helpers."""

from __future__ import annotations

import os
from collections.abc import Mapping


def resolve_env_mapping(
    direct: Mapping[str, str],
    from_env: Mapping[str, str],
) -> dict[str, str]:
    resolved = dict(direct)
    missing: list[str] = []

    for key, env_var in from_env.items():
        value = os.getenv(env_var)
        if value is None:
            missing.append(env_var)
            continue
        resolved[key] = value

    if missing:
        missing_text = ", ".join(sorted(missing))
        raise RuntimeError(f"Missing environment variables for MCP config: {missing_text}")

    return resolved
