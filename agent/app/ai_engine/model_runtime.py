"""Per-request OpenAI-compatible model execution."""
from __future__ import annotations

from typing import AsyncIterator, Dict, List, Optional
from urllib.parse import urlparse

from openai import AsyncOpenAI


REASONING_INSTRUCTIONS = {
    "low": "简短思考后直接回答，优先速度，只保留必要的核验。",
    "medium": "先分析关键条件并核验结论，再给出结构清晰的回答。",
    "high": "进行深入、全面的分析，检查边界条件和潜在反例后再回答。",
}


def validate_runtime_config(model: str, base_url: str, api_key: str) -> None:
    if not model.strip() or not base_url.strip() or not api_key.strip():
        raise ValueError("模型、API 地址和 API Key 均不能为空")
    parsed = urlparse(base_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("API 地址必须是有效的 http:// 或 https:// 地址")
    if parsed.username or parsed.password:
        raise ValueError("API 地址不能包含用户名或密码")


def apply_reasoning_instruction(messages: List[Dict[str, str]], effort: str) -> List[Dict[str, str]]:
    instruction = REASONING_INSTRUCTIONS.get(effort)
    if not instruction:
        return messages
    result = [dict(message) for message in messages]
    for message in result:
        if message.get("role") == "system":
            message["content"] = f"{message.get('content', '')}\n\n回答策略：{instruction}".strip()
            return result
    return [{"role": "system", "content": f"回答策略：{instruction}"}, *result]


def build_messages(
    text: str,
    context: Optional[List[Dict[str, str]]],
    reasoning_effort: str,
) -> List[Dict[str, str]]:
    messages = [
        {"role": item["role"], "content": item["content"]}
        for item in (context or [])
        if item.get("role") in {"system", "user", "assistant"} and item.get("content")
    ]
    if not messages or messages[-1].get("role") != "user" or messages[-1].get("content") != text:
        messages.append({"role": "user", "content": text})
    return apply_reasoning_instruction(messages, reasoning_effort)


def completion_options(model: str, base_url: str, reasoning_effort: str) -> Dict:
    normalized_model = model.lower()
    is_deepseek_v4 = normalized_model.startswith("deepseek-v4")
    if reasoning_effort == "off":
        if "dashscope.aliyuncs.com" in base_url and "qwen3" in model.lower():
            return {"extra_body": {"enable_thinking": False}}
        if is_deepseek_v4:
            return {"extra_body": {"thinking": {"type": "disabled"}}}
        return {}

    if normalized_model.startswith(("o1", "o3", "o4", "gpt-5")):
        return {"reasoning_effort": reasoning_effort}
    if is_deepseek_v4:
        return {
            "reasoning_effort": "max" if reasoning_effort == "high" else "high",
            "extra_body": {"thinking": {"type": "enabled"}},
        }
    if "dashscope.aliyuncs.com" in base_url and "qwen3" in normalized_model:
        budgets = {"low": 1024, "medium": 4096, "high": 8192}
        return {
            "extra_body": {
                "enable_thinking": True,
                "thinking_budget": budgets.get(reasoning_effort, 4096),
            }
        }
    return {}


async def generate_with_runtime_model(
    *,
    text: str,
    context: Optional[List[Dict[str, str]]],
    model: str,
    base_url: str,
    api_key: str,
    reasoning_effort: str = "off",
) -> Dict:
    validate_runtime_config(model, base_url, api_key)
    client = AsyncOpenAI(api_key=api_key, base_url=base_url.rstrip("/"))
    try:
        response = await client.chat.completions.create(
            model=model,
            messages=build_messages(text, context, reasoning_effort),
            **completion_options(model, base_url, reasoning_effort),
        )
        content = response.choices[0].message.content if response.choices else ""
        return {
            "text": content or "",
            "confidence": 0.95,
            "tokens_used": response.usage.total_tokens if response.usage else 0,
            "model": model,
        }
    finally:
        await client.close()


async def stream_with_runtime_model(
    *,
    text: str,
    context: Optional[List[Dict[str, str]]],
    model: str,
    base_url: str,
    api_key: str,
    reasoning_effort: str = "off",
) -> AsyncIterator[str]:
    validate_runtime_config(model, base_url, api_key)
    client = AsyncOpenAI(api_key=api_key, base_url=base_url.rstrip("/"))
    try:
        stream = await client.chat.completions.create(
            model=model,
            messages=build_messages(text, context, reasoning_effort),
            stream=True,
            **completion_options(model, base_url, reasoning_effort),
        )
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    finally:
        await client.close()
