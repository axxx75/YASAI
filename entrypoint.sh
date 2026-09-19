#!/bin/bash

cat << "EOF"
======================================================================
  🧪 YASAI LAB - Agentic Sandbox Environment
======================================================================
  ⚠️  DISCLAIMER: Ambiente di sviluppo isolato.
      Nessuno script viene eseguito automaticamente all'avvio.

  🛠️  COMANDI UTILI DISPONIBILI:

      • Agent Router (Free):     python ./agent-router/main_free.py
      • Agent Router (Paid):     python ./agent-router/main_paid.py
      • Claude Code CLI:         claude
      • OpenCode CLI:            opencode
      • Test Suite:              ./test/test-stack.sh
      • Git Status:              git status
      • Gh Status:               gh status


  📍 Workspace montato su: /workspaces ($PWD dell'host)
======================================================================
EOF

exec "$@"
