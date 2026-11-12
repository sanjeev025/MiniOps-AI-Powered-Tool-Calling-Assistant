from typing import Dict, List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment or .env.

    This is the single source of truth for provider/model mapping. ``scripts/run_agent.sh``
    consumes it via ``python -m config.export_env``.
    """

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
    # Supported providers: groq, custom, openai-api, xai, anthropic, openrouter
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
    def utcp_manual_url(self) -> str:
        return self.UTCP_MANUAL_URL or f"http://{self.DEMO_API_HOST}:{self.DEMO_API_PORT}/utcp"

    def _resolve_inference(self) -> Dict[str, Optional[str]]:
        """Map LLM_PROVIDER to the provider/base_url/api_key Hermes should use.

        Groq and custom OpenAI-compatible endpoints go through Hermes' "custom" provider
        (plain /chat/completions) so proprietary OpenAI fields like 'include' aren't sent.
        The configured LLM_MODEL is always used as-is.
        """
        provider = self.LLM_PROVIDER.lower()
        if provider in ("groq", "groq-api"):
            return {
                "provider": "custom",
                "display": f"groq (via {self.GROQ_BASE_URL} as custom endpoint)",
                "base_url": self.GROQ_BASE_URL,
                "api_key": self.GROQ_API_KEY or self.OPENAI_API_KEY,
            }
        if provider == "custom" or (provider == "openai-api" and self.OPENAI_BASE_URL):
            base_url = self.OPENAI_BASE_URL or self.GROQ_BASE_URL
            return {
                "provider": "custom",
                "display": f"custom ({base_url})",
                "base_url": base_url,
                "api_key": self.OPENAI_API_KEY or self.GROQ_API_KEY,
            }
        return {
            "provider": self.LLM_PROVIDER,
            "display": self.LLM_PROVIDER,
            "base_url": self.OPENAI_BASE_URL,
            "api_key": self.OPENAI_API_KEY,
        }

    @property
    def display_provider(self) -> str:
        return self._resolve_inference()["display"] or self.LLM_PROVIDER

    @property
    def hermes_env_vars(self) -> Dict[str, str]:
        """Return environment variables ready to export for Hermes Agent."""
        inf = self._resolve_inference()
        env: Dict[str, str] = {
            "HERMES_INFERENCE_PROVIDER": inf["provider"],
            "HERMES_MODEL": self.LLM_MODEL,
            "HERMES_INFERENCE_MODEL": self.LLM_MODEL,
            "UTCP_MANUAL_URL": self.utcp_manual_url,
            "HERMES_LANGFUSE_ENV": self.HERMES_LANGFUSE_ENV,
            "HERMES_LANGFUSE_SAMPLE_RATE": str(self.HERMES_LANGFUSE_SAMPLE_RATE),
        }

        if inf["base_url"]:
            env["OPENAI_BASE_URL"] = inf["base_url"].rstrip("/")
        if inf["api_key"]:
            env["OPENAI_API_KEY"] = inf["api_key"]

        optional = {
            "GROQ_API_KEY": self.GROQ_API_KEY,
            "XAI_API_KEY": self.XAI_API_KEY,
            "ANTHROPIC_API_KEY": self.ANTHROPIC_API_KEY,
            "OPENROUTER_API_KEY": self.OPENROUTER_API_KEY,
        }
        env.update({k: v for k, v in optional.items() if v})

        for suffix, value in (
            ("PUBLIC_KEY", self.LANGFUSE_PUBLIC_KEY),
            ("SECRET_KEY", self.LANGFUSE_SECRET_KEY),
            ("BASE_URL", self.LANGFUSE_BASE_URL),
        ):
            if value:
                env[f"LANGFUSE_{suffix}"] = value
                env[f"HERMES_LANGFUSE_{suffix}"] = value

        return env

    @property
    def hermes_cli_args(self) -> List[str]:
        """CLI args for ``hermes chat``. Secrets are never included: keys travel via env only."""
        inf = self._resolve_inference()
        args = ["--provider", inf["provider"], "-m", self.LLM_MODEL]
        if inf["base_url"]:
            args += ["--base-url", inf["base_url"].rstrip("/")]
        return args


settings = Settings()
