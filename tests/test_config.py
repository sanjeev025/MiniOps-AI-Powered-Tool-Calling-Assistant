import pytest
from config.settings import Settings
from hermes_plugin.tools import get_active_llm_info


def test_default_llm_settings():
    """Verify default settings fallback to OpenAI GPT-4o-mini when no env is provided."""
    cfg = Settings(_env_file=None)
    assert cfg.LLM_PROVIDER == "openai-api"
    assert cfg.LLM_MODEL == "gpt-4o-mini"
    env_vars = cfg.hermes_env_vars
    assert env_vars["HERMES_INFERENCE_PROVIDER"] == "openai-api"
    assert env_vars["HERMES_MODEL"] == "gpt-4o-mini"


def test_groq_settings(monkeypatch):
    """Verify Groq provider configuration via env vars."""
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.setenv("GROQ_API_KEY", "gsk_test_key_123")

    cfg = Settings(_env_file=None)
    assert cfg.LLM_PROVIDER == "groq"
    assert cfg.GROQ_API_KEY == "gsk_test_key_123"

    env_vars = cfg.hermes_env_vars
    # Groq connects through custom OpenAI-compatible endpoint
    assert env_vars["HERMES_INFERENCE_PROVIDER"] == "custom"
    assert env_vars["OPENAI_BASE_URL"] == "https://api.groq.com/openai/v1"
    assert env_vars["OPENAI_API_KEY"] == "gsk_test_key_123"
    assert env_vars["HERMES_MODEL"] == "openai/gpt-oss-120b"


def test_groq_custom_model_settings(monkeypatch):
    """Verify Groq with an explicit model selection."""
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.setenv("LLM_MODEL", "qwen-2.5-32b")
    monkeypatch.setenv("GROQ_API_KEY", "gsk_test_key_456")

    cfg = Settings(_env_file=None)
    assert cfg.LLM_PROVIDER == "groq"
    assert cfg.LLM_MODEL == "qwen-2.5-32b"

    env_vars = cfg.hermes_env_vars
    assert env_vars["HERMES_INFERENCE_PROVIDER"] == "custom"
    assert env_vars["OPENAI_BASE_URL"] == "https://api.groq.com/openai/v1"
    assert env_vars["OPENAI_API_KEY"] == "gsk_test_key_456"
    assert env_vars["HERMES_MODEL"] == "qwen-2.5-32b"


def test_custom_xai_grok_settings(monkeypatch):
    """Verify xAI Grok provider and model configuration via env vars."""
    monkeypatch.setenv("LLM_PROVIDER", "xai")
    monkeypatch.setenv("LLM_MODEL", "grok-2")
    monkeypatch.setenv("XAI_API_KEY", "xai-test-key-123")

    cfg = Settings(_env_file=None)
    assert cfg.LLM_PROVIDER == "xai"
    assert cfg.LLM_MODEL == "grok-2"
    assert cfg.XAI_API_KEY == "xai-test-key-123"

    env_vars = cfg.hermes_env_vars
    assert env_vars["HERMES_INFERENCE_PROVIDER"] == "xai"
    assert env_vars["HERMES_MODEL"] == "grok-2"
    assert env_vars["XAI_API_KEY"] == "xai-test-key-123"


def test_anthropic_settings(monkeypatch):
    """Verify Anthropic provider and model configuration via env vars."""
    monkeypatch.setenv("LLM_PROVIDER", "anthropic")
    monkeypatch.setenv("LLM_MODEL", "claude-sonnet-4-6")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-key")

    cfg = Settings(_env_file=None)
    assert cfg.LLM_PROVIDER == "anthropic"
    assert cfg.LLM_MODEL == "claude-sonnet-4-6"
    assert cfg.ANTHROPIC_API_KEY == "sk-ant-test-key"

    env_vars = cfg.hermes_env_vars
    assert env_vars["HERMES_INFERENCE_PROVIDER"] == "anthropic"
    assert env_vars["HERMES_MODEL"] == "claude-sonnet-4-6"
    assert env_vars["ANTHROPIC_API_KEY"] == "sk-ant-test-key"


def test_plugin_get_active_llm_info(monkeypatch):
    """Verify hermes_plugin.tools.get_active_llm_info reflects current environment."""
    monkeypatch.setenv("HERMES_INFERENCE_PROVIDER", "groq")
    monkeypatch.setenv("HERMES_MODEL", "llama-3.3-70b-versatile")

    info = get_active_llm_info()
    assert info["provider"] == "groq"
    assert info["model"] == "llama-3.3-70b-versatile"
