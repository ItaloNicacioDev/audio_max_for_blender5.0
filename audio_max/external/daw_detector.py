import os
import sys
import shutil
import ctypes

# Palavras-chave genéricas (não fixas)
KEYWORDS = [
    "reaper",
    "fl",
    "studio",
    "ableton",
    "live",
    "ardour",
    "bitwig",
    "audacity",
    "carla",
    "vst",
    "host",
    "tracktion",
    "waveform"
]

# -------------------------------------------------
# SYSTEM BASE PATHS
# -------------------------------------------------
def _get_base_paths():
    if sys.platform == "win32":
        return _get_all_drives_windows()
    elif sys.platform == "darwin":
        return ["/Applications"]
    else:  # Linux
        return ["/usr/bin", "/usr/local/bin", "/opt"]

def _get_all_drives_windows():
    """Retorna todas as letras de drives existentes no Windows"""
    drives = []
    bitmask = ctypes.windll.kernel32.GetLogicalDrives()
    for i in range(26):
        if bitmask & (1 << i):
            drives.append(f"{chr(65 + i)}:\\")
    return drives

# -------------------------------------------------
# DETECT FROM PATH
# -------------------------------------------------
def _detect_from_path():
    found = []
    for keyword in KEYWORDS:
        exe = shutil.which(keyword)
        if exe:
            found.append(exe)
    return found

# -------------------------------------------------
# SEARCH DIRECTORIES
# -------------------------------------------------
def _search_directories(max_depth=5):
    """Busca DAWs em todos os diretórios base"""
    found = []
    bases = _get_base_paths()

    for base in bases:
        if not os.path.exists(base):
            continue

        for root, dirs, files in os.walk(base):
            depth = root[len(base):].count(os.sep)
            if depth > max_depth:
                # Não entra em subpastas profundas
                dirs[:] = []
                continue

            for file in files:
                name = file.lower()
                if any(k in name for k in KEYWORDS):
                    full_path = os.path.join(root, file)
                    if os.access(full_path, os.X_OK):
                        found.append(full_path)

    return found

# -------------------------------------------------
# PUBLIC FUNCTION
# -------------------------------------------------
def detect_all_audio_hosts():
    """
    Retorna lista única de possíveis DAWs / Hosts encontrados.
    """
    results = set()

    # Camada 1: via PATH
    for r in _detect_from_path():
        results.add(os.path.abspath(r))

    # Camada 2: via pastas
    for r in _search_directories():
        results.add(os.path.abspath(r))

    return sorted(list(results))

# -------------------------------------------------
# DETECT DAW (FUNÇÃO ADICIONAL PARA COMPATIBILIDADE)
# -------------------------------------------------
def detect_daw():
    """Retorna lista de DAWs, compatível com chamadas antigas"""
    return detect_all_audio_hosts()