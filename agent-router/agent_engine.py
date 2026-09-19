import os
import re
import json
import time
import subprocess
import requests
from config import OPENROUTER_API_BASE, OPENROUTER_API_KEY, DEFAULT_HEADERS

# --- TOOLS ---
def list_files(path=".") -> str:
    files_list = []
    ignore_dirs = {'.git', '__pycache__', '.venv', 'node_modules', '.pytest_cache', 'dist', 'build'}
    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        for file in files:
            rel_path = os.path.relpath(os.path.join(root, file), path)
            files_list.append(rel_path)
    return "\n".join(files_list[:100]) if files_list else "Nessun file trovato."

def read_file(filepath: str) -> str:
    try:
        with open(filepath.strip(), 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"[TOOL ERROR]: Errore lettura file '{filepath}': {e}"

def write_file(filepath: str, content: str) -> str:
    try:
        clean_path = filepath.strip()
        if os.path.dirname(clean_path):
            os.makedirs(os.path.dirname(clean_path), exist_ok=True)
        with open(clean_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"[TOOL SUCCESS]: File '{clean_path}' salvato con successo."
    except Exception as e:
        return f"[TOOL ERROR]: Errore scrittura file '{filepath}': {e}"

def run_command(cmd: str) -> str:
    try:
        res = subprocess.run(cmd.strip(), shell=True, capture_output=True, text=True, timeout=30)
        output = res.stdout if res.stdout else res.stderr
        return output[:3000] if output else "[TOOL SUCCESS]: Comando eseguito senza output."
    except subprocess.TimeoutExpired:
        return "[TOOL ERROR]: Esecuzione comando terminata per timeout (30s)."
    except Exception as e:
        return f"[TOOL ERROR]: Impossibile eseguire il comando: {e}"

CODING_AGENT_SYSTEM_PROMPT = """Sei un software engineer autonomo che opera via CLI nel workspace dell'utente.
Hai a disposizione i seguenti STRUMENTI per interagire con il file system e l'ambiente:

1. Per elencare i file nel progetto:
   [LIST_FILES]

2. Per leggere un file:
   [READ_FILE: percorso/al/file]

3. Per creare o modificare un file:
   [WRITE_FILE: percorso/al/file]
   <<<
   contenuto del file
   >>>

4. Per eseguire un comando shell:
   [RUN_CMD: comando shell]

REGOLE DI COMPORTAMENTO:
- Lavora in modo iterativo (ReAct pattern): analizza la richiesta, esplora o leggi i file necessari, applica le modifiche e testa l'output.
- Usa GLI STRUMENTI esattamente con la sintassi indicata sopra.
- Puoi eseguire un solo blocco strumento per ogni turno o rispondere direttamente all'utente se il task è completato.
"""

def call_llm_stream(model: str, messages: list) -> str:
    headers = {
        **DEFAULT_HEADERS,
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": messages,
        "stream": True,
        "temperature": 0.2
    }

    response = requests.post(
        f"{OPENROUTER_API_BASE}/chat/completions",
        json=payload,
        headers=headers,
        stream=True,
        timeout=45
    )
    
    if response.status_code == 429:
        raise requests.exceptions.HTTPError("429 Too Many Requests")
        
    response.raise_for_status()

    full_response = ""
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
                        full_response += content
                except json.JSONDecodeError:
                    continue
    print()
    return full_response

def run_agent_loop(primary_model: str, user_prompt: str, fallback_models: list, max_turns: int = 8):
    models_to_try = [primary_model] + [m for m in fallback_models if m != primary_model]
    
    messages = [
        {"role": "system", "content": CODING_AGENT_SYSTEM_PROMPT},
        {"role": "user", "content": f"Richiesta Utente: {user_prompt}\nStruttura Workspace attuale:\n{list_files()}"}
    ]

    active_model = primary_model

    for turn in range(max_turns):
        print(f"\n--- Turno {turn + 1}/{max_turns} | Modello: [{active_model}] ---")
        
        response_text = None
        for model in models_to_try:
            try:
                response_text = call_llm_stream(model, messages)
                active_model = model
                break
            except requests.exceptions.HTTPError as e:
                if "429" in str(e):
                    print(f"\n[RATE LIMIT 429]: Modello '{model}' saturo. Fallback al successivo...")
                    time.sleep(1)
                    continue
                else:
                    print(f"\n[ERRORE HTTP {model}]: {e}")
                    break
            except Exception as e:
                print(f"\n[ERRORE {model}]: {e}")
                break

        if not response_text:
            print("\n[ERRORE FATALE]: Nessun modello disponibile.\n")
            return

        messages.append({"role": "assistant", "content": response_text})

        # Exec tools
        if "[LIST_FILES]" in response_text:
            print("\n[TOOL EXECUTION]: Elenco file workspace...")
            res = list_files()
            messages.append({"role": "user", "content": f"[TOOL RESULT LIST_FILES]:\n{res}"})
            continue

        write_match = re.search(r'\[WRITE_FILE:\s*(.*?)\]\s*<<<\n(.*?)\n>>>', response_text, re.DOTALL)
        if write_match:
            filepath = write_match.group(1).strip()
            content = write_match.group(2)
            print(f"\n[TOOL EXECUTION]: Scrittura file '{filepath}'...")
            res = write_file(filepath, content)
            messages.append({"role": "user", "content": res})
            continue

        read_match = re.search(r'\[READ_FILE:\s*(.*?)\]', response_text)
        if read_match:
            filepath = read_match.group(1).strip()
            print(f"\n[TOOL EXECUTION]: Lettura file '{filepath}'...")
            res = read_file(filepath)
            messages.append({"role": "user", "content": f"[TOOL RESULT READ_FILE '{filepath}']:\n{res}"})
            continue

        cmd_match = re.search(r'\[RUN_CMD:\s*(.*?)\]', response_text)
        if cmd_match:
            cmd = cmd_match.group(1).strip()
            print(f"\n[TOOL EXECUTION]: Esecuzione comando shell '$ {cmd}'...")
            res = run_command(cmd)
            messages.append({"role": "user", "content": f"[TOOL RESULT RUN_CMD '$ {cmd}']:\n{res}"})
            continue

        print("\n[AGENTE]: Task completato.")
        break