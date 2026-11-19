"""Filtros de busqueda. Agregar un criterio nuevo = agregar una entrada (OCP)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable

from .dominio import Solicitud
from .errores import ErrorDeValidacion


@dataclass(frozen=True)
class Filtro:
    normalizar: Callable[[str], str]
    coincide: Callable[[Solicitud, str], bool]

    def aplicar(self, solicitudes: Iterable[Solicitud], valor: str) -> list[Solicitud]:
        valor_normalizado = self.normalizar(valor.strip())
        return [s for s in solicitudes if self.coincide(s, valor_normalizado)]


FILTROS: dict[str, Filtro] = {
    "estado": Filtro(str.upper, lambda s, v: s.estado.value == v),
    "tipo": Filtro(str.upper, lambda s, v: s.tipo.value == v),
    "prioridad": Filtro(str.upper, lambda s, v: s.prioridad.value == v),
    "legajo": Filtro(lambda v: v, lambda s, v: s.legajo == v),
}


def obtener_filtro(criterio: str) -> Filtro:
    try:
        return FILTROS[criterio]
    except KeyError:
        raise ErrorDeValidacion("criterio de filtro invalido") from None
