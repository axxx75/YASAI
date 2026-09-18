import os
import requests

def fetch_free_models():
    url = "https://openrouter.ai/api/v1/models"
    try:
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        data = res.json().get("data", [])
        
        # Filtra i modelli con prezzo prompt e completion a 0
        free = [
            m["id"] for m in data 
            if m.get("pricing", {}).get("prompt") == "0" 
            and m.get("pricing", {}).get("completion") == "0"
        ]
        return free
    except Exception as e:
        print(f"Errore nel recupero modelli: {e}")
        return []

if __name__ == "__main__":
    models = fetch_free_models()
    print(f"\n--- MODELLI GRATUITI ATTIVI SU OPENROUTER ({len(models)}) ---")
    for m in models:
        print(f"  • {m}")
        
    if models:
        top_model = models[0]
        print(f"\nModello consigliato per DEFAULT_MODEL: {top_model}")
