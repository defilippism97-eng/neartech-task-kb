"""Colonna sonora degli effetti del video del pitch (nessuna musica, nessuna voce).

Tutti i suoni sono sintetizzati qui, in modo deterministico: nessun file di terzi, nessuna licenza.
La tavolozza segue l'identità: discreta, calda, senza rimbalzi.
  - soffio: l'ingresso di un titolo;
  - tick: il lavoro del sistema (contatori, punti, moduli del logo);
  - toni: le quote che si colorano, i quadranti che si accendono;
  - campanella a due note: la sfera ambra, cioè la decisione di una persona (il suono firma).

Uso (serve numpy; ffmpeg per l'm4a):
    python suoni_pitch.py [percorso di ffmpeg]
Scrive suoni/pitch-effetti.wav e suoni/pitch-effetti.m4a.

I tempi seguono la tabella SCENE, che deve coincidere con la variabile S di pitch.sorgente.html.
"""
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

SR = 44100
DURATA = 79.0
SCENE = [(0, 4), (4, 5.5), (9.5, 6.5), (16, 8), (24, 8), (32, 9), (41, 6), (47, 5.5), (52.5, 5.5), (58, 8), (66, 6), (72, 7)]
rng = np.random.default_rng(20261017)  # seme fisso: il rumore dei soffi è sempre lo stesso
traccia = np.zeros(int(SR * DURATA) + SR)


def at(n, r):
    return SCENE[n - 1][0] + r


def aggiungi(t, suono, gain=1.0):
    i = int(t * SR)
    traccia[i:i + len(suono)] += suono[: len(traccia) - i] * gain


def inviluppo(n, attacco, rilascio):
    """Attacco lineare e coda esponenziale, in secondi."""
    t = np.arange(n) / SR
    att = np.clip(t / max(attacco, 1e-4), 0, 1)
    return att * np.exp(-np.maximum(t - attacco, 0) / rilascio)


def banda(x, f_bassa, f_alta):
    """Filtro passa-banda nel dominio della frequenza, con bordi morbidi."""
    spettro = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    maschera = 1 / (1 + (f_bassa / np.maximum(f, 1)) ** 4) / (1 + (f / f_alta) ** 4)
    return np.fft.irfft(spettro * maschera, len(x))


def soffio(durata=0.6, verso="su", forza=1.0):
    """Rumore filtrato che sale (o scende) di registro: l'ingresso di un titolo."""
    n = int(durata * SR)
    rumore = rng.standard_normal(n)
    basso, alto = banda(rumore, 250, 1400), banda(rumore, 1200, 6500)
    p = np.linspace(0, 1, n) if verso == "su" else np.linspace(1, 0, n)
    mix = basso * (1 - p) + alto * p
    forma = np.sin(np.pi * np.linspace(0, 1, n)) ** 1.6
    return mix * forma * 0.22 * forza


def tick(freq=1400, durata=0.05, forza=1.0):
    """Un clic breve e legnoso: il lavoro del sistema."""
    n = int(durata * SR)
    t = np.arange(n) / SR
    corpo = np.sin(2 * np.pi * freq * t) * np.exp(-t / 0.012)
    click = banda(rng.standard_normal(n), 2000, 9000) * np.exp(-t / 0.002) * 0.4
    return (corpo + click) * 0.32 * forza


def pop(f0=520, durata=0.16, forza=1.0):
    """Un tono che scende di poco: un elemento che si posa."""
    n = int(durata * SR)
    t = np.arange(n) / SR
    f = f0 * (1 - 0.35 * (t / durata))
    fase = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(fase) * inviluppo(n, 0.004, 0.05) * 0.35 * forza


def tono(freq=523.25, durata=1.1, forza=1.0):
    """Tono a campana morbida: armoniche 1, 2 e 3 con coda esponenziale."""
    n = int(durata * SR)
    t = np.arange(n) / SR
    corpo = (np.sin(2 * np.pi * freq * t) + 0.35 * np.sin(2 * np.pi * 2.0 * freq * t) * np.exp(-t / 0.25)
             + 0.12 * np.sin(2 * np.pi * 3.01 * freq * t) * np.exp(-t / 0.12))
    return corpo * inviluppo(n, 0.006, durata / 3.5) * 0.18 * forza


def campanella(forza=1.0):
    """Il suono firma della sfera ambra: due note calde, mi e si, una dopo l'altra."""
    a, b = tono(659.25, 1.6, forza), tono(987.77, 1.6, forza * 0.8)
    out = np.zeros(len(a) + int(0.11 * SR))
    out[: len(a)] += a
    out[int(0.11 * SR):] += b
    return out * 1.3


def glissando(f_da, f_a, durata, forza=1.0):
    """Tono che scivola: la quota che passa da quasi tutti al 6%."""
    n = int(durata * SR)
    p = np.linspace(0, 1, n)
    f = f_da * (f_a / f_da) ** (p ** 1.4)
    fase = 2 * np.pi * np.cumsum(f) / SR
    forma = np.clip(p / 0.05, 0, 1) * (1 - p) ** 1.2
    return np.sin(fase) * forma * 0.14 * forza


def contatore(t0, durata, n, f_da=900, f_a=1500, forza=0.55):
    """Clic che seguono un conteggio con andamento power2.out: fitti all'inizio, radi alla fine."""
    for k in range(1, n + 1):
        p = k / n
        t = 1 - np.sqrt(1 - p)  # inverso di p = 1 - (1 - t)^2
        aggiungi(t0 + t * durata, tick(f_da + (f_a - f_da) * p, forza=forza))


def scintille(t0, durata, n, forza=0.3):
    """Tanti clic minimi: i punti che compaiono."""
    for k in range(n):
        f = 1800 + 900 * np.sin(k * 2.399)  # passo aureo: varietà senza caso
        aggiungi(t0 + durata * k / max(n - 1, 1), tick(f, 0.03, forza))


def logo(t0, v):
    """Il logo che si costruisce: asta, moduli, seconda asta, sfera che si posa."""
    aggiungi(t0, pop(180, 0.22, 0.9))
    aggiungi(t0 + 0.18 * v, tick(1250, forza=0.7))
    aggiungi(t0 + 0.30 * v, tick(1550, forza=0.7))
    aggiungi(t0 + 0.42 * v, pop(220, 0.2, 0.7))
    aggiungi(t0 + 0.62 * v + 0.28, campanella(0.9))


# ---------------------------------------------------------------- partitura, scena per scena
# S1 · logo
logo(at(1, 0.3), 1.25)
aggiungi(at(1, 1.35), soffio(0.7, "su", 0.6))

# S2 · domanda: soffio del titolo, tasti dell'accento, punto di domanda
aggiungi(at(2, 0.35), soffio(0.75))
for k in range(20):
    aggiungi(at(2, 1.0 + k * 0.045), tick(2200 + 300 * np.sin(k * 1.7), 0.03, 0.28))
aggiungi(at(2, 1.95), pop(700, 0.14, 0.8))

# S3 · 96%
aggiungi(at(3, 0.25), soffio(0.7))
contatore(at(3, 0.3), 1.5, 14)
aggiungi(at(3, 1.2), soffio(1.3, "su", 0.55))
aggiungi(at(3, 2.3), tono(880, 0.6, 0.7))

# S4 · oggi e 2030
aggiungi(at(4, 0.3), soffio(0.75))
for k, f in enumerate((392, 494, 587)):
    aggiungi(at(4, 1.1 + 0.15 * k), pop(f, 0.18, 0.75))
aggiungi(at(4, 4.2), soffio(0.7, "su", 0.8))
contatore(at(4, 4.3), 1.4, 10, 700, 1100, 0.45)

# S5 · cento lavoratori: punti, poi quattro toni per i quattro gruppi
aggiungi(at(5, 0.3), soffio(0.75))
scintille(at(5, 0.8), 0.6, 24, 0.22)
for k, f in enumerate((523.25, 659.25, 783.99, 440.0)):
    aggiungi(at(5, 1.7 + 0.75 * k), tono(f, 1.2, 0.9 if k < 3 else 0.6))

# S6 · uso e ritorno
aggiungi(at(6, 0.3), soffio(0.75))
aggiungi(at(6, 1.0), soffio(1.4, "su", 0.5))
contatore(at(6, 1.0), 1.5, 12)
aggiungi(at(6, 4.2), soffio(0.7, "giu", 0.8))
aggiungi(at(6, 4.7), glissando(660, 300, 1.4))
contatore(at(6, 4.7), 1.5, 8, 1300, 800, 0.4)

# S7 · 25%
aggiungi(at(7, 0.25), soffio(0.7))
contatore(at(7, 0.3), 1.3, 10)
scintille(at(7, 1.2), 0.8, 20, 0.22)
aggiungi(at(7, 2.6), tono(587.33, 1.0, 0.6))

# S8 · il punto
aggiungi(at(8, 0.3), soffio(0.8))
aggiungi(at(8, 1.5), soffio(0.6, "su", 0.45))

# S9 · chi siamo
logo(at(9, 0.2), 0.9)
aggiungi(at(9, 0.7), soffio(0.75, "su", 0.7))

# S10 · due assi
aggiungi(at(10, 0.3), soffio(0.75))
aggiungi(at(10, 0.5), soffio(0.6, "su", 0.35))
aggiungi(at(10, 0.65), soffio(0.6, "su", 0.35))
for k, f in enumerate((392, 493.88, 587.33, 659.25)):
    aggiungi(at(10, 1.0 + 0.18 * k), tono(f, 1.0, 0.7))
scintille(at(10, 2.2), 0.63, 10, 0.3)

# S11 · il sistema propone, le persone decidono
aggiungi(at(11, 0.3), soffio(0.75))
for k in range(7):
    aggiungi(at(11, 0.5 + 0.07 * k + 0.25), tick(1000 + 60 * k, 0.05, 0.6))
aggiungi(at(11, 1.95), campanella(1.1))

# Transizione verso l'invito: un respiro che sale e si apre
riser = soffio(0.9, "su", 1.1) + glissando(220, 440, 0.9, 0.8)
aggiungi(at(12, 0) - 0.85, riser)

# S12 · invito
logo(at(12, 0.35), 1.0)
aggiungi(at(12, 0.55), soffio(0.75, "su", 0.7))
aggiungi(at(12, 1.6), pop(523.25, 0.2, 0.8))
aggiungi(at(12, 1.65), tono(783.99, 1.8, 0.6))

# ---------------------------------------------------------------- uscita
traccia = traccia[: int(SR * DURATA)]
coda = int(0.8 * SR)
traccia[-coda:] *= np.linspace(1, 0, coda)
traccia *= 0.7 / max(np.abs(traccia).max(), 1e-9)  # picco a circa −3 dBFS
stereo = np.repeat((traccia * 32767).astype(np.int16)[:, None], 2, axis=1)

cartella = Path(__file__).parent / "suoni"
cartella.mkdir(exist_ok=True)
wav = cartella / "pitch-effetti.wav"
with wave.open(str(wav), "wb") as f:
    f.setnchannels(2)
    f.setsampwidth(2)
    f.setframerate(SR)
    f.writeframes(stereo.tobytes())
print(f"{wav}: {wav.stat().st_size // 1024} KB")

ffmpeg = sys.argv[1] if len(sys.argv) > 1 else "ffmpeg"
m4a = cartella / "pitch-effetti.m4a"
subprocess.run([ffmpeg, "-v", "error", "-y", "-i", str(wav), "-c:a", "aac", "-b:a", "160k", str(m4a)], check=True)
print(f"{m4a}: {m4a.stat().st_size // 1024} KB")
