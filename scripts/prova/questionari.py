"""Seme di prova della corsia «questionari» (docs/piani/fase-6-cantiere.md): questionari d3/d4 e rotte pubbliche per
chi risponde.

Modulo della sola corsia questionari. Gira dopo il seme di base (ACME S.p.A.) e dopo le corsie che lo precedono in
prova.SEMI, e ne usa gli identificativi dal contesto.
"""

import psycopg

from .comune import Contesto


def semina(conn: psycopg.Connection, ctx: Contesto) -> None:
    """Dati di prova della corsia questionari.

    Per ora non semina nulla. Dati sintetici della corsia, solo nel database temporaneo della prova; ciò che serve
    ad altre corsie va in ctx.extra["questionari"].
    """
