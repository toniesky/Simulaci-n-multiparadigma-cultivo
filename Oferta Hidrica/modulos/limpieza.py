"""Limpieza del entorno antes de ejecutar el modelo: puerto 5000 y caché de Python."""

import subprocess
import platform
import shutil
import time


def limpiar_puerto(puerto=5000):
    """Termina cualquier proceso escuchando en el puerto dado."""
    print(f"[INICIO] Limpiando puerto {puerto} y procesos anteriores...")
    try:
        if platform.system() == 'Windows':
            result = subprocess.run(
                ['netstat', '-ano'], capture_output=True, text=True, timeout=5
            )
            for linea in result.stdout.split('\n'):
                if f':{puerto}' in linea and 'LISTENING' in linea:
                    pid = linea.split()[-1]
                    try:
                        subprocess.run(['taskkill', '/PID', pid, '/F'], timeout=2)
                        print(f"[OK] Proceso anterior (PID {pid}) terminado")
                    except Exception:
                        pass
        else:
            subprocess.run(
                f'lsof -ti:{puerto} | xargs kill -9', shell=True, timeout=2
            )
        time.sleep(1)
        print(f"[OK] Puerto {puerto} limpiado\n")
    except Exception as e:
        print(f"[!] No se pudo limpiar puerto {puerto}: {e}\n")


def limpiar_cache(script_dir):
    """Elimina el directorio __pycache__ dentro de src/ si existe."""
    pycache_path = script_dir / 'src' / '__pycache__'
    if pycache_path.exists():
        try:
            shutil.rmtree(pycache_path)
            print("[OK] Caché de Python limpiado")
        except (PermissionError, OSError):
            pass
