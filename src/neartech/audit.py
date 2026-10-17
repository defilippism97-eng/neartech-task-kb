"""Report di audit unico per organizzazione (ADR 0004).

Raccoglie in un documento l'analisi e le decisioni di un'organizzazione: atti del registro con i
testi letti dal suo spazio, parametri propri e comuni (con l'adozione del comitato), indirizzi,
ruoli, campioni di revisione e misure, stati dei task decisi dall'organizzazione, e i controlli di
integrità (catena del registro, testi nello spazio, contenuti di parametri e indirizzi).

Il report contiene testo dell'organizzazione: si conserva fuori dal repository.
Sola lettura; serve il permesso leggere_audit.
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

import psycopg
from psycopg import sql

from neartech.governance import parametri_comuni, verifica_contenuti
from neartech.permessi import richiedi
from neartech.registro import MARCATORE_SPAZIO, spazio, verifica_catena, verifica_testi

VERSIONE_REPORT = "report-audit-v1"


def _json(valore: Any) -> Any:
    if isinstance(valore, dict):
        return {k: _json(v) for k, v in valore.items()}
    if isinstance(valore, (list, tuple)):
        return [_json(v) for v in valore]
    if isinstance(valore, datetime):
        return valore.isoformat()
    if isinstance(valore, Decimal):
        return float(valore)
    if isinstance(valore, uuid.UUID):
        return str(valore)
    return valore


def _righe(conn: psycopg.Connection, query: sql.Composable | str, parametri: Any) -> list[dict[str, Any]]:
    cursore = conn.execute(query, parametri)
    nomi = [c.name for c in cursore.description]
    return [dict(zip(nomi, r)) for r in cursore.fetchall()]


def report_organizzazione(
    conn: psycopg.Connection, utente_id: str, org_id: str, *, ancora: tuple[int, str] | None = None
) -> dict[str, Any]:
    org_id = str(uuid.UUID(str(org_id)))
    richiedi(conn, utente_id, "leggere_audit", org_id, risorsa=f"report_audit:{org_id}")
    organizzazione = conn.execute(
        "SELECT org_id, name, codice FROM organizations WHERE org_id = %s", (org_id,)
    ).fetchone()
    if organizzazione is None:
        raise LookupError(f"organizzazione {org_id} inesistente")
    schema = spazio(conn, org_id)
    if schema is None:
        raise LookupError(f"l'organizzazione {org_id} non ha uno spazio")

    atti = _righe(conn, sql.SQL(
        """SELECT r.posizione, r.decisione_id, r.registrata_il, r.tipo_oggetto, r.oggetto_id, r.atto,
                  u.soggetto_sso AS autore, COALESCE(t.motivazione, r.motivazione) AS motivazione,
                  r.dettagli, COALESCE(t.dettagli, '{{}}'::jsonb) AS dettagli_riservati, r.corregge_id,
                  r.motivazione = %(marcatore)s AS testo_nello_spazio
           FROM registro_decisioni r JOIN utenti u ON u.utente_id = r.autore_id
           LEFT JOIN {}.testi_atti t USING (decisione_id)
           WHERE r.org_id = %(org)s ORDER BY r.posizione""").format(schema),
        {"org": org_id, "marcatore": MARCATORE_SPAZIO})
    for atto in atti:
        atto["dettagli"] = {k: v for k, v in atto["dettagli"].items() if k != "hash_testo"}

    indirizzi = _righe(conn, sql.SQL(
        """SELECT i.indirizzo_id, i.codice, i.versione, t.testo, t.ambito,
                  COALESCE(s.ultimo_atto, 'proposta') AS stato
           FROM indirizzi_comitato i LEFT JOIN {}.testi_indirizzi t USING (indirizzo_id)
           LEFT JOIN stato_oggetti_governance s
             ON s.tipo_oggetto = 'indirizzo' AND s.oggetto_id = i.indirizzo_id::text
           WHERE i.org_id = %s ORDER BY i.codice, i.versione""").format(schema), (org_id,))

    parametri_propri = _righe(conn, sql.SQL(
        """SELECT p.parametro_id, p.codice, p.versione, p.valore, t.descrizione,
                  COALESCE(s.ultimo_atto, 'proposta') AS stato
           FROM parametri_governance p LEFT JOIN {}.testi_parametri t USING (parametro_id)
           LEFT JOIN stato_oggetti_governance s
             ON s.tipo_oggetto = 'parametro' AND s.oggetto_id = p.parametro_id::text
           WHERE p.org_id = %s ORDER BY p.codice, p.versione""").format(schema), (org_id,))

    comuni = [vars(p) for p in parametri_comuni(conn, utente_id, org_id)]

    ruoli = _righe(conn,
        """SELECT u.soggetto_sso AS utente, a.ruolo, a.valida_dal, a.valida_al
           FROM assegnazioni_ruolo a JOIN utenti u USING (utente_id)
           WHERE a.org_id = %s ORDER BY a.ruolo, a.valida_dal""", (org_id,))

    campioni = _righe(conn,
        """SELECT c.campione_id, c.tipo_proposta, c.criterio, c.seme, c.popolazione, c.dimensione,
                  c.versione_istruzioni, c.creato_il,
                  (SELECT jsonb_object_agg(esito, n) FROM (
                     SELECT esito, count(*) AS n FROM (
                       SELECT DISTINCT ON (g.posizione, g.revisore_id) g.esito
                       FROM giudizi_revisione g WHERE g.campione_id = c.campione_id
                       ORDER BY g.posizione, g.revisore_id, g.giudizio_id DESC) ultimi
                     GROUP BY esito) conteggi) AS giudizi
           FROM campioni_revisione c WHERE c.org_id = %s ORDER BY c.creato_il""", (org_id,))
    for campione in campioni:
        campione["misure"] = _righe(conn,
            """SELECT misura_id, calcolata_il, n_elementi, n_corretti, n_parziali, n_errati, regola_parziali,
                      precisione, intervallo_basso, intervallo_alto, livello_confidenza, soglia, esito,
                      soglia_nell_intervallo, parametro_soglia_id, parametro_regola_id, parametro_confidenza_id,
                      origine_proposte, versione_calcolo, versione_istruzioni
               FROM misure_precisione WHERE campione_id = %s ORDER BY calcolata_il""",
            (campione["campione_id"],))

    stati_task = dict(conn.execute(
        """SELECT stato, count(*) FROM (
             SELECT DISTINCT ON (v.task_id) v.stato
             FROM stati_validazione_task v JOIN registro_decisioni r ON r.decisione_id = v.decisione_id
             WHERE r.org_id = %s ORDER BY v.task_id, v.cambio_id DESC) ultimi
           GROUP BY stato ORDER BY stato""", (org_id,)).fetchall())

    propri = {str(p["parametro_id"]) for p in parametri_propri} | {str(i["indirizzo_id"]) for i in indirizzi}
    posizione_alterata = verifica_catena(conn, ancora=ancora)
    integrita = {
        "catena": "integra" if posizione_alterata is None else f"alterata dalla posizione {posizione_alterata}",
        "ancora": list(ancora) if ancora else None,
        "testi": [{"decisione_id": d, "problema": p} for d, p in verifica_testi(conn, org_id)],
        "contenuti": [{"tipo": t, "oggetto_id": o} for t, o in verifica_contenuti(conn) if o in propri],
    }

    return _json({
        "versione_report": VERSIONE_REPORT,
        "generato_il": datetime.now(timezone.utc),
        "organizzazione": {"org_id": organizzazione[0], "nome": organizzazione[1], "codice": organizzazione[2]},
        "integrita": integrita,
        "parametri_comuni": comuni,
        "parametri_propri": parametri_propri,
        "indirizzi": indirizzi,
        "ruoli": ruoli,
        "campioni": campioni,
        "stati_task": stati_task,
        "atti": atti,
    })


def _tabella(intestazioni: list[str], righe: list[list[Any]]) -> list[str]:
    def cella(v: Any) -> str:
        return ("" if v is None else str(v)).replace("|", "\\|").replace("\n", " ")
    return (["| " + " | ".join(intestazioni) + " |", "|" + "---|" * len(intestazioni)]
            + ["| " + " | ".join(cella(v) for v in r) + " |" for r in righe] + [""])


def report_in_markdown(report: dict[str, Any]) -> str:
    """Versione leggibile del report. Il JSON resta la fonte per la verifica."""
    o, i = report["organizzazione"], report["integrita"]
    righe = [f"# Report di audit: {o['nome']} ({o['codice']})", "",
             f"Versione {report['versione_report']}, generato il {report['generato_il']}.", "",
             "## Integrità", "",
             f"- Catena del registro: {i['catena']}" + (f" (ancora {i['ancora'][0]})" if i["ancora"] else ""),
             f"- Testi nello spazio non corrispondenti: {len(i['testi'])}",
             f"- Parametri o indirizzi non corrispondenti alla proposta: {len(i['contenuti'])}", "",
             "## Parametri comuni", ""]
    righe += _tabella(["Codice", "Versione", "Valore", "Stato per l'organizzazione"],
                      [[p["codice"], p["versione"], p["valore"], p["stato"]] for p in report["parametri_comuni"]])
    righe += ["## Parametri dell'organizzazione", ""]
    righe += _tabella(["Codice", "Versione", "Valore", "Stato", "Descrizione"],
                      [[p["codice"], p["versione"], p["valore"], p["stato"], p["descrizione"]]
                       for p in report["parametri_propri"]])
    righe += ["## Indirizzi del comitato guida", ""]
    righe += _tabella(["Codice", "Versione", "Stato", "Testo", "Ambito"],
                      [[x["codice"], x["versione"], x["stato"], x["testo"], x["ambito"]] for x in report["indirizzi"]])
    righe += ["## Ruoli", ""]
    righe += _tabella(["Utente", "Ruolo", "Dal", "Al"],
                      [[r["utente"], r["ruolo"], r["valida_dal"], r["valida_al"]] for r in report["ruoli"]])
    righe += ["## Campioni e misure", ""]
    for c in report["campioni"]:
        righe += [f"- Campione {c['campione_id']} ({c['tipo_proposta']}, {c['criterio']}, "
                  f"{c['dimensione']} su {c['popolazione']}, istruzioni {c['versione_istruzioni']}): "
                  f"giudizi {c['giudizi'] or {}}"]
        righe += [f"  - misura {m['calcolata_il']}: precisione {m['precisione']:.3f} "
                  f"[{m['intervallo_basso']:.3f}; {m['intervallo_alto']:.3f}], soglia {m['soglia']}, "
                  f"regola parziali {m['regola_parziali']}, esito {m['esito']}" for m in c["misure"]]
    righe += ["", "## Stati dei task decisi dall'organizzazione", ""]
    righe += [f"- {stato}: {n}" for stato, n in report["stati_task"].items()] + [""]
    righe += ["## Atti", ""]
    righe += _tabella(["Pos.", "Data", "Oggetto", "Atto", "Autore", "Motivazione", "Stesso proponente"],
                      [[a["posizione"], a["registrata_il"], f"{a['tipo_oggetto']} {a['oggetto_id']}", a["atto"],
                        a["autore"], a["motivazione"], a["dettagli"].get("stesso_proponente", "")]
                       for a in report["atti"]])
    return "\n".join(righe)
