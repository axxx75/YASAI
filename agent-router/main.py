import sys
import time
import json
import requests
from config import (
    OPENROUTER_API_BASE,
    OPENROUTER_API_KEY,
    DEFAULT_HEADERS,
    AVAILABLE_FREE_MODELS
)
from router import analyze_and_route

def execute_task_with_fallback(primary_model: str, prompt: str):
    """
    Esegue la richiesta in streaming col modello selezionato dal Router.
    Se il modello restituisce 429 (Rate Limit) o errori HTTP, effettua il rollover
    automatico sui modelli free alternativi.
    """
    # Ordina i modelli provando prima quello scelto dal Router, poi gli altri free attivi
    models_to_try = [primary_model] + [m for m in AVAILABLE_FREE_MODELS if m != primary_model]
    
    headers = {
        **DEFAULT_HEADERS, 
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    for model in models_to_try:
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": True
        }
        
        try:
            response = requests.post(
                f"{OPENROUTER_API_BASE}/chat/completions", 
                json=payload, 
                headers=headers, 
                stream=True, 
                timeout=30
            )
            
            if response.status_code == 429:
                print(f"\n[RATE LIMIT 429]: Modello '{model}' saturo. Rollover al modello successivo...")
                time.sleep(1)
                continue
                
            response.raise_for_status()
            
            print(f"\n--- Risposta da [{model}] ---")
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith("data: ") and not line_str.endswith("[DONE]"):
                        try:
                            chunk = json.loads(line_str[6:])
                            delta = chunk['choices'][0]['delta']
                            content = delta.get('content')
                            if content:
                                print(content, end="", flush=True)
                        except json.JSONDecodeError:
                            continue
            print("\n----------------\n")
            return  # Esecuzione completata con successo

        except requests.exceptions.HTTPError as e:
            print(f"\n[ERRORE HTTP {model}]: {e}. Prova con modello alternativo...")
            time.sleep(1)
        except Exception as e:
            print(f"\n[ERRORE IMPREVISTO {model}]: {e}")
            break

    print("\n[ERRORE FATALE]: Impossibile completare la richiesta. Tutti i modelli free sono in rate limit o non disponibili.\n")

def repl():
    """Loop REPL dell'Agentic Router."""
    print("=" * 60)
    print("  AI LAB - Agentic Router & REPL Engine initialized")
    print(f"  Modelli Free rilevati attivi: {len(AVAILABLE_FREE_MODELS)}")
    print("  Digita 'exit' o 'quit' per uscire.")
    print("=" * 60 + "\n")

    if not OPENROUTER_API_KEY:
        print("[WARNING]: OPENROUTER_API_KEY non trovata nell'ambiente!\n")

    while True:
        try:
            user_input = input("ai-agent> ").strip()
            if not user_input:
                continue
            if user_input.lower() in ["exit", "quit"]:
                print("Chiusura agent harness.")
                sys.exit(0)

            # 1. Fase di Triage / Routing
            decision = analyze_and_route(user_input)
            print(f"\n[ROUTER]: Categoria -> {decision.category.value.upper()} | Modello Target -> {decision.selected_model}")
            print(f"[ROUTER REASONING]: {decision.reasoning}")

            # 2. Esecuzione con Rollover / Fallback
            execute_task_with_fallback(decision.selected_model, user_input)

        except (KeyboardInterrupt, EOFError):
            print("\nChiusura sessione.")
            sys.exit(0)

if __name__ == "__main__":
    repl()