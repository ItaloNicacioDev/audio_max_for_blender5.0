import os
import datetime
from .paths import get_temp_dir


# -------------------------------------------------
# CONFIG
# -------------------------------------------------

DEBUG_MODE = True
LOG_TO_FILE = False


# -------------------------------------------------
# INTERNAL
# -------------------------------------------------

def _timestamp():
    return datetime.datetime.now().strftime("%H:%M:%S")


def _write_to_file(message: str):
    if not LOG_TO_FILE:
        return

    log_file = os.path.join(get_temp_dir(), "audio_max.log")

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(message + "\n")


def _log(level: str, message: str):
    formatted = f"[AudioMax {level} {_timestamp()}] {message}"

    print(formatted)
    _write_to_file(formatted)


# -------------------------------------------------
# PUBLIC API
# -------------------------------------------------

def info(message: str):
    _log("INFO", message)


def warning(message: str):
    _log("WARNING", message)


def error(message: str):
    _log("ERROR", message)


def debug(message: str):
    if DEBUG_MODE:
        _log("DEBUG", message)


# -------------------------------------------------
# SETTINGS CONTROL
# -------------------------------------------------

def set_debug(enabled: bool):
    global DEBUG_MODE
    DEBUG_MODE = enabled


def set_log_to_file(enabled: bool):
    global LOG_TO_FILE
    LOG_TO_FILE = enabled