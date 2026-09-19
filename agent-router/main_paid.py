import sys
from config import ROUTER_MODEL_PAID, MODEL_CATALOG_PAID, PAID_FALLBACK_CHAIN
from router import analyze_and_route
from agent_engine import run_agent_loop, call_llm_stream
from schemas import TaskCategory

def main():
    print("=" * 65)
    print("  AI LAB - Agentic CLI Engine [MODE: PAID / PRODUCTION]")
    print(f"  Primary Coding Model: {MODEL_CATALOG_PAID['coding']['model_id']}")
    print("  Digita 'exit' o 'quit' per uscire.")
    print("=" * 65 + "\n")

    while True:
        try:
            user_input = input("paid-agent> ").strip()
            if not user_input:
                continue
            if user_input.lower() in ["exit", "quit"]:
                sys.exit(0)

            # Triage su modelli Paid (GPT-4o Mini per il triage veloce ed economico)
            decision = analyze_and_route(
                user_prompt=user_input,
                router_model=ROUTER_MODEL_PAID,
                catalog=MODEL_CATALOG_PAID,
                candidate_fallback_models=PAID_FALLBACK_CHAIN
            )

            print(f"\n[ROUTER PAID]: Categoria -> {decision.category.value.upper()} | Modello Target -> {decision.selected_model}")
            print(f"[ROUTER REASONING]: {decision.reasoning}")

            if decision.category in [TaskCategory.CODING, TaskCategory.REASONING]:
                run_agent_loop(
                    primary_model=decision.selected_model,
                    user_prompt=user_input,
                    fallback_models=PAID_FALLBACK_CHAIN
                )
            else:
                call_llm_stream(decision.selected_model, [{"role": "user", "content": user_input}])

        except (KeyboardInterrupt, EOFError):
            print("\nChiusura sessione.")
            sys.exit(0)

if __name__ == "__main__":
    main()