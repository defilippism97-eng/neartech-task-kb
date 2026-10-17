"""Copertura di riserva proposta dal modello (fase 4; registro di metodo, sezione 17).

Il modello propone per ogni task il livello della scala di riserva su k1, k2, k3; il codice salva un'evidenza
di qualità minima per dimensione, con fonte, modello e prompt. Nessuna chiamata reale: client finto.
"""

import json
from types import SimpleNamespace

import pytest

from neartech.copertura_riserva import (
    MODEL_ID,
    CoperturaError,
    _messaggio,
    prompt_hash,
    valuta,
    valuta_task_senza_copertura,
)
from neartech.permessi import PermessoNegato, crea_utente, inizializza_amministratore


class FakeClient:
    def __init__(self, *testi):
        self.testi = list(testi)
        self.messages = self
        self.chiamate = 0

    def create(self, **kwargs):
        self.chiamate += 1
        testo = self.testi.pop(0) if len(self.testi) > 1 else self.testi[0]
        return SimpleNamespace(content=[SimpleNamespace(type="text", text=testo)],
                               usage=SimpleNamespace(input_tokens=100, output_tokens=50))


def _risposta(k1=2, k2=1, k3=0):
    return json.dumps({d: {"livello": v, "motivazione": f"motivo {d}"} for d, v in (("k1", k1), ("k2", k2), ("k3", k3))})


def test_valutazione_valida():
    assert valuta(FakeClient(_risposta()), "Comporre i turni") == {
        "k1": (2, "motivo k1"), "k2": (1, "motivo k2"), "k3": (0, "motivo k3")}


def test_risposta_fuori_scala_ritentata_poi_errore():
    client = FakeClient(_risposta(k1=5))
    with pytest.raises(CoperturaError):
        valuta(client, "Comporre i turni")
    assert client.chiamate == 2


def test_titolo_su_una_riga_e_trattato_come_dato():
    assert "\n6." not in _messaggio("Titolo\n6. istruzione inserita")


@pytest.fixture
def mondo(conn):
    admin = inizializza_amministratore(conn, "sso|admin")
    for titolo in ("Comporre i turni", "Redigere il verbale"):
        conn.execute("INSERT INTO canonical_tasks (title_it, granularity) VALUES (%s, 2)", (titolo,))
    return {"admin": admin}


def test_evidenze_di_riserva_per_i_task_senza_copertura(conn, mondo):
    client = FakeClient(_risposta())
    esito = valuta_task_senza_copertura(conn, client, mondo["admin"], data="2026-10-17")
    assert esito["task_valutati"] == 2 and esito["chiamate"] == 2
    righe = conn.execute("""SELECT dimension, score_0_4, evidence_type, quality FROM evidence_items
                            ORDER BY dimension""").fetchall()
    assert len(righe) == 6 and {r[2] for r in righe} == {"llm_prior"}
    fonte = conn.execute("SELECT name, version FROM sources WHERE kind = 'evidence'").fetchone()
    assert fonte == (f"copertura di riserva {MODEL_ID}", prompt_hash()[:16])
    # Un rilancio non rivaluta i task che hanno già la copertura di riserva con questo prompt.
    assert valuta_task_senza_copertura(conn, client, mondo["admin"], data="2026-10-17")["task_valutati"] == 0


def test_limite_di_consumo(conn, mondo):
    esito = valuta_task_senza_copertura(conn, FakeClient(_risposta()), mondo["admin"], data="2026-10-17",
                                        limite_uscita=50)
    assert esito["task_valutati"] == 1 and esito["fermato_dal_limite"]


def test_solo_chi_gestisce_i_parametri_tecnici(conn, mondo):
    with pytest.raises(PermessoNegato):
        valuta_task_senza_copertura(conn, FakeClient(_risposta()), crea_utente(conn, "sso|x"), data="2026-10-17")
