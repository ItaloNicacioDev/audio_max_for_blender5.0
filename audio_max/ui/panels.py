import bpy

from ..external.host_priority import get_best_host
from ..core import global_cache


# -------------------------------------------------
# BASE DRAW FUNCTION (compartilhada entre painéis)
# Usada apenas no VIEW_3D onde não há painel dedicado
# -------------------------------------------------

def draw_main_ui(self, context):
    layout = self.layout

    box = layout.box()
    box.label(text="Host Detection", icon="SOUND")

    hosts = global_cache.get_cached_daws()
    if hosts:
        best = get_best_host(hosts)
        # Mostra apenas o nome do executável, não o caminho completo
        box.label(text=f"Best Host: {best}", icon="CHECKBOX_HLT")
    else:
        box.label(text="No Host Found", icon="ERROR")

    box = layout.box()
    box.label(text="Export to DAW", icon="EXPORT")
    box.operator("audiomax.select_daw", icon="EXPORT")


# -------------------------------------------------
# VIEW 3D PANEL
# -------------------------------------------------

class AUDIOMAX_PT_View3D(bpy.types.Panel):
    bl_label = "Audio Max"
    bl_idname = "AUDIOMAX_PT_view3d"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "AudioMax"

    def draw(self, context):
        draw_main_ui(self, context)


# -------------------------------------------------
# SEQUENCER (VSE) PANEL — painel principal
# -------------------------------------------------

class AUDIOMAX_PT_MainPanel(bpy.types.Panel):
    bl_label = "AudioMax"
    bl_idname = "AUDIOMAX_PT_main_panel"
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"
    bl_category = "AudioMax"

    def draw(self, context):
        layout = self.layout

        # --- Host Detection ---
        box = layout.box()
        box.label(text="Host Detection", icon="SOUND")
        hosts = global_cache.get_cached_daws()
        if hosts:
            best = get_best_host(hosts)
            box.label(text=f"Best: {best}", icon="CHECKBOX_HLT")
        else:
            box.label(text="No Host Found", icon="ERROR")

        layout.separator()

        # --- Convert Audio ---
        box = layout.box()
        box.label(text="Convert Audio from VSE:", icon="SOUND")
        box.operator("audiomax.convert_vse_audio", icon="EXPORT")

        layout.separator()

        # --- Send to DAW ---
        box = layout.box()
        box.label(text="Send Audio to DAW:", icon="PLAY")
        box.operator("audiomax.select_daw", icon="PLAY")

        layout.separator()

        # --- Analyze Audio ---
        box = layout.box()
        box.label(text="Analyze Audio:", icon="GRAPH")
        box.operator("audiomax.analyze_audio", icon="GRAPH")


# -------------------------------------------------
# EXPORT CLASSES — todas as classes usadas pelo __init__.py
# -------------------------------------------------

PANEL_CLASSES = (
    AUDIOMAX_PT_View3D,
    AUDIOMAX_PT_MainPanel,   # ← corrigido: estava faltando aqui
)