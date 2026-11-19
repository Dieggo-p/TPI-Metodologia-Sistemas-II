"""Pruebas de caracterizacion (antes/despues).

Cada escenario se ejecuta contra la version INICIAL y la REFACTORIZADA y se
compara con el resultado de referencia: salida de consola + datos persistidos.
Si ambas coinciden, el refactoring no altero el comportamiento externo.
"""
import json
import unittest
from pathlib import Path

from ayuda_ejecucion import ejecutar_escenario
from escenarios import ESCENARIOS

GOLDEN = Path(__file__).parent / "golden"


def _crear_prueba(version, nombre, sesiones):
    def prueba(self):
        esperado = json.loads((GOLDEN / f"{nombre}.json").read_text(encoding="utf-8"))
        salida, datos = ejecutar_escenario(version, sesiones)
        self.assertEqual(salida, esperado["salida"], "difiere la salida de consola")
        self.assertEqual(datos, esperado["datos"], "difieren los datos persistidos")
    return prueba


class CaracterizacionInicial(unittest.TestCase):
    """Linea base: la version inicial reproduce su propio golden master."""


class CaracterizacionRefactorizada(unittest.TestCase):
    """La version refactorizada debe comportarse igual que la inicial."""


for _nombre, _sesiones in ESCENARIOS.items():
    setattr(CaracterizacionInicial, f"test_{_nombre}",
            _crear_prueba("inicial", _nombre, _sesiones))
    setattr(CaracterizacionRefactorizada, f"test_{_nombre}",
            _crear_prueba("refactorizado", _nombre, _sesiones))

if __name__ == "__main__":
    unittest.main()
