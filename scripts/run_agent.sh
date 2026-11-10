#!/usr/bin/env bash
# ==============================================================================
# MiniOps Agent Runner
# Reads provider, model, and credentials from .env and launches Hermes Agent
# with the hermes-utcp tool-calling plugin.
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
ENV_FILE="${PROJECT_ROOT}/.env"

# Preserve any variables explicitly exported in the current shell
CLI_PROVIDER="${LLM_PROVIDER:-}"
CLI_MODEL="${LLM_MODEL:-}"

# Load .env if present
if [[ -f "${ENV_FILE}" ]]; then
    set -a
    # shellcheck disable=SC1090
    source "${ENV_FILE}"
    set +a
fi

# Shell exports override .env file entries
if [[ -n "${CLI_PROVIDER}" ]]; then
    LLM_PROVIDER="${CLI_PROVIDER}"
fi
if [[ -n "${CLI_MODEL}" ]]; then
    LLM_MODEL="${CLI_MODEL}"
fi

RAW_PROVIDER="${LLM_PROVIDER:-openai-api}"
RAW_MODEL="${LLM_MODEL:-gpt-4o}"

# Portable lowercase conversion compatible with macOS default bash
PROVIDER_LOWER="$(printf '%s' "${RAW_PROVIDER}" | tr '[:upper:]' '[:lower:]')"

# Special handling for Groq LPU inference & custom OpenAI-compatible endpoints
# Note: Hermes must use --provider custom when routing to Groq so it uses standard
# /chat/completions without proprietary OpenAI extensions (like 'include' field) that Groq rejects.
if [[ "${PROVIDER_LOWER}" == "groq" || "${PROVIDER_LOWER}" == "groq-api" ]]; then
    EFFECTIVE_PROVIDER="custom"
    EFFECTIVE_MODEL="${RAW_MODEL}"
    if [[ "${EFFECTIVE_MODEL}" == "gpt-4o" || "${EFFECTIVE_MODEL}" == "gpt-4o-mini" || "${EFFECTIVE_MODEL}" == "llama-3.3-70b-versatile" ]]; then
        EFFECTIVE_MODEL="openai/gpt-oss-120b"
    fi
    EFFECTIVE_BASE_URL="${GROQ_BASE_URL:-https://api.groq.com/openai/v1}"
    EFFECTIVE_API_KEY="${GROQ_API_KEY:-${OPENAI_API_KEY:-}}"
    DISPLAY_PROVIDER="groq (via ${EFFECTIVE_BASE_URL} as custom endpoint)"
elif [[ "${PROVIDER_LOWER}" == "custom" ]]; then
    EFFECTIVE_PROVIDER="custom"
    EFFECTIVE_MODEL="${RAW_MODEL}"
    EFFECTIVE_BASE_URL="${OPENAI_BASE_URL:-${GROQ_BASE_URL:-}}"
    EFFECTIVE_API_KEY="${OPENAI_API_KEY:-${GROQ_API_KEY:-}}"
    DISPLAY_PROVIDER="custom (${EFFECTIVE_BASE_URL})"
elif [[ "${PROVIDER_LOWER}" == "openai-api" && -n "${OPENAI_BASE_URL:-}" ]]; then
    EFFECTIVE_PROVIDER="custom"
    EFFECTIVE_MODEL="${RAW_MODEL}"
    EFFECTIVE_BASE_URL="${OPENAI_BASE_URL}"
    EFFECTIVE_API_KEY="${OPENAI_API_KEY:-}"
    DISPLAY_PROVIDER="custom (${EFFECTIVE_BASE_URL})"
else
    EFFECTIVE_PROVIDER="${RAW_PROVIDER}"
    EFFECTIVE_MODEL="${RAW_MODEL}"
    EFFECTIVE_BASE_URL="${OPENAI_BASE_URL:-}"
    EFFECTIVE_API_KEY="${OPENAI_API_KEY:-}"
    DISPLAY_PROVIDER="${EFFECTIVE_PROVIDER}"
fi

# Export canonical Hermes environment variables
export HERMES_INFERENCE_PROVIDER="${EFFECTIVE_PROVIDER}"
export HERMES_MODEL="${EFFECTIVE_MODEL}"
export HERMES_INFERENCE_MODEL="${EFFECTIVE_MODEL}"
if [[ -n "${EFFECTIVE_BASE_URL:-}" ]]; then
    export OPENAI_BASE_URL="${EFFECTIVE_BASE_URL}"
fi
if [[ -n "${EFFECTIVE_API_KEY:-}" ]]; then
    export OPENAI_API_KEY="${EFFECTIVE_API_KEY}"
fi

# Forward Langfuse credentials to Hermes if set
if [[ -n "${LANGFUSE_PUBLIC_KEY:-}" ]]; then
    export HERMES_LANGFUSE_PUBLIC_KEY="${LANGFUSE_PUBLIC_KEY}"
fi
if [[ -n "${LANGFUSE_SECRET_KEY:-}" ]]; then
    export HERMES_LANGFUSE_SECRET_KEY="${LANGFUSE_SECRET_KEY}"
fi
if [[ -n "${LANGFUSE_BASE_URL:-}" ]]; then
    export HERMES_LANGFUSE_BASE_URL="${LANGFUSE_BASE_URL}"
fi

# Locate hermes binary
HERMES_BIN="${HOME}/.local/bin/hermes"
if ! command -v "${HERMES_BIN}" &>/dev/null; then
    if command -v hermes &>/dev/null; then
        HERMES_BIN="hermes"
    else
        echo "Error: hermes CLI not found at ${HERMES_BIN} or in PATH."
        echo "Please install Hermes Agent using the official installer."
        exit 1
    fi
fi

# Ensure hermes-utcp plugin is installed and enabled
if [[ ! -d "${HOME}/.hermes/plugins/hermes-utcp" ]]; then
    echo "==> hermes-utcp plugin not found in ~/.hermes/plugins. Installing..."
    "${SCRIPT_DIR}/install_plugin.sh"
    "${HERMES_BIN}" plugins enable hermes-utcp || true
fi

echo "=========================================================="
echo " Starting MiniOps Agent (Hermes + UTCP + Langfuse)"
echo " Provider : ${DISPLAY_PROVIDER}"
echo " Model    : ${EFFECTIVE_MODEL}"
echo "=========================================================="

# Assemble CLI arguments for Hermes chat
CLI_ARGS=("chat" "--provider" "${EFFECTIVE_PROVIDER}" "-m" "${EFFECTIVE_MODEL}")

if [[ -n "${EFFECTIVE_BASE_URL:-}" ]]; then
    CLI_ARGS+=("--base-url" "${EFFECTIVE_BASE_URL}")
fi

if [[ -n "${EFFECTIVE_API_KEY:-}" ]]; then
    CLI_ARGS+=("--api-key" "${EFFECTIVE_API_KEY}")
fi

# Scope toolsets to MiniOps demo_ops and disable unused skills if not overridden.
# This prevents Hermes from injecting ~11,000 tokens of 21 built-in tools and 44 skills
# into the system prompt, keeping requests comfortably within Groq's 8,000 TPM rate limit.
HAS_TOOLSET_FLAG=false
for arg in "$@"; do
    if [[ "$arg" == "-t" || "$arg" == "--toolsets" ]]; then
        HAS_TOOLSET_FLAG=true
        break
    fi
done

if [[ "$HAS_TOOLSET_FLAG" == false ]]; then
    CLI_ARGS+=("-t" "demo_ops" "--skills" "")
fi

# Append any caller-supplied arguments (e.g. -q "query")
CLI_ARGS+=("$@")

# Launch Hermes chat
exec "${HERMES_BIN}" "${CLI_ARGS[@]}"
