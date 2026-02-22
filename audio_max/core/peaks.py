from pydub import AudioSegment
from pydub.silence import detect_silence


# -------------------------------------------------
# PEAK DETECTION
# -------------------------------------------------

def detect_peaks(segment: AudioSegment, threshold_db=-1.0, chunk_ms=10):
    """
    Detecta picos acima de um threshold.
    Retorna lista de tempos em ms.
    """

    peaks = []
    duration = len(segment)

    for i in range(0, duration, chunk_ms):
        chunk = segment[i:i + chunk_ms]
        if chunk.max_dBFS >= threshold_db:
            peaks.append(i)

    return peaks


# -------------------------------------------------
# CLIPPING DETECTION
# -------------------------------------------------

def detect_clipping(segment: AudioSegment, clip_db=0.0, chunk_ms=5):
    """
    Detecta possíveis trechos clipados.
    """

    clips = []
    duration = len(segment)

    for i in range(0, duration, chunk_ms):
        chunk = segment[i:i + chunk_ms]
        if chunk.max_dBFS >= clip_db:
            clips.append(i)

    return clips


# -------------------------------------------------
# SILENCE DETECTION
# -------------------------------------------------

def detect_silences(segment: AudioSegment,
                    min_silence_len=500,
                    silence_thresh=-40):
    """
    Detecta trechos de silêncio.
    Retorna lista de [start, end]
    """

    silences = detect_silence(
        segment,
        min_silence_len=min_silence_len,
        silence_thresh=silence_thresh
    )

    return silences


# -------------------------------------------------
# RMS ANALYSIS
# -------------------------------------------------

def get_rms_over_time(segment: AudioSegment, chunk_ms=50):
    """
    Retorna lista de RMS ao longo do tempo.
    Pode ser usado para waveform simplificada.
    """

    rms_values = []
    duration = len(segment)

    for i in range(0, duration, chunk_ms):
        chunk = segment[i:i + chunk_ms]
        rms_values.append(chunk.rms)

    return rms_values