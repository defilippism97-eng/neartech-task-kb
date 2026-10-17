"""Impostazioni della piattaforma (ADR 0007). Tutto arriva dall'ambiente, nessun segreto nel codice.

NEARTECH_AMBIENTE          sviluppo | prova | produzione (obbligatoria: nessun valore predefinito)
NEARTECH_URL_PUBBLICA      indirizzo pubblico (https://...) fuori dallo sviluppo: host ammesso e ritorno dello SSO
NEARTECH_CHIAVE_SESSIONE   chiave per firmare il cookie di sessione (almeno 32 caratteri fuori dallo sviluppo)
NEARTECH_OIDC_NOME         nome breve del fornitore SSO (es. entra): prefisso del soggetto SSO
NEARTECH_OIDC_METADATI     URL https dei metadati OpenID Connect del fornitore
NEARTECH_OIDC_CLIENT_ID, NEARTECH_OIDC_CLIENT_SECRET
NEARTECH_CARTELLA_WEB      cartella con il frontend compilato (web/dist)
NEARTECH_ACCESSO_SVILUPPO  1 per l'accesso senza SSO, solo in sviluppo e solo da localhost
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

AMBIENTI = ("sviluppo", "prova", "produzione")
HOST_SVILUPPO = ("localhost", "127.0.0.1")


@dataclass(frozen=True)
class Oidc:
    nome: str
    metadati: str
    client_id: str
    client_secret: str = field(repr=False)


@dataclass(frozen=True)
class Impostazioni:
    ambiente: str
    chiave_sessione: str = field(repr=False)
    oidc: Oidc | None = None
    cartella_web: Path | None = None
    url_pubblica: str | None = None
    # Accesso senza SSO, indicando un soggetto esistente: solo in sviluppo, solo da questi indirizzi.
    accesso_sviluppo: bool = False
    client_sviluppo: tuple[str, ...] = ("127.0.0.1", "::1")
    host_consentiti: tuple[str, ...] = HOST_SVILUPPO
    durata_sessione_ore: int = 8

    def __post_init__(self) -> None:
        if self.ambiente not in AMBIENTI:
            raise ValueError(f"ambiente non ammesso: {self.ambiente!r}")
        if self.accesso_sviluppo and self.ambiente != "sviluppo":
            raise ValueError("l'accesso senza SSO è ammesso solo nell'ambiente di sviluppo")
        if self.ambiente != "sviluppo":
            if len(self.chiave_sessione) < 32:
                raise ValueError("fuori dallo sviluppo la chiave di sessione deve avere almeno 32 caratteri")
            if self.oidc is None:
                raise ValueError("fuori dallo sviluppo serve l'accesso SSO (NEARTECH_OIDC_*)")
            if not self.oidc.metadati.startswith("https://"):
                raise ValueError("i metadati SSO vanno letti in https")
            if not (self.url_pubblica or "").startswith("https://"):
                raise ValueError("fuori dallo sviluppo serve NEARTECH_URL_PUBBLICA in https")

    @property
    def cookie_sicuro(self) -> bool:
        return self.ambiente != "sviluppo"

    @property
    def nome_cookie(self) -> str:
        # __Host-: solo https, senza Domain, percorso / (non piantabile da un sottodominio).
        return "__Host-neartech_sessione" if self.cookie_sicuro else "neartech_sessione"

    @property
    def host(self) -> tuple[str, ...]:
        if self.ambiente == "sviluppo":
            return self.host_consentiti
        return (urlparse(self.url_pubblica or "").hostname or "",)

    @classmethod
    def da_ambiente(cls) -> "Impostazioni":
        ambiente = os.environ.get("NEARTECH_AMBIENTE")
        if not ambiente:
            raise ValueError("NEARTECH_AMBIENTE va impostata esplicitamente (sviluppo, prova o produzione)")
        oidc = None
        if os.environ.get("NEARTECH_OIDC_METADATI"):
            oidc = Oidc(nome=os.environ["NEARTECH_OIDC_NOME"], metadati=os.environ["NEARTECH_OIDC_METADATI"],
                        client_id=os.environ["NEARTECH_OIDC_CLIENT_ID"],
                        client_secret=os.environ["NEARTECH_OIDC_CLIENT_SECRET"])
        cartella = os.environ.get("NEARTECH_CARTELLA_WEB")
        return cls(
            ambiente=ambiente,
            chiave_sessione=os.environ.get("NEARTECH_CHIAVE_SESSIONE", ""),
            oidc=oidc,
            cartella_web=Path(cartella) if cartella else None,
            url_pubblica=os.environ.get("NEARTECH_URL_PUBBLICA"),
            accesso_sviluppo=os.environ.get("NEARTECH_ACCESSO_SVILUPPO") == "1",
        )
