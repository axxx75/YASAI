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