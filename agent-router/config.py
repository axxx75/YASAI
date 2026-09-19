import os
import requests

OPENROUTER_API_BASE = "https://openrouter.ai/api/v1"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

DEFAULT_HEADERS = {
    "HTTP-Referer": "https://github.com/ai-lab-sandbox",
    "X-Title": "AI Lab Agentic Router"
}

def fetch_free_models() -> list[str]:
    """Interroga OpenRouter per recuperare l'elenco aggiornato dei modelli free."""
    url = f"{OPENROUTER_API_BASE}/models"
    try:
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        data = res.json().get("data", [])

        free_models = [
            m["id"] for m in data
            if m.get("pricing", {}).get("prompt") == "0"
            and m.get("pricing", {}).get("completion") == "0"
        ]
        return free_models
    except Exception as e:
        print(f"[WARNING]: Impossibile recuperare modelli dinamici: {e}")
        return []

# Dynamic Model Discovery
AVAILABLE_FREE_MODELS = fetch_free_models()

# Fallback se la chiamata di discovery fallisce
FALLBACK_MODEL = "openrouter/free"

# Assegnazione dinamica basata sui modelli attualmente online
def select_model_by_keyword(keywords: list[str], default: str) -> str:
    for m in AVAILABLE_FREE_MODELS:
        if any(kw in m.lower() for kw in keywords):
            return m
    return default if default in AVAILABLE_FREE_MODELS else (AVAILABLE_FREE_MODELS[0] if AVAILABLE_FREE_MODELS else FALLBACK_MODEL)

# Router Model (un modello flash/mini veloce per il triage)
ROUTER_MODEL = select_model_by_keyword(["flash", "mini", "small"], FALLBACK_MODEL)

# Catalog Modelli dinamico
MODEL_CATALOG = {
    "coding": {
        "model_id": select_model_by_keyword(["code", "qwen", "gemma"], ROUTER_MODEL),
        "description": "Ottimizzato per scrittura codice e debugging"
    },
    "reasoning": {
        "model_id": select_model_by_keyword(["deepseek", "nemotron", "reasoning"], ROUTER_MODEL),
        "description": "Ottimizzato per logica di sistema e architettura"
    },
    "general": {
        "model_id": select_model_by_keyword(["gemma", "nemotron", "glm"], ROUTER_MODEL),
        "description": "Conversazione generica e sintesi"
    },
    "fast_check": {
        "model_id": ROUTER_MODEL,
        "description": "Check sintetici rapidi e task veloci"
    }
}