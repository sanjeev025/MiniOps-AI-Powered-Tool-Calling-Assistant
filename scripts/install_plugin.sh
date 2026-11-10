#!/usr/bin/env bash
# Script to install/symlink the hermes-utcp plugin into ~/.hermes/plugins/
set -euo pipefail

HERMES_PLUGINS_DIR="${HOME}/.hermes/plugins"
PLUGIN_TARGET="${HERMES_PLUGINS_DIR}/hermes-utcp"
SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/hermes_plugin"

echo "==> Installing hermes-utcp plugin"
echo "Source: ${SOURCE_DIR}"
echo "Target: ${PLUGIN_TARGET}"

mkdir -p "${HERMES_PLUGINS_DIR}"
rm -rf "${PLUGIN_TARGET}"
cp -R "${SOURCE_DIR}" "${PLUGIN_TARGET}"

echo "==> Successfully installed hermes-utcp into ${PLUGIN_TARGET}"
