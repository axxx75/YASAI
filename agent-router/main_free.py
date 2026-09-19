import sys
from config import (
    MEMORY_DB_PATH,
    MEMORY_MAX_CONTENT_CHARS,
    MEMORY_MAX_MESSAGES,
    MEMORY_OWNER_ID,
    MEMORY_RETENTION_DAYS,
    MEMORY_SESSION_ID,
    ROUTER_MODEL_FREE,
    MODEL_CATALOG_FREE,
    AVAILABLE_FREE_MODELS,
)
from router import analyze_and_route
from agent_engine import run_agent_loop, call_llm_stream
from memory import ConversationStore
from schemas import TaskCategory

def main():
    if not MEMORY_OWNER_ID:
        raise RuntimeError("YASAI_MEMORY_OWNER_ID è obbligatorio per isolare le sessioni tra utenti.")
    memory = ConversationStore(
        MEMORY_DB_PATH,
        owner_id=MEMORY_OWNER_ID,
        max_messages=MEMORY_MAX_MESSAGES,
        max_content_chars=MEMORY_MAX_CONTENT_CHARS,
        retention_days=MEMORY_RETENTION_DAYS,
    )
    session_id = memory.ensure_session(MEMORY_SESSION_ID)

    print("=" * 65)
    print("  AI LAB - Agentic CLI Engine [MODE: FREE / TESTING]")
    print(f"  Modelli Free attivi nel pool: {len(AVAILABLE_FREE_MODELS)}")
    print(f"  Sessione memoria: {session_id}")
    print("  Comandi: /new nuova sessione | /clear cancella memoria | exit esci")
    print("=" * 65 + "\n")

    while True:
        try:
            user_input = input("free-agent> ").strip()
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

            # Triage su pool Free
            decision = analyze_and_route(
                user_prompt=user_input,
                router_model=ROUTER_MODEL_FREE,
                catalog=MODEL_CATALOG_FREE,
                candidate_fallback_models=AVAILABLE_FREE_MODELS,
                conversation_context=conversation_context,
            )

            print(f"\n[ROUTER FREE]: Categoria -> {decision.category.value.upper()} | Modello Target -> {decision.selected_model}")
            print(f"[ROUTER REASONING]: {decision.reasoning}")

            if decision.category in [TaskCategory.CODING, TaskCategory.REASONING]:
                response = run_agent_loop(
                    primary_model=decision.selected_model,
                    user_prompt=user_input,
                    fallback_models=AVAILABLE_FREE_MODELS,
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