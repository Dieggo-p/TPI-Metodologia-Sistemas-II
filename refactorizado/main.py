"""Punto de entrada: arma las dependencias y lanza la interfaz."""
import sys

from solicitudes.cli import Interfaz
from solicitudes.errores import ErrorDeAlmacenamiento
from solicitudes.repositorio import RepositorioJson
from solicitudes.servicio import ServicioSolicitudes


def main() -> int:
    try:
        servicio = ServicioSolicitudes(RepositorioJson("datos.json"))
    except ErrorDeAlmacenamiento as error:
        print(f"Error: {error}")
        return 1
    Interfaz(servicio).ejecutar()
    return 0


if __name__ == "__main__":
    sys.exit(main())
