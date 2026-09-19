import os
import subprocess

def list_files(path="."):
    """Mostra la struttura delle cartelle ignorando file inutili."""
    files_list = []
    for root, dirs, files in os.walk(path):
        # Escludi cartelle pesanti o nascoste
        dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', '.venv', 'node_modules']]
        for file in files:
            files_list.append(os.path.relpath(os.path.join(root, file), path))
    return files_list[:100]  # Limita a 100 file per non saturare i token

def read_file(filepath: str) -> str:
    """Legge il contenuto di un file di codice."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Errore lettura file {filepath}: {e}"

def write_file(filepath: str, content: str) -> str:
    """Scrive o sovrascrive un file nel workspace."""
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"File {filepath} scritto con successo."
    except Exception as e:
        return f"Errore scrittura file {filepath}: {e}"

def run_command(cmd: str) -> str:
    """Esegue un comando shell (es. pytest, git status, python script.py)."""
    try:
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        output = res.stdout if res.stdout else res.stderr
        return output[:2000] # Trunca output troppo lunghi
    except Exception as e:
        return f"Errore esecuzione comando: {e}"