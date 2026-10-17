"""Mixa la musica di sottofondo con gli effetti di un video (pitch o metodo).

La musica accompagna l'attenzione e copre i silenzi, ma resta sotto gli effetti:
  - livello costante e basso (MUSICA_LUFS): niente abbassamenti automatici, che si sentono come pompaggio;
  - un piccolo incavo fisso nelle frequenze medio-alte della musica lascia spazio a clic e campanelle;
  - entra con una dissolvenza breve ed esce con una più lunga sulla chiusura.
Il mix finale è normalizzato a FINALE_LUFS, con limitatore sotto −1 dBTP.

Musiche in uso (verificare licenza ed eventuale obbligo di citare l'autore prima della diffusione):
  - pitch:  «Security» di MokkaMusic, la minore;
  - metodo: «Upbeat Inspiring Corporate» di Wavecont (RiseArt), re maggiore, circa 117 BPM.
Gli effetti dei due video usano solo note della tonalità della rispettiva musica.

Uso:
    python mixa_audio.py <ffmpeg> <musica.mp3> <nome> <durata_s> [inizio_musica_s]
    es.: python mixa_audio.py ffmpeg security.mp3 pitch 79
         python mixa_audio.py ffmpeg wavecont.mp3 metodo 136.5
Legge suoni/<nome>-effetti.wav, scrive suoni/<nome>-audio.wav e suoni/<nome>-audio.m4a.
"""
import re
import subprocess
import sys
from pathlib import Path

# Livello costante della musica per video: tarato perché gli effetti stiano in media ~5 dB sopra (attacchi ~16 dB).
# La musica del metodo è più densa e brillante, quindi va tenuta 2,5 dB più bassa.
MUSICA_LUFS_PER_VIDEO = {"pitch": -31.0, "metodo": -33.5}
FINALE_LUFS = -16.0   # livello d'ascolto per video sul web
DISSOLVENZA_IN, DISSOLVENZA_OUT = 0.8, 2.6

ffmpeg, musica, nome, durata = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4])
inizio = float(sys.argv[5]) if len(sys.argv) > 5 else 0.0
MUSICA_LUFS = MUSICA_LUFS_PER_VIDEO.get(nome, -31.0)
cartella = Path(__file__).parent / "suoni"
effetti = cartella / f"{nome}-effetti.wav"


def misura(*args):
    """Loudness integrata (LUFS) secondo EBU R128."""
    out = subprocess.run([ffmpeg, "-hide_banner", *args, "-af", "ebur128=framelog=quiet", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    return float(re.findall(r"I:\s+(-?[\d.]+) LUFS", out)[-1])


def mixa(guadagno_musica, guadagno_finale, uscita):
    filtro = (
        f"[0:a]atrim={inizio}:{inizio + durata},asetpts=PTS-STARTPTS,aresample=44100,"
        f"afade=t=in:d={DISSOLVENZA_IN},afade=t=out:st={durata - DISSOLVENZA_OUT}:d={DISSOLVENZA_OUT},"
        f"volume={guadagno_musica}dB[m];"
        "[1:a]aresample=44100[fx];"
        # incavo fisso (non dinamico) dove stanno clic e campanelle: la musica non cambia mai volume
        "[m]equalizer=f=2500:t=q:w=1.0:g=-4,equalizer=f=900:t=q:w=1.2:g=-2[md];"
        "[md][fx]amix=inputs=2:normalize=0:duration=first,"
        f"volume={guadagno_finale}dB,alimiter=limit=0.89:level=false[out]"
    )
    subprocess.run([ffmpeg, "-v", "error", "-y", "-i", musica, "-i", str(effetti), "-filter_complex", filtro,
                    "-map", "[out]", "-t", str(durata), str(uscita)], check=True)


l_musica = misura("-ss", str(inizio), "-t", str(durata), "-i", musica)
g_musica = MUSICA_LUFS - l_musica
wav = cartella / f"{nome}-audio.wav"
mixa(g_musica, 0.0, wav)
g_finale = FINALE_LUFS - misura("-i", str(wav))
mixa(g_musica, g_finale, wav)
print(f"musica: {l_musica:.1f} → {MUSICA_LUFS} LUFS · effetti: {misura('-i', str(effetti)):.1f} LUFS · "
      f"mix finale: {misura('-i', str(wav)):.1f} LUFS")

m4a = cartella / f"{nome}-audio.m4a"
subprocess.run([ffmpeg, "-v", "error", "-y", "-i", str(wav), "-c:a", "aac", "-b:a", "192k", str(m4a)], check=True)
print(f"{m4a}: {m4a.stat().st_size // 1024} KB")
