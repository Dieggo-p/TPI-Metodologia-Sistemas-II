"""Pruebas unitarias de la version refactorizada (posibles gracias a DIP)."""
import json
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "refactorizado"))

from solicitudes.dominio import (Estado, NuevaSolicitud, Prioridad, Solicitud,
                                 Tipo)
from solicitudes.errores import (ErrorDeAlmacenamiento, ErrorDeValidacion,
                                 OperacionNoPermitida, SolicitudNoEncontrada,
                                 TransicionNoPermitida)
from solicitudes.filtros import obtener_filtro
from solicitudes.reportes import formatear_reporte, generar_reporte
from solicitudes.repositorio import RepositorioEnMemoria, RepositorioJson
from solicitudes.servicio import ServicioSolicitudes

RELOJ_FIJO = lambda: datetime(2026, 1, 15, 10, 30)  # noqa: E731


def nueva(**cambios):
    datos = dict(legajo="1001", nombre="Ana Perez", tipo="OTRO",
                 prioridad="MEDIA", descripcion="Consulta")
    datos.update(cambios)
    return NuevaSolicitud(**datos)


class PruebasDominio(unittest.TestCase):
    def test_transiciones_validas_e_invalidas(self):
        self.assertTrue(Estado.PENDIENTE.puede_pasar_a(Estado.EN_PROCESO))
        self.assertTrue(Estado.EN_PROCESO.puede_pasar_a(Estado.RESUELTA))
        self.assertFalse(Estado.PENDIENTE.puede_pasar_a(Estado.RESUELTA))
        self.assertFalse(Estado.RESUELTA.puede_pasar_a(Estado.RECHAZADA))

    def test_estados_finales(self):
        self.assertTrue(Estado.RESUELTA.es_final)
        self.assertTrue(Estado.RECHAZADA.es_final)
        self.assertFalse(Estado.EN_PROCESO.es_final)

    def _solicitud(self, estado=Estado.PENDIENTE, responsable=None):
        return Solicitud(1, "1001", Tipo.OTRO, Prioridad.MEDIA, estado, "d",
                         responsable, "2026-01-15 10:30")

    def test_no_pasa_a_en_proceso_sin_responsable(self):
        with self.assertRaises(OperacionNoPermitida):
            self._solicitud().cambiar_estado(Estado.EN_PROCESO)

    def test_transicion_invalida_lanza_error(self):
        with self.assertRaises(TransicionNoPermitida):
            self._solicitud().cambiar_estado(Estado.RESUELTA)

    def test_no_se_asigna_responsable_a_solicitud_cerrada(self):
        with self.assertRaises(OperacionNoPermitida):
            self._solicitud(Estado.RESUELTA).asignar_responsable("Bedelia")


class PruebasServicio(unittest.TestCase):
    def setUp(self):
        self.repo = RepositorioEnMemoria()
        self.servicio = ServicioSolicitudes(self.repo, reloj=RELOJ_FIJO)

    def test_registrar_usa_reloj_inyectado_y_persiste(self):
        s = self.servicio.registrar(nueva())
        self.assertEqual(s.fecha, "2026-01-15 10:30")
        self.assertEqual(s.estado, Estado.PENDIENTE)
        self.assertEqual(self.repo.cargar().contador, 1)

    def test_baja_fuerza_prioridad_alta(self):
        s = self.servicio.registrar(nueva(tipo="baja", prioridad="BAJA"))
        self.assertEqual(s.prioridad, Prioridad.ALTA)

    def test_validaciones_de_registro(self):
        casos = {"legajo obligatorio": nueva(legajo=" "),
                 "el legajo debe ser numerico": nueva(legajo="12a"),
                 "nombre obligatorio para estudiante nuevo": nueva(nombre=""),
                 "tipo invalido": nueva(tipo="X"),
                 "prioridad invalida": nueva(prioridad="X"),
                 "descripcion obligatoria": nueva(descripcion=""),
                 "descripcion demasiado larga (max 200)": nueva(descripcion="x" * 201)}
        for mensaje, entrada in casos.items():
            with self.subTest(mensaje):
                with self.assertRaisesRegex(ErrorDeValidacion, mensaje.replace("(", r"\(").replace(")", r"\)")):
                    self.servicio.registrar(entrada)

    def test_registro_invalido_no_crea_estudiante_ni_consume_id(self):
        with self.assertRaises(ErrorDeValidacion):
            self.servicio.registrar(nueva(tipo="X"))
        datos = self.repo.cargar()
        self.assertEqual((datos.contador, datos.estudiantes), (0, []))

    def test_flujo_asignar_y_cambiar_estado(self):
        s = self.servicio.registrar(nueva())
        self.servicio.asignar_responsable(s.id, "alumnado")
        self.servicio.cambiar_estado(s.id, "en_proceso")
        self.assertEqual(self.servicio.obtener(s.id).responsable, "Alumnado")
        self.assertEqual(self.servicio.obtener(s.id).estado, Estado.EN_PROCESO)

    def test_solicitud_inexistente(self):
        with self.assertRaises(SolicitudNoEncontrada):
            self.servicio.obtener(99)

    def test_responsable_inexistente(self):
        s = self.servicio.registrar(nueva())
        with self.assertRaises(ErrorDeValidacion):
            self.servicio.asignar_responsable(s.id, "Rectorado")


class PruebasFiltrosYReportes(unittest.TestCase):
    def setUp(self):
        self.servicio = ServicioSolicitudes(RepositorioEnMemoria(), reloj=RELOJ_FIJO)
        self.servicio.registrar(nueva(legajo="1", tipo="BAJA"))
        self.servicio.registrar(nueva(legajo="2", tipo="OTRO", prioridad="BAJA"))

    def test_filtro_por_tipo_y_legajo(self):
        todas = self.servicio.listar()
        self.assertEqual(len(obtener_filtro("tipo").aplicar(todas, "baja")), 1)
        self.assertEqual(len(obtener_filtro("legajo").aplicar(todas, "2")), 1)

    def test_criterio_invalido(self):
        with self.assertRaises(ErrorDeValidacion):
            obtener_filtro("color")

    def test_reporte_cuenta_incluyendo_ceros(self):
        reporte = generar_reporte(self.servicio.listar())
        self.assertEqual(reporte.total, 2)
        self.assertEqual(reporte.por_estado[Estado.RESUELTA], 0)
        self.assertEqual(reporte.por_prioridad[Prioridad.ALTA], 1)
        self.assertEqual(reporte.sin_responsable, 2)
        self.assertEqual(formatear_reporte(reporte)[0], "--- REPORTE ---")


class ContratoRepositorio:
    """Pruebas de contrato: cualquier implementacion debe cumplirlas (LSP)."""

    def crear_repositorio(self):
        raise NotImplementedError

    def test_repositorio_nuevo_devuelve_datos_vacios(self):
        datos = self.crear_repositorio().cargar()
        self.assertEqual((datos.contador, datos.estudiantes, datos.solicitudes), (0, [], []))

    def test_lo_guardado_se_puede_recuperar(self):
        repo = self.crear_repositorio()
        servicio = ServicioSolicitudes(repo, reloj=RELOJ_FIJO)
        servicio.registrar(nueva())
        recuperado = ServicioSolicitudes(repo, reloj=RELOJ_FIJO).listar()
        self.assertEqual(len(recuperado), 1)
        self.assertEqual(recuperado[0].tipo, Tipo.OTRO)


class PruebasContratoEnMemoria(ContratoRepositorio, unittest.TestCase):
    def crear_repositorio(self):
        return RepositorioEnMemoria()


class PruebasContratoJson(ContratoRepositorio, unittest.TestCase):
    def setUp(self):
        self._carpeta = tempfile.TemporaryDirectory()
        self.addCleanup(self._carpeta.cleanup)
        self.ruta = Path(self._carpeta.name) / "datos.json"

    def crear_repositorio(self):
        return RepositorioJson(self.ruta)

    def test_archivo_danado_se_informa_y_no_se_pisa(self):
        # Mejora deliberada respecto de la version inicial (que lo ignoraba en silencio).
        self.ruta.write_text("{esto no es json", encoding="utf-8")
        with self.assertRaises(ErrorDeAlmacenamiento):
            self.crear_repositorio().cargar()
        self.assertEqual(self.ruta.read_text(encoding="utf-8"), "{esto no es json")

    def test_formato_del_archivo_compatible_con_version_inicial(self):
        ServicioSolicitudes(self.crear_repositorio(), reloj=RELOJ_FIJO).registrar(nueva())
        datos = json.loads(self.ruta.read_text(encoding="utf-8"))
        self.assertEqual(set(datos), {"contador", "estudiantes", "solicitudes"})
        self.assertEqual(set(datos["solicitudes"][0]),
                         {"id", "legajo", "tipo", "prioridad", "estado",
                          "descripcion", "responsable", "fecha"})


if __name__ == "__main__":
    unittest.main()
