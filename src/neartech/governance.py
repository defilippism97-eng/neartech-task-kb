"""Parametri di governance, indirizzi del comitato guida e segnalazioni dei revisori.

Ogni proposta e ogni decisione passa da neartech.permessi e lascia un atto nel
registro. Le versioni non si modificano; lo stato si ricava dal registro.
Nessun valore di default nel codice: un parametro non approvato non esiste.

Ritiro: ritirare la versione vigente lascia il parametro senza valore. Non si torna
alla versione precedente né al valore comune NEARTECH: serve una decisione nuova.

Testi (ADR 0004): testo e ambito degli indirizzi, descrizioni dei parametri dell'organizzazione e
motivazioni dei suoi atti stanno nello spazio dell'organizzazione; nel registro resta l'hash.

Parametri comuni (metodologia, sezione 10): il comitato guida li vede (parametri_comuni), li adotta
o chiede una ricalibrazione motivata all'amministratore tecnico. Il valore comune vale anche senza
adozione; parametro_vigente dice se la versione in uso è stata adottata (adozione_id).
"""

import uuid
from dataclasses import dataclass
from typing import Any

import psycopg
from psycopg import sql
from psycopg.types.json import Jsonb

from neartech.permessi import richiedi
from neartech.registro import chiave_spazio, impronta, registra, spazio


class ParametroAssente(LookupError):
    """Nessuna versione approvata e vigente per il parametro."""


class ParametroRitirato(ParametroAssente):
    """L'organizzazione ha ritirato la versione vigente e non ne ha approvata una nuova."""


class DecisioneGiaPresa(RuntimeError):
    """La versione è già stata approvata o rifiutata, o non si può ritirare."""


@dataclass(frozen=True)
class Parametro:
    parametro_id: str
    codice: str
    org_id: str | None
    versione: int
    valore: Any
    approvazione_id: int
    adozione_id: int | None = None  # atto di adozione della versione comune da parte dell'organizzazione


@dataclass(frozen=True)
class StatoParametroComune:
    parametro_id: str
    codice: str
    versione: int
    valore: Any
    descrizione: str
    stato: str  # da_esaminare | adottato | ricalibrazione_richiesta | parametro_proprio
    ultimo_atto_id: int | None


@dataclass(frozen=True)
class Indirizzo:
    indirizzo_id: str
    org_id: str
    codice: str
    versione: int
    testo: str
    ambito: str
    approvazione_id: int


# Tipo di oggetto nel registro -> (tabella, colonna chiave, permesso per decidere)
_OGGETTI = {
    "parametro": ("parametri_governance", "parametro_id", "approvare_parametro"),
    "indirizzo": ("indirizzi_comitato", "indirizzo_id", "approvare_indirizzo"),
}

# Separatore fra testo e ambito nell'hash del contenuto di un indirizzo (stesso valore in verifica_contenuti).
_SEPARATORE = "\x1f"


def _hash_indirizzo(chiave: bytes, testo: str, ambito: str) -> str:
    return impronta(chiave, f"{testo}{_SEPARATORE}{ambito}")


def _spazio_richiesto(conn: psycopg.Connection, org_id: str) -> sql.Identifier:
    schema = spazio(conn, org_id)
    if schema is None:
        raise LookupError(f"l'organizzazione {org_id} non ha uno spazio: i suoi testi non hanno dove stare")
    return schema


def _spazi(conn: psycopg.Connection, org_id: str | None = None) -> list[tuple[str, sql.Identifier]]:
    """Spazi esistenti (di tutte le organizzazioni o di una). Uno spazio mancante non blocca gli altri:
    i suoi atti non si possono scrivere (registra), e il report di quell'organizzazione lo segnala."""
    spazi = []
    for (org,) in conn.execute(
        "SELECT org_id FROM organizations WHERE codice IS NOT NULL AND (%s::uuid IS NULL OR org_id = %s::uuid)"
        " ORDER BY codice", (org_id, org_id),
    ).fetchall():
        try:
            schema = spazio(conn, str(org))
        except LookupError:
            continue
        if schema is not None:
            spazi.append((str(org), schema))
    return spazi


def _blocca(conn: psycopg.Connection, chiave: str) -> None:
    conn.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", (chiave,))


def _prossima_versione(conn: psycopg.Connection, tabella: str, codice: str, org_id: str | None) -> int:
    _blocca(conn, f"versione:{tabella}:{codice}:{org_id}")
    return conn.execute(
        sql.SQL("SELECT COALESCE(max(versione), 0) + 1 FROM {} WHERE codice = %s AND org_id IS NOT DISTINCT FROM %s")
        .format(sql.Identifier(tabella)),
        (codice, org_id),
    ).fetchone()[0]


def _decidi(
    conn: psycopg.Connection, utente_id: str, tipo: str, oggetto_id: str, atto: str, motivazione: str
) -> int:
    tabella, chiave, permesso = _OGGETTI[tipo]
    oggetto_id = str(uuid.UUID(str(oggetto_id)))
    with conn.transaction():
        riga = conn.execute(
            sql.SQL("SELECT org_id, codice, versione FROM {} WHERE {} = %s")
            .format(sql.Identifier(tabella), sql.Identifier(chiave)),
            (oggetto_id,),
        ).fetchone()
        if riga is None:
            raise LookupError(f"{tipo} {oggetto_id} inesistente")
        org_id = str(riga[0]) if riga[0] is not None else None
        codice, versione = riga[1], riga[2]
        if tipo == "parametro" and org_id is None:
            permesso = "approvare_parametro_comune"  # parametri NEARTECH comuni: metodologia, sezione 9
        richiedi(conn, utente_id, permesso, org_id, risorsa=f"{tipo}:{oggetto_id}")
        _blocca(conn, f"decisione:{tipo}:{oggetto_id}")
        if atto == "approvazione":
            # Lo stesso lock delle nuove versioni: nessuna versione nuova si inserisce durante il controllo.
            _blocca(conn, f"versione:{tabella}:{codice}:{org_id}")
            superata = conn.execute(
                sql.SQL("""SELECT EXISTS (
                             SELECT 1 FROM {} t JOIN stato_oggetti_governance s
                               ON s.tipo_oggetto = %s AND s.oggetto_id = t.{}::text
                             WHERE t.codice = %s AND t.org_id IS NOT DISTINCT FROM %s AND t.versione > %s
                               AND s.ultimo_atto IN ('approvazione', 'ritiro'))""")
                .format(sql.Identifier(tabella), sql.Identifier(chiave)),
                (tipo, codice, org_id, versione),
            ).fetchone()[0]
            if superata:
                raise DecisioneGiaPresa(f"{tipo} {oggetto_id}: esiste una versione successiva già decisa")
        ultimo = conn.execute(
            "SELECT ultimo_atto FROM stato_oggetti_governance WHERE tipo_oggetto = %s AND oggetto_id = %s",
            (tipo, str(oggetto_id)),
        ).fetchone()
        ultimo_atto = ultimo[0] if ultimo else None
        if atto in ("approvazione", "rifiuto") and ultimo_atto is not None:
            raise DecisioneGiaPresa(f"{tipo} {oggetto_id}: già {ultimo_atto}")
        if atto == "ritiro" and ultimo_atto != "approvazione":
            raise DecisioneGiaPresa(f"{tipo} {oggetto_id}: si ritira solo una versione approvata")
        # Chi propone può anche decidere, ma l'atto lo dice (metodologia, sezione 10).
        proponente = conn.execute(
            sql.SQL("""SELECT r.autore_id FROM {} t JOIN registro_decisioni r ON r.decisione_id = t.proposta_id
                       WHERE t.{} = %s""").format(sql.Identifier(tabella), sql.Identifier(chiave)),
            (oggetto_id,),
        ).fetchone()
        if proponente is None:
            raise LookupError(f"{tipo} {oggetto_id}: proposta non trovata nel registro")
        proponente = proponente[0]
        return registra(conn, autore_id=utente_id, tipo_oggetto=tipo, oggetto_id=str(oggetto_id),
                        atto=atto, motivazione=motivazione, org_id=org_id,
                        dettagli={"stesso_proponente": proponente == uuid.UUID(str(utente_id))})


# --- parametri -------------------------------------------------------------------

def proponi_parametro(
    conn: psycopg.Connection,
    utente_id: str,
    *,
    codice: str,
    valore: Any,
    descrizione: str,
    motivazione: str,
    org_id: str | None,
) -> str:
    org_id = str(uuid.UUID(str(org_id))) if org_id is not None else None
    with conn.transaction():
        azione = "proporre_parametro_comune" if org_id is None else "proporre_parametro"
        richiedi(conn, utente_id, azione, org_id, risorsa=f"parametro:{codice}")
        schema = _spazio_richiesto(conn, org_id) if org_id is not None else None
        parametro_id = str(uuid.uuid4())
        versione = _prossima_versione(conn, "parametri_governance", codice, org_id)
        dettagli = {"codice": codice, "versione": versione, "valore": valore}
        if schema is not None:
            dettagli["hash_descrizione"] = impronta(chiave_spazio(conn, schema), descrizione)
        proposta = registra(
            conn, autore_id=utente_id, tipo_oggetto="parametro", oggetto_id=parametro_id, atto="proposta",
            motivazione=motivazione, org_id=org_id, dettagli=dettagli,
        )
        # La descrizione dei parametri comuni resta in public; quella dell'organizzazione va nel suo spazio.
        conn.execute(
            """INSERT INTO parametri_governance
                 (parametro_id, codice, org_id, versione, valore, descrizione, proposta_id)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (parametro_id, codice, org_id, versione, Jsonb(valore), descrizione if schema is None else None,
             proposta),
        )
        if schema is not None:
            conn.execute(sql.SQL("INSERT INTO {}.testi_parametri (parametro_id, descrizione) VALUES (%s, %s)")
                         .format(schema), (parametro_id, descrizione))
        return parametro_id


def approva_parametro(conn: psycopg.Connection, utente_id: str, parametro_id: str, *, motivazione: str) -> int:
    return _decidi(conn, utente_id, "parametro", parametro_id, "approvazione", motivazione)


def rifiuta_parametro(conn: psycopg.Connection, utente_id: str, parametro_id: str, *, motivazione: str) -> int:
    return _decidi(conn, utente_id, "parametro", parametro_id, "rifiuto", motivazione)


def ritira_parametro(conn: psycopg.Connection, utente_id: str, parametro_id: str, *, motivazione: str) -> int:
    return _decidi(conn, utente_id, "parametro", parametro_id, "ritiro", motivazione)



def parametro_vigente(conn: psycopg.Connection, codice: str, org_id: str | None) -> Parametro:
    """Versione vigente per l'organizzazione; se l'organizzazione non ne ha mai decisa una, quella comune.

    Una sola query: la scelta fra valore proprio, ritiro e valore comune vede un'unica fotografia.
    """
    riga = conn.execute(
        """WITH proprio AS (
             SELECT parametro_id, codice, org_id, versione, valore, approvazione_id, NULL::bigint AS adozione_id
             FROM parametri_vigenti WHERE codice = %(codice)s AND org_id = %(org)s::uuid
           ), deciso_proprio AS (
             SELECT 1 FROM parametri_governance p
             JOIN stato_oggetti_governance s
               ON s.tipo_oggetto = 'parametro' AND s.oggetto_id = p.parametro_id::text
             WHERE p.codice = %(codice)s AND p.org_id = %(org)s::uuid
               AND s.ultimo_atto IN ('approvazione', 'ritiro')
           ), comune AS (
             SELECT v.parametro_id, v.codice, v.org_id, v.versione, v.valore, v.approvazione_id,
                    (SELECT a.decisione_id FROM registro_decisioni a
                     WHERE a.atto = 'adozione' AND a.org_id = %(org)s::uuid
                       AND a.oggetto_id = v.parametro_id::text) AS adozione_id
             FROM parametri_vigenti v WHERE v.codice = %(codice)s AND v.org_id IS NULL
           )
           SELECT 'proprio', * FROM proprio
           UNION ALL
           SELECT 'ritirato', NULL, NULL, NULL, NULL, NULL, NULL, NULL
           WHERE NOT EXISTS (SELECT 1 FROM proprio) AND EXISTS (SELECT 1 FROM deciso_proprio)
           UNION ALL
           SELECT 'comune', * FROM comune
           WHERE NOT EXISTS (SELECT 1 FROM proprio) AND NOT EXISTS (SELECT 1 FROM deciso_proprio)""",
        {"codice": codice, "org": org_id},
    ).fetchone()
    if riga is None:
        raise ParametroAssente(f"nessun valore approvato per '{codice}'")
    if riga[0] == "ritirato":
        raise ParametroRitirato(f"'{codice}' ritirato dall'organizzazione, nessuna versione nuova approvata")
    return Parametro(str(riga[1]), riga[2], str(riga[3]) if riga[3] else None, riga[4], riga[5], riga[6], riga[7])


# --- indirizzi del comitato -------------------------------------------------------

def proponi_indirizzo(
    conn: psycopg.Connection,
    utente_id: str,
    *,
    org_id: str,
    codice: str,
    testo: str,
    ambito: str,
    motivazione: str,
) -> str:
    org_id = str(uuid.UUID(str(org_id)))
    with conn.transaction():
        richiedi(conn, utente_id, "proporre_indirizzo", org_id, risorsa=f"indirizzo:{codice}")
        schema = _spazio_richiesto(conn, org_id)
        indirizzo_id = str(uuid.uuid4())
        versione = _prossima_versione(conn, "indirizzi_comitato", codice, org_id)
        proposta = registra(
            conn, autore_id=utente_id, tipo_oggetto="indirizzo", oggetto_id=indirizzo_id, atto="proposta",
            motivazione=motivazione, org_id=org_id,
            dettagli={"codice": codice, "versione": versione,
                      "hash_contenuto": _hash_indirizzo(chiave_spazio(conn, schema), testo, ambito)},
        )
        conn.execute(
            """INSERT INTO indirizzi_comitato (indirizzo_id, org_id, codice, versione, proposta_id)
               VALUES (%s, %s, %s, %s, %s)""",
            (indirizzo_id, org_id, codice, versione, proposta),
        )
        conn.execute(
            sql.SQL("INSERT INTO {}.testi_indirizzi (indirizzo_id, testo, ambito) VALUES (%s, %s, %s)").format(schema),
            (indirizzo_id, testo, ambito),
        )
        return indirizzo_id


def approva_indirizzo(conn: psycopg.Connection, utente_id: str, indirizzo_id: str, *, motivazione: str) -> int:
    return _decidi(conn, utente_id, "indirizzo", indirizzo_id, "approvazione", motivazione)


def rifiuta_indirizzo(conn: psycopg.Connection, utente_id: str, indirizzo_id: str, *, motivazione: str) -> int:
    return _decidi(conn, utente_id, "indirizzo", indirizzo_id, "rifiuto", motivazione)


def ritira_indirizzo(conn: psycopg.Connection, utente_id: str, indirizzo_id: str, *, motivazione: str) -> int:
    return _decidi(conn, utente_id, "indirizzo", indirizzo_id, "ritiro", motivazione)


def indirizzi_vigenti(conn: psycopg.Connection, org_id: str) -> list[Indirizzo]:
    schema = _spazio_richiesto(conn, org_id)
    return [
        Indirizzo(str(r[0]), str(r[1]), r[2], r[3], r[4], r[5], r[6])
        for r in conn.execute(
            sql.SQL("""SELECT v.indirizzo_id, v.org_id, v.codice, v.versione, t.testo, t.ambito, v.approvazione_id
                       FROM indirizzi_vigenti v JOIN {}.testi_indirizzi t USING (indirizzo_id)
                       WHERE v.org_id = %s ORDER BY v.codice""").format(schema),
            (org_id,),
        )
    ]


def verifica_contenuti(conn: psycopg.Connection, org_id: str | None = None) -> list[tuple[str, str]]:
    """Confronta parametri e indirizzi con quanto registrato nella loro proposta. Restituisce le discordanze.

    I testi delle organizzazioni si confrontano, nel loro spazio, con l'impronta registrata nella proposta.
    Con org_id, solo gli oggetti di quell'organizzazione.
    """
    discordanze = {
        (r[0], str(r[1]))
        for r in conn.execute(
            """SELECT 'parametro', p.parametro_id
               FROM parametri_governance p JOIN registro_decisioni r ON r.decisione_id = p.proposta_id
               WHERE (%(org)s::uuid IS NULL OR p.org_id = %(org)s::uuid)
                 AND (r.dettagli -> 'valore' IS DISTINCT FROM p.valore
                  OR r.org_id IS DISTINCT FROM p.org_id
                  OR r.dettagli ->> 'codice' IS DISTINCT FROM p.codice
                  OR (r.dettagli ->> 'versione')::int IS DISTINCT FROM p.versione)
               UNION ALL
               SELECT 'indirizzo', i.indirizzo_id
               FROM indirizzi_comitato i JOIN registro_decisioni r ON r.decisione_id = i.proposta_id
               WHERE (%(org)s::uuid IS NULL OR i.org_id = %(org)s::uuid)
                 AND (r.org_id IS DISTINCT FROM i.org_id
                  OR r.dettagli ->> 'codice' IS DISTINCT FROM i.codice
                  OR (r.dettagli ->> 'versione')::int IS DISTINCT FROM i.versione)""",
            {"org": org_id},
        )
    }
    for org, schema in _spazi(conn, org_id):
        discordanze.update(
            (r[0], str(r[1]))
            for r in conn.execute(
                sql.SQL("""SELECT 'parametro', p.parametro_id
                           FROM parametri_governance p JOIN registro_decisioni r ON r.decisione_id = p.proposta_id
                           LEFT JOIN {0}.testi_parametri t USING (parametro_id)
                           CROSS JOIN {0}.chiave_impronte k
                           WHERE p.org_id = %(org)s
                             AND (t.descrizione IS NULL OR r.dettagli ->> 'hash_descrizione' IS DISTINCT FROM
                                  encode(sha256(k.chiave || convert_to(t.descrizione, 'UTF8')), 'hex'))
                           UNION ALL
                           SELECT 'indirizzo', i.indirizzo_id
                           FROM indirizzi_comitato i JOIN registro_decisioni r ON r.decisione_id = i.proposta_id
                           LEFT JOIN {0}.testi_indirizzi t USING (indirizzo_id)
                           CROSS JOIN {0}.chiave_impronte k
                           WHERE i.org_id = %(org)s
                             AND (t.testo IS NULL OR r.dettagli ->> 'hash_contenuto' IS DISTINCT FROM
                                  encode(sha256(k.chiave || convert_to(t.testo || chr(31) || t.ambito, 'UTF8')),
                                         'hex'))""")
                .format(schema),
                {"org": org},
            )
        )
    return sorted(discordanze)


# --- parametri comuni e comitato guida ------------------------------------------------

def _parametro_comune_vigente(conn: psycopg.Connection, parametro_id: str) -> str:
    """Codice del parametro, se è la versione comune vigente; sotto lock contro nuove decisioni comuni."""
    riga = conn.execute(
        "SELECT codice, org_id FROM parametri_governance WHERE parametro_id = %s", (parametro_id,)
    ).fetchone()
    if riga is None:
        raise LookupError(f"parametro {parametro_id} inesistente")
    if riga[1] is not None:
        raise ValueError(f"il parametro {parametro_id} non è comune: si decide nell'organizzazione")
    _blocca(conn, f"versione:parametri_governance:{riga[0]}:None")
    vigente = conn.execute(
        "SELECT parametro_id FROM parametri_vigenti WHERE codice = %s AND org_id IS NULL", (riga[0],)
    ).fetchone()
    if vigente is None or str(vigente[0]) != parametro_id:
        raise ValueError(f"il parametro {parametro_id} non è la versione comune vigente")
    return riga[0]


def _atto_su_parametro_comune(
    conn: psycopg.Connection, utente_id: str, permesso: str, atto: str,
    org_id: str, parametro_id: str, motivazione: str,
) -> int:
    org_id = str(uuid.UUID(str(org_id)))
    parametro_id = str(uuid.UUID(str(parametro_id)))
    if not motivazione.strip():
        raise ValueError("motivazione obbligatoria")
    with conn.transaction():
        richiedi(conn, utente_id, permesso, org_id, risorsa=f"parametro:{parametro_id}")
        codice = _parametro_comune_vigente(conn, parametro_id)
        if atto == "adozione" and conn.execute(
            """SELECT EXISTS (SELECT 1 FROM registro_decisioni
                              WHERE atto = 'adozione' AND org_id = %s AND oggetto_id = %s)""",
            (org_id, parametro_id),
        ).fetchone()[0]:
            raise DecisioneGiaPresa(f"parametro {parametro_id}: già adottato dall'organizzazione")
        return registra(conn, autore_id=utente_id, tipo_oggetto="parametro", oggetto_id=parametro_id, atto=atto,
                        motivazione=motivazione, org_id=org_id, dettagli={"codice": codice})


def adotta_parametro_comune(
    conn: psycopg.Connection, utente_id: str, *, org_id: str, parametro_id: str, motivazione: str
) -> int:
    """Il comitato guida adotta la versione comune vigente. Una versione nuova va adottata di nuovo."""
    return _atto_su_parametro_comune(conn, utente_id, "adottare_parametro_comune", "adozione",
                                     org_id, parametro_id, motivazione)


def chiedi_ricalibrazione(
    conn: psycopg.Connection, utente_id: str, *, org_id: str, parametro_id: str, motivazione: str
) -> int:
    """Il comitato guida chiede all'amministratore tecnico di ricalibrare un parametro comune, motivando."""
    return _atto_su_parametro_comune(conn, utente_id, "chiedere_ricalibrazione", "richiesta_ricalibrazione",
                                     org_id, parametro_id, motivazione)


def parametri_comuni(conn: psycopg.Connection, utente_id: str, org_id: str) -> list[StatoParametroComune]:
    """Parametri comuni vigenti e, per ciascuno, l'ultimo atto dell'organizzazione sulla versione vigente."""
    org_id = str(uuid.UUID(str(org_id)))
    richiedi(conn, utente_id, "leggere", org_id, risorsa="parametri_comuni")
    righe = conn.execute(
        """SELECT v.parametro_id, v.codice, v.versione, v.valore, v.descrizione, a.atto, a.decisione_id,
                  EXISTS (SELECT 1 FROM parametri_governance p
                          JOIN stato_oggetti_governance s
                            ON s.tipo_oggetto = 'parametro' AND s.oggetto_id = p.parametro_id::text
                          WHERE p.codice = v.codice AND p.org_id = %(org)s
                            AND s.ultimo_atto IN ('approvazione', 'ritiro')) AS proprio
           FROM parametri_vigenti v
           LEFT JOIN LATERAL (
             SELECT r.atto, r.decisione_id FROM registro_decisioni r
             WHERE r.org_id = %(org)s AND r.oggetto_id = v.parametro_id::text
               AND r.atto IN ('adozione', 'richiesta_ricalibrazione')
             ORDER BY r.posizione DESC LIMIT 1
           ) a ON true
           WHERE v.org_id IS NULL ORDER BY v.codice""",
        {"org": org_id},
    ).fetchall()
    stati = {"adozione": "adottato", "richiesta_ricalibrazione": "ricalibrazione_richiesta", None: "da_esaminare"}
    return [
        StatoParametroComune(str(r[0]), r[1], r[2], r[3], r[4], "parametro_proprio" if r[7] else stati[r[5]], r[6])
        for r in righe
    ]


def richieste_ricalibrazione(conn: psycopg.Connection, utente_id: str) -> list[dict[str, Any]]:
    """Richieste dei comitati, con la motivazione letta dallo spazio di ciascuna organizzazione.

    Ogni spazio letto lascia la sua voce nel log di accesso, con l'organizzazione. Una richiesta è
    superata quando la versione comune a cui si riferisce non è più vigente (nuova versione o ritiro).
    """
    richiedi(conn, utente_id, "approvare_parametro_comune", risorsa="richieste_ricalibrazione")
    richieste = []
    for org_id, schema in _spazi(conn):
        richiedi(conn, utente_id, "approvare_parametro_comune", org_id, risorsa="richieste_ricalibrazione")
        for r in conn.execute(
            sql.SQL("""SELECT r.decisione_id, r.oggetto_id, r.dettagli ->> 'codice', r.autore_id, r.registrata_il,
                              t.motivazione,
                              NOT EXISTS (SELECT 1 FROM parametri_vigenti v
                                          WHERE v.org_id IS NULL AND v.parametro_id::text = r.oggetto_id)
                       FROM registro_decisioni r LEFT JOIN {}.testi_atti t USING (decisione_id)
                       WHERE r.org_id = %s AND r.atto = 'richiesta_ricalibrazione'
                       ORDER BY r.posizione""").format(schema),
            (org_id,),
        ):
            richieste.append({"decisione_id": r[0], "org_id": org_id, "parametro_id": r[1], "codice": r[2],
                              "autore_id": str(r[3]), "registrata_il": r[4], "motivazione": r[5],
                              "superata": r[6]})
    return sorted(richieste, key=lambda r: r["decisione_id"])


# --- segnalazioni dei revisori ---------------------------------------------------

def segnala(
    conn: psycopg.Connection,
    utente_id: str,
    *,
    org_id: str,
    tipo_oggetto: str,
    oggetto_id: str,
    motivazione: str,
    dettagli: dict[str, Any] | None = None,
) -> int:
    """Segnalazione di un revisore, visibile a comitato guida, auditor e rappresentanti.

    Per parametri e indirizzi l'oggetto deve appartenere all'organizzazione del revisore.
    Motivazione e dettagli sono testo del revisore: stanno nello spazio dell'organizzazione (ADR 0004).
    """
    org_id = str(uuid.UUID(str(org_id)))
    with conn.transaction():
        richiedi(conn, utente_id, "segnalare", org_id, risorsa=f"{tipo_oggetto}:{oggetto_id}")
        if tipo_oggetto in _OGGETTI:
            oggetto_id = str(uuid.UUID(str(oggetto_id)))
            tabella, chiave, _ = _OGGETTI[tipo_oggetto]
            proprio = conn.execute(
                sql.SQL("SELECT EXISTS (SELECT 1 FROM {} WHERE {}::text = %s AND org_id = %s)")
                .format(sql.Identifier(tabella), sql.Identifier(chiave)),
                (str(oggetto_id), org_id),
            ).fetchone()[0]
            if not proprio:
                raise LookupError(f"{tipo_oggetto} {oggetto_id} non appartiene all'organizzazione")
        return registra(conn, autore_id=utente_id, tipo_oggetto=tipo_oggetto, oggetto_id=str(oggetto_id),
                        atto="segnalazione", motivazione=motivazione, org_id=org_id,
                        dettagli_riservati=dettagli)
