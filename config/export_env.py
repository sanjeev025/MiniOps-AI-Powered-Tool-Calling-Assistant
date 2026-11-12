"""Print shell-evaluable exports for Hermes Agent.

Usage (from bash):  eval "$(python -m config.export_env)"

Defines exported env vars plus a bash array ``HERMES_CLI_ARGS`` and a
``HERMES_DISPLAY_PROVIDER`` string. Secrets are only emitted as env vars, never as CLI args.
"""

import shlex
import sys

from config.settings import Settings


def render(cfg: Settings) -> str:
    lines = [f"export {k}={shlex.quote(v)}" for k, v in cfg.hermes_env_vars.items()]
    args = " ".join(shlex.quote(a) for a in cfg.hermes_cli_args)
    lines.append(f"HERMES_CLI_ARGS=({args})")
    lines.append(f"HERMES_DISPLAY_PROVIDER={shlex.quote(cfg.display_provider)}")
    return "\n".join(lines)


if __name__ == "__main__":
    sys.stdout.write(render(Settings()) + "\n")
