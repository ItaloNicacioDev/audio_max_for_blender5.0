import shlex
import sys


# -------------------------------------------------
# SAFE PATH FORMAT
# -------------------------------------------------

def quote_path(path: str) -> str:
    """
    Garante que o caminho funcione em qualquer sistema.
    """

    if sys.platform == "win32":
        return f'"{path}"'

    return shlex.quote(path)


# -------------------------------------------------
# BUILD COMMAND FROM TEMPLATE
# -------------------------------------------------

def build_command(template: str,
                  host_path: str,
                  input_path: str,
                  output_path: str,
                  plugin_path: str = "",
                  preset_path: str = "") -> str:
    """
    Substitui placeholders no template.

    Placeholders suportados:
    {host}
    {input}
    {output}
    {plugin}
    {preset}
    """

    if not template:
        raise ValueError("Template de comando vazio.")

    replacements = {
        "{host}": quote_path(host_path),
        "{input}": quote_path(input_path),
        "{output}": quote_path(output_path),
        "{plugin}": quote_path(plugin_path) if plugin_path else "",
        "{preset}": quote_path(preset_path) if preset_path else "",
    }

    command = template

    for key, value in replacements.items():
        command = command.replace(key, value)

    return command


# -------------------------------------------------
# DEFAULT TEMPLATES
# -------------------------------------------------

def get_default_template(host_path: str) -> str:
    """
    Retorna template básico baseado no nome do host.
    """

    name = host_path.lower()

    if "carla" in name:
        return '{host} --nogui --load "{plugin}" --input {input} --output {output}'

    if "reaper" in name:
        return '{host} -batchconvert {input} {output}'

    return '{host} {input} {output}'