"""Parti condivise dai semi di prova (scripts/prova): il contesto che passa da un seme all'altro e i vettori finti.

Solo per il database temporaneo di scripts/prova_locale.py: nessun seme tocca mai il database di produzione.
"""

import hashlib
import math
import re
from dataclasses import dataclass, field
from pathlib import Path

from neartech.abbinamento import MODELLO_EMBEDDING

RADICE = Path(__file__).resolve().parents[2]


@dataclass
class Contesto:
    """Identificativi creati dai semi, in ordine: il seme di base li riempie, quelli delle corsie li usano.

    Una corsia che crea qualcosa di utile alle altre lo aggiunge in `extra` sotto una chiave con il proprio nome
    (es. extra["questionari"]), senza cambiare i campi qui sotto.
    """

    admin: str = ""                                          # utente_id dell'amministratore tecnico (prova|admin)
    org: str = ""                                            # org_id di ACME S.p.A.
    codice_org: str = ""                                     # codice di ACME ("acme")
    utenti: dict[str, str] = field(default_factory=dict)     # soggetto SSO -> utente_id
    ruoli: dict[str, str] = field(default_factory=dict)      # ruolo organizzativo -> ruolo_id
    task_id: dict[str, str] = field(default_factory=dict)    # titolo del task -> task_id
    documento: str = ""                                      # documento_id dei mansionari sintetici
    snapshot: str = ""                                       # snapshot di copertura di riserva
    parametri: dict[str, str] = field(default_factory=dict)  # codice del parametro -> parametro_id approvato
    calcolo: dict = field(default_factory=dict)              # esito del calcolo di ACME
    extra: dict[str, object] = field(default_factory=dict)   # dati delle corsie, una chiave per corsia


def incorpora_prova(titoli: list[str]) -> list[list[float]]:
    """Vettori di prova al posto di bge-m3: parole in comune, titoli vicini. Solo nel database temporaneo."""
    vettori = []
    for titolo in titoli:
        v = [0.0] * 1024
        for parola in re.findall(r"\w{4,}", titolo.lower()):
            v[int(hashlib.sha256(parola[:6].encode()).hexdigest(), 16) % 1024] += 1.0
        norma = math.sqrt(sum(x * x for x in v)) or 1.0
        vettori.append([x / norma for x in v])
    return vettori


incorpora_prova.modello = MODELLO_EMBEDDING
