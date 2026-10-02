import os
import tempfile
from pydub import AudioSegment


# -------------------------------------------------
# LOAD
# -------------------------------------------------

def load_audio(path: str) -> AudioSegment:
    """
    Carrega qualquer formato suportado pelo ffmpeg.
    """
    if not path or not os.path.exists(path):
        raise FileNotFoundError(f"Arquivo não encontrado: {path}")

    return AudioSegment.from_file(path)


# -------------------------------------------------
# EXPORT
# -------------------------------------------------

def export_audio(segment: AudioSegment, original_path: str) -> str:
    """
    Exporta o áudio processado mantendo formato original.
    Retorna o novo caminho.
    """
    ext = os.path.splitext(original_path)[1].replace(".", "").lower()

    if not ext:
        ext = "wav"

    temp_dir = tempfile.gettempdir()
    output_path = os.path.join(temp_dir, f"amax_processed.{ext}")

    segment.export(output_path, format=ext)

    return output_path


# -------------------------------------------------
# BASIC PROCESSING
# -------------------------------------------------

def normalize(segment: AudioSegment) -> AudioSegment:
    return segment.normalize()


def apply_gain(segment: AudioSegment, db: float) -> AudioSegment:
    return segment + db


def trim(segment: AudioSegment, start_ms: int, end_ms: int) -> AudioSegment:
    return segment[start_ms:end_ms]


# -------------------------------------------------
# SAFE PROCESS WRAPPER
# -------------------------------------------------

def process_safe(path: str, processor_func, *args, **kwargs) -> str:
    """
    Wrapper seguro:
    - carrega
    - processa
    - exporta
    """
    segment = load_audio(path)
    processed = processor_func(segment, *args, **kwargs)
    return export_audio(processed, path)