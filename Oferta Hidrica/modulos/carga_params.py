"""Carga del archivo de parámetros (initial_values.py) sin caché de módulos."""

import sys
import importlib.util as _imp_util
from pathlib import Path as _Path


def cargar_initial_values(script_dir):
    """
    Carga src/initial_values.py forzando recarga completa (sin caché).

    Args:
        script_dir: directorio raíz del proyecto (Path o str)

    Returns:
        Módulo initial_values recién importado
    """
    for key in [k for k in sys.modules if 'initial_values' in k]:
        del sys.modules[key]

    path = _Path(script_dir) / 'src' / 'initial_values.py'
    spec = _imp_util.spec_from_file_location('initial_values', path)
    iv = _imp_util.module_from_spec(spec)
    spec.loader.exec_module(iv)
    return iv
