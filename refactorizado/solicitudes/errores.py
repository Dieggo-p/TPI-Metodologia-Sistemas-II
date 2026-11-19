"""Excepciones del dominio. La interfaz las muestra como 'Error: <mensaje>'."""


class ErrorDeDominio(Exception):
    """Base de los errores de regla de negocio o validacion."""


class ErrorDeValidacion(ErrorDeDominio):
    """Dato de entrada invalido o faltante."""


class SolicitudNoEncontrada(ErrorDeDominio):
    """No existe una solicitud con el ID indicado."""


class TransicionNoPermitida(ErrorDeDominio):
    """El cambio de estado no esta permitido por el flujo de trabajo."""


class OperacionNoPermitida(ErrorDeDominio):
    """La operacion viola una regla de negocio sobre el estado actual."""


class ErrorDeAlmacenamiento(Exception):
    """No se pudo leer o interpretar el archivo de datos."""
