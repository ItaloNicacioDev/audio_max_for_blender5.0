import os


# Palavras-chave por prioridade
HIGH_PRIORITY = [
    "carla",
    "vsthost",
    "reajs",
    "yabridge",
    "host"
]

MEDIUM_PRIORITY = [
    "reaper",
]

LOW_PRIORITY = [
    "fl",
    "ableton",
    "live",
    "studio",
    "bitwig",
    "ardour",
    "tracktion",
    "waveform"
]


# -------------------------------------------------
# CLASSIFY
# -------------------------------------------------

def classify_host(path: str) -> str:
    """
    Retorna: high | medium | low | unknown
    """
    name = os.path.basename(path).lower()

    if any(k in name for k in HIGH_PRIORITY):
        return "high"

    if any(k in name for k in MEDIUM_PRIORITY):
        return "medium"

    if any(k in name for k in LOW_PRIORITY):
        return "low"

    return "unknown"


# -------------------------------------------------
# SORT BY PRIORITY
# -------------------------------------------------

def sort_hosts_by_priority(hosts: list) -> list:
    """
    Ordena lista com base na prioridade.
    """

    def priority_value(path):
        level = classify_host(path)

        if level == "high":
            return 0
        if level == "medium":
            return 1
        if level == "low":
            return 2
        return 3

    return sorted(hosts, key=priority_value)


# -------------------------------------------------
# GET BEST HOST
# -------------------------------------------------

def get_best_host(hosts: list):
    """
    Retorna o melhor host disponível.
    """
    if not hosts:
        return None

    sorted_hosts = sort_hosts_by_priority(hosts)

    return sorted_hosts[0]