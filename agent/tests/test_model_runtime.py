import pytest

from app.ai_engine.model_runtime import (
    apply_reasoning_instruction,
    build_messages,
    completion_options,
    resolve_system_runtime_config,
    validate_runtime_config,
)


def test_runtime_config_rejects_invalid_or_embedded_credentials():
    with pytest.raises(ValueError, match="http"):
        validate_runtime_config("model", "ftp://example.com/v1", "secret")
    with pytest.raises(ValueError, match="用户名"):
        validate_runtime_config("model", "https://user:pass@example.com/v1", "secret")


def test_build_messages_does_not_duplicate_latest_user_message():
    messages = build_messages(
        "同一个问题",
        [{"role": "user", "content": "同一个问题"}],
        "off",
    )
    assert messages == [{"role": "user", "content": "同一个问题"}]


def test_reasoning_instruction_reuses_existing_system_message():
    messages = apply_reasoning_instruction(
        [{"role": "system", "content": "你是助手"}, {"role": "user", "content": "分析"}],
        "high",
    )
    assert len(messages) == 2
    assert "深入" in messages[0]["content"]


def test_native_reasoning_options_cover_openai_and_qwen():
    assert completion_options("gpt-5-mini", "https://api.openai.com/v1", "medium") == {
        "reasoning_effort": "medium"
    }
    qwen_options = completion_options(
        "qwen3-plus",
        "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "high",
    )
    assert qwen_options["extra_body"]["enable_thinking"] is True
    assert qwen_options["extra_body"]["thinking_budget"] == 8192

    deepseek_options = completion_options(
        "deepseek-v4-pro",
        "https://api.deepseek.com/v1",
        "high",
    )
    assert deepseek_options == {
        "reasoning_effort": "max",
        "extra_body": {"thinking": {"type": "enabled"}},
    }


def test_system_runtime_model_override_reuses_server_credentials(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "DEEPSEEK_API_KEY", "server-secret")
    monkeypatch.setattr(settings, "DEEPSEEK_BASE_URL", "https://api.example.com/v1")
    monkeypatch.setattr(settings, "DEEPSEEK_MODEL", "deepseek-chat")

    assert resolve_system_runtime_config("deepseek-v4-pro") == (
        "deepseek-v4-pro",
        "https://api.example.com/v1",
        "server-secret",
    )
