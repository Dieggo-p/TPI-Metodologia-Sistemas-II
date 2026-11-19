"""Utilidades para ejecutar una version del sistema como lo haria un usuario."""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PUNTOS_DE_ENTRADA = {
    "inicial": RAIZ / "inicial" / "app.py",
    "refactorizado": RAIZ / "refactorizado" / "main.py",
}


def ejecutar_escenario(version: str, sesiones: list[list[str]]):
    """Devuelve (salida_de_todas_las_sesiones, datos_persistidos_sin_fecha)."""
    entorno = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    salidas = []
    with tempfile.TemporaryDirectory() as carpeta:
        for i, lineas in enumerate(sesiones, 1):
            resultado = subprocess.run(
                [sys.executable, str(PUNTOS_DE_ENTRADA[version])],
                input="\n".join(lineas) + "\n", capture_output=True, text=True,
                encoding="utf-8", cwd=carpeta, env=entorno, timeout=30)
            assert resultado.returncode == 0, resultado.stderr
            salidas.append(f"##### SESION {i} #####\n{resultado.stdout}")
        return "\n".join(salidas), _leer_datos(Path(carpeta) / "datos.json")


def _leer_datos(ruta: Path):
    if not ruta.exists():
        return None
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    for solicitud in datos["solicitudes"]:
        solicitud.pop("fecha")  # dato no determinista (fecha/hora de registro)
    return datos
