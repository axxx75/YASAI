<div align="center">

# 🧪 YASAI
### **Y**et **A**nother **S**imple **A**gentic **I**nfrastructure
*Un laboratorio agentico leggero, deterministico e containerizzato per lo sviluppo assistito da AI.*

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Docker Compliant](https://img.shields.io/badge/docker-ready-2496ED.svg?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![OpenRouter Integrated](https://img.shields.io/badge/OpenRouter-API-6466E9.svg?style=for-the-badge&logo=openai&logoColor=white)](https://openrouter.ai/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

[Caratteristiche](#-caratteristiche-chiave) • [Architettura](#-architettura-del-sistema) • [Requisiti](#-requisiti) • [Quickstart Docker](#-quickstart-docker-sandbox-ristretta) • [Configurazione](#-modalità-di-esecuzione)

---

</div>

## 📌 Cos'è YASAI?

**YASAI** è un'infrastruttura agentica CLI progettata per trasformare modelli LLM generici in **assistenti di sviluppo autonomi** legati al tuo workspace locale. 

Ispirato a strumenti come Claude Code o Replit Agent, YASAI integra un **Router semantico a due ingressi (Free / Paid)** con fallback automatico e un ciclo **ReAct (Reasoning + Acting)** che consente all'agente di esplorare il file system, modificare file di codice ed eseguire comandi shell in sicurezza.

---

## 🚀 Caratteristiche Chiave

* **🤖 Dynamic Model Routing & Triage:**
  * **Triage Automatico:** Classifica le richieste in categorie (`coding`, `reasoning`, `general`, `fast_check`) prima dell'esecuzione.
  * **Dual Engine (Free vs Paid):** Separazione netta tra un ambiente di **testing a costo zero** (con rollover su 25+ modelli gratuiti di OpenRouter) e un ambiente di **produzione ad alta affidabilità** (Claude 3.5 Sonnet, DeepSeek R1, GPT-4o Mini).
* **🔄 ReAct Agent Loop Integrato:**
  * Ciclo di esecuzione iterativo per l'analisi dei problemi, la lettura dei sorgenti, la scrittura delle modifiche e la verifica automatica tramite comandi di test.
* **🔒 Sandbox Docker Ristretta:**
  * Isolamento completo dell'ambiente di esecuzione: l'agente opera su volumi Docker montati con risorse limitate (`CPU`, `Memory`, `PIDs`) prevenendo modifiche indesiderate al sistema host.
* **🛠️ Tooling Engine Nativo:**
  * `[LIST_FILES]`: Esplorazione della struttura di progetto con filtri per `.gitignore` e file binari.
  * `[READ_FILE]`: Lettura sicura del contenuto dei file sorgente.
  * `[WRITE_FILE]`: Scrittura e refactoring atomico del codice.
  * `[RUN_CMD]`: Esecuzione di comandi shell isolati (es. `pytest`, `python`, `git status`).

---

## 🏗️ Architettura del Sistema

```text
                                 ┌──────────────────────────┐
                                 │   Richiesta Utente CLI   │
                                 └────────────┬─────────────┘
                                              │
                                              ▼
                                 ┌──────────────────────────┐
                                 │   Dynamic Triage Router  │
                                 └───────┬──────────┬───────┘
                                         │          │
                         ┌───────────────┘          └───────────────┐
                         ▼                                          ▼
           ┌───────────────────────────┐              ┌───────────────────────────┐
           │     MODE: MAIN_FREE       │              │     MODE: MAIN_PAID       │
           │ (Rollover 25+ Free Models)│              │  (Claude 3.5 / DeepSeek)  │
           └─────────────┬─────────────┘              └─────────────┬─────────────┘
                         │                                          │
                         └───────────────────┬──────────────────────┘
                                             │
                                             ▼
                               ┌───────────────────────────┐
                               │     ReAct Agent Loop      │
                               │  (agent_engine.py / Tools) │
                               └─────────────┬─────────────┘
                                             │
                       ┌─────────────────────┼─────────────────────┐
                       ▼                     ▼                     ▼
               ┌───────────────┐     ┌───────────────┐     ┌───────────────┐
               │ READ / WRITE  │     │  LIST FILES   │     │  RUN CMD      │
               │ File System   │     │ Workspace     │     │ Shell Sandbox │
               └───────────────┘     └───────────────┘     └───────────────┘


## 📋 Struttura del Progetto

```text
YASAI/
├── config.py          # Gestione chiavi API, scopritore modelli OpenRouter e cataloghi (Free/Paid)
├── router.py          # Classificazione e Triage delle query dell'utente
├── schemas.py         # Data models e enumerazioni (Pydantic / dataclasses)
├── agent_engine.py    # ReAct Loop, parser della sintassi dei tool ed esecuzione comandi
├── main_free.py       # Entrypoint CLI per la modalità testing/esperimenti gratuiti
├── main_paid.py       # Entrypoint CLI per la modalità produzione/lavoro reale
├── Dockerfile         # Dockerfile sandbox ristretto e privo di privilegi root
└── compose.yaml       # Configurazione Docker Compose con limiti di risorse


## 📦 Quickstart Docker (Sandbox Ristretta)
Il metodo consigliato per eseguire YASAI in totale sicurezza è all'interno di un container Docker con risorse limitate e senza privilegi root.

1. Clona il repository
Bash
git clone [https://github.com/axxx75/YASAI.git](https://github.com/axxx75/YASAI.git)
cd YASAI
2. Configura le variabili d'ambiente
Crea un file .env nella radice del progetto:

Bash
OPENROUTER_API_KEY=your_openrouter_api_key_here
3. Avvia l'ambiente isolato
Modalità Free (Testing):

Bash
docker compose run --rm yasai-free
Modalità Paid (Produzione):

Bash
docker compose run --rm yasai-paid
Nota di Sicurezza: Il container esegue con un utente non-root (appuser), mem_limit fissato a 512MB e CPU limitata a 1.0 core per evitare processi runaway o esecuzioni dannose sulla macchina host.

##💻 Configurazione ed Esecuzione Locale (Senza Docker)
Se preferisci eseguire l'infrastruttura direttamente nel tuo terminale locale:

Bash
# 1. Crea e attiva un ambiente virtuale
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 2. Installa le dipendenze
pip install -r requirements.txt

# 3. Esporta la chiave API di OpenRouter
export OPENROUTER_API_KEY="la-tua-chiave-api"

# 4. Avvia la CLI desiderata
python main_free.py   # Per la modalità gratuita con rollover
# oppure
python main_paid.py   # Per la modalità produzione con Claude/GPT-4o

##🧪 Esempio di Utilizzo CLI
Plaintext
=================================================================
  AI LAB - Agentic CLI Engine [MODE: PAID / PRODUCTION]
  Primary Coding Model: anthropic/claude-3.5-sonnet
  Digita 'exit' o 'quit' per uscire.
=================================================================

paid-agent> Crea una suite di test con pytest per la funzione di triage in router.py

[ROUTER PAID]: Categoria -> CODING | Modello Target -> anthropic/claude-3.5-sonnet
[ROUTER REASONING]: Richiesta di creazione test unitari in Python per il modulo router.py

--- Turno 1/8 | Modello: [anthropic/claude-3.5-sonnet] ---
[TOOL EXECUTION]: Lettura file 'router.py'...
[TOOL EXECUTION]: Scrittura file 'tests/test_router.py'...
[TOOL EXECUTION]: Esecuzione comando shell '$ pytest tests/test_router.py'...

--- Output Pytest ---
2 passed in 0.35s
--------------------

[AGENTE]: La suite di test è stata creata ed eseguita con successo. Tutti i test sono passati!

##🛡️ Licenza
Questo progetto è distribuito sotto licenza MIT. Consulta il file LICENSE per ulteriori dettagli.
