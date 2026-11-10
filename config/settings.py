from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Dict, Optional


class Settings(BaseSettings):
    """Application configuration loaded from environment or .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Demo API service configuration
    DEMO_API_HOST: str = "127.0.0.1"
    DEMO_API_PORT: int = 8000
    UTCP_MANUAL_URL: Optional[str] = None

    # LLM Provider & Model Selection
    # Supported providers: groq, openai-api, xai, anthropic, openrouter
    LLM_PROVIDER: str = "openai-api"
    LLM_MODEL: str = "gpt-4o-mini"

    # LLM Provider Credentials
    GROQ_API_KEY: Optional[str] = None
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"

    OPENAI_API_KEY: Optional[str] = None
    OPENAI_BASE_URL: Optional[str] = None

    XAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    OPENROUTER_API_KEY: Optional[str] = None

    # Observability credentials (Langfuse)
    LANGFUSE_PUBLIC_KEY: Optional[str] = None
    LANGFUSE_SECRET_KEY: Optional[str] = None
    LANGFUSE_BASE_URL: str = "https://cloud.langfuse.com"
    HERMES_LANGFUSE_ENV: str = "development"
    HERMES_LANGFUSE_SAMPLE_RATE: float = 1.0

    @property
    def hermes_env_vars(self) -> Dict[str, str]:
        """Return environment variables ready to export for Hermes Agent."""
        provider_lower = self.LLM_PROVIDER.lower()
        
        # When using Groq or custom base URLs, Hermes must use the "custom" provider
        # (standard chat_completions mode) to avoid proprietary OpenAI wire extensions
        # such as the 'include' field that Groq rejects with HTTP 400.
        if provider_lower in ("groq", "groq-api"):
            effective_provider = "custom"
            effective_model = (
                self.LLM_MODEL
                if self.LLM_MODEL not in ("gpt-4o", "gpt-4o-mini", "llama-3.3-70b-versatile")
                else "openai/gpt-oss-120b"
            )
            base_url = self.GROQ_BASE_URL
            api_key = self.GROQ_API_KEY or self.OPENAI_API_KEY or ""
        elif provider_lower == "custom":
            effective_provider = "custom"
            effective_model = self.LLM_MODEL
            base_url = self.OPENAI_BASE_URL or self.GROQ_BASE_URL
            api_key = self.OPENAI_API_KEY or self.GROQ_API_KEY or ""
        elif provider_lower == "openai-api" and self.OPENAI_BASE_URL:
            effective_provider = "custom"
            effective_model = self.LLM_MODEL
            base_url = self.OPENAI_BASE_URL
            api_key = self.OPENAI_API_KEY or ""
        else:
            effective_provider = self.LLM_PROVIDER
            effective_model = self.LLM_MODEL
            base_url = self.OPENAI_BASE_URL
            api_key = self.OPENAI_API_KEY or ""

        env: Dict[str, str] = {
            "HERMES_INFERENCE_PROVIDER": effective_provider,
            "HERMES_MODEL": effective_model,
            "HERMES_INFERENCE_MODEL": effective_model,
        }

        if base_url:
            env["OPENAI_BASE_URL"] = base_url
        if api_key:
            env["OPENAI_API_KEY"] = api_key
        if self.GROQ_API_KEY:
            env["GROQ_API_KEY"] = self.GROQ_API_KEY
        if self.XAI_API_KEY:
            env["XAI_API_KEY"] = self.XAI_API_KEY
        if self.ANTHROPIC_API_KEY:
            env["ANTHROPIC_API_KEY"] = self.ANTHROPIC_API_KEY
        if self.OPENROUTER_API_KEY:
            env["OPENROUTER_API_KEY"] = self.OPENROUTER_API_KEY
        if self.LANGFUSE_PUBLIC_KEY:
            env["LANGFUSE_PUBLIC_KEY"] = self.LANGFUSE_PUBLIC_KEY
            env["HERMES_LANGFUSE_PUBLIC_KEY"] = self.LANGFUSE_PUBLIC_KEY
        if self.LANGFUSE_SECRET_KEY:
            env["LANGFUSE_SECRET_KEY"] = self.LANGFUSE_SECRET_KEY
            env["HERMES_LANGFUSE_SECRET_KEY"] = self.LANGFUSE_SECRET_KEY
        if self.LANGFUSE_BASE_URL:
            env["LANGFUSE_BASE_URL"] = self.LANGFUSE_BASE_URL
            env["HERMES_LANGFUSE_BASE_URL"] = self.LANGFUSE_BASE_URL

        return env


settings = Settings()
