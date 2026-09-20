import json
import re
import shutil
import subprocess


_TASK_ID_PATTERN = re.compile(
    r"^(?:[0-9]+(?:\.[0-9]+)*|[A-Za-z][A-Za-z0-9_-]{0,31}-[0-9]+(?:\.[0-9]+)*)$"
)
_MAX_TITLE_CHARS = 200
_MAX_TEXT_CHARS = 5000
_MAX_OUTPUT_CHARS = 12000


def _bounded_json(output: str) -> str:
    """Keep JSON valid while bounding large task lists."""
    try:
        data = json.loads(output)
    except json.JSONDecodeError as error:
        return json.dumps(
            {
                "error": "Backlog.md ha restituito JSON non valido",
                "detail": str(error),
            },
            ensure_ascii=False,
        )

    encoded = json.dumps(data, ensure_ascii=False)
    if len(encoded) <= _MAX_OUTPUT_CHARS:
        return encoded

    if isinstance(data, dict) and isinstance(data.get("tasks"), list):
        tasks = data["tasks"]
        bounded = {key: value for key, value in data.items() if key != "tasks"}
        bounded["tasks"] = []
        bounded["_truncated"] = True
        bounded["_total_tasks"] = len(tasks)

        for task in tasks:
            bounded["tasks"].append(task)
            candidate = json.dumps(bounded, ensure_ascii=False)
            if len(candidate) > _MAX_OUTPUT_CHARS:
                bounded["tasks"].pop()
                break
        return json.dumps(bounded, ensure_ascii=False)

    return json.dumps(
        {
            "error": "Output Backlog.md troppo grande",
            "output_chars": len(encoded),
        },
        ensure_ascii=False,
    )


def _run_backlog(args: list[str], expect_json: bool = False) -> str:
    """Run Backlog.md without a shell and return bounded output."""
    executable = shutil.which("backlog")
    if not executable:
        return (
            "[BACKLOG ERROR]: comando 'backlog' non disponibile. "
            "Ricostruisci il container o installa backlog.md."
        )

    try:
        result = subprocess.run(
            [executable, *args],
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return "[BACKLOG ERROR]: comando terminato per timeout (20s)."
    except OSError as error:
        return f"[BACKLOG ERROR]: impossibile avviare Backlog.md: {error}"

    output = (result.stdout or result.stderr).strip()
    if result.returncode != 0:
        detail = output or f"uscita con codice {result.returncode}"
        return f"[BACKLOG ERROR]: {detail[:_MAX_OUTPUT_CHARS]}"
    if expect_json:
        return _bounded_json(output)
    return output[:_MAX_OUTPUT_CHARS] or "[BACKLOG SUCCESS]: operazione completata."


def _validate_task_id(task_id: str) -> str:
    task_id = task_id.strip()
    if not _TASK_ID_PATTERN.fullmatch(task_id):
        raise ValueError(
            "ID task non valido: usa lettere, numeri, trattino o underscore."
        )
    return task_id


def list_backlog_tasks() -> str:
    """List project tasks using Backlog.md's stable JSON output."""
    return _run_backlog(["task", "list", "--json"], expect_json=True)


def view_backlog_task(task_id: str) -> str:
    """Read one task using stable JSON output."""
    try:
        task_id = _validate_task_id(task_id)
    except ValueError as error:
        return f"[BACKLOG ERROR]: {error}"
    return _run_backlog(["task", "view", task_id, "--json"], expect_json=True)


def create_backlog_task(title: str, description: str = "") -> str:
    """Create a task after validating and bounding model-provided text."""
    title = " ".join(title.split())
    description = description.strip()
    if not title:
        return "[BACKLOG ERROR]: il titolo è obbligatorio."
    if len(title) > _MAX_TITLE_CHARS:
        return f"[BACKLOG ERROR]: titolo troppo lungo (massimo {_MAX_TITLE_CHARS} caratteri)."
    if len(description) > _MAX_TEXT_CHARS:
        return (
            f"[BACKLOG ERROR]: descrizione troppo lunga "
            f"(massimo {_MAX_TEXT_CHARS} caratteri)."
        )

    args = ["task", "create", title]
    if description:
        args.extend(["-d", description])
    return _run_backlog(args)


def append_backlog_notes(task_id: str, notes: str) -> str:
    """Append execution notes without replacing the task description."""
    try:
        task_id = _validate_task_id(task_id)
    except ValueError as error:
        return f"[BACKLOG ERROR]: {error}"

    notes = notes.strip()
    if not notes:
        return "[BACKLOG ERROR]: la nota è obbligatoria."
    if len(notes) > _MAX_TEXT_CHARS:
        return (
            f"[BACKLOG ERROR]: nota troppo lunga "
            f"(massimo {_MAX_TEXT_CHARS} caratteri)."
        )
    return _run_backlog(
        [
            "task",
            "edit",
            task_id,
            "--append-notes",
            notes,
        ]
    )


def complete_backlog_task(task_id: str) -> str:
    """Mark a task complete using Backlog.md's standard Done status."""
    try:
        task_id = _validate_task_id(task_id)
    except ValueError as error:
        return f"[BACKLOG ERROR]: {error}"
    return _run_backlog(["task", "edit", task_id, "-s", "Done"])