"""Casos de uso. Depende de abstracciones (repositorio y reloj), no de detalles."""
from __future__ import annotations

from datetime import datetime
from typing import Callable

from .dominio import (LONGITUD_MAXIMA_DESCRIPCION, RESPONSABLES,
                      TIPOS_CON_PRIORIDAD_ALTA, Estado, Estudiante,
                      NuevaSolicitud, Prioridad, Solicitud, Tipo, parsear_enum)
from .errores import ErrorDeValidacion, SolicitudNoEncontrada
from .repositorio import RepositorioSolicitudes


class ServicioSolicitudes:
    def __init__(self, repositorio: RepositorioSolicitudes,
                 reloj: Callable[[], datetime] = datetime.now) -> None:
        self._repositorio = repositorio
        self._reloj = reloj
        self._datos = repositorio.cargar()

    # --- consultas ---------------------------------------------------------
    def listar(self) -> list[Solicitud]:
        return list(self._datos.solicitudes)

    def obtener(self, id_solicitud: int) -> Solicitud:
        for solicitud in self._datos.solicitudes:
            if solicitud.id == id_solicitud:
                return solicitud
        raise SolicitudNoEncontrada("solicitud no encontrada")

    def nombre_de(self, legajo: str) -> str:
        estudiante = self._buscar_estudiante(legajo)
        return estudiante.nombre if estudiante else ""

    # --- comandos ----------------------------------------------------------
    def registrar(self, nueva: NuevaSolicitud) -> Solicitud:
        legajo = self._validar_legajo(nueva.legajo)
        nombre = self._validar_nombre(legajo, nueva.nombre)
        tipo = parsear_enum(Tipo, nueva.tipo, "tipo invalido")
        prioridad = parsear_enum(Prioridad, nueva.prioridad, "prioridad invalida")
        descripcion = self._validar_descripcion(nueva.descripcion)

        if self._buscar_estudiante(legajo) is None:
            self._datos.estudiantes.append(Estudiante(legajo, nombre))
        if tipo in TIPOS_CON_PRIORIDAD_ALTA:
            prioridad = Prioridad.ALTA
        self._datos.contador += 1
        solicitud = Solicitud(
            id=self._datos.contador, legajo=legajo, tipo=tipo, prioridad=prioridad,
            estado=Estado.PENDIENTE, descripcion=descripcion, responsable=None,
            fecha=self._reloj().strftime("%Y-%m-%d %H:%M"))
        self._datos.solicitudes.append(solicitud)
        self._repositorio.guardar(self._datos)
        return solicitud

    def cambiar_estado(self, id_solicitud: int, estado_texto: str) -> Solicitud:
        solicitud = self.obtener(id_solicitud)
        nuevo = parsear_enum(Estado, estado_texto, "estado invalido")
        solicitud.cambiar_estado(nuevo)
        self._repositorio.guardar(self._datos)
        return solicitud

    def validar_asignable(self, id_solicitud: int) -> Solicitud:
        solicitud = self.obtener(id_solicitud)
        solicitud.verificar_asignable()
        return solicitud

    def asignar_responsable(self, id_solicitud: int, nombre: str) -> Solicitud:
        solicitud = self.validar_asignable(id_solicitud)
        solicitud.asignar_responsable(self._resolver_responsable(nombre))
        self._repositorio.guardar(self._datos)
        return solicitud

    # --- validaciones privadas ---------------------------------------------
    def _buscar_estudiante(self, legajo: str) -> Estudiante | None:
        for estudiante in self._datos.estudiantes:
            if estudiante.legajo == legajo:
                return estudiante
        return None

    @staticmethod
    def _validar_legajo(texto: str) -> str:
        legajo = texto.strip()
        if not legajo:
            raise ErrorDeValidacion("legajo obligatorio")
        if not legajo.isdigit():
            raise ErrorDeValidacion("el legajo debe ser numerico")
        return legajo

    def _validar_nombre(self, legajo: str, texto: str) -> str:
        nombre = texto.strip()
        if self._buscar_estudiante(legajo) is None and not nombre:
            raise ErrorDeValidacion("nombre obligatorio para estudiante nuevo")
        return nombre

    @staticmethod
    def _validar_descripcion(texto: str) -> str:
        descripcion = texto.strip()
        if not descripcion:
            raise ErrorDeValidacion("descripcion obligatoria")
        if len(descripcion) > LONGITUD_MAXIMA_DESCRIPCION:
            raise ErrorDeValidacion(
                f"descripcion demasiado larga (max {LONGITUD_MAXIMA_DESCRIPCION})")
        return descripcion

    @staticmethod
    def _resolver_responsable(nombre: str) -> str:
        for responsable in RESPONSABLES:
            if responsable.lower() == nombre.strip().lower():
                return responsable
        raise ErrorDeValidacion("responsable inexistente")
