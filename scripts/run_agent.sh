#!/usr/bin/env bash
# ==============================================================================
# MiniOps Agent Runner
# Resolves provider, model, and credentials via config/settings.py (the single
# source of truth, reading .env + shell env) and launches Hermes Agent with the
# hermes-utcp tool-calling plugin.
#
# Shell exports override .env entries, e.g.:
#   LLM_MODEL=openai/gpt-oss-20b ./scripts/run_agent.sh -q "status?"
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Pick the project venv's python if available
if [[ -x "${PROJECT_ROOT}/.venv/bin/python" ]]; then
    PY="${PROJECT_ROOT}/.venv/bin/python"
else
    PY="python3"
fi

# Export Hermes env vars and define HERMES_CLI_ARGS / HERMES_DISPLAY_PROVIDER.
# API keys are exported as env vars only — never passed on the command line.
ENV_EXPORTS="$(cd "${PROJECT_ROOT}" && "${PY}" -m config.export_env)"
eval "${ENV_EXPORTS}"

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
echo " Provider : ${HERMES_DISPLAY_PROVIDER}"
echo " Model    : ${HERMES_MODEL}"
echo " UTCP     : ${UTCP_MANUAL_URL}"
echo "=========================================================="

CLI_ARGS=("chat" "${HERMES_CLI_ARGS[@]}")

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

exec "${HERMES_BIN}" "${CLI_ARGS[@]}"
