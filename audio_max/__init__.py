bl_info = {
    "name": "Audio Max",
    "author": "Italo Nicacio",
    "version": (7, 0, 0),
    "blender": (4, 0, 0),
    "location": "Sequencer > Sidebar > AudioMax",
    "description": "Advanced Audio Processing for Blender",
    "category": "Animation",
}

import bpy

from .ui.panels import PANEL_CLASSES
from .ui.operators import OPERATOR_CLASSES
from .core import global_cache

# detect_all_audio_hosts e detect_daw removidos daqui —
# nunca foram usados diretamente neste arquivo e causavam
# circular import na inicialização do addon

CLASSES = (
    *PANEL_CLASSES,
    *OPERATOR_CLASSES,
)


def initialize_system():
    print("Audio Max: Inicializando sistema...")

    def detect_daws_callback():
        global_cache.update_daw_cache()
        print("DAWs detectadas:", global_cache.get_cached_daws())
        return None

    bpy.app.timers.register(detect_daws_callback, first_interval=1.0)


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)

    if hasattr(bpy.context, 'scene'):
        initialize_system()

    print("Audio Max registrado com sucesso.")


def unregister():
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)

    print("Audio Max removido.")