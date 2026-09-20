#!/usr/bin/env bash
set -e

echo "=================================================="
echo "  🚀 AI LAB SANDBOX - INTEGRATION SMOKE TEST"
echo "=================================================="
echo ""

# Color output helpers (ANSI escape sequences corrette)
GREEN='\033[1;32m'
RED='\033[1;31m'
NC='\033[0m'

pass_check() { echo -e "${GREEN}[PASS]${NC} $1"; }
fail_check() { echo -e "${RED}[FAIL]${NC} $1"; }

# 1. Verification of Binary Executables in PATH
echo "--- [1/5] Checking Tool Availability ---"
for tool in aichat litellm claude superclaude opencode openclaude pi backlog uv npm; do
  if command -v "$tool" >/dev/null 2>&1; then
    pass_check "Binary '$tool' found in PATH: $(command -v $tool)"
  else
    fail_check "Binary '$tool' missing from PATH!"
  fi
done
echo ""

# 2. Test OpenRouter & AI Chat Base Functionality
echo "--- [2/5] Testing aichat with OpenRouter ---"
if [ -z "$OPENROUTER_API_KEY" ]; then
  fail_check "OPENROUTER_API_KEY environment variable is missing or empty!"
else
  pass_check "OPENROUTER_API_KEY variable detected."
  
  echo "  -> Querying default model (Claude 3.7 via OpenRouter)..."
  RESP=$(aichat "Rispondi OK se ricevi questo messaggio." 2>&1)
  if [[ "$RESP" == *"OK"* ]] || [[ "$RESP" == *"ok"* ]]; then
    pass_check "aichat OpenRouter response received correctly!"
  else
    fail_check "aichat OpenRouter query failed! Details: $RESP"
  fi
fi
echo ""

# 3. Test Pre-baked Roles in aichat
echo "--- [3/5] Testing Pre-baked aichat Roles ---"
echo "  -> Testing 'code-expert' role..."
ROLE_CODE=$(aichat -r code-expert "Restituisci solo un commento Python #TEST_OK" 2>&1)
if [[ "$ROLE_CODE" == *"#TEST_OK"* ]]; then
  pass_check "Role 'code-expert' executed successfully."
else
  fail_check "Role 'code-expert' failed! Details: $ROLE_CODE"
fi

echo "  -> Testing 'refactor' role..."
ROLE_REF=$(aichat -r refactor "def x(): pass # clean this" 2>&1)
if [ -n "$ROLE_REF" ]; then
  pass_check "Role 'refactor' executed successfully."
else
  fail_check "Role 'refactor' returned empty output."
fi
echo ""

# 4. Test LiteLLM CLI Execution
echo "--- [4/5] Testing LiteLLM CLI ---"
LITELLM_VER=$(litellm --version 2>&1 || true)
if [ -n "$LITELLM_VER" ]; then
  pass_check "LiteLLM operational ($LITELLM_VER)"
else
  fail_check "LiteLLM failed to run."
fi
echo ""

# 5. Test Claude Code & MCP Servers Setup
echo "--- [5/5] Checking Claude Code MCP Registrations ---"
MCP_LIST=$(claude mcp list 2>&1 || true)

for mcp in "sequential-thinking" "context7" "serena" "playwright" "memory" "mattpocock-skills" "atlassian"; do
  if echo "$MCP_LIST" | grep -q "$mcp"; then
    pass_check "MCP Server '$mcp' registered."
  else
    fail_check "MCP Server '$mcp' NOT found in claude mcp list!"
  fi
done

echo ""
echo "=================================================="
echo "  ✅ ALL CHECKS COMPLETED!"
echo "=================================================="
