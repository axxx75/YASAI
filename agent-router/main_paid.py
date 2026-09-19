import sys
from config import (
    MEMORY_DB_PATH,
    MEMORY_MAX_CONTENT_CHARS,
    MEMORY_MAX_MESSAGES,
    MEMORY_SESSION_ID,
    ROUTER_MODEL_PAID,
    MODEL_CATALOG_PAID,
    PAID_FALLBACK_CHAIN,
)
from router import analyze_and_route
from agent_engine import run_agent_loop, call_llm_stream
from memory import ConversationStore
from schemas import TaskCategory

def main():
    memory = ConversationStore(
        MEMORY_DB_PATH,
        max_messages=MEMORY_MAX_MESSAGES,
        max_content_chars=MEMORY_MAX_CONTENT_CHARS,
    )
    session_id = memory.ensure_session(MEMORY_SESSION_ID)

    print("=" * 65)
    print("  AI LAB - Agentic CLI Engine [MODE: PAID / PRODUCTION]")
    print(f"  Primary Coding Model: {MODEL_CATALOG_PAID['coding']['model_id']}")
    print(f"  Sessione memoria: {session_id}")
    print("  Comandi: /new nuova sessione | /clear cancella memoria | exit esci")
    print("=" * 65 + "\n")

    while True:
        try:
            user_input = input("paid-agent> ").strip()
            if not user_input:
                continue
            if user_input.lower() in ["exit", "quit"]:
                sys.exit(0)
            if user_input.lower() == "/new":
                session_id = memory.new_session()
                print(f"[MEMORIA]: nuova sessione {session_id}")
                continue
            if user_input.lower() == "/clear":
                memory.clear(session_id)
                print("[MEMORIA]: cronologia cancellata.")
                continue

            conversation_context = memory.recent_context(session_id)

            # Triage su modelli Paid (GPT-4o Mini per il triage veloce ed economico)
            decision = analyze_and_route(
                user_prompt=user_input,
                router_model=ROUTER_MODEL_PAID,
                catalog=MODEL_CATALOG_PAID,
                candidate_fallback_models=PAID_FALLBACK_CHAIN,
                conversation_context=conversation_context,
            )

            print(f"\n[ROUTER PAID]: Categoria -> {decision.category.value.upper()} | Modello Target -> {decision.selected_model}")
            print(f"[ROUTER REASONING]: {decision.reasoning}")

            if decision.category in [TaskCategory.CODING, TaskCategory.REASONING]:
                response = run_agent_loop(
                    primary_model=decision.selected_model,
                    user_prompt=user_input,
                    fallback_models=PAID_FALLBACK_CHAIN,
                    conversation_context=conversation_context,
                )
            else:
                response = call_llm_stream(
                    decision.selected_model,
                    conversation_context + [{"role": "user", "content": user_input}],
                )

            if response:
                memory.append_exchange(session_id, user_input, response)

        except (KeyboardInterrupt, EOFError):
            print("\nChiusura sessione.")
            sys.exit(0)

if __name__ == "__main__":
    main()