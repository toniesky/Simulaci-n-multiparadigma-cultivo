"""Exportación de resultados a CSV y lanzamiento de la animación interactiva."""

import os
import time


def guardar_csv(df, filepath):
    """
    Guarda el DataFrame en CSV con reintentos si el archivo está bloqueado.

    Args:
        df: DataFrame a guardar
        filepath: ruta absoluta del archivo CSV de destino
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    for intento in range(3):
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
            break
        except (PermissionError, OSError):
            if intento < 2:
                time.sleep(0.5)

    df.to_csv(filepath, index=False, mode='w')
    print(f"[OK] Resultados guardados en: {filepath}")


def lanzar_animacion(script_dir):
    """
    Lanza el servidor Flask de la animación interactiva en un subprocess.

    Args:
        script_dir: directorio raíz del proyecto (Path o str)
    """
    import subprocess
    import sys
    from pathlib import Path

    backend_path = Path(script_dir) / 'Animacion' / 'backend' / 'app.py'
    if not backend_path.exists():
        print(f"[ERR] No se encontró {backend_path}")
        print("[OK] Puedes iniciar manualmente:")
        print("  cd Animacion/backend")
        print("  python app.py")
        return

    print(f"[OK] Iniciando servidor en {backend_path}")
    subprocess.Popen([sys.executable, str(backend_path)])
