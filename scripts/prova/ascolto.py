"""Seme di prova della corsia «ascolto» (docs/piani/fase-6-cantiere.md): ascolto del comitato: materiali,
interviste, schede di scenario, stima dei pesi.

Modulo della sola corsia ascolto. Gira dopo il seme di base (ACME S.p.A.) e dopo le corsie che lo precedono in
prova.SEMI, e ne usa gli identificativi dal contesto.
"""

import psycopg

from .comune import Contesto


def semina(conn: psycopg.Connection, ctx: Contesto) -> None:
    """Dati di prova della corsia ascolto.

    Per ora non semina nulla. Dati sintetici della corsia, solo nel database temporaneo della prova; ciò che serve
    ad altre corsie va in ctx.extra["ascolto"].
    """
