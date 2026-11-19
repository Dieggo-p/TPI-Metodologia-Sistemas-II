"""Persistencia: contrato abstracto e implementacion en archivo JSON."""
from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path

from .dominio import Estado, Estudiante, Prioridad, Solicitud, Tipo
from .errores import ErrorDeAlmacenamiento


@dataclass
class Datos:
    contador: int = 0
    estudiantes: list[Estudiante] = field(default_factory=list)
    solicitudes: list[Solicitud] = field(default_factory=list)


class RepositorioSolicitudes(ABC):
    """Contrato minimo (ISP): solo cargar y guardar el conjunto de datos."""

    @abstractmethod
    def cargar(self) -> Datos: ...

    @abstractmethod
    def guardar(self, datos: Datos) -> None: ...


class RepositorioEnMemoria(RepositorioSolicitudes):
    """Implementacion sin disco, util para pruebas."""

    def __init__(self) -> None:
        self._datos = Datos()

    def cargar(self) -> Datos:
        return self._datos

    def guardar(self, datos: Datos) -> None:
        self._datos = datos


class RepositorioJson(RepositorioSolicitudes):
    def __init__(self, ruta: str | Path = "datos.json") -> None:
        self._ruta = Path(ruta)

    def cargar(self) -> Datos:
        if not self._ruta.exists():
            return Datos()
        try:
            with self._ruta.open("r", encoding="utf-8") as archivo:
                crudo = json.load(archivo)
            return _a_datos(crudo)
        except (json.JSONDecodeError, KeyError, ValueError, TypeError) as error:
            raise ErrorDeAlmacenamiento(
                f"el archivo de datos '{self._ruta}' esta danado: {error}") from error

    def guardar(self, datos: Datos) -> None:
        with self._ruta.open("w", encoding="utf-8") as archivo:
            json.dump(_a_dict(datos), archivo, indent=2, ensure_ascii=False)


def _a_datos(crudo: dict) -> Datos:
    return Datos(
        contador=crudo["contador"],
        estudiantes=[Estudiante(e["legajo"], e["nombre"]) for e in crudo["estudiantes"]],
        solicitudes=[
            Solicitud(id=s["id"], legajo=s["legajo"], tipo=Tipo(s["tipo"]),
                      prioridad=Prioridad(s["prioridad"]), estado=Estado(s["estado"]),
                      descripcion=s["descripcion"], responsable=s["responsable"],
                      fecha=s["fecha"])
            for s in crudo["solicitudes"]
        ],
    )


def _a_dict(datos: Datos) -> dict:
    return {
        "contador": datos.contador,
        "estudiantes": [{"legajo": e.legajo, "nombre": e.nombre}
                        for e in datos.estudiantes],
        "solicitudes": [
            {"id": s.id, "legajo": s.legajo, "tipo": s.tipo.value,
             "prioridad": s.prioridad.value, "estado": s.estado.value,
             "descripcion": s.descripcion, "responsable": s.responsable,
             "fecha": s.fecha}
            for s in datos.solicitudes
        ],
    }
