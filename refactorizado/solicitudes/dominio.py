"""Entidades, enumeraciones y reglas del dominio."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TypeVar

from .errores import (ErrorDeValidacion, OperacionNoPermitida,
                      TransicionNoPermitida)

TEnum = TypeVar("TEnum", bound=Enum)

LONGITUD_MAXIMA_DESCRIPCION = 200
RESPONSABLES = ("Alumnado", "Bedelia", "Secretaria Academica")


class Tipo(str, Enum):
    CONSTANCIA = "CONSTANCIA"
    EQUIVALENCIA = "EQUIVALENCIA"
    BAJA = "BAJA"
    OTRO = "OTRO"


class Prioridad(str, Enum):
    ALTA = "ALTA"
    MEDIA = "MEDIA"
    BAJA = "BAJA"


class Estado(str, Enum):
    PENDIENTE = "PENDIENTE"
    EN_PROCESO = "EN_PROCESO"
    RESUELTA = "RESUELTA"
    RECHAZADA = "RECHAZADA"

    def puede_pasar_a(self, nuevo: Estado) -> bool:
        return nuevo in _TRANSICIONES[self]

    @property
    def es_final(self) -> bool:
        return not _TRANSICIONES[self]


_TRANSICIONES = {
    Estado.PENDIENTE: frozenset({Estado.EN_PROCESO, Estado.RECHAZADA}),
    Estado.EN_PROCESO: frozenset({Estado.RESUELTA, Estado.RECHAZADA}),
    Estado.RESUELTA: frozenset(),
    Estado.RECHAZADA: frozenset(),
}

TIPOS_CON_PRIORIDAD_ALTA = frozenset({Tipo.BAJA})


def parsear_enum(clase_enum: type[TEnum], texto: str, mensaje_error: str) -> TEnum:
    """Convierte texto (sin distinguir mayusculas) a un miembro de la enum."""
    try:
        return clase_enum(texto.strip().upper())
    except ValueError:
        raise ErrorDeValidacion(mensaje_error) from None


@dataclass(frozen=True)
class NuevaSolicitud:
    """Parameter Object: datos crudos ingresados para registrar una solicitud."""
    legajo: str
    nombre: str
    tipo: str
    prioridad: str
    descripcion: str


@dataclass
class Estudiante:
    legajo: str
    nombre: str


@dataclass
class Solicitud:
    id: int
    legajo: str
    tipo: Tipo
    prioridad: Prioridad
    estado: Estado
    descripcion: str
    responsable: str | None
    fecha: str

    def esta_cerrada(self) -> bool:
        return self.estado.es_final

    def cambiar_estado(self, nuevo: Estado) -> None:
        if not self.estado.puede_pasar_a(nuevo):
            raise TransicionNoPermitida(
                f"transicion no permitida de {self.estado.value} a {nuevo.value}")
        if nuevo is Estado.EN_PROCESO and self.responsable is None:
            raise OperacionNoPermitida(
                "debe asignar un responsable antes de pasar a EN_PROCESO")
        self.estado = nuevo

    def verificar_asignable(self) -> None:
        if self.esta_cerrada():
            raise OperacionNoPermitida("la solicitud ya esta cerrada")

    def asignar_responsable(self, responsable: str) -> None:
        self.verificar_asignable()
        self.responsable = responsable
