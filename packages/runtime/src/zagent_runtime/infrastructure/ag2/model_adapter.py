"""AG2 model adapter."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from zagent_runtime.application.runtime_context import RuntimeContext
from zagent_runtime.domain.model import ModelProvider
from zagent_runtime.infrastructure.tools.base import ToolBackend
from zagent_runtime.infrastructure.tools.registry import ToolRegistry


@dataclass(frozen=True, slots=True)
class Ag2LlmConfigSpec:
    config_list: dict[str, Any]


class Ag2ModelConfigBuilder:
    def build(self, context: RuntimeContext, tool_registry: ToolRegistry) -> Ag2LlmConfigSpec:
        model = context.run_spec.model
        if model.provider is not ModelProvider.OPENAI_COMPATIBLE:
            raise ValueError(f"Unsupported AG2 model provider: {model.provider}")

        ag2_native_tools = tool_registry.backend_names(ToolBackend.AG2_NATIVE)
        payload: dict[str, Any] = {
            "model": model.model,
            "api_key": os.getenv(model.api_key_env),
        }

        if ag2_native_tools:
            payload["api_type"] = "responses_v2"
            payload["built_in_tools"] = list(ag2_native_tools)
            payload["workspace_dir"] = str(context.paths.workspace)
        else:
            payload["api_type"] = "openai"

        if model.api_base:
            payload["base_url"] = model.api_base

        return Ag2LlmConfigSpec(config_list=payload)
