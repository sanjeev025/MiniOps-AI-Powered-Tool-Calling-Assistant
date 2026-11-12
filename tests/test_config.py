import os
import subprocess

import pytest
from config.export_env import render
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
    # Configured model is used as-is (default here), never silently swapped
    assert env_vars["HERMES_MODEL"] == "gpt-4o-mini"


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


def test_groq_keeps_configured_llama_model(monkeypatch):
    """llama-3.3-70b-versatile (recommended in older docs) is no longer swapped out."""
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.setenv("LLM_MODEL", "llama-3.3-70b-versatile")
    cfg = Settings(_env_file=None)
    assert cfg.hermes_env_vars["HERMES_MODEL"] == "llama-3.3-70b-versatile"
    assert "llama-3.3-70b-versatile" in cfg.hermes_cli_args


def test_cli_args_never_contain_secrets(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.setenv("GROQ_API_KEY", "gsk_secret_value")
    cfg = Settings(_env_file=None)
    args = cfg.hermes_cli_args
    assert "--api-key" not in args
    assert "gsk_secret_value" not in args
    assert args[:2] == ["--provider", "custom"]
    assert args[args.index("--base-url") + 1] == "https://api.groq.com/openai/v1"


def test_utcp_manual_url_exported(monkeypatch):
    monkeypatch.setenv("DEMO_API_PORT", "9123")
    cfg = Settings(_env_file=None)
    assert cfg.hermes_env_vars["UTCP_MANUAL_URL"] == "http://127.0.0.1:9123/utcp"

    monkeypatch.setenv("UTCP_MANUAL_URL", "http://ops.internal/utcp")
    assert Settings(_env_file=None).hermes_env_vars["UTCP_MANUAL_URL"] == "http://ops.internal/utcp"


def test_export_env_roundtrips_through_bash(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.setenv("LLM_MODEL", "openai/gpt-oss-20b")
    monkeypatch.setenv("GROQ_API_KEY", "gsk_with'quote $x")
    script = render(Settings(_env_file=None)) + (
        '\nprintf "%s|%s|%s\\n" "$HERMES_MODEL" "$OPENAI_API_KEY" "${HERMES_CLI_ARGS[*]}"'
    )
    out = subprocess.run(["bash", "-c", script], capture_output=True, text=True,
                         env={"PATH": os.environ["PATH"]}, check=True).stdout.strip()
    model, key, args = out.split("|")
    assert model == "openai/gpt-oss-20b"
    assert key == "gsk_with'quote $x"
    assert args == "--provider custom -m openai/gpt-oss-20b --base-url https://api.groq.com/openai/v1"
