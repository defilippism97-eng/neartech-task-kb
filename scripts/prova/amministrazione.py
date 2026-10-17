"""Seme di prova della corsia «amministrazione» (docs/piani/fase-6-cantiere.md): account, credenziali, utenti,
ruoli, organizzazioni e console di amministrazione.

Modulo della sola corsia amministrazione. Gira dopo il seme di base (ACME S.p.A.) e dopo le corsie che lo precedono
in prova.SEMI, e ne usa gli identificativi dal contesto.
"""

import psycopg

from .comune import Contesto


def semina(conn: psycopg.Connection, ctx: Contesto) -> None:
    """Dati di prova della corsia amministrazione.

    Per ora non semina nulla. Dati sintetici della corsia, solo nel database temporaneo della prova; ciò che serve
    ad altre corsie va in ctx.extra["amministrazione"].
    """
