"""Accesso a PostgreSQL attraverso l'endpoint SQL HTTPS di Neon.

Serve quando la rete dell'ambiente lascia uscire solo il traffico HTTPS (porta 443)
e blocca la porta 5432. Espone la stessa interfaccia minima usata dai moduli
del progetto (`execute`, `fetchone`, `fetchall`, `rowcount`, `transaction`, `commit`),
così il codice di caricamento resta lo stesso.

Limiti da conoscere:
- ogni istruzione è una richiesta separata: non ci sono transazioni interattive.
  Per questo i caricamenti sono idempotenti (ON CONFLICT) e vanno rilanciati se si interrompono;
- un'istruzione per volta: gli script SQL vanno spezzati (vedi `split_statements`);
- i parametri `%s` sono convertiti in `$1, $2, ...`.
"""

import json
import re
import urllib.error
import urllib.request
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any

# OID PostgreSQL che l'endpoint HTTP restituisce come stringa e che convertiamo in tipi Python.
_INT_OIDS = {20, 21, 23, 26}
_BOOL_OIDS = {16}


def split_statements(text: str) -> list[str]:
    """Spezza uno script SQL in istruzioni, togliendo i commenti di riga (senza dollar-quoting)."""
    kept = "\n".join(line for line in text.splitlines() if not line.strip().startswith("--"))
    return [stmt.strip() for stmt in kept.split(";") if stmt.strip()]


def _to_dollar(sql: str) -> str:
    counter = iter(range(1, 10_000))
    return re.sub(r"%s", lambda _: f"${next(counter)}", sql)


@dataclass
class HttpCursor:
    rows: list[tuple] = field(default_factory=list)
    rowcount: int = -1

    def fetchone(self):
        return self.rows[0] if self.rows else None

    def fetchall(self):
        return list(self.rows)


class HttpConnection:
    def __init__(self, url: str, timeout: int = 600):
        self._url = url
        self._host = url.split("@", 1)[1].split("/", 1)[0].split("?")[0]
        self._timeout = timeout

    # --- richiesta HTTP -------------------------------------------------
    def _post(self, sql: str, params: list[Any]) -> dict:
        body = json.dumps({"query": sql, "params": params}, default=str).encode("utf-8")
        req = urllib.request.Request(
            f"https://{self._host}/sql",
            method="POST",
            data=body,
            headers={"Content-Type": "application/json", "Neon-Connection-String": self._url},
        )
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f"Errore SQL via HTTPS ({exc.code}): {exc.read()[:800].decode('utf-8', 'replace')}") from exc

    # --- interfaccia compatibile con psycopg ------------------------------
    def execute(self, sql: str, params: tuple | list | None = None) -> HttpCursor:
        payload = self._post(_to_dollar(sql), list(params or []))
        fields = payload.get("fields", [])
        conv = [(f["name"], f["dataTypeID"]) for f in fields]
        rows = []
        for raw in payload.get("rows", []):
            row = []
            for name, oid in conv:
                value = raw[name]
                if value is not None and oid in _INT_OIDS:
                    value = int(value)
                elif value is not None and oid in _BOOL_OIDS:
                    value = value in (True, "t", "true")
                row.append(value)
            rows.append(tuple(row))
        count = payload.get("rowCount")
        return HttpCursor(rows=rows, rowcount=count if count is not None else -1)

    @contextmanager
    def transaction(self):
        # Nessuna transazione interattiva su HTTP: vedi la nota in testa al modulo.
        yield self

    def commit(self) -> None:
        return None

    def rollback(self) -> None:
        return None

    def __enter__(self) -> "HttpConnection":
        return self

    def __exit__(self, *exc) -> None:
        return None
