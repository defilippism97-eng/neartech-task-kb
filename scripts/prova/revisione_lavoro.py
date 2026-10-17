"""Seme di prova della corsia «revisione_lavoro» (docs/piani/fase-6-cantiere.md): lavoro del revisore: giudizi sulla
rubrica, lotti, coda unificata, somiglianze, ritaratura.

Modulo della sola corsia revisione_lavoro. Gira dopo il seme di base (ACME S.p.A.) e dopo le corsie che lo precedono
in prova.SEMI, e ne usa gli identificativi dal contesto.
"""

import psycopg

from .comune import Contesto


def semina(conn: psycopg.Connection, ctx: Contesto) -> None:
    """Dati di prova della corsia revisione_lavoro.

    Per ora non semina nulla. Dati sintetici della corsia, solo nel database temporaneo della prova; ciò che serve
    ad altre corsie va in ctx.extra["revisione_lavoro"].
    """
