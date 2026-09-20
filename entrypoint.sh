#!/usr/bin/env bash
set -e

cat << "EOF"
======================================================================
  🧪 YASAI LAB - Agentic Sandbox Environment
======================================================================
  ⚠️  DISCLAIMER: Ambiente di sviluppo isolato.
      Il container parte come utente non-root `dev`.

  🤖 AGENTI E ROUTER:

      Agent Router Free       python agent-router/main_free.py
      Agent Router Paid       python agent-router/main_paid.py
      Claude Code             claude
      SuperClaude             superclaude
      OpenCode                opencode
      OpenClaude              openclaude
      Pi coding agent         pi

  💬 CHAT, MODELLI E PROXY:

      aichat                  aichat
      Ruolo router            aichat -r router       (alias: ai-router)
      Ruolo code expert       aichat -r code-expert  (alias: ai-coder)
      Ruolo refactor          aichat -r refactor
      Modello rapido          ai-fast
      Modello reasoning       ai-deep
      LiteLLM proxy           litellm --config config/config_litellm.yaml

  📋 TASK E MCP:

      Inizializza backlog     backlog init "Nome progetto"
      Elenca task             backlog task list
      Board terminale         backlog board
      Istruzioni agenti       backlog instructions overview
      Server MCP Claude       claude mcp list

  🧰 TOOLCHAIN:

      Python / uv / pipx      python --version | uv --version | pipx --version
      Node.js / npm           node --version   | npm --version
      Java / Maven            java --version   | mvn --version
      Git / GitHub CLI        git --version    | gh --version
      JSON / shell tools      jq --version     | bash --version

  🔎 VERIFICA:

      Smoke test stack        ./test/test-stack.sh
      Stato repository        git status
      Modelli free attivi     python test/get_free_models.py

  📍 Workspace montato su: /workspaces ($PWD dell'host)
======================================================================
EOF

if [ "${1:-}" = "--banner-only" ]; then
    exit 0
fi

if [ "$#" -eq 0 ]; then
    set -- /bin/bash
fi

export YASAI_BANNER_SHOWN=1
exec "$@"
