"""Test dell'estrazione AEI su dati sintetici: nessun file reale necessario."""

import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "estrai_aei.py"
spec = importlib.util.spec_from_file_location("estrai_aei", SCRIPT)
estrai = importlib.util.module_from_spec(spec)
spec.loader.exec_module(estrai)

ONET = [
    {"Task ID": "1", "Task": "Revise documents."},
    {"Task ID": "2", "Task": "Compile lists of products."},
    {"Task ID": "3", "Task": "Compile lists of products"},  # stesso testo di ID 2: ambiguo
]


def test_testo_normalizzato_collega_un_solo_task():
    indice = estrai.indice_onet(ONET)
    rec = estrai.record_aei({"task": "  REVISE documents ", "penetration": "0.25"}, 2, indice)
    assert rec["relation"] == "exact"
    assert rec["task_link"] == "ONET_TASK 1"
    assert rec["value_raw"] == 0.25


def test_testo_con_piu_task_e_ambiguo_e_non_collegato():
    indice = estrai.indice_onet(ONET)
    rec = estrai.record_aei({"task": "Compile lists of products.", "penetration": "0.1"}, 3, indice)
    assert rec["task_link"] is None
    assert rec["relation"].startswith("ambiguo")


def test_uso_osservato_resta_contesto_e_non_ha_score():
    indice = estrai.indice_onet(ONET)
    rec = estrai.record_aei({"task": "Revise documents.", "penetration": "0.5"}, 2, indice)
    assert rec["use"] == "contesto"
    assert rec["value_0_4"] is None
    assert rec["evidence_type"] == "usage"


def test_task_assente_da_onet_non_ha_collegamento():
    indice = estrai.indice_onet(ONET)
    rec = estrai.record_aei({"task": "Un task che non esiste.", "penetration": "0"}, 5, indice)
    assert rec["relation"] == "nessun collegamento"
