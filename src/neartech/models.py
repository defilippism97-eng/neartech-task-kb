"""Modelli tipizzati per i dati in ingresso.

Le validazioni qui riflettono i vincoli dello schema (db/schema.sql).
Nessuna soglia di policy (pesi, λ, θ) è definita in questo file: stanno
nelle tabelle di governance, versionate e approvate.
"""

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field


class TaxonomyScheme(StrEnum):
    ONET_TASK = "ONET_TASK"
    ONET_DWA = "ONET_DWA"
    ONET_IWA = "ONET_IWA"
    ESCO_OCC = "ESCO_OCC"
    ESCO_SKILL = "ESCO_SKILL"
    ATLANTE_ADA = "ATLANTE_ADA"
    ATLANTE_RA = "ATLANTE_RA"
    ATLANTE_ATTIVITA = "ATLANTE_ATTIVITA"
    ISCO08 = "ISCO08"
    CP2021 = "CP2021"


class TaxonomyNodeIn(BaseModel):
    scheme: TaxonomyScheme
    code: str = Field(min_length=1)
    label: str = Field(min_length=1)
    lang: str = Field(min_length=2, max_length=5)
    parent_code: str | None = None


EvidenceType = Literal["benchmark", "usage_success", "usage", "internal_pilot", "expert", "llm_prior"]
Dimension = Literal["k1", "k2", "k3", "any"]


class EvidenceIn(BaseModel):
    source_name: str
    source_version: str
    evidence_type: EvidenceType
    dimension: Dimension
    raw_value: float
    # Scala 0–4 imposta dallo schema (CHECK score_0_4 BETWEEN 0 AND 4).
    score_0_4: float = Field(ge=0, le=4)
    # Scala non definita dal piano: qui solo non negativa, da fissare in governance.
    quality: float = Field(ge=0)
    observed_at: str  # ISO 8601, AAAA-MM-GG
    node_scheme: TaxonomyScheme | None = None
    node_code: str | None = None
