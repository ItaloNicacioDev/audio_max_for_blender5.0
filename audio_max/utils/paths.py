import os
import sys
import tempfile
from .system_info import is_windows, is_mac, is_linux
try:
    import bpy
except ImportError:
    bpy = None




# -------------------------------------------------
# Selection of OS
# -------------------------------------------------
def get_ffmpeg_path() -> str:
    """
    Retorna o caminho do FFmpeg embutido no addon.
    """

    base_dir = os.path.dirname(os.path.dirname(__file__))
    binaries_dir = os.path.join(base_dir, "binaries")

    if is_windows():
        return os.path.join(binaries_dir, "windows", "ffmpeg.exe")

    if is_mac():
        return os.path.join(binaries_dir, "mac", "ffmpeg")

    if is_linux():
        return os.path.join(binaries_dir, "linux", "ffmpeg")

    return ""


# -------------------------------------------------
# ABSOLUTE PATH (Blender Safe)
# -------------------------------------------------

def to_absolute(path: str) -> str:
    """
    Converte caminho relativo do Blender (//) em absoluto.
    """
    if not path:
        return ""

    if bpy and path.startswith("//"):
        return bpy.path.abspath(path)

    return os.path.abspath(path)


# -------------------------------------------------
# FILE EXISTS
# -------------------------------------------------

def file_exists(path: str) -> bool:
    return os.path.isfile(to_absolute(path))


# -------------------------------------------------
# ENSURE DIRECTORY
# -------------------------------------------------

def ensure_directory(path: str):
    """
    Cria diretório se não existir.
    """
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)


# -------------------------------------------------
# TEMP DIRECTORY FOR ADDON
# -------------------------------------------------

def get_temp_dir() -> str:
    """
    Retorna pasta temporária exclusiva do Audio Max.
    """
    base = tempfile.gettempdir()
    addon_temp = os.path.join(base, "audio_max")

    ensure_directory(addon_temp)

    return addon_temp


# -------------------------------------------------
# BUILD TEMP FILE
# -------------------------------------------------

def build_temp_file(filename: str) -> str:
    """
    Retorna caminho completo dentro da pasta temporária do addon.
    """
    temp_dir = get_temp_dir()
    return os.path.join(temp_dir, filename)


# -------------------------------------------------
# PLATFORM INFO
# -------------------------------------------------

def get_platform() -> str:
    return sys.platform