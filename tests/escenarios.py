"""Escenarios de caracterizacion: secuencias de entradas por consola.

Cada escenario es una lista de SESIONES (una ejecucion del programa cada una,
sobre el mismo directorio de trabajo, para probar la persistencia).
Todos los datos son sinteticos.
"""


def reg(legajo, nombre, tipo, prioridad, desc):
    return ["1", legajo, nombre, tipo, prioridad, desc]


def est(id_, estado):
    return ["2", str(id_), estado]


def asig(id_, responsable):
    return ["3", str(id_), responsable]


def buscar(criterio, valor=None):
    return ["4", criterio] + ([valor] if valor is not None else [])


REPORTE = ["5"]
SALIR = ["0"]

ANA = reg("1001", "Ana Perez", "CONSTANCIA", "MEDIA", "Constancia de alumno regular")
LUIS = reg("1002", "Luis Gomez", "EQUIVALENCIA", "BAJA", "Equivalencia de Matematica")
BAJA = reg("1003", "Marta Diaz", "baja", "media", "Baja por motivos laborales")

ESCENARIOS = {
    "01_registrar_ok": [ANA + buscar("ninguno") + SALIR],
    "02_baja_fuerza_prioridad_alta": [BAJA + buscar("ninguno") + SALIR],
    "03_validaciones_registro": [
        reg("", "X", "OTRO", "ALTA", "d")
        + reg("12ab", "X", "OTRO", "ALTA", "d")
        + reg("2001", "", "OTRO", "ALTA", "d")
        + reg("2001", "Nuevo", "XYZ", "ALTA", "d")
        + reg("2001", "Nuevo", "OTRO", "URGENTE", "d")
        + reg("2001", "Nuevo", "OTRO", "ALTA", "")
        + reg("2001", "Nuevo", "OTRO", "ALTA", "x" * 201)
        + reg("2001", "Nuevo", "OTRO", "ALTA", "x" * 200)
        + buscar("ninguno") + SALIR],
    "04_estudiante_existente_conserva_nombre": [
        ANA + reg("1001", "Otro Nombre", "OTRO", "ALTA", "Segunda solicitud")
        + reg("1001", "", "OTRO", "ALTA", "Sin nombre pero ya existe")
        + buscar("legajo", "1001") + SALIR],
    "05_flujo_completo_estados": [
        ANA + est(1, "EN_PROCESO") + asig(1, "Bedelia") + est(1, "en_proceso")
        + est(1, "RESUELTA") + est(1, "RECHAZADA") + asig(1, "Alumnado")
        + buscar("estado", "resuelta") + SALIR],
    "06_errores_cambiar_estado": [
        ANA + ["2", "abc"] + ["2", "99"] + est(1, "XYZ") + est(1, "RESUELTA")
        + est(1, "PENDIENTE") + est(1, "RECHAZADA") + est(1, "EN_PROCESO") + SALIR],
    "07_errores_asignar": [
        ANA + ["3", "x"] + ["3", "7"] + asig(1, "Rectorado")
        + asig(1, "  SECRETARIA academica ") + est(1, "RECHAZADA")
        + asig(1, "Alumnado") + buscar("ninguno") + SALIR],
    "08_filtros": [
        ANA + LUIS + BAJA + asig(2, "Alumnado") + est(2, "EN_PROCESO")
        + buscar("estado", "PENDIENTE") + buscar("tipo", "baja")
        + buscar("prioridad", "alta") + buscar("legajo", "1002")
        + buscar("legajo", "9999") + buscar("estado", "NADA")
        + buscar("color") + buscar("ninguno") + SALIR],
    "09_reporte_vacio": [REPORTE + SALIR],
    "10_reporte_con_datos": [
        ANA + LUIS + BAJA + asig(1, "Bedelia") + est(1, "EN_PROCESO")
        + est(1, "RESUELTA") + asig(3, "Alumnado") + est(3, "RECHAZADA")
        + REPORTE + SALIR],
    "11_opcion_invalida": [["9", "", "abc"] + SALIR],
    "12_persistencia_entre_sesiones": [
        ANA + asig(1, "Alumnado") + SALIR,
        LUIS + est(1, "EN_PROCESO") + buscar("ninguno") + REPORTE + SALIR,
        buscar("ninguno") + SALIR],
    "13_busqueda_sin_resultados_y_vacio": [buscar("ninguno") + buscar("tipo", "OTRO") + SALIR],
}
