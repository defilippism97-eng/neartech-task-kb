"""Seme di prova della corsia «flusso» (docs/piani/fase-6-cantiere.md): lavori di ricalcolo, fase di verifica,
storico e stampa delle restituzioni, reversibilità della pipeline dei documenti.

Modulo della sola corsia flusso. Gira dopo il seme di base (ACME S.p.A.) e dopo le corsie che lo precedono in
prova.SEMI, e ne usa gli identificativi dal contesto.
"""

import psycopg

from .comune import Contesto


def semina(conn: psycopg.Connection, ctx: Contesto) -> None:
    """Dati di prova della corsia flusso.

    Per ora non semina nulla. Dati sintetici della corsia, solo nel database temporaneo della prova; ciò che serve
    ad altre corsie va in ctx.extra["flusso"].
    """
