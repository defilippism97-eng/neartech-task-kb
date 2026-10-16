"""Coda dei job: presa in carico esclusiva, tentativi, recupero dei job bloccati."""

from datetime import timedelta

import psycopg
import pytest

from neartech.coda import accoda, completa, fallisci, prendi, recupera_bloccati


def _stato(conn, job_id):
    return conn.execute("SELECT status, attempts FROM jobs WHERE job_id = %s", (job_id,)).fetchone()


def test_accoda_e_prendi(conn):
    job = accoda(conn, "prova", {"x": 1})
    preso = prendi(conn, "lavoratore-1", tipi=["prova"])
    assert preso.job_id == job
    assert preso.payload == {"x": 1}
    assert _stato(conn, job) == ("running", 1)
    assert prendi(conn, "lavoratore-1", tipi=["prova"]) is None


def test_job_futuro_non_viene_preso(conn):
    accoda(conn, "prova", {}, esegui_dopo=timedelta(hours=1))
    assert prendi(conn, "lavoratore-1", tipi=["prova"]) is None


def test_completa(conn):
    job = accoda(conn, "prova", {})
    prendi(conn, "lavoratore-1", tipi=["prova"])
    assert completa(conn, job, "lavoratore-1")
    assert _stato(conn, job) == ("done", 1)


def test_solo_chi_ha_preso_il_job_lo_chiude(conn):
    job = accoda(conn, "prova", {})
    prendi(conn, "lavoratore-1", tipi=["prova"])
    assert not completa(conn, job, "lavoratore-2")
    assert not fallisci(conn, job, "lavoratore-2", "errore", riprova_tra=timedelta(0))
    assert _stato(conn, job) == ("running", 1)


def test_fallimento_rimette_in_coda_finche_restano_tentativi(conn):
    job = accoda(conn, "prova", {}, tentativi_massimi=2)
    prendi(conn, "lavoratore-1", tipi=["prova"])
    fallisci(conn, job, "lavoratore-1", "errore uno", riprova_tra=timedelta(0))
    assert _stato(conn, job) == ("queued", 1)
    prendi(conn, "lavoratore-1", tipi=["prova"])
    fallisci(conn, job, "lavoratore-1", "errore due", riprova_tra=timedelta(0))
    assert _stato(conn, job) == ("failed", 2)
    assert conn.execute("SELECT ultimo_errore FROM jobs WHERE job_id = %s", (job,)).fetchone()[0] == "errore due"


def test_recupera_job_bloccati(conn):
    job = accoda(conn, "prova", {}, tentativi_massimi=2)
    prendi(conn, "lavoratore-1", tipi=["prova"])
    conn.execute("UPDATE jobs SET preso_il = now() - interval '2 hours' WHERE job_id = %s", (job,))
    assert recupera_bloccati(conn, piu_vecchi_di=timedelta(hours=1)) == 1
    assert _stato(conn, job)[0] == "queued"


def test_job_bloccato_senza_tentativi_residui_fallisce(conn):
    job = accoda(conn, "prova", {}, tentativi_massimi=1)
    prendi(conn, "lavoratore-1", tipi=["prova"])
    conn.execute("UPDATE jobs SET preso_il = now() - interval '2 hours' WHERE job_id = %s", (job,))
    recupera_bloccati(conn, piu_vecchi_di=timedelta(hours=1))
    assert _stato(conn, job)[0] == "failed"


def test_due_lavoratori_non_prendono_lo_stesso_job(dsn):
    with psycopg.connect(dsn, autocommit=True) as setup:
        job = accoda(setup, "prova_concorrenza", {})
    try:
        with psycopg.connect(dsn) as primo, psycopg.connect(dsn) as secondo:
            preso_primo = prendi(primo, "lavoratore-1", tipi=["prova_concorrenza"])
            preso_secondo = prendi(secondo, "lavoratore-2", tipi=["prova_concorrenza"])
            assert preso_primo.job_id == job
            assert preso_secondo is None
            primo.rollback()
            secondo.rollback()
    finally:
        with psycopg.connect(dsn, autocommit=True) as pulizia:
            pulizia.execute("DELETE FROM jobs WHERE kind = 'prova_concorrenza'")
