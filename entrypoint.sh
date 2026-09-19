#!/bin/bash

cat << "EOF"
======================================================================
  🧪 YASAI LAB - Agentic Sandbox Environment
======================================================================
  ⚠️  DISCLAIMER: Ambiente di sviluppo isolato.
      Nessuno script viene eseguito automaticamente all'avvio.

  🛠️  COMANDI UTILI DISPONIBILI:

      • Agent Router (Free):     python main_free.py
      • Agent Router (Paid):     python main_paid.py
      • Claude Code CLI:         claude
      • Test Suite:              pytest
      • Git Status:              git status

  📍 Workspace montato su: /app ($PWD dell'host)
======================================================================
EOF

exec "$@"