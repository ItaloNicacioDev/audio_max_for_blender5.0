import sys
import platform


# -------------------------------------------------
# PLATFORM CHECKS
# -------------------------------------------------

def get_platform() -> str:
    return sys.platform


def is_windows() -> bool:
    return sys.platform == "win32"


def is_mac() -> bool:
    return sys.platform == "darwin"


def is_linux() -> bool:
    return sys.platform.startswith("linux")


# -------------------------------------------------
# ARCHITECTURE
# -------------------------------------------------

def get_architecture() -> str:
    """
    Retorna '32bit' ou '64bit'
    """
    return platform.architecture()[0]


# -------------------------------------------------
# PYTHON INFO
# -------------------------------------------------

def get_python_version() -> str:
    return platform.python_version()


# -------------------------------------------------
# BLENDER ENV CHECK
# -------------------------------------------------

def is_running_in_blender() -> bool:
    try:
        import bpy  # noqa
        return True
    except ImportError:
        return False


# -------------------------------------------------
# SYSTEM SUMMARY
# -------------------------------------------------

def get_system_summary() -> dict:
    """
    Retorna informações úteis para debug.
    """

    return {
        "platform": get_platform(),
        "architecture": get_architecture(),
        "python_version": get_python_version(),
        "in_blender": is_running_in_blender(),
    }