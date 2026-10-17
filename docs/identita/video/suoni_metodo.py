"""Effetti sonori del video del metodo (nessuna voce; la musica si aggiunge con mixa_audio.py).

Stessa tavolozza del pitch, sintetizzata qui in modo deterministico: soffio per i titoli, clic per il lavoro
del sistema, toni per ciò che si accende, campanella a due note per la sfera ambra (la decisione di una persona).
Tonalità: re maggiore, come la musica del metodo. La campanella (mi–si) è la stessa del pitch.

Uso (serve numpy):
    python suoni_metodo.py
Scrive suoni/metodo-effetti.wav. I tempi seguono SCENE, che deve coincidere con S di metodo.sorgente.html.
"""
import wave
from pathlib import Path

import numpy as np

SR = 44100
DURATA = 136.5
SCENE = [(0, 3.5), (3.5, 5.5), (9, 6), (15, 6), (21, 7), (28, 7), (35, 7.5), (42.5, 6), (48.5, 6.5), (55, 8), (63, 7),
         (70, 7), (77, 7), (84, 6.5), (90.5, 8), (98.5, 7.5), (106, 6), (112, 6), (118, 6), (124, 4.5), (128.5, 8)]
UMANE = {4, 5, 7, 8, 9}                     # tappe in cui decide una persona
SCENA_TAPPA = {5: 1, 6: 2, 7: 3, 8: 3, 9: 4, 10: 5, 11: 5, 12: 6, 13: 6, 14: 7, 15: 8, 16: 9}
RE, MI, FA_D, SOL, LA, SI, DO_D = 587.33, 659.25, 739.99, 783.99, 880.0, 987.77, 1108.73  # quinta ottava, re maggiore
rng = np.random.default_rng(20261018)
traccia = np.zeros(int(SR * DURATA) + SR)


def at(n, r):
    return SCENE[n - 1][0] + r


def aggiungi(t, suono, gain=1.0):
    i = int(t * SR)
    traccia[i:i + len(suono)] += suono[: len(traccia) - i] * gain


def inviluppo(n, attacco, rilascio):
    t = np.arange(n) / SR
    return np.clip(t / max(attacco, 1e-4), 0, 1) * np.exp(-np.maximum(t - attacco, 0) / rilascio)


def banda(x, f_bassa, f_alta):
    spettro = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    return np.fft.irfft(spettro / (1 + (f_bassa / np.maximum(f, 1)) ** 4) / (1 + (f / f_alta) ** 4), len(x))


def soffio(durata=0.6, verso="su", forza=1.0):
    n = int(durata * SR)
    rumore = rng.standard_normal(n)
    basso, alto = banda(rumore, 250, 1400), banda(rumore, 1200, 6500)
    p = np.linspace(0, 1, n) if verso == "su" else np.linspace(1, 0, n)
    return (basso * (1 - p) + alto * p) * np.sin(np.pi * np.linspace(0, 1, n)) ** 1.6 * 0.22 * forza


def tick(freq=1400, durata=0.05, forza=1.0):
    n = int(durata * SR)
    t = np.arange(n) / SR
    corpo = np.sin(2 * np.pi * freq * t) * np.exp(-t / 0.012)
    click = banda(rng.standard_normal(n), 2000, 9000) * np.exp(-t / 0.002) * 0.4
    return (corpo + click) * 0.32 * forza


def pop(f0=520, durata=0.16, forza=1.0):
    n = int(durata * SR)
    t = np.arange(n) / SR
    fase = 2 * np.pi * np.cumsum(f0 * (1 - 0.35 * (t / durata))) / SR
    return np.sin(fase) * inviluppo(n, 0.004, 0.05) * 0.35 * forza


def tono(freq, durata=1.1, forza=1.0):
    n = int(durata * SR)
    t = np.arange(n) / SR
    corpo = (np.sin(2 * np.pi * freq * t) + 0.35 * np.sin(2 * np.pi * 2.0 * freq * t) * np.exp(-t / 0.25)
             + 0.12 * np.sin(2 * np.pi * 3.01 * freq * t) * np.exp(-t / 0.12))
    return corpo * inviluppo(n, 0.006, durata / 3.5) * 0.18 * forza


def campanella(forza=1.0):
    a, b = tono(MI, 1.6, forza), tono(SI, 1.6, forza * 0.8)
    out = np.zeros(len(a) + int(0.11 * SR))
    out[: len(a)] += a
    out[int(0.11 * SR):] += b
    return out * 1.3


def glissando(f_da, f_a, durata, forza=1.0):
    n = int(durata * SR)
    p = np.linspace(0, 1, n)
    fase = 2 * np.pi * np.cumsum(f_da * (f_a / f_da) ** (p ** 1.4)) / SR
    return np.sin(fase) * np.clip(p / 0.05, 0, 1) * (1 - p) ** 1.2 * 0.14 * forza


def scintille(t0, durata, n, forza=0.3):
    for k in range(n):
        aggiungi(t0 + durata * k / max(n - 1, 1), tick(1800 + 900 * np.sin(k * 2.399), 0.03, forza))


def logo(t0, v):
    aggiungi(t0, pop(146.83, 0.22, 0.9))           # re, un'ottava sotto: l'asta
    aggiungi(t0 + 0.18 * v, tick(1250, forza=0.7))
    aggiungi(t0 + 0.30 * v, tick(1550, forza=0.7))
    aggiungi(t0 + 0.42 * v, pop(220, 0.2, 0.7))     # la: la seconda asta
    aggiungi(t0 + 0.62 * v + 0.28, campanella(0.9))


def passo(n, sotto=True):
    """Ingresso di una scena-passo: tappa del binario, sfera ambra se decide una persona, titolo."""
    tappa = SCENA_TAPPA[n]
    if tappa in UMANE:
        prima = n == min(s for s, t in SCENA_TAPPA.items() if t == tappa)
        aggiungi(at(n, 0.65), campanella(1.0 if prima else 0.55))   # la sfera si posa sulla tappa
    else:
        aggiungi(at(n, 0.2), pop(LA, 0.16, 0.7))                    # la tappa del sistema si accende
    aggiungi(at(n, 0.4), soffio(0.75, "su", 0.85))
    if sotto:
        aggiungi(at(n, 1.3), soffio(0.5, "su", 0.3))


# ---------------------------------------------------------------- partitura
# M1 · logo
logo(at(1, 0.25), 1.15)
aggiungi(at(1, 1.2), soffio(0.7, "su", 0.6))
# M2 · apertura: titolo e tasti della domanda
aggiungi(at(2, 0.3), soffio(0.8))
for k in range(29):
    aggiungi(at(2, 1.0 + k * 0.04), tick(2200 + 300 * np.sin(k * 1.7), 0.03, 0.26))
# M3 · promessa
aggiungi(at(3, 0.35), soffio(0.8))
aggiungi(at(3, 1.4), tono(LA, 1.2, 0.6))
# M4 · tre tempi: i tratti del binario, le nove tappe, i tre nomi
aggiungi(at(4, 0.3), soffio(0.8))
for k in range(3):
    aggiungi(at(4, 0.8 + 0.35 * k), soffio(0.6, "su", 0.35))
for k in range(9):
    aggiungi(at(4, 0.9 + 0.12 * k), tick(1100 + 60 * k, 0.05, 0.5))
for k, f in enumerate((RE, FA_D, LA)):
    aggiungi(at(4, 1.3 + 0.35 * k), tono(f, 1.1, 0.75))
# M5 · 01 scomposizione
passo(5)
aggiungi(at(5, 0.8), soffio(0.5, "su", 0.3))
for k in range(8):
    aggiungi(at(5, 1.0 + 0.06 * k), tick(1600 + 40 * k, 0.03, 0.25))
aggiungi(at(5, 1.7), soffio(0.6, "su", 0.35))
for k, f in enumerate((RE, MI, FA_D, LA)):
    aggiungi(at(5, 1.9 + 0.2 * k), pop(f, 0.16, 0.65))
# M6 · 02 abbinamento
passo(6)
for k in range(3):
    aggiungi(at(6, 2.0 + 0.2 * k), soffio(0.5, "su", 0.35))
    aggiungi(at(6, 2.55 + 0.2 * k), tick(1300 + 120 * k, 0.05, 0.6))
aggiungi(at(6, 3.1), campanella(0.55))              # il lotto approvato da una persona
# M7 · 03 punteggio
passo(7, sotto=False)
aggiungi(at(7, 1.0), pop(SOL, 0.18, 0.7))
for k in range(3):
    aggiungi(at(7, 1.3 + 0.15 * k), tick(1200 + 100 * k, 0.05, 0.5))
for k, f in enumerate((LA, FA_D, RE)):
    aggiungi(at(7, 1.9 + 0.15 * k), tono(f, 0.9, 0.55))
aggiungi(at(7, 2.7), pop(LA, 0.16, 0.6))
# M8 · dati
passo(8)
aggiungi(at(8, 0.9), pop(293.66, 0.2, 0.7))
aggiungi(at(8, 1.15), pop(440.0, 0.2, 0.7))
# M9 · 04 comitato
passo(9, sotto=False)
for k in range(3):
    aggiungi(at(9, 1.05 + 0.15 * k), soffio(0.45, "su", 0.3))
scintille(at(9, 1.1), 0.9, 12, 0.22)
aggiungi(at(9, 2.2), pop(RE, 0.18, 0.6))
aggiungi(at(9, 3.0), soffio(1.2, "su", 0.25))
# M10 · 05 indirizzi: i cursori trovano la loro posizione
passo(10, sotto=False)
for k, (f0, f1) in enumerate(((RE, LA), (RE, SOL), (RE, FA_D), (RE, LA))):
    aggiungi(at(10, 2.05 + 0.25 * k), glissando(f0, f1, 1.0, 0.7))
# M11 · 05 garanzie
passo(11)
for k in range(3):
    aggiungi(at(11, 0.9 + 0.12 * k), pop(293.66, 0.18, 0.55))
aggiungi(at(11, 1.4), soffio(0.6, "su", 0.35))
aggiungi(at(11, 2.1), tono(FA_D, 1.0, 0.65))
aggiungi(at(11, 2.3), tono(LA, 1.0, 0.65))
aggiungi(at(11, 2.8), pop(MI, 0.16, 0.6))
aggiungi(at(11, 3.1), pop(SI, 0.16, 0.6))
# Transizione verso la matrice: un respiro che sale (la → la)
aggiungi(at(12, 0) - 0.85, soffio(0.9, "su", 1.1) + glissando(220, 440, 0.9, 0.8))
# M12 · 06 classificazione: i punti si spostano nei quadranti
passo(12)
for k in range(9):
    aggiungi(at(12, 2.0 + 0.06 * k), tick(1000 + 90 * k, 0.05, 0.4))
aggiungi(at(12, 2.0), glissando(RE, LA, 1.4, 0.6))
# M13 · questionari
passo(13)
aggiungi(at(13, 0.9), soffio(0.5, "su", 0.35))
for k in range(3):
    aggiungi(at(13, 1.5 + 0.15 * k), tick(1500 + 100 * k, 0.04, 0.45))
aggiungi(at(13, 2.6), pop(FA_D, 0.16, 0.7))
# M14 · 07 revisione: il campione, prima gli incerti
passo(14, sotto=False)
scintille(at(14, 0.9), 0.64, 16, 0.2)
for k in range(14):
    aggiungi(at(14, 2.0 + 0.1 * k), tick(1000 + 45 * k, 0.04, 0.35))
# M15 · 08 correzioni: la correzione si propaga, poi la proposta al comitato
passo(15)
for k, f in enumerate((MI, FA_D, LA)):
    aggiungi(at(15, 2.0 + 0.3 * k), tono(f, 0.9, 0.6))
aggiungi(at(15, 3.1), campanella(0.5))
# M16 · 09 restituzione: l'accordo di re all'approvazione
passo(16)
scintille(at(16, 1.1), 0.9, 12, 0.2)
for f in (RE, FA_D, LA):
    aggiungi(at(16, 2.6), tono(f, 1.6, 0.55))
# M17 · trasparenza
aggiungi(at(17, 0.3), soffio(0.8))
for k in range(4):
    aggiungi(at(17, 1.3 + 0.3 * k), tick(1200 + 100 * k, 0.05, 0.5))
# M18 · aggiornamento: le nove tappe in cerchio
aggiungi(at(18, 0.3), soffio(0.8))
for k in range(9):
    aggiungi(at(18, 0.9 + 0.1 * k), tick(1100 + 60 * k, 0.05, 0.45))
# M19 · risultato: tre righe, tre toni
aggiungi(at(19, 0.25), soffio(0.6, "su", 0.5))
for k, f in enumerate((RE, FA_D, LA)):
    aggiungi(at(19, 0.35 + 0.35 * k), tono(f, 1.3, 0.75))
# M20 · persone
aggiungi(at(20, 0.3), soffio(0.8, "su", 0.7))
aggiungi(at(20, 0.7), campanella(0.7))
# M21 · invito
logo(at(21, 0.35), 1.0)
aggiungi(at(21, 0.55), soffio(0.8, "su", 0.7))
aggiungi(at(21, 1.8), pop(RE, 0.2, 0.8))
aggiungi(at(21, 1.85), tono(LA, 1.8, 0.6))

# ---------------------------------------------------------------- uscita
traccia = traccia[: int(SR * DURATA)]
coda = int(0.8 * SR)
traccia[-coda:] *= np.linspace(1, 0, coda)
traccia *= 0.7 / max(np.abs(traccia).max(), 1e-9)
stereo = np.repeat((traccia * 32767).astype(np.int16)[:, None], 2, axis=1)
cartella = Path(__file__).parent / "suoni"
cartella.mkdir(exist_ok=True)
wav = cartella / "metodo-effetti.wav"
with wave.open(str(wav), "wb") as f:
    f.setnchannels(2)
    f.setsampwidth(2)
    f.setframerate(SR)
    f.writeframes(stereo.tobytes())
print(f"{wav}: {wav.stat().st_size // 1024} KB")
