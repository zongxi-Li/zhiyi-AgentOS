"""Application runtime wiring for AgentOS execution adapters."""

from __future__ import annotations

import logging
from typing import Any, Dict

from agentos.core.models.types import WorkflowDefinition
from agentos.core.runtime import WorkflowRuntime, build_default_runtime as build_core_default_runtime

from app.execution.langgraph_adapter import LangGraphAdapter
from app.execution.langgraph_registry import get_default_langgraph_registry

logger = logging.getLogger(__name__)


def build_langgraph_adapter(
    *,
    runtime: Any,
    workflow: WorkflowDefinition,
    implementation_id: str,
):
    return LangGraphAdapter(
        runtime=runtime,
        implementation_id=implementation_id,
        registry=get_default_langgraph_registry(),
    )


class _GatewayIntentLLM:
    """把 app 层 LLM 网关适配为规划器意图解析所需的 IntentLLM 接口。

    让认知规划引擎的意图解析走真实 DeepSeek；网关本身在 key 缺失或
    调用失败时回落 mock，规划器再在异常时回落启发式，多层兜底不阻断规划。
    """

    def generate_json(self, prompt: str, schema: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        from app.llm.gateway import get_llm_gateway

        return get_llm_gateway().generate_json(prompt, schema, **kwargs)


def configure_execution_adapters(runtime: WorkflowRuntime) -> WorkflowRuntime:
    runtime.register_execution_adapter("langgraph", build_langgraph_adapter)
    # 注入真实 LLM 意图解析（规划器认知决策走 DeepSeek）。
    try:
        runtime.set_intent_llm(_GatewayIntentLLM())
    except Exception as exc:  # 容错：注入失败不应阻断运行时构建
        logger.warning("Failed to wire intent LLM into planning engine: %s", exc)
    return runtime


def build_default_runtime() -> WorkflowRuntime:
    return configure_execution_adapters(build_core_default_runtime())
