# core/global_cache.py
DAW_CACHE = []

def get_cached_daws():
    """Retorna a lista de DAWs detectadas (rápido, sem buscar no sistema)."""
    global DAW_CACHE
    return DAW_CACHE

def update_daw_cache():
    """Atualiza a lista de DAWs chamando detect_all_audio_hosts UMA vez."""
    global DAW_CACHE
    from ..external.daw_detector import detect_all_audio_hosts
    DAW_CACHE = detect_all_audio_hosts()