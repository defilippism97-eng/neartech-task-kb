"""Registro delle migrazioni: ogni file applicato è registrato con il suo hash,
e una migrazione già applicata non può essere modificata in silenzio."""

import shutil
from pathlib import Path

import psycopg
import pytest

from neartech.migrazioni import (
    CARTELLA_CONDIVISA,
    MigrazioneModificata,
    applica,
    da_applicare,
    hash_migrazione,
    inizializza_registro,
    percorso_migrazione,
    registra_senza_eseguire,
)


def _copia_migrazioni(destinazione: Path) -> Path:
    cartella = destinazione / "migrazioni"
    shutil.copytree(CARTELLA_CONDIVISA, cartella)
    return cartella


def test_registro_contiene_tutte_le_migrazioni_con_hash(conn):
    righe = dict(conn.execute(
        "SELECT nome, hash_sha256 FROM public.migrazioni_applicate WHERE schema_destinazione = 'public'"
    ).fetchall())
    attese = {p.name: hash_migrazione(p) for p in sorted(CARTELLA_CONDIVISA.glob("*.sql"))}
    assert righe == attese


def test_nulla_da_applicare_dopo_la_preparazione(conn):
    assert da_applicare(conn, CARTELLA_CONDIVISA) == []


def test_hash_ignora_la_differenza_tra_fine_riga(tmp_path):
    lf = tmp_path / "lf.sql"
    crlf = tmp_path / "crlf.sql"
    lf.write_bytes(b"SELECT 1;\nSELECT 2;\n")
    crlf.write_bytes(b"SELECT 1;\r\nSELECT 2;\r\n")
    assert hash_migrazione(lf) == hash_migrazione(crlf)


def test_migrazione_modificata_viene_rilevata(conn, tmp_path):
    cartella = _copia_migrazioni(tmp_path)
    prima = sorted(cartella.glob("*.sql"))[0]
    prima.write_text(prima.read_text(encoding="utf-8") + "\n-- modifica successiva\n", encoding="utf-8")
    with pytest.raises(MigrazioneModificata):
        da_applicare(conn, cartella)


def test_file_nuovo_risulta_da_applicare(conn, tmp_path):
    cartella = _copia_migrazioni(tmp_path)
    nuovo = cartella / "9999_prova.sql"
    nuovo.write_text("CREATE TABLE prova_migrazione (x int);", encoding="utf-8")
    assert da_applicare(conn, cartella) == [nuovo]


def test_applica_esegue_e_registra(conn, tmp_path):
    cartella = _copia_migrazioni(tmp_path)
    (cartella / "9999_prova.sql").write_text("CREATE TABLE prova_migrazione (x int);", encoding="utf-8")

    applicate = applica(conn, cartella)

    assert [p.name for p in applicate] == ["9999_prova.sql"]
    assert conn.execute("SELECT to_regclass('public.prova_migrazione')").fetchone()[0] is not None
    assert da_applicare(conn, cartella) == []


def test_senza_registro_tutte_le_migrazioni_risultano_da_applicare(conn):
    conn.execute("ALTER TABLE public.migrazioni_applicate RENAME TO migrazioni_nascoste")
    assert [p.name for p in da_applicare(conn, CARTELLA_CONDIVISA)] == [
        p.name for p in sorted(CARTELLA_CONDIVISA.glob("*.sql"))
    ]


def test_registra_senza_eseguire_non_tocca_lo_schema(conn, tmp_path):
    """Serve per le migrazioni già applicate a mano in produzione prima del registro."""
    cartella = _copia_migrazioni(tmp_path)
    nuovo = cartella / "9999_prova.sql"
    nuovo.write_text("CREATE TABLE prova_migrazione (x int);", encoding="utf-8")

    registra_senza_eseguire(conn, [nuovo])

    assert da_applicare(conn, cartella) == []
    assert conn.execute("SELECT to_regclass('public.prova_migrazione')").fetchone()[0] is None



def test_inizializza_registro_su_database_gia_migrato_a_mano(conn):
    """Produzione: 0002-0006 applicate a mano, registro assente."""
    conn.execute("DROP TABLE public.migrazioni_applicate")
    gia_applicate = [p.name for p in sorted(CARTELLA_CONDIVISA.glob("*.sql")) if p.name < "0007"]
    inizializza_registro(conn, gia_applicate)
    registrate = [r[0] for r in conn.execute(
        "SELECT nome FROM public.migrazioni_applicate ORDER BY nome"
    ).fetchall()]
    assert registrate == gia_applicate + ["0007_registro_migrazioni.sql"]


@pytest.mark.parametrize("nome", ["../schema.sql", "0002_x.txt", "nonesiste.sql", "0099_inesistente.sql"])
def test_nome_di_migrazione_non_valido(nome):
    with pytest.raises(ValueError):
        percorso_migrazione(nome)


def test_registro_delle_migrazioni_non_si_modifica(conn):
    with pytest.raises(psycopg.errors.RaiseException):
        conn.execute("DELETE FROM public.migrazioni_applicate")
