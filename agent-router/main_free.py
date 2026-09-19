import sys
from config import ROUTER_MODEL_FREE, MODEL_CATALOG_FREE, AVAILABLE_FREE_MODELS
from router import analyze_and_route
from agent_engine import run_agent_loop, call_llm_stream
from schemas import TaskCategory

def main():
    print("=" * 65)
    print("  AI LAB - Agentic CLI Engine [MODE: FREE / TESTING]")
    print(f"  Modelli Free attivi nel pool: {len(AVAILABLE_FREE_MODELS)}")
    print("  Digita 'exit' o 'quit' per uscire.")
    print("=" * 65 + "\n")

    while True:
        try:
            user_input = input("free-agent> ").strip()
            if not user_input:
                continue
            if user_input.lower() in ["exit", "quit"]:
                sys.exit(0)

            # Triage su pool Free
            decision = analyze_and_route(
                user_prompt=user_input,
                router_model=ROUTER_MODEL_FREE,
                catalog=MODEL_CATALOG_FREE,
                candidate_fallback_models=AVAILABLE_FREE_MODELS
            )

            print(f"\n[ROUTER FREE]: Categoria -> {decision.category.value.upper()} | Modello Target -> {decision.selected_model}")
            print(f"[ROUTER REASONING]: {decision.reasoning}")

            if decision.category in [TaskCategory.CODING, TaskCategory.REASONING]:
                run_agent_loop(
                    primary_model=decision.selected_model,
                    user_prompt=user_input,
                    fallback_models=AVAILABLE_FREE_MODELS
                )
            else:
                call_llm_stream(decision.selected_model, [{"role": "user", "content": user_input}])

        except (KeyboardInterrupt, EOFError):
            print("\nChiusura sessione.")
            sys.exit(0)

if __name__ == "__main__":
    main()