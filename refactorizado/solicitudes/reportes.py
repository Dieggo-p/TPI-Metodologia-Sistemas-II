"""Generacion y formato de reportes (sin entrada/salida ni persistencia)."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Callable, Iterable

from .dominio import Estado, Prioridad, Solicitud, Tipo


@dataclass(frozen=True)
class Reporte:
    total: int
    por_estado: dict[Estado, int]
    por_tipo: dict[Tipo, int]
    por_prioridad: dict[Prioridad, int]
    sin_responsable: int


def generar_reporte(solicitudes: list[Solicitud]) -> Reporte:
    return Reporte(
        total=len(solicitudes),
        por_estado=_contar(solicitudes, Estado, lambda s: s.estado),
        por_tipo=_contar(solicitudes, Tipo, lambda s: s.tipo),
        por_prioridad=_contar(solicitudes, Prioridad, lambda s: s.prioridad),
        sin_responsable=sum(1 for s in solicitudes if s.responsable is None),
    )


def _contar(solicitudes: Iterable[Solicitud], clase_enum, clave: Callable) -> dict:
    cantidades = Counter(clave(s) for s in solicitudes)
    return {miembro: cantidades[miembro] for miembro in clase_enum}


def formatear_reporte(reporte: Reporte) -> list[str]:
    lineas = ["--- REPORTE ---", f"Total de solicitudes: {reporte.total}"]
    for titulo, cantidades in (("Por estado:", reporte.por_estado),
                               ("Por tipo:", reporte.por_tipo),
                               ("Por prioridad:", reporte.por_prioridad)):
        lineas.append(titulo)
        lineas.extend(f"  {miembro.value}: {cant}" for miembro, cant in cantidades.items())
    lineas.append(f"Sin responsable asignado: {reporte.sin_responsable}")
    return lineas


def formatear_solicitud(solicitud: Solicitud, nombre_estudiante: str) -> str:
    responsable = solicitud.responsable or "-"
    return (f"#{solicitud.id} | {solicitud.legajo} {nombre_estudiante} | "
            f"{solicitud.tipo.value} | {solicitud.prioridad.value} | "
            f"{solicitud.estado.value} | {responsable}")
