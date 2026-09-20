#!/usr/bin/env bash
set -e

GREEN='\033[1;32m'
RED='\033[1;31m'
NC='\033[0m'
FAILURES=0

pass_check() { echo -e "${GREEN}[PASS]${NC} $1"; }
fail_check() {
  echo -e "${RED}[FAIL]${NC} $1"
  FAILURES=$((FAILURES + 1))
}

echo "=================================================="
echo "  🚀 AI LAB SANDBOX - INTEGRATION SMOKE TEST"
echo "=================================================="
echo ""

if [ ! -f /.dockerenv ] && [ ! -f /run/.containerenv ]; then
  fail_check "Questo smoke test deve essere eseguito dentro il container YASAI."
  echo ""
  echo "Entra nel laboratorio e rilancia il test:"
  echo "  lab"
  echo "  ./test/test-stack.sh"
  echo ""
  echo "Oppure eseguilo direttamente dall'host:"
  echo "  docker exec -it -w /workspaces yasai ./test/test-stack.sh"
  exit 2
fi

# 1. Verification of Binary Executables in PATH
echo "--- [1/5] Checking Tool Availability ---"
MISSING_TOOLS=0
for tool in aichat litellm claude superclaude opencode openclaude pi backlog uv npm; do
  if command -v "$tool" >/dev/null 2>&1; then
    pass_check "Binary '$tool' found in PATH: $(command -v "$tool")"
  else
    fail_check "Binary '$tool' missing from PATH!"
    MISSING_TOOLS=$((MISSING_TOOLS + 1))
  fi
done
echo ""

if [ "$MISSING_TOOLS" -gt 0 ]; then
  fail_check "Impossibile continuare: mancano $MISSING_TOOLS binari richiesti nel container."
  exit 1
fi

# 2. Test OpenRouter & AI Chat Base Functionality
echo "--- [2/5] Testing aichat with OpenRouter ---"
if [ -z "$OPENROUTER_API_KEY" ]; then
  fail_check "OPENROUTER_API_KEY environment variable is missing or empty!"
else
  pass_check "OPENROUTER_API_KEY variable detected."

  echo "  -> Querying the configured default model via OpenRouter..."
  if RESP=$(aichat "Rispondi OK se ricevi questo messaggio." 2>&1) \
    && { [[ "$RESP" == *"OK"* ]] || [[ "$RESP" == *"ok"* ]]; }; then
    pass_check "aichat OpenRouter response received correctly!"
  else
    fail_check "aichat OpenRouter query failed! Details: $RESP"
  fi
fi
echo ""

# 3. Test Pre-baked Roles in aichat
echo "--- [3/5] Testing Pre-baked aichat Roles ---"
echo "  -> Testing 'code-expert' role..."
if ROLE_CODE=$(aichat -r code-expert "Restituisci solo un commento Python #TEST_OK" 2>&1) \
  && [[ "$ROLE_CODE" == *"#TEST_OK"* ]]; then
  pass_check "Role 'code-expert' executed successfully."
else
  fail_check "Role 'code-expert' failed! Details: $ROLE_CODE"
fi

echo "  -> Testing 'refactor' role..."
if ROLE_REF=$(aichat -r refactor "def x(): pass # clean this" 2>&1) \
  && [ -n "$ROLE_REF" ]; then
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
if [ "$FAILURES" -eq 0 ]; then
  echo "  ✅ ALL CHECKS PASSED!"
else
  echo "  ❌ CHECKS COMPLETED WITH $FAILURES FAILURE(S)"
fi
echo "=================================================="

if [ "$FAILURES" -gt 0 ]; then
  exit 1
fi
