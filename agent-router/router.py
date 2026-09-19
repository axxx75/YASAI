import json
import re
import requests
from config import (
    OPENROUTER_API_BASE,
    OPENROUTER_API_KEY,
    DEFAULT_HEADERS,
    ROUTER_MODEL,
    MODEL_CATALOG,
    AVAILABLE_FREE_MODELS
)
from schemas import RoutingDecision, TaskCategory

ROUTER_SYSTEM_PROMPT = """Sei un router di triage per task AI. Il tuo unico compito è analizzare la richiesta dell'utente e classificarla in una delle seguenti categorie:
- 'coding': scrittura codice, debugging, Containerfile/Dockerfile, Bash, Python, SQL.
- 'reasoning': architetture di sistema, logica complessa, analisi di trade-off, problemi matematici/algoritmici.
- 'general': conversazione generica, spiegazioni di concetti base, traduzioni.
- 'fast_check': domande immediate, sintassi di comandi veloci, checklist.

Rispondi ESCLUSIVAMENTE con un oggetto JSON valido con la seguente struttura:
{
  "category": "coding" | "reasoning" | "general" | "fast_check",
  "reasoning": "breve motivazione della scelta"
}
"""

def analyze_and_route(user_prompt: str) -> RoutingDecision:
    """
    Analizza il prompt dell'utente tentandolo sui modelli free disponibili.
    Esegue il parsing flessibile del JSON per evitare errori 400 dovuti a response_format non supportati.
    """
    headers = {
        **DEFAULT_HEADERS,
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    # Prova prima il ROUTER_MODEL, poi scorre gli altri modelli free come fallback
    candidate_models = [ROUTER_MODEL] + [m for m in AVAILABLE_FREE_MODELS if m != ROUTER_MODEL]

    for model in candidate_models:
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": ROUTER_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.0
        }

        try:
            res = requests.post(
                f"{OPENROUTER_API_BASE}/chat/completions",
                json=payload,
                headers=headers,
                timeout=10
            )
            res.raise_for_status()
            
            content = res.json()['choices'][0]['message']['content']
            
            # Estrazione del blocco JSON via Regex per gestire Markdown ```json ... ```
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group(0))
                category_str = parsed.get("category", "general").lower()
                
                # Mappatura della categoria identificata
                if category_str in TaskCategory.__members__.values():
                    cat_enum = TaskCategory(category_str)
                else:
                    cat_enum = TaskCategory.GENERAL

                target_model = MODEL_CATALOG.get(cat_enum.value, {}).get("model_id", model)

                return RoutingDecision(
                    category=cat_enum,
                    selected_model=target_model,
                    confidence=0.9,
                    reasoning=parsed.get("reasoning", f"Classificato via {model}")
                )
        except Exception:
            # In caso di errore (400, 429, timeout), tenta col candidato successivo
            continue

    # Fallback estremo se tutti i modelli di routing falliscono
    fallback_selected = MODEL_CATALOG["coding"]["model_id"] if MODEL_CATALOG else "openrouter/free"
    return RoutingDecision(
        category=TaskCategory.CODING,
        selected_model=fallback_selected,
        confidence=0.5,
        reasoning="Fallback deterministico: servizio di triage momentaneamente non disponibile."
    )