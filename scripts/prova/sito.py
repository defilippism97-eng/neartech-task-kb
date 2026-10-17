"""Seme di prova della corsia «sito» (docs/piani/fase-6-cantiere.md): sito pubblico e candidature ai piloti.

Modulo della sola corsia sito. Gira dopo il seme di base (ACME S.p.A.) e dopo le corsie che lo precedono in
prova.SEMI, e ne usa gli identificativi dal contesto.
"""

import psycopg

from .comune import Contesto


def semina(conn: psycopg.Connection, ctx: Contesto) -> None:
    """Dati di prova della corsia sito.

    Per ora non semina nulla. Dati sintetici della corsia, solo nel database temporaneo della prova; ciò che serve
    ad altre corsie va in ctx.extra["sito"].
    """
