"""Genera los resultados de referencia (golden master) con la VERSION INICIAL.

Se ejecuta una sola vez, antes de refactorizar:  python tests/generar_golden.py
"""
import json
from pathlib import Path

from ayuda_ejecucion import ejecutar_escenario
from escenarios import ESCENARIOS

CARPETA = Path(__file__).parent / "golden"
CARPETA.mkdir(exist_ok=True)
for nombre, sesiones in ESCENARIOS.items():
    salida, datos = ejecutar_escenario("inicial", sesiones)
    (CARPETA / f"{nombre}.json").write_text(
        json.dumps({"salida": salida, "datos": datos}, indent=2, ensure_ascii=False),
        encoding="utf-8")
    print("golden generado:", nombre)
