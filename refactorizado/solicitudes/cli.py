"""Capa de presentacion: menu por consola. No contiene reglas de negocio."""
from __future__ import annotations

from typing import Callable

from .dominio import NuevaSolicitud
from .errores import ErrorDeDominio, ErrorDeValidacion
from .filtros import obtener_filtro
from .reportes import formatear_reporte, formatear_solicitud, generar_reporte
from .servicio import ServicioSolicitudes


class Interfaz:
    def __init__(self, servicio: ServicioSolicitudes,
                 entrada: Callable[[str], str] = input,
                 salida: Callable[[str], None] = print) -> None:
        self._servicio = servicio
        self._entrada = entrada
        self._salida = salida
        self._acciones: dict[str, Callable[[], None]] = {
            "1": self._registrar,
            "2": self._cambiar_estado,
            "3": self._asignar_responsable,
            "4": self._buscar,
            "5": self._reporte,
        }

    def ejecutar(self) -> None:
        while True:
            self._mostrar_menu()
            opcion = self._entrada("Opcion: ").strip()
            if opcion == "0":
                self._salida("Hasta luego")
                return
            self._ejecutar_opcion(opcion)

    def _ejecutar_opcion(self, opcion: str) -> None:
        accion = self._acciones.get(opcion)
        if accion is None:
            self._salida("Opcion invalida")
            return
        try:
            accion()
        except ErrorDeDominio as error:
            self._salida(f"Error: {error}")

    def _mostrar_menu(self) -> None:
        for linea in ("", "=== Gestion de Solicitudes Academicas ===",
                      "1. Registrar solicitud", "2. Cambiar estado",
                      "3. Asignar responsable", "4. Buscar / filtrar",
                      "5. Reporte", "0. Salir"):
            self._salida(linea)

    def _leer_id(self) -> int:
        texto = self._entrada("ID de solicitud: ").strip()
        if not texto.isdigit():
            raise ErrorDeValidacion("ID invalido")
        return int(texto)

    def _registrar(self) -> None:
        nueva = NuevaSolicitud(
            legajo=self._entrada("Legajo: "),
            nombre=self._entrada("Nombre del estudiante: "),
            tipo=self._entrada("Tipo (CONSTANCIA/EQUIVALENCIA/BAJA/OTRO): "),
            prioridad=self._entrada("Prioridad (ALTA/MEDIA/BAJA): "),
            descripcion=self._entrada("Descripcion: "))
        solicitud = self._servicio.registrar(nueva)
        self._salida(f"Solicitud #{solicitud.id} registrada "
                     f"(estado {solicitud.estado.value}, "
                     f"prioridad {solicitud.prioridad.value})")

    def _cambiar_estado(self) -> None:
        id_solicitud = self._leer_id()
        self._servicio.obtener(id_solicitud)
        estado = self._entrada("Nuevo estado (EN_PROCESO/RESUELTA/RECHAZADA): ")
        solicitud = self._servicio.cambiar_estado(id_solicitud, estado)
        self._salida(f"Solicitud #{solicitud.id} ahora esta {solicitud.estado.value}")

    def _asignar_responsable(self) -> None:
        id_solicitud = self._leer_id()
        self._servicio.validar_asignable(id_solicitud)
        nombre = self._entrada("Responsable: ")
        solicitud = self._servicio.asignar_responsable(id_solicitud, nombre)
        self._salida(f"Solicitud #{solicitud.id} asignada a {solicitud.responsable}")

    def _buscar(self) -> None:
        criterio = self._entrada(
            "Filtrar por (estado/tipo/prioridad/legajo/ninguno): ").strip().lower()
        resultado = self._servicio.listar()
        if criterio != "ninguno":
            filtro = obtener_filtro(criterio)
            resultado = filtro.aplicar(resultado, self._entrada("Valor: "))
        if not resultado:
            self._salida("Sin resultados")
        for solicitud in resultado:
            nombre = self._servicio.nombre_de(solicitud.legajo)
            self._salida(formatear_solicitud(solicitud, nombre))

    def _reporte(self) -> None:
        for linea in formatear_reporte(generar_reporte(self._servicio.listar())):
            self._salida(linea)
