# core/audio_export.py
import bpy
import os
from ..utils.paths import get_temp_dir
from ..utils.logging import info, error


def get_audio_strips():
    scene = bpy.context.scene
    seq = scene.sequence_editor

    if not seq:
        error("sequence_editor é None — abra o VSE e adicione um strip antes.")
        return []

    if hasattr(seq, 'strips_all'):
        sequences = seq.strips_all
    elif hasattr(seq, 'strips'):
        sequences = seq.strips
    else:
        error("Não foi possível acessar os strips do VSE.")
        return []

    audio = [s for s in sequences if s.type == 'SOUND']
    info(f"Strips de áudio encontrados: {len(audio)}")
    return audio


def has_audio_in_vse():
    return bool(get_audio_strips())


def get_free_channel():
    """
    Retorna o primeiro canal que não está sendo usado por nenhum strip.
    Começa do canal 1 e vai subindo.
    """
    scene = bpy.context.scene
    seq = scene.sequence_editor

    if hasattr(seq, 'strips_all'):
        sequences = seq.strips_all
    elif hasattr(seq, 'strips'):
        sequences = seq.strips
    else:
        return 1

    occupied = set(s.channel for s in sequences)

    channel = 1
    while channel in occupied:
        channel += 1

    info(f"Canal livre encontrado: {channel}")
    return channel


def export_vse_audio(format='WAV'):
    """
    Exporta os strips de áudio do VSE em WAV ou MP3.
    Usa bpy.ops.sound.mixdown() — método correto para áudio no Blender.
    Após exportar, adiciona o arquivo resultante de volta ao VSE
    no primeiro canal livre.
    Retorna o caminho do arquivo exportado ou None.
    """
    strips = get_audio_strips()
    if not strips:
        error("Nenhum áudio encontrado no VSE")
        return None

    # Cria caminho temporário
    temp_dir = get_temp_dir()
    os.makedirs(temp_dir, exist_ok=True)

    format_upper = format.upper()
    filename = f"audiomax_export.{format.lower()}"
    filepath = os.path.join(temp_dir, filename)

    FORMAT_MAP = {
        'WAV':  {'container': 'WAV',  'codec': 'PCM'},
        'MP3':  {'container': 'MP3',  'codec': 'MP3'},
        'FLAC': {'container': 'FLAC', 'codec': 'FLAC'},
        'OGG':  {'container': 'OGG',  'codec': 'VORBIS'},
    }

    if format_upper not in FORMAT_MAP:
        error(f"Formato não suportado: {format}. Use WAV, MP3, FLAC ou OGG.")
        return None

    fmt = FORMAT_MAP[format_upper]

    try:
        result = bpy.ops.sound.mixdown(
            filepath=filepath,
            check_existing=False,
            relative_path=False,
            accuracy=1024,
            container=fmt['container'],
            codec=fmt['codec'],
            format='S16',
            mixrate=44100,
        )

        if 'FINISHED' not in result:
            error(f"mixdown retornou: {result}")
            return None

        if not os.path.exists(filepath):
            error(f"Arquivo não foi gerado em: {filepath}")
            return None

        info(f"Áudio exportado para {filepath}")

        # Adiciona o áudio exportado de volta ao VSE no primeiro canal livre
        _add_audio_to_vse(filepath)

        return filepath

    except Exception as e:
        error(f"Erro ao exportar áudio: {str(e)}")
        return None


def _add_audio_to_vse(filepath: str):
    """
    Adiciona o arquivo de áudio exportado ao VSE
    no primeiro canal livre, no frame 1.
    """
    try:
        scene = bpy.context.scene
        channel = get_free_channel()

        # Garante que o sequence_editor existe
        if not scene.sequence_editor:
            scene.sequence_editor_create()

        scene.sequence_editor.strips.new_sound(
            name=os.path.basename(filepath),
            filepath=filepath,
            channel=channel,
            frame_start=1,
        )

        info(f"Áudio adicionado ao VSE no canal {channel}")

    except Exception as e:
        error(f"Erro ao adicionar áudio ao VSE: {str(e)}")