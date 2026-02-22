# operators.py
import bpy
import os
import subprocess
from ..core import global_cache
from ..utils.paths import get_temp_dir
from ..utils.logging import info, error


# -------------------------------------------------
# HELPER — verifica se o VSE está pronto para uso
# -------------------------------------------------
def _vse_is_ready(operator, context):
    scene = context.scene
    if not scene:
        operator.report({'ERROR'}, "Nenhuma cena ativa encontrada")
        return False

    seq = scene.sequence_editor
    if not seq:
        scene.sequence_editor_create()
        seq = scene.sequence_editor

    if not seq:
        operator.report({'ERROR'}, "Não foi possível inicializar o Sequencer")
        return False

    # Blender 5.0 usa strips/strips_all
    strips = None
    for attr in ('strips_all', 'strips', 'sequences_all', 'sequences'):
        try:
            strips = list(getattr(seq, attr))
            break
        except AttributeError:
            continue

    if strips is None:
        operator.report({'ERROR'}, "Não foi possível acessar os strips do VSE")
        return False

    if len(strips) == 0:
        operator.report({'ERROR'}, "Nenhum strip encontrado no VSE. Adicione um vídeo ou áudio primeiro.")
        return False

    return True


# -------------------------------------------------
# ANALYZE AUDIO OPERATOR
# -------------------------------------------------
class AUDIOMAX_OT_AnalyzeAudio(bpy.types.Operator):
    bl_idname = "audiomax.analyze_audio"
    bl_label = "Analyze Audio"
    bl_description = "Process audio from VSE (placeholder)"

    def execute(self, context):
        info("Iniciando análise de áudio...")
        return {'FINISHED'}


# -------------------------------------------------
# EXTRACT / CONVERT AUDIO OPERATOR
# -------------------------------------------------
class AUDIOMAX_OT_ConvertVSEAudio(bpy.types.Operator):
    bl_idname = "audiomax.convert_vse_audio"
    bl_label = "Convert Audio (MP4 → WAV/MP3)"
    bl_description = "Extract audio from VSE video strips as WAV or MP3"

    audio_format: bpy.props.EnumProperty(
        name="Audio Format",
        description="Choose format to export audio",
        items=[("WAV", "WAV", ""), ("MP3", "MP3", "")]
    )

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        # Lazy import para evitar circular import
        from ..core.audio_export import export_vse_audio, has_audio_in_vse

        if not _vse_is_ready(self, context):
            return {'CANCELLED'}

        if not has_audio_in_vse():
            self.report({'ERROR'}, "Nenhum strip de áudio encontrado no VSE. O vídeo tem faixa de áudio?")
            return {'CANCELLED'}

        audio_file = export_vse_audio(format=self.audio_format.lower())
        if not audio_file:
            self.report({'ERROR'}, "Falha ao exportar o áudio")
            return {'CANCELLED'}

        self.report({'INFO'}, f"Áudio exportado: {audio_file}")
        info(f"Áudio exportado: {audio_file}")

        bpy.ops.audiomax.send_daw_popup('INVOKE_DEFAULT', audio_file=audio_file)
        return {'FINISHED'}


# -------------------------------------------------
# SEND AUDIO TO DAW
# -------------------------------------------------
class AUDIOMAX_OT_SendAudioToDAW(bpy.types.Operator):
    bl_idname = "audiomax.send_audio_to_daw"
    bl_label = "Send Audio to DAW"
    bl_description = "Send audio to the selected DAW"

    daw_path: bpy.props.StringProperty()
    audio_file: bpy.props.StringProperty()

    def execute(self, context):
        if not os.path.exists(self.audio_file):
            self.report({'ERROR'}, "Arquivo de áudio não encontrado")
            return {'CANCELLED'}

        if not os.path.exists(self.daw_path):
            self.report({'ERROR'}, f"DAW não encontrada: {self.daw_path}")
            return {'CANCELLED'}

        try:
            subprocess.Popen([self.daw_path, self.audio_file])
            info(f"Áudio enviado para {self.daw_path}")
            self.report({'INFO'}, f"Áudio enviado para {os.path.basename(self.daw_path)}")
        except Exception as e:
            error(str(e))
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}

        return {'FINISHED'}


# -------------------------------------------------
# SEND TO DAW POPUP
# -------------------------------------------------
class AUDIOMAX_OT_SendDAWPopup(bpy.types.Operator):
    bl_idname = "audiomax.send_daw_popup"
    bl_label = "Send Audio to DAW?"
    bl_description = "Ask the user if they want to send the audio to a DAW now"

    audio_file: bpy.props.StringProperty()

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=300)

    def draw(self, context):
        layout = self.layout
        layout.label(text=f"Do you want to send {os.path.basename(self.audio_file)} to a DAW now?")

    def execute(self, context):
        bpy.ops.audiomax.select_daw('INVOKE_DEFAULT', audio_file=self.audio_file)
        return {'FINISHED'}


# -------------------------------------------------
# SELECT / BROWSE DAW OPERATOR
# -------------------------------------------------
class AUDIOMAX_OT_SelectDAW(bpy.types.Operator):
    bl_idname = "audiomax.select_daw"
    bl_label = "Export to DAW"
    bl_description = "Select a DAW to export audio"

    audio_file: bpy.props.StringProperty()

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=500)

    def draw(self, context):
        layout = self.layout
        daw_paths = global_cache.get_cached_daws()

        if daw_paths:
            layout.label(text="Installed DAWs detected:")
            for path in daw_paths:
                row = layout.row()
                daw_name = os.path.basename(path)
                op = row.operator("audiomax.send_audio_to_daw", text=daw_name)
                op.daw_path = path
                op.audio_file = self.audio_file
        else:
            layout.label(text="No DAWs detected")

        layout.separator()
        layout.operator("audiomax.browse_daw", icon="FILE_FOLDER").audio_file = self.audio_file

    def execute(self, context):
        return {'FINISHED'}


# -------------------------------------------------
# BROWSE DAW MANUALLY
# -------------------------------------------------
class AUDIOMAX_OT_BrowseDAW(bpy.types.Operator):
    bl_idname = "audiomax.browse_daw"
    bl_label = "Browse for DAW"
    bl_description = "Manually select a DAW executable"

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")
    audio_file: bpy.props.StringProperty()

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        if not os.path.exists(self.filepath):
            self.report({'ERROR'}, "Arquivo selecionado não existe")
            return {'CANCELLED'}

        bpy.ops.audiomax.send_audio_to_daw(daw_path=self.filepath, audio_file=self.audio_file)
        return {'FINISHED'}


# -------------------------------------------------
# REGISTER
# -------------------------------------------------
OPERATOR_CLASSES = (
    AUDIOMAX_OT_AnalyzeAudio,
    AUDIOMAX_OT_ConvertVSEAudio,
    AUDIOMAX_OT_SendAudioToDAW,
    AUDIOMAX_OT_SendDAWPopup,
    AUDIOMAX_OT_SelectDAW,
    AUDIOMAX_OT_BrowseDAW,
)

def register():
    for cls in OPERATOR_CLASSES:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(OPERATOR_CLASSES):
        bpy.utils.unregister_class(cls)