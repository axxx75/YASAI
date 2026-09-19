import os
import re
import sqlite3
import uuid
import hashlib
from datetime import datetime, timezone
from pathlib import Path


_SESSION_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")
_OWNER_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.@-]{0,127}$")

# These patterns cover the provider credentials used by this project and the
# most common token formats that may appear in command output or model replies.
_SENSITIVE_PATTERNS = (
    (re.compile(r"\bsk-[A-Za-z0-9_-]{12,}\b"), "[REDACTED_API_KEY]"),
    (re.compile(r"\bsk-or-v1-[A-Za-z0-9_-]{8,}\b"), "[REDACTED_OPENROUTER_KEY]"),
    (re.compile(r"\bgh[pousr]_[A-Za-z0-9_-]{10,}\b"), "[REDACTED_GITHUB_TOKEN]"),
    (re.compile(r"\bgithub_pat_[A-Za-z0-9_]{10,}\b"), "[REDACTED_GITHUB_TOKEN]"),
    (re.compile(r"\bhf_[A-Za-z0-9]{10,}\b"), "[REDACTED_HF_TOKEN]"),
    (re.compile(r"\bgsk_[A-Za-z0-9_-]{10,}\b"), "[REDACTED_PROVIDER_KEY]"),
    (re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"), "[REDACTED_SLACK_TOKEN]"),
    (
        re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]{12,}"),
        "Bearer [REDACTED_TOKEN]",
    ),
    (
        re.compile(
            r"(?im)^([ \t]*[A-Z][A-Z0-9_]*(?:API_KEY|AUTH_TOKEN|ACCESS_TOKEN|"
            r"SECRET|PASSWORD|PRIVATE_KEY))([ \t]*[=:][ \t]*)([^\s\"']+|\"[^\"]*\"|'[^']*')"
        ),
        r"\1\2[REDACTED_SECRET]",
    ),
    (
        re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b"),
        "[REDACTED_JWT]",
    ),
    (
        re.compile(
            r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----.*?"
            r"-----END (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
            re.DOTALL,
        ),
        "[REDACTED_PRIVATE_KEY]",
    ),
)


def redact_sensitive_content(content: str) -> str:
    """Remove common credentials before content is written to the memory DB."""
    redacted = content
    for pattern, replacement in _SENSITIVE_PATTERNS:
        redacted = pattern.sub(replacement, redacted)
    return redacted


class ConversationStore:
    """Small SQLite-backed conversation store for one or more CLI sessions."""

    def __init__(
        self,
        db_path: str,
        owner_id: str,
        max_messages: int = 20,
        max_content_chars: int = 20000,
        retention_days: int = 30,
    ):
        if max_messages < 1:
            raise ValueError("YASAI_MEMORY_MAX_MESSAGES deve essere almeno 1.")
        if max_content_chars < 1:
            raise ValueError("YASAI_MEMORY_MAX_CONTENT_CHARS deve essere almeno 1.")
        if retention_days < 1:
            raise ValueError("YASAI_MEMORY_RETENTION_DAYS deve essere almeno 1.")
        if not isinstance(owner_id, str) or not _OWNER_ID_PATTERN.fullmatch(owner_id):
            raise ValueError(
                "ID proprietario non valido: usa 1-128 caratteri alfanumerici, '.', '_', '@' o '-'."
            )

        self.db_path = Path(db_path).expanduser()
        self.owner_id = owner_id
        self.max_messages = max_messages
        self.max_content_chars = max_content_chars
        self.retention_days = retention_days
        self.db_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        try:
            os.chmod(self.db_path.parent, 0o700)
        except OSError:
            pass

        if self.db_path.exists() and self.db_path.is_symlink():
            raise RuntimeError(f"Il database memoria non può essere un symlink: {self.db_path}")

        self._initialize()
        self.delete_expired()
        try:
            os.chmod(self.db_path, 0o600)
        except OSError:
            # Windows and some mounted filesystems may not support chmod.
            pass

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path, timeout=10)
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 10000")
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    owner_id TEXT NOT NULL DEFAULT 'legacy',
                    public_id TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            columns = {
                row[1] for row in connection.execute("PRAGMA table_info(sessions)").fetchall()
            }
            if "owner_id" not in columns:
                connection.execute(
                    "ALTER TABLE sessions ADD COLUMN owner_id TEXT NOT NULL DEFAULT 'legacy'"
                )
            if "public_id" not in columns:
                connection.execute(
                    "ALTER TABLE sessions ADD COLUMN public_id TEXT NOT NULL DEFAULT ''"
                )
                connection.execute("UPDATE sessions SET public_id = id WHERE public_id = ''")
            connection.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS idx_sessions_owner_public
                ON sessions(owner_id, public_id)
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_messages_session_id_id
                ON messages(session_id, id)
                """
            )

    @staticmethod
    def _validate_session_id(session_id: str) -> str:
        if not isinstance(session_id, str) or not _SESSION_ID_PATTERN.fullmatch(session_id):
            raise ValueError(
                "ID sessione non valido: usa 1-64 caratteri alfanumerici, '.', '_' o '-'."
            )
        return session_id

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def _storage_id(self, session_id: str) -> str:
        value = f"{self.owner_id}\0{session_id}".encode("utf-8")
        return hashlib.sha256(value).hexdigest()

    def ensure_session(self, session_id: str) -> str:
        session_id = self._validate_session_id(session_id)
        storage_id = self._storage_id(session_id)
        now = self._now()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO sessions (id, owner_id, public_id, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(id) DO NOTHING
                """,
                (storage_id, self.owner_id, session_id, now, now),
            )
        return session_id

    def new_session(self) -> str:
        session_id = uuid.uuid4().hex
        self.ensure_session(session_id)
        return session_id

    def append(self, session_id: str, role: str, content: str) -> None:
        session_id = self._validate_session_id(session_id)
        storage_id = self._storage_id(session_id)
        if role not in {"user", "assistant"}:
            raise ValueError(f"Ruolo memoria non supportato: {role}")
        if not isinstance(content, str) or not content.strip():
            return

        self.ensure_session(session_id)
        safe_content = redact_sensitive_content(content)[: self.max_content_chars]
        now = self._now()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO messages (session_id, role, content, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (storage_id, role, safe_content, now),
            )
            connection.execute(
                """
                DELETE FROM messages
                WHERE session_id = ?
                  AND id NOT IN (
                      SELECT id FROM messages
                      WHERE session_id = ?
                      ORDER BY id DESC
                      LIMIT ?
                  )
                """,
                (storage_id, storage_id, self.max_messages),
            )
            connection.execute(
                "UPDATE sessions SET updated_at = ? WHERE id = ?",
                (now, storage_id),
            )

    def append_exchange(self, session_id: str, user_content: str, assistant_content: str) -> None:
        """Persist one completed user/assistant turn in a single transaction."""
        session_id = self._validate_session_id(session_id)
        storage_id = self._storage_id(session_id)
        if not user_content.strip() or not assistant_content.strip():
            return

        self.ensure_session(session_id)
        user_content = redact_sensitive_content(user_content)[: self.max_content_chars]
        assistant_content = redact_sensitive_content(assistant_content)[: self.max_content_chars]
        now = self._now()

        with self._connect() as connection:
            connection.executemany(
                """
                INSERT INTO messages (session_id, role, content, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (
                    (storage_id, "user", user_content, now),
                    (storage_id, "assistant", assistant_content, now),
                ),
            )
            connection.execute(
                """
                DELETE FROM messages
                WHERE session_id = ?
                  AND id NOT IN (
                      SELECT id FROM messages
                      WHERE session_id = ?
                      ORDER BY id DESC
                      LIMIT ?
                  )
                """,
                (storage_id, storage_id, self.max_messages),
            )
            connection.execute(
                "UPDATE sessions SET updated_at = ? WHERE id = ?",
                (now, storage_id),
            )

    def recent_context(self, session_id: str, limit: int | None = None) -> list[dict[str, str]]:
        session_id = self._validate_session_id(session_id)
        storage_id = self._storage_id(session_id)
        requested_limit = self.max_messages if limit is None else min(limit, self.max_messages)
        if requested_limit < 1:
            return []

        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT role, content
                FROM messages
                WHERE session_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (storage_id, requested_limit),
            ).fetchall()
        rows.reverse()
        return [{"role": role, "content": content} for role, content in rows]

    def clear(self, session_id: str) -> None:
        session_id = self._validate_session_id(session_id)
        storage_id = self._storage_id(session_id)
        self.ensure_session(session_id)
        with self._connect() as connection:
            connection.execute("DELETE FROM messages WHERE session_id = ?", (storage_id,))
            connection.execute(
                "UPDATE sessions SET updated_at = ? WHERE id = ?",
                (self._now(), storage_id),
            )

    def delete_session(self, session_id: str) -> None:
        """Delete a session and all of its messages for the current owner."""
        session_id = self._validate_session_id(session_id)
        with self._connect() as connection:
            connection.execute(
                "DELETE FROM sessions WHERE id = ? AND owner_id = ?",
                (self._storage_id(session_id), self.owner_id),
            )

    def delete_expired(self) -> int:
        """Delete sessions older than the configured retention period."""
        with self._connect() as connection:
            cursor = connection.execute(
                """
                DELETE FROM sessions
                WHERE owner_id = ?
                  AND julianday(updated_at) < julianday('now', ?)
                """,
                (self.owner_id, f"-{self.retention_days} days"),
            )
        return cursor.rowcount