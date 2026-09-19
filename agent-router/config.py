import os
import requests

OPENROUTER_API_BASE = "https://openrouter.ai/api/v1"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

DEFAULT_HEADERS = {
    "HTTP-Referer": "https://github.com/ai-lab-sandbox",
    "X-Title": "AI Lab Agentic Router"
}

MEMORY_DB_PATH = os.getenv(
    "YASAI_MEMORY_DB_PATH",
    "~/.local/share/yasai/conversations.db",
)
MEMORY_MAX_MESSAGES = int(os.getenv("YASAI_MEMORY_MAX_MESSAGES", "20"))
MEMORY_MAX_CONTENT_CHARS = int(os.getenv("YASAI_MEMORY_MAX_CONTENT_CHARS", "20000"))
MEMORY_RETENTION_DAYS = int(os.getenv("YASAI_MEMORY_RETENTION_DAYS", "30"))
MEMORY_OWNER_ID = os.getenv("YASAI_MEMORY_OWNER_ID", "").strip()
MEMORY_SESSION_ID = os.getenv("YASAI_SESSION_ID", "default").strip() or "default"

def fetch_all_models() -> list[dict]:
    """Recupera l'elenco completo dei modelli da OpenRouter."""
    url = f"{OPENROUTER_API_BASE}/models"
    try:
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        return res.json().get("data", [])
    except Exception as e:
        print(f"[WARNING]: Impossibile recuperare modelli da OpenRouter: {e}")
        return []

# Fetch iniziale di tutti i modelli
_ALL_MODELS_DATA = fetch_all_models()

# List dei modelli FREE attivi
AVAILABLE_FREE_MODELS = [
    m["id"] for m in _ALL_MODELS_DATA
    if m.get("pricing", {}).get("prompt") == "0" and m.get("pricing", {}).get("completion") == "0"
]

# Helper per selezione modello free
def select_free_model(keywords: list[str], default: str) -> str:
    for m in AVAILABLE_FREE_MODELS:
        if any(kw in m.lower() for kw in keywords):
            return m
    return default if default in AVAILABLE_FREE_MODELS else (AVAILABLE_FREE_MODELS[0] if AVAILABLE_FREE_MODELS else "openrouter/free")

# --- CATALOGO FREE ---
ROUTER_MODEL_FREE = select_free_model(["flash", "mini", "small"], "openrouter/free")

MODEL_CATALOG_FREE = {
    "coding": {
        "model_id": select_free_model(["code", "qwen", "gemma"], ROUTER_MODEL_FREE),
        "description": "Modello free ottimizzato per codice"
    },
    "reasoning": {
        "model_id": select_free_model(["deepseek", "nemotron", "reasoning"], ROUTER_MODEL_FREE),
        "description": "Modello free ottimizzato per logica e architettura"
    },
    "general": {
        "model_id": select_free_model(["gemma", "nemotron", "glm"], ROUTER_MODEL_FREE),
        "description": "Modello free per conversazione generica"
    },
    "fast_check": {
        "model_id": ROUTER_MODEL_FREE,
        "description": "Modello free per risposte rapide"
    }
}

# --- CATALOGO PAID (PRODUZIONE) ---
ROUTER_MODEL_PAID = "openai/gpt-4o-mini"

MODEL_CATALOG_PAID = {
    "coding": {
        "model_id": "anthropic/claude-3.5-sonnet",
        "description": "Top per sviluppo, refactoring, e ReAct Tool execution"
    },
    "reasoning": {
        "model_id": "deepseek/deepseek-r1",
        "description": "Deep reasoning e analisi architetturale avanzata"
    },
    "general": {
        "model_id": "openai/gpt-4o-mini",
        "description": "Sintesi e conversazione ad altissima velocità"
    },
    "fast_check": {
        "model_id": "google/gemini-flash-1.5",
        "description": "Risposte istantanee ad alto throughput"
    }
}

# Catena di fallback di emergenza per l'ambiente Paid
PAID_FALLBACK_CHAIN = [
    "anthropic/claude-3.5-sonnet",
    "openai/gpt-4o-mini",
    "deepseek/deepseek-chat"
]