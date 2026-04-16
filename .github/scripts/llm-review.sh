#!/bin/bash
set -e
MODEL="${LLM_MODEL:-minimax/minimax-m2.7}"
OPENROUTER_API_KEY="${OPENROUTER_API_KEY:-}"
OUTPUT_DIR=".llm-review"
mkdir -p "$OUTPUT_DIR"
echo "🤖 LLM Code Review..."
if [ -z "$OPENROUTER_API_KEY" ]; then echo "❌ OPENROUTER_API_KEY fehlt"; exit 1; fi
BRANCH="${{ github.head_ref }}"
BASE="${{ github.base_ref }}"
DIFF=$(git diff origin/$BASE..$BRANCH -- . ':!node_modules' ':!.next' 2>/dev/null | head -8000)
PROMPT="Du bist Senior Code Reviewer. Analysiere PR:
VOTE: APPROVE / REQUEST_CHANGES / REJECT
SECURITY: ✅ / ⚠️ / ❌
TESTS: ✅ / ⚠️ / ❌
Gib strukturierte Antwort mit: VOTE, ZUSAMMENFASSUNG, CRITICAL ISSUES, MINOR ISSUES, POSITIVE POINTS, FINAL VERDICT
DIFF: $DIFF"
RESP=$(curl -s -X POST "https://openrouter.ai/api/v1/chat/completions" \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"model\":\"$MODEL\",\"messages\":[{\"role\":\"user\",\"content\":$(echo "$PROMPT" | jq -Rs .)}],\"temperature\":0.3,\"max_tokens\":3000}")
if echo "$RESP" | jq -e '.choices[0].message.content' >/dev/null 2>&1; then
    echo "$RESP" | jq -r '.choices[0].message.content' > "$OUTPUT_DIR/report.md"
    echo "✅ Review done"
    if echo "$RESP" | grep -qi "REQUEST_CHANGES\|REJECT"; then echo "blocked" > "$OUTPUT_DIR/blocked"; fi
else echo "## ❌ LLM Error" > "$OUTPUT_DIR/report.md"; fi
