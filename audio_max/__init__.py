# audio_max - __init__.py (versão completa, otimizada para Blender 5.0)
bl_info = {
    "name": "audio_max",
    "author": "Italo Nicacio",
    "version": (1, 0, 4),
    "blender": (5, 0, 0),
    "location": "Sequencer (VSE) > Sidebar",
    "description": "Audio Max — processamento de áudio offline para VSE, instalador automático de dependências, interface estilo Vegas (Track Mixer + Rack de efeitos). Suporta EQ interno e processamento via VST externo (configurável).",
    "category": "Sequencer",
}

# Standard library
import os
import sys
import tempfile
import shutil
import threading
import importlib
import subprocess
import shlex
import json
import time
from math import log10
from pathlib import Path

# Blender
import bpy
from bpy.props import FloatProperty, IntProperty, StringProperty, BoolProperty
from bpy.types import AddonPreferences

# Third-party installation helper (may fail depending on Blender build)
try:
    import ensurepip
except Exception:
    ensurepip = None

# ---------- Configuration ----------
DEPENDENCIAS = [
    "python-osc",
    "pydub",
    "numpy",
    "scipy",
    "noisereduce"
]

# Folder variables
ADDON_DIR = os.path.dirname(os.path.abspath(__file__))
LIBS_DIR = os.path.join(ADDON_DIR, "libs")
LOG_FILE = os.path.join(ADDON_DIR, "audio_max.log")

# ---------- Logging helper ----------
def log(msg):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[audio_max] {ts} - {msg}"
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        # fallback to print if not writable
        print(line)

# ---------- Dependency installer (best-effort) ----------
def instalar_dependencias():
    python_exe = sys.executable
    log("Starting dependency installer")
    try:
        if ensurepip:
            try:
                ensurepip.bootstrap()
                log("ensurepip bootstrap OK")
            except Exception as e:
                log(f"ensurepip.bootstrap failed: {e}")
    except Exception as e:
        log(f"ensurepip availability check failed: {e}")

    try:
        subprocess.check_call([python_exe, "-m", "pip", "install", "--upgrade", "pip"])
    except Exception as e:
        log(f"pip upgrade failed: {e}")

    for dep in DEPENDENCIAS:
        try:
            installed = False
            # try local wheels first
            if os.path.isdir(LIBS_DIR):
                for fname in os.listdir(LIBS_DIR):
                    if dep.replace("-", "_") in fname and fname.endswith(".whl"):
                        whl = os.path.join(LIBS_DIR, fname)
                        log(f"Installing local wheel: {whl}")
                        subprocess.check_call([python_exe, "-m", "pip", "install", whl])
                        installed = True
                        break
            if not installed:
                log(f"Installing from pip: {dep}")
                subprocess.check_call([python_exe, "-m", "pip", "install", dep])
            log(f"Installed dependency: {dep}")
        except Exception as e:
            log(f"Failed installing {dep}: {e}")

def dependencias_instaladas():
    try:
        for mod in ["pythonosc", "pydub", "numpy", "scipy", "noisereduce"]:
            importlib.import_module(mod)
        return True
    except Exception as e:
        log(f"dependency check failed: {e}")
        return False

# ---------- Helpers for VSE strips ----------
def _get_sequences_collection(seq):
    """
    Return a sequences iterable compatible with multiple Blender versions.
    Prefer sequences_all if available (older API), otherwise sequences.
    """
    if not seq:
        return []
    if hasattr(seq, "sequences_all"):
        try:
            return seq.sequences_all
        except Exception:
            pass
    if hasattr(seq, "sequences"):
        try:
            return seq.sequences
        except Exception:
            pass
    # fallback: try to iterate attributes
    return []

def get_all_sound_strips(scene):
    seq = getattr(scene, "sequence_editor", None)
    if not seq:
        return []
    sequences = _get_sequences_collection(seq)
    return [s for s in sequences if getattr(s, "type", None) == 'SOUND']

def get_selected_sound_strip(context):
    seq = getattr(context.scene, "sequence_editor", None)
    if not seq:
        return None
    sequences = _get_sequences_collection(seq)
    for s in sequences:
        if getattr(s, "select", False) and getattr(s, "type", None) == 'SOUND':
            return s
    return None

def get_sound_path(strip):
    if not strip or not getattr(strip, "sound", None):
        return None
    try:
        from bpy import path as bpy_path
        return bpy_path.abspath(strip.sound.filepath)
    except Exception:
        return strip.sound.filepath

# ---------- WindowManager state helpers ----------
def ensure_wm_state(wm):
    if "audio_max_tracks" not in wm:
        wm["audio_max_tracks"] = {}
    return wm["audio_max_tracks"]

def get_track_state(wm, strip):
    tracks = ensure_wm_state(wm)
    key = getattr(strip, "name", f"strip_{strip.as_pointer()}")
    if key not in tracks:
        tracks[key] = {
            "volume_db": 0.0,
            "pan": 0.0,
            "mute": False,
            "solo": False,
            "vu_level": 0.0,
            "slots": ["", "", ""],
        }
    return tracks[key]

# ---------- Audio IO & basic effects (pydub) ----------
def load_audio_segment(filepath):
    # Lazy import to avoid hard dependency at import time
    try:
        from pydub import AudioSegment
    except Exception as e:
        log(f"pydub import failed: {e}")
        raise
    return AudioSegment.from_file(filepath)

def export_temp_wav(seg, prefix="audio_max"):
    tmp = tempfile.mkdtemp(prefix=prefix)
    outpath = os.path.join(tmp, "processed.wav")
    seg.export(outpath, format="wav")
    return outpath, tmp

def change_volume(seg, db_change):
    return seg + db_change

def apply_normalize(seg):
    from pydub.effects import normalize
    return normalize(seg)

def apply_fade(seg, fade_in_ms, fade_out_ms):
    return seg.fade_in(int(fade_in_ms)).fade_out(int(fade_out_ms))

def apply_pan(seg, percent):
    return seg.pan(percent)

def apply_delay(seg, delay_ms=250, repeats=2):
    out = seg
    for i in range(1, repeats + 1):
        delayed = seg - (i * 6)
        out = out.overlay(delayed, position=delay_ms * i)
    return out

def apply_reverb_simple(seg):
    out = seg
    delays = [50, 120, 200]
    for i, d in enumerate(delays):
        copy = seg - (i * 3)
        out = out.overlay(copy, position=d)
    return out

def apply_compressor_simple(seg, threshold_db=-20.0, ratio=4.0):
    try:
        import numpy as np
    except Exception as e:
        log(f"numpy import failed in compressor: {e}")
        raise
    samples = seg.get_array_of_samples()
    arr = np.array(samples).astype(float)
    maxv = np.max(np.abs(arr)) or 1.0
    arr_norm = arr / maxv
    rms = (arr_norm ** 2).mean() ** 0.5
    level_db = 20 * log10(rms + 1e-12)
    gain = 1.0
    if level_db > threshold_db:
        gain = 1.0 / ratio
    arr2 = (arr * gain).astype(seg.array_type)
    new = seg._spawn(arr2.tobytes())
    return new

def apply_denoise(seg):
    try:
        import numpy as np
        import noisereduce as nr
    except Exception as e:
        log(f"noisereduce or numpy missing in denoise: {e}")
        return seg
    samples = seg.get_array_of_samples()
    arr = (np.array(samples)).astype(float)
    if seg.channels > 1:
        arr = arr.reshape((-1, seg.channels)).T
        reduced = []
        for ch in arr:
            reduced_ch = nr.reduce_noise(y=ch, sr=seg.frame_rate)
            reduced.append(reduced_ch)
        out = (np.vstack(reduced).T.flatten()).astype(seg.array_type)
    else:
        reduced = nr.reduce_noise(y=arr, sr=seg.frame_rate)
        out = reduced.astype(seg.array_type)
    return seg._spawn(out.tobytes())

def detect_peaks(seg, threshold_db=-6.0):
    try:
        import numpy as np
    except Exception as e:
        log(f"numpy missing in detect_peaks: {e}")
        raise
    samples = seg.get_array_of_samples()
    arr = np.array(samples).astype(float)
    peak_threshold = seg.max_possible_amplitude * (10 ** (threshold_db / 20.0))
    peak_idx = (abs(arr) > peak_threshold)
    positions = []
    if peak_idx.any():
        idxs = np.nonzero(peak_idx)[0]
        for i in idxs[::max(1, len(idxs) // 50)]:
            ms = (i / seg.frame_rate) * 1000.0
            positions.append(ms)
    return len(positions), positions

# ---------- Internal EQ (10-band) using scipy.signal ----------
def internal_eq_10band(seg, gains_db):
    try:
        import numpy as np
        from scipy.signal import iirpeak, lfilter
    except Exception as e:
        log(f"scipy/numpy required for internal EQ: {e}")
        return seg

    centers = [31, 62, 125, 250, 500, 1000, 2000, 4000, 8000, 16000]
    sr = seg.frame_rate
    samples = seg.get_array_of_samples()
    arr = np.array(samples).astype(float)

    channels = seg.channels
    if channels > 1:
        arr = arr.reshape((-1, channels)).T

    def process_channel(y):
        out = y.copy()
        for center, gain_db in zip(centers, gains_db):
            if abs(gain_db) < 0.01:
                continue
            Q = 1.0
            try:
                # iirpeak expects normalized frequency in (0, 1) relative to Nyquist
                b, a = iirpeak(center / (sr / 2), Q)
                filtered = lfilter(b, a, out)
                gain_lin = 10 ** (gain_db / 20.0)
                out = out + (filtered - out) * (gain_lin - 1.0) * 0.5
            except Exception as e:
                # don't fail whole eq for single band error
                log(f"internal_eq band error center={center}: {e}")
                pass
        return out

    if channels > 1:
        out_ch = []
        for ch in arr:
            out_ch.append(process_channel(ch))
        out = np.vstack(out_ch).T.flatten()
    else:
        out = process_channel(arr)

    out = out.astype(seg.array_type)
    new = seg._spawn(out.tobytes())
    return new

# ---------- VST external processing operator ----------
def run_external_vst_processing(cmd_template, vst_path, in_wav, out_wav, timeout=120):
    """
    Supports templates using either:
        {input}, {output}, {vst}
    or
        {in}, {out}, {vst}
    We format using dict to allow reserved keywords safely.
    """
    if not cmd_template:
        raise RuntimeError("Empty external processing command template.")
    # Check for required placeholders (be permissive)
    if not (("{in}" in cmd_template and "{out}" in cmd_template) or ("{input}" in cmd_template and "{output}" in cmd_template)):
        raise RuntimeError("Invalid external processing command template. Must contain {in}/{input} and {out}/{output} placeholders.")

    # Build format mapping (include both names for compatibility)
    mapping = {
        "in": in_wav,
        "out": out_wav,
        "vst": vst_path,
        "input": in_wav,
        "output": out_wav,
        "plugin": vst_path
    }

    # Safe format: use str.format_map to avoid reserved word errors
    try:
        cmd = cmd_template.format_map(mapping)
    except Exception as e:
        # fallback to manual replace for simple templates
        try:
            cmd = cmd_template.replace("{in}", mapping["in"]).replace("{out}", mapping["out"]).replace("{vst}", mapping["vst"]).replace("{input}", mapping["input"]).replace("{output}", mapping["output"]).replace("{plugin}", mapping["plugin"])
        except Exception as e2:
            raise RuntimeError(f"Failed to build command from template: {e} / {e2}")

    # Choose shell usage: on Windows we use shell True by default to allow paths with spaces,
    # on other OS enable shell only if the template contains shell operators.
    shell_operators = (";", "|", "&&")
    use_shell = isinstance(cmd, str) and (sys.platform == "win32" or any(op in cmd for op in shell_operators))
    log(f"Executing external VST command: {cmd} (use_shell={use_shell})")
    try:
        if use_shell:
            proc = subprocess.Popen(cmd, shell=True)
        else:
            parts = shlex.split(cmd)
            proc = subprocess.Popen(parts)
        try:
            proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            proc.kill()
            raise RuntimeError("External host timed out")
        if proc.returncode != 0:
            raise RuntimeError(f"External host returned code {proc.returncode}")
        return True
    except Exception as e:
        raise RuntimeError(f"External processing failed: {e}")

# ---------- Operators ----------
class AMAX_OT_apply_volume(bpy.types.Operator):
    bl_idname = "amax.apply_volume"
    bl_label = "Aplicar Volume (offline)"
    db_change: FloatProperty(name="dB", default=0.0, min=-60.0, max=60.0)

    def execute(self, context):
        s = get_selected_sound_strip(context)
        if not s:
            self.report({'ERROR'}, "Selecione uma faixa de áudio")
            return {'CANCELLED'}
        path = get_sound_path(s)
        try:
            seg = load_audio_segment(path)
            new = change_volume(seg, self.db_change)
            outpath, tmp = export_temp_wav(new, "audio_max_vol")
            bpy.ops.sequencer.sound_strip_add(filepath=outpath, frame_start=s.frame_start, channel=s.channel + 1)
            self.report({'INFO'}, "Volume aplicado (novo strip criado)")
            return {'FINISHED'}
        except Exception as e:
            log(f"apply_volume error: {e}")
            self.report({'ERROR'}, f"Erro: {e}")
            return {'CANCELLED'}

class AMAX_OT_normalize(bpy.types.Operator):
    bl_idname = "amax.normalize"
    bl_label = "Normalizar"

    def execute(self, context):
        s = get_selected_sound_strip(context)
        if not s:
            self.report({'ERROR'}, "Selecione uma faixa")
            return {'CANCELLED'}
        try:
            seg = load_audio_segment(get_sound_path(s))
            new = apply_normalize(seg)
            outpath, tmp = export_temp_wav(new, "audio_max_norm")
            bpy.ops.sequencer.sound_strip_add(filepath=outpath, frame_start=s.frame_start, channel=s.channel + 1)
            self.report({'INFO'}, "Normalização aplicada")
            return {'FINISHED'}
        except Exception as e:
            log(f"normalize error: {e}")
            self.report({'ERROR'}, f"Erro: {e}")
            return {'CANCELLED'}

class AMAX_OT_fade(bpy.types.Operator):
    bl_idname = "amax.fade"
    bl_label = "Fade In/Out"
    fade_in_ms: IntProperty(name="Fade In (ms)", default=500, min=0)
    fade_out_ms: IntProperty(name="Fade Out (ms)", default=500, min=0)

    def execute(self, context):
        s = get_selected_sound_strip(context)
        if not s:
            self.report({'ERROR'}, "Selecione")
            return {'CANCELLED'}
        try:
            seg = load_audio_segment(get_sound_path(s))
            new = apply_fade(seg, self.fade_in_ms, self.fade_out_ms)
            outpath, tmp = export_temp_wav(new, "audio_max_fade")
            bpy.ops.sequencer.sound_strip_add(filepath=outpath, frame_start=s.frame_start, channel=s.channel + 1)
            self.report({'INFO'}, "Fade aplicado")
            return {'FINISHED'}
        except Exception as e:
            log(f"fade error: {e}")
            self.report({'ERROR'}, f"Erro: {e}")
            return {'CANCELLED'}

class AMAX_OT_denoise(bpy.types.Operator):
    bl_idname = "amax.denoise"
    bl_label = "Remover Ruído"

    def execute(self, context):
        s = get_selected_sound_strip(context)
        if not s:
            self.report({'ERROR'}, "Selecione")
            return {'CANCELLED'}
        try:
            seg = load_audio_segment(get_sound_path(s))
            new = apply_denoise(seg)
            outpath, tmp = export_temp_wav(new, "audio_max_denoise")
            bpy.ops.sequencer.sound_strip_add(filepath=outpath, frame_start=s.frame_start, channel=s.channel + 1)
            self.report({'INFO'}, "Denoise aplicado")
            return {'FINISHED'}
        except Exception as e:
            log(f"denoise error: {e}")
            self.report({'ERROR'}, f"Erro: {e}")
            return {'CANCELLED'}

class AMAX_OT_detect_peaks(bpy.types.Operator):
    bl_idname = "amax.detect_peaks"
    bl_label = "Detect Peaks"
    threshold: FloatProperty(name="Threshold dB", default=-6.0)

    def execute(self, context):
        s = get_selected_sound_strip(context)
        if not s:
            self.report({'ERROR'}, "Selecione")
            return {'CANCELLED'}
        try:
            seg = load_audio_segment(get_sound_path(s))
            count, positions = detect_peaks(seg, self.threshold)
            self.report({'INFO'}, f"Picos: {count}")
            print("[audio_max] peak positions:", positions[:50])
            return {'FINISHED'}
        except Exception as e:
            log(f"detect_peaks error: {e}")
            self.report({'ERROR'}, f"Erro: {e}")
            return {'CANCELLED'}

class AMAX_OT_send_osc(bpy.types.Operator):
    bl_idname = "amax.send_osc"
    bl_label = "Enviar OSC Test"

    def execute(self, context):
        try:
            from pythonosc import udp_client
            client = udp_client.SimpleUDPClient("127.0.0.1", 9000)
            client.send_message("/audio_max/test", ["hello"])
            self.report({'INFO'}, "OSC enviado")
            return {'FINISHED'}
        except Exception as e:
            log(f"send_osc error: {e}")
            self.report({'ERROR'}, f"OSC falhou: {e}")
            return {'CANCELLED'}

class AMAX_OT_internal_eq(bpy.types.Operator):
    bl_idname = "amax.internal_eq"
    bl_label = "Equalizador Interno (10 bandas)"
    g0: FloatProperty(name="31Hz (dB)", default=0.0)
    g1: FloatProperty(name="62Hz (dB)", default=0.0)
    g2: FloatProperty(name="125Hz (dB)", default=0.0)
    g3: FloatProperty(name="250Hz (dB)", default=0.0)
    g4: FloatProperty(name="500Hz (dB)", default=0.0)
    g5: FloatProperty(name="1kHz (dB)", default=0.0)
    g6: FloatProperty(name="2kHz (dB)", default=0.0)
    g7: FloatProperty(name="4kHz (dB)", default=0.0)
    g8: FloatProperty(name="8kHz (dB)", default=0.0)
    g9: FloatProperty(name="16kHz (dB)", default=0.0)

    def execute(self, context):
        s = get_selected_sound_strip(context)
        if not s:
            self.report({'ERROR'}, "Selecione strip")
            return {'CANCELLED'}
        try:
            seg = load_audio_segment(get_sound_path(s))
            gains = [self.g0, self.g1, self.g2, self.g3, self.g4,
                     self.g5, self.g6, self.g7, self.g8, self.g9]
            new = internal_eq_10band(seg, gains)
            outpath, tmp = export_temp_wav(new, "audio_max_eq")
            bpy.ops.sequencer.sound_strip_add(filepath=outpath, frame_start=s.frame_start, channel=s.channel + 1)
            self.report({'INFO'}, "EQ interno aplicado")
            return {'FINISHED'}
        except Exception as e:
            log(f"internal_eq error: {e}")
            self.report({'ERROR'}, f"Erro: {e}")
            return {'CANCELLED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=420)

class AMAX_OT_apply_eq_vst(bpy.types.Operator):
    bl_idname = "amax.eq_vst"
    bl_label = "Equalizar via VST externo (host configurável)"

    plugin_path: StringProperty(name="VST path / ID", default="", subtype='FILE_PATH')
    timeout_seconds: IntProperty(name="Timeout (s)", default=120, min=10, max=3600)

    def execute(self, context):
        prefs = context.preferences.addons.get(__name__)
        if prefs:
            prefs = prefs.preferences
        else:
            # fallback to AddonPreferences retrieval by module name 'audio_max'
            try:
                prefs = bpy.context.preferences.addons["audio_max"].preferences
            except Exception:
                prefs = None

        cmd_template = getattr(prefs, "vst_command_template", "").strip() if prefs else ""
        vst = self.plugin_path if self.plugin_path else (getattr(prefs, "default_vst_path", "") if prefs else "")

        if not vst:
            self.report({'ERROR'}, "Forneça caminho/ID do plugin no campo ou nas Preferências do Addon")
            return {'CANCELLED'}

        s = get_selected_sound_strip(context)
        if not s:
            self.report({'ERROR'}, "Selecione strip")
            return {'CANCELLED'}
        in_wav, tmpdir1 = None, None
        tmpdir2 = None
        try:
            seg = load_audio_segment(get_sound_path(s))
            in_wav, tmpdir1 = export_temp_wav(seg, "audio_max_in")
            tmpdir2 = tempfile.mkdtemp(prefix="audio_max_out")
            out_wav = os.path.join(tmpdir2, "processed.wav")
            run_external_vst_processing(cmd_template, vst, in_wav, out_wav, timeout=self.timeout_seconds)
            if os.path.exists(out_wav):
                bpy.ops.sequencer.sound_strip_add(filepath=out_wav, frame_start=s.frame_start, channel=s.channel + 1)
                self.report({'INFO'}, "EQ via VST aplicado (novo strip criado)")
            else:
                self.report({'ERROR'}, "Arquivo de saída não foi gerado pelo host externo")
                return {'CANCELLED'}
            return {'FINISHED'}
        except Exception as e:
            log(f"apply_eq_vst error: {e}")
            self.report({'ERROR'}, f"VST processing failed: {e}")
            return {'CANCELLED'}
        finally:
            # cleanup tmp input dir if created
            try:
                if in_wav and tmpdir1 and os.path.isdir(tmpdir1):
                    shutil.rmtree(tmpdir1)
            except Exception:
                pass
            # do not remove tmpdir2 because we add the out file into VSE from there — user might want to inspect
            # but we could schedule later cleanup; keep it for now

class AMAX_OT_toggle_mute(bpy.types.Operator):
    bl_idname = "amax.toggle_mute"
    bl_label = "Toggle Mute"
    strip_name: StringProperty()

    def execute(self, context):
        wm = context.window_manager
        strips = ensure_wm_state(wm)
        if self.strip_name not in strips:
            strips[self.strip_name] = {"volume_db": 0.0, "pan": 0.0, "mute": False, "solo": False, "vu_level": 0.0, "slots": ["", "", ""]}
        strips[self.strip_name]["mute"] = not strips[self.strip_name]["mute"]
        self.report({'INFO'}, f"Mute toggled for {self.strip_name}")
        return {'FINISHED'}

class AMAX_OT_toggle_solo(bpy.types.Operator):
    bl_idname = "amax.toggle_solo"
    bl_label = "Toggle Solo"
    strip_name: StringProperty()

    def execute(self, context):
        wm = context.window_manager
        strips = ensure_wm_state(wm)
        if self.strip_name not in strips:
            strips[self.strip_name] = {"volume_db": 0.0, "pan": 0.0, "mute": False, "solo": False, "vu_level": 0.0, "slots": ["", "", ""]}
        strips[self.strip_name]["solo"] = not strips[self.strip_name]["solo"]
        self.report({'INFO'}, f"Solo toggled for {self.strip_name}")
        return {'FINISHED'}

class AMAX_OT_slot_edit(bpy.types.Operator):
    bl_idname = "amax.slot_edit"
    bl_label = "Edit Effect Slot"
    slot_index: IntProperty()

    def execute(self, context):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "slot_index")
        layout.label(text="(Offline placeholder) Escolha efeito para o slot")

    def invoke(self, context, event):
        return self.execute(context)

class AMAX_OT_open_track_rack(bpy.types.Operator):
    bl_idname = "amax.open_track_rack"
    bl_label = "Open Track Rack"

    def execute(self, context):
        return context.window_manager.invoke_props_dialog(self, width=800)

    def draw(self, context):
        layout = self.layout
        s = get_selected_sound_strip(context)
        if not s:
            layout.label(text="Selecione uma faixa antes de abrir o rack")
            return
        wm = context.window_manager
        st = get_track_state(wm, s)
        layout.label(text=f"Track Rack - {s.name}")
        layout.label(text=f"Volume: {st['volume_db']:+.1f} dB")
        row = layout.row()
        row.operator("amax.apply_volume", text="Apply Volume (offline)").db_change = st["volume_db"]
        layout.operator("amax.denoise", text="Remove Ruído")
        layout.operator("amax.fade", text="Fade In/Out")
        layout.operator("amax.normalize", text="Normalize")
        layout.separator()
        layout.label(text="Equalizadores")
        layout.operator("amax.internal_eq", text="EQ Interno (10 bands)")
        layout.operator("amax.eq_vst", text="EQ via VST externo")

# ---------- Panels ----------
class AMAX_PT_track_mixer(bpy.types.Panel):
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"
    bl_category = "Audio Max"
    bl_label = "Track Mixer (Vegas-like)"

    def draw(self, context):
        layout = self.layout
        wm = context.window_manager
        scene = context.scene
        strips = get_all_sound_strips(scene)
        layout.label(text="Track Mixer")
        if not strips:
            layout.label(text="Nenhuma faixa de áudio no VSE")
            return

        for s in strips:
            box = layout.box()
            row = box.row(align=True)
            row.label(text=s.name, icon='SOUND')
            st = get_track_state(wm, s)
            row.operator("amax.toggle_mute", text=("Mute" if not st["mute"] else "Unmute")).strip_name = s.name
            row.operator("amax.toggle_solo", text=("Solo" if not st["solo"] else "Unsolo")).strip_name = s.name

            col = box.column()
            col.label(text=f"Volume: {st['volume_db']:+.1f} dB")
            op = col.operator("amax.apply_volume", text="Apply Volume (offline)")
            op.db_change = st["volume_db"]
            col.label(text=f"Pan: {st['pan']:+.2f}")
            col.operator("amax.send_osc", text="Send OSC")
            vu = st.get("vu_level", 0.0)
            col.label(text=f"VU: {vu:.2f}")
            slot_row = box.row()
            slot_row.label(text="Effect Slots:")
            for i in range(len(st["slots"])):
                slot_row.operator("amax.slot_edit", text=(st["slots"][i] if st["slots"][i] else f"Slot {i+1}")).slot_index = i
            box.operator("amax.open_track_rack", text="Open Rack")

class AMAX_PT_dopesheet(bpy.types.Panel):
    bl_space_type = "DOPESHEET_EDITOR"
    bl_region_type = "UI"
    bl_category = "Audio Max"
    bl_label = "Audio Max - Timeline (compact)"

    def draw(self, context):
        layout = self.layout
        layout.label(text="Audio Max (Timeline quick access)")
        layout.operator("amax.export_selected", icon='SOUND')
        layout.operator("amax.apply_volume", text="Apply Volume")
        layout.operator("amax.normalize")
        layout.operator("amax.fade")
        layout.operator("amax.denoise")

# Additional FX Rack panel
class AMAX_PT_fx_rack(bpy.types.Panel):
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"
    bl_category = "Audio Max"
    bl_label = "FX Rack (offline)"

    def draw(self, context):
        layout = self.layout
        s = get_selected_sound_strip(context)
        if not s:
            layout.label(text="Selecione um strip de áudio para editar o Rack")
            return
        wm = context.window_manager
        st = get_track_state(wm, s)
        layout.label(text=f"FX Rack - {s.name}")
        # Show slots
        for i, slot in enumerate(st["slots"]):
            row = layout.row(align=True)
            row.label(text=f"Slot {i+1}: {slot if slot else '(vazio)'}")
            op = row.operator("amax.slot_edit", text="Editar")
            op.slot_index = i
            rm = row.operator("amax.fx_slot_clear", text="", icon='X')
            rm.slot_index = i
        layout.separator()
        layout.label(text="Offline effects")
        col = layout.column()
        col.operator("amax.denoise", text="Denoise")
        col.operator("amax.internal_eq", text="EQ Interno (10 bands)")
        col.operator("amax.eq_vst", text="EQ via VST externo")
        col.operator("amax.apply_volume", text="Apply Volume (offline)")

# Operator to clear a slot (added for FX Rack)
class AMAX_OT_fx_slot_clear(bpy.types.Operator):
    bl_idname = "amax.fx_slot_clear"
    bl_label = "Clear FX Slot"
    slot_index: IntProperty()

    def execute(self, context):
        s = get_selected_sound_strip(context)
        if not s:
            self.report({'ERROR'}, "Selecione strip")
            return {'CANCELLED'}
        wm = context.window_manager
        st = get_track_state(wm, s)
        st["slots"][self.slot_index] = ""
        self.report({'INFO'}, f"Slot {self.slot_index+1} limpo")
        return {'FINISHED'}

# Utilities panel: logs and dependency control
class AMAX_PT_utils(bpy.types.Panel):
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"
    bl_category = "Audio Max"
    bl_label = "Audio Max - Utils"

    def draw(self, context):
        layout = self.layout
        layout.label(text="Utilities")
        row = layout.row()
        row.operator("amax.show_log", text="Show Log")
        row.operator("amax.clear_log", text="", icon='TRASH')
        layout.separator()
        prefs = context.preferences.addons.get("audio_max")
        auto = True
        if prefs:
            prefs = prefs.preferences
            auto = getattr(prefs, "auto_install_deps", True)
        layout.prop(prefs, "auto_install_deps" if prefs else None, text="Auto install deps") if prefs else layout.label(text="Preferences not loaded")
        layout.operator("amax.install_deps", text="Install Missing Deps (manual)")

class AMAX_OT_show_log(bpy.types.Operator):
    bl_idname = "amax.show_log"
    bl_label = "Show audio_max log"

    def execute(self, context):
        if not os.path.exists(LOG_FILE):
            self.report({'INFO'}, "Log file não existe")
            return {'FINISHED'}
        # Open a text editor area and load log for quick view
        try:
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                txt = f.read()
            # create a new blender text datablock to show contents
            name = "audio_max_log.txt"
            if name in bpy.data.texts:
                t = bpy.data.texts[name]
                t.clear()
                t.write(txt)
            else:
                t = bpy.data.texts.new(name)
                t.write(txt)
            # switch area to text editor (best-effort, not mandatory)
            for area in bpy.context.screen.areas:
                if area.type == 'TEXT_EDITOR':
                    area.spaces.active.text = t
                    break
            self.report({'INFO'}, f"Log carregado: {LOG_FILE}")
            return {'FINISHED'}
        except Exception as e:
            log(f"show_log error: {e}")
            self.report({'ERROR'}, f"Erro mostrando log: {e}")
            return {'CANCELLED'}

class AMAX_OT_clear_log(bpy.types.Operator):
    bl_idname = "amax.clear_log"
    bl_label = "Clear audio_max log"

    def execute(self, context):
        try:
            if os.path.exists(LOG_FILE):
                os.remove(LOG_FILE)
            self.report({'INFO'}, "Log limpo")
            return {'FINISHED'}
        except Exception as e:
            log(f"clear_log error: {e}")
            self.report({'ERROR'}, f"Erro limpando log: {e}")
            return {'CANCELLED'}

class AMAX_OT_install_deps(bpy.types.Operator):
    bl_idname = "amax.install_deps"
    bl_label = "Install Missing Dependencies"

    def execute(self, context):
        t = threading.Thread(target=instalar_dependencias, daemon=True)
        t.start()
        self.report({'INFO'}, "Instalação de dependências iniciada em background")
        return {'FINISHED'}

# ---------- Export operator ----------
class AMAX_OT_export_selected(bpy.types.Operator):
    bl_idname = "amax.export_selected"
    bl_label = "Export Selected Strip to WAV"

    def execute(self, context):
        s = get_selected_sound_strip(context)
        if not s:
            self.report({'ERROR'}, "Selecione strip")
            return {'CANCELLED'}
        path = get_sound_path(s)
        if not path or not os.path.exists(path):
            self.report({'ERROR'}, f"Arquivo não encontrado: {path}")
            return {'CANCELLED'}
        try:
            seg = load_audio_segment(path)
            outpath, tmp = export_temp_wav(seg, "audio_max_export")
            self.report({'INFO'}, f"Exportado: {outpath}")
            return {'FINISHED'}
        except Exception as e:
            log(f"export_selected error: {e}")
            self.report({'ERROR'}, f"Falha export: {e}")
            return {'CANCELLED'}

# ---------- Addon Preferences (VST command template) ----------
class AMAX_Preferences(bpy.types.AddonPreferences):
    bl_idname = "audio_max"
    vst_command_template: StringProperty(
        name="VST Processing Command Template",
        description=(
            "Command template used to process audio with an external host/plugin. "
            "Use placeholders {in}/{input}, {out}/{output}, {vst}."
        ),
        default="",
    )
    default_vst_path: StringProperty(
        name="Default VST path/ID",
        default="",
        subtype='FILE_PATH'
    )
    auto_install_deps: BoolProperty(
        name="Auto install missing Python deps (best-effort)",
        default=True,
        description="Attempt to install python dependencies into Blender's Python environment"
    )

    def draw(self, context):
        layout = self.layout
        layout.label(text="External VST processing configuration")
        layout.prop(self, "vst_command_template")
        layout.prop(self, "default_vst_path")
        layout.prop(self, "auto_install_deps")
        layout.label(text="Template must contain placeholders {in} or {input} and {out} or {output}.")

# ---------- Registration ----------
classes = (
    AMAX_OT_apply_volume,
    AMAX_OT_normalize,
    AMAX_OT_fade,
    AMAX_OT_denoise,
    AMAX_OT_detect_peaks,
    AMAX_OT_send_osc,
    AMAX_OT_internal_eq,
    AMAX_OT_apply_eq_vst,
    AMAX_OT_toggle_mute,
    AMAX_OT_toggle_solo,
    AMAX_OT_slot_edit,
    AMAX_OT_open_track_rack,
    AMAX_OT_fx_slot_clear,
    AMAX_OT_show_log,
    AMAX_OT_clear_log,
    AMAX_OT_install_deps,
    AMAX_OT_export_selected,
    AMAX_PT_track_mixer,
    AMAX_PT_dopesheet,
    AMAX_PT_fx_rack,
    AMAX_PT_utils,
    AMAX_Preferences,
)

def _start_dependency_thread_if_needed():
    try:
        prefs = bpy.context.preferences.addons.get("audio_max")
        if prefs:
            prefs = prefs.preferences
        else:
            prefs = None
    except Exception:
        prefs = None

    do_install = True
    if prefs:
        do_install = getattr(prefs, "auto_install_deps", True)

    if do_install and not dependencias_instaladas():
        t = threading.Thread(target=instalar_dependencias, daemon=True)
        t.start()
        log("Started dependency installation thread")

def register():
    log("Registering audio_max addon")
    for c in classes:
        try:
            bpy.utils.register_class(c)
        except Exception as e:
            log(f"Failed to register {c}: {e}")
    # Start dependency installer thread if needed
    try:
        _start_dependency_thread_if_needed()
    except Exception as e:
        log(f"start_dependency_thread error: {e}")
    log("Registered audio_max")

def unregister():
    log("Unregistering audio_max addon")
    for c in reversed(classes):
        try:
            bpy.utils.unregister_class(c)
        except Exception as e:
            log(f"Failed to unregister {c}: {e}")
    log("Unregistered audio_max")

# If executed as script (for development)
if __name__ == "__main__":
    register()
