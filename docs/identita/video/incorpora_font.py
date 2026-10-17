"""Incorpora i font del marchio in una composizione HyperFrames.

Il percorso «Send to HyperFrames» importa un solo file HTML: i font devono viaggiare dentro il file
come data URI base64, altrimenti il render ricade su un font di sistema.

Uso:
    python incorpora_font.py pitch.sorgente.html pitch-hyperframes.html
"""
import base64
import sys
from pathlib import Path

CARTELLA_FONT = Path(__file__).parent / "font"
SEGNAPOSTO = {
    "__FONT_INTER__": "Inter.woff2",
    "__FONT_JBMONO__": "JetBrainsMono.woff2",
}


def incorpora(sorgente: Path, destinazione: Path) -> None:
    testo = sorgente.read_text(encoding="utf-8")
    for segnaposto, nome in SEGNAPOSTO.items():
        if segnaposto not in testo:
            raise SystemExit(f"Segnaposto {segnaposto} assente in {sorgente}")
        dati = base64.b64encode((CARTELLA_FONT / nome).read_bytes()).decode("ascii")
        testo = testo.replace(segnaposto, dati)
    destinazione.write_text(testo, encoding="utf-8")
    print(f"{destinazione}: {destinazione.stat().st_size // 1024} KB")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    incorpora(Path(sys.argv[1]), Path(sys.argv[2]))
