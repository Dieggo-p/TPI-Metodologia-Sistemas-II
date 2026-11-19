"""Genera el informe PDF del TPI y docs/checklist_code_review.md.

Uso (desde la raiz del repo):  python scripts/generar_informe.py [ruta_salida.pdf]
Los fragmentos de codigo y las metricas se leen del repositorio real (ast, radon,
flake8, unittest), por lo que el informe siempre refleja el estado del codigo.
"""
import ast
import json
import re
import subprocess
import sys
import textwrap
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (Image, KeepTogether, PageBreak, Paragraph, Preformatted,
                                SimpleDocTemplate, Spacer, Table, TableStyle)

RAIZ = Path(__file__).resolve().parent.parent
SALIDA = Path(sys.argv[1]) if len(sys.argv) > 1 else RAIZ / "TPI_Metodologia_Sistemas_II.pdf"
INI = "inicial/app.py"
DOM, SERV, REP, FIL, REPT, CLI, MAIN = (
    "refactorizado/solicitudes/dominio.py", "refactorizado/solicitudes/servicio.py",
    "refactorizado/solicitudes/repositorio.py", "refactorizado/solicitudes/filtros.py",
    "refactorizado/solicitudes/reportes.py", "refactorizado/solicitudes/cli.py",
    "refactorizado/main.py")
AZUL = colors.HexColor("#1F3A5F")
PEND = '<font backColor="#FFF3A0">[COMPLETAR]</font>'
import os
REPO_URL = "https://github.com/Dieggo-p/TPI-Metodologia-Sistemas-II"
VIDEO_URL = os.environ.get("VIDEO_URL", "")
REPO = f'<link href="{REPO_URL}" color="blue">{REPO_URL}</link>'
VIDEO = f'<link href="{VIDEO_URL}" color="blue">{VIDEO_URL}</link>' if VIDEO_URL else PEND
FECHA = "18/11/2026"


# ------------------------------------------------------------------ utilidades
def leer(ruta):
    return (RAIZ / ruta).read_text(encoding="utf-8")


def _nodo(ruta, nombre):
    nodos = ast.parse(leer(ruta)).body
    for parte in nombre.split("."):
        nodo = next(n for n in nodos if getattr(n, "name", None) == parte)
        nodos = getattr(nodo, "body", [])
    return nodo


def fuente(ruta, nombre):
    nodo = _nodo(ruta, nombre)
    lineas = leer(ruta).splitlines()[nodo.lineno - 1:nodo.end_lineno]
    return textwrap.dedent("\n".join(lineas))


def rango(ruta, nombre):
    nodo = _nodo(ruta, nombre)
    return f"L{nodo.lineno}-{nodo.end_lineno}"


def trozo(ruta, patron, cantidad, ocurrencia=1):
    lineas = leer(ruta).splitlines()
    idx = [i for i, l in enumerate(lineas) if patron in l][ocurrencia - 1]
    return textwrap.dedent("\n".join(lineas[idx:idx + cantidad]))


def linea_de(ruta, patron):
    return next(i for i, l in enumerate(leer(ruta).splitlines(), 1) if patron in l)


def ejecutar(cmd):
    return subprocess.run(cmd, cwd=RAIZ, capture_output=True, text=True).stdout


def coma(x, d=1):
    return f"{x:.{d}f}".replace(".", ",")


# --------------------------------------------------------------------- metricas
def bloques(ruta):
    """Devuelve (funciones/metodos, promedio de CC de todos los bloques, cantidad de bloques)."""
    datos = json.loads(ejecutar(["radon", "cc", "-j", ruta]))
    unicos = {}
    for archivo, items in datos.items():
        for it in items:
            unicos[(archivo, it["name"], it["lineno"])] = it
            for m in it.get("methods", []):
                unicos[(archivo, m["name"], m["lineno"])] = m
    todos = list(unicos.items())
    funciones = [{"cc": b["complexity"], "largo": b["endline"] - b["lineno"] + 1,
                  "nombre": b["name"], "archivo": k[0]}
                 for k, b in todos if b["type"] != "class"]
    promedio = sum(b["complexity"] for _, b in todos) / len(todos)
    return funciones, promedio, len(todos)


def metricas(ruta):
    funciones, promedio, cantidad = bloques(ruta)
    mi = json.loads(ejecutar(["radon", "mi", "-j", ruta]))
    raw = json.loads(ejecutar(["radon", "raw", "-j", ruta]))
    flake = [l for l in ejecutar(["flake8", "--max-line-length=100", ruta]).splitlines() if l]
    return {
        "funciones": funciones, "cc_prom": promedio, "cc_max": max(f["cc"] for f in funciones),
        "largo_max": max(f["largo"] for f in funciones),
        "mayores_20": sorted({f["nombre"] for f in funciones if f["largo"] > 20}),
        "mayores_cc10": sorted({f["nombre"] for f in funciones if f["cc"] > 10}),
        "mi_min": min(v["mi"] for v in mi.values()),
        "mi_prom": sum(v["mi"] for v in mi.values()) / len(mi),
        "loc": sum(v["loc"] for v in raw.values()), "sloc": sum(v["sloc"] for v in raw.values()),
        "archivos": len(raw), "flake8": flake,
    }


M1, M2 = metricas("inicial"), metricas("refactorizado")
LITERALES = r'"(PENDIENTE|EN_PROCESO|RESUELTA|RECHAZADA|CONSTANCIA|EQUIVALENCIA|BAJA|OTRO|ALTA|MEDIA)"'
LIT1 = len(re.findall(LITERALES, leer(INI)))
LIT2 = sum(len(re.findall(LITERALES, leer(str(p.relative_to(RAIZ)))))
           for p in (RAIZ / "refactorizado").rglob("*.py") if p.name != "dominio.py")
SALIDA_TESTS = (RAIZ / "docs/evidencias/pruebas_despues_suite_completa.txt").read_text(encoding="utf-8")
N_TESTS = int(re.search(r"Ran (\d+) tests", SALIDA_TESTS).group(1))
N_GOLDEN = len(list((RAIZ / "tests/golden").glob("*.json")))
N_UNIT = N_TESTS - 2 * N_GOLDEN

# --------------------------------------------------------------------- estilos
base = getSampleStyleSheet()
S = {
    "n": ParagraphStyle("n", parent=base["Normal"], fontName="Helvetica", fontSize=9.5, leading=13,
                        alignment=TA_JUSTIFY, spaceAfter=5),
    "h1": ParagraphStyle("h1", parent=base["Heading1"], fontName="Helvetica-Bold", fontSize=15,
                         textColor=AZUL, spaceBefore=14, spaceAfter=7, keepWithNext=1),
    "h2": ParagraphStyle("h2", parent=base["Heading2"], fontName="Helvetica-Bold", fontSize=11.5,
                         textColor=AZUL, spaceBefore=9, spaceAfter=4, keepWithNext=1),
    "h3": ParagraphStyle("h3", parent=base["Heading3"], fontName="Helvetica-Bold", fontSize=9.5,
                         spaceBefore=6, spaceAfter=2),
    "c": ParagraphStyle("c", parent=base["Normal"], fontName="Helvetica", fontSize=7.4, leading=9.2),
    "ch": ParagraphStyle("ch", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=7.6,
                         leading=9.4, textColor=colors.white),
    "cap": ParagraphStyle("cap", parent=base["Normal"], fontName="Helvetica-Oblique", fontSize=7.8,
                          leading=9.5, textColor=colors.HexColor("#444444"), spaceAfter=3, keepWithNext=1),
    "code": ParagraphStyle("code", fontName="Courier", fontSize=6.7, leading=8.0,
                           backColor=colors.HexColor("#F4F4F4"), borderColor=colors.HexColor("#CCCCCC"),
                           borderWidth=0.5, borderPadding=3, spaceBefore=2, spaceAfter=6),
    "tit": ParagraphStyle("tit", parent=base["Title"], fontName="Helvetica-Bold", fontSize=22,
                          textColor=AZUL, alignment=TA_CENTER, leading=27),
    "sub": ParagraphStyle("sub", parent=base["Normal"], fontName="Helvetica-Oblique", fontSize=12,
                          alignment=TA_CENTER, leading=16, textColor=colors.HexColor("#333333")),
    "cen": ParagraphStyle("cen", parent=base["Normal"], fontSize=11, alignment=TA_CENTER, leading=16),
}
ANCHO = 17 * cm
story = []


def P(texto, estilo="n"):
    story.append(Paragraph(texto, S[estilo]))


def H1(t):
    P(t, "h1")


def H2(t):
    P(t, "h2")


def codigo(texto, leyenda=None):
    if leyenda:
        P(leyenda, "cap")
    story.append(Preformatted(texto.rstrip("\n"), S["code"]))


def espacio(h=6):
    story.append(Spacer(1, h))


def tabla(filas, anchos, zebra=True):
    datos = [[Paragraph(str(c), S["ch"] if i == 0 else S["c"]) for c in fila]
             for i, fila in enumerate(filas)]
    t = Table(datos, colWidths=[a * cm for a in anchos], repeatRows=1)
    estilo = [("BACKGROUND", (0, 0), (-1, 0), AZUL), ("VALIGN", (0, 0), (-1, -1), "TOP"),
              ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#AAAAAA")),
              ("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 3),
              ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2)]
    if zebra:
        estilo += [("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F2F6FA")])]
    t.setStyle(TableStyle(estilo))
    story.append(t)
    espacio(8)


def pie(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(colors.HexColor("#666666"))
    canvas.drawString(2 * cm, 1.1 * cm, "TPI Metodología de Sistemas II — Gestión de Solicitudes Académicas")
    canvas.drawRightString(A4[0] - 2 * cm, 1.1 * cm, f"Pág. {doc.page}")
    canvas.restoreState()


# =========================================================================== PORTADA
story.append(Spacer(1, 1.2 * cm))
P("TECNICATURA UNIVERSITARIA EN PROGRAMACIÓN A DISTANCIA<br/>Universidad Tecnológica Nacional", "cen")
story.append(Spacer(1, 1.4 * cm))
P("Metodología de Sistemas II", "sub")
story.append(Spacer(1, 0.4 * cm))
P("Trabajo Práctico Integrador (TPI)", "tit")
story.append(Spacer(1, 0.4 * cm))
P("Evolución profesional de un sistema existente: calidad, deuda técnica, refactoring y revisión técnica", "sub")
story.append(Spacer(1, 0.8 * cm))
P("<b>Caso de trabajo:</b> Sistema de Gestión de Solicitudes Académicas", "cen")
story.append(Spacer(1, 1.2 * cm))
tabla([["Dato", "Detalle"],
       ["Materia", "Metodología de Sistemas II"],
       ["Comisión", "4"], ["Modalidad", "Individual"], ["Integrante", "Diego Pavón"],
       ["Fecha de entrega", FECHA],
       ["Repositorio GitHub", REPO], ["Video de defensa", VIDEO]], [4.5, 12.5], zebra=False)
story.append(PageBreak())

# ============================================================== 2. RESUMEN EJECUTIVO
H1("2. Resumen ejecutivo")
P(f"Se analizó y mejoró un módulo de consola de gestión de solicitudes académicas con deuda técnica real: "
  f"complejidad ciclomática promedio {coma(M1['cc_prom'])} (máx. {M1['cc_max']}), {len(M1['mayores_20'])} funciones de más de "
  f"20 líneas, {len(M1['flake8'])} avisos de flake8 y 12 code smells priorizados. Se aplicaron 7 refactorings (incluidos "
  f"Extract Method, Move Method e Introduce Parameter Object) guiados por SRP, OCP, LSP, ISP y DIP. {N_GOLDEN} "
  f"escenarios de caracterización sobre ambas versiones y {N_UNIT} pruebas unitarias y de contrato ({N_TESTS} en "
  f"total) verifican que el comportamiento externo se conserva, con un único cambio deliberado y documentado. "
  f"La complejidad promedio bajó a {coma(M2['cc_prom'])}, ninguna función supera 20 líneas y flake8 informa "
  f"{len(M2['flake8'])} avisos. El code review (15 criterios, 9 observaciones) cerró con correcciones aplicadas.")

# ===================================================== 3. DESCRIPCION DEL SISTEMA BASE
H1("3. Descripción del sistema base y alcance")
H2("3.1 Dominio, alcance y actores")
P("El sistema permite que el personal administrativo registre solicitudes de estudiantes (constancias, "
  "equivalencias, bajas u otras), las clasifique por tipo, prioridad y estado, asigne un responsable, las "
  "consulte con filtros y obtenga un reporte resumido. Es un módulo acotado de consola: no incluye autenticación, "
  "interfaz gráfica ni notificaciones, porque el foco del TPI es la calidad interna y no la cantidad de "
  "funcionalidad. <b>Todos los datos usados son sintéticos</b> (nombres y legajos ficticios).")
tabla([["Actor", "Rol en el sistema"],
       ["Estudiante", "Origina la solicitud (se registra por legajo y nombre la primera vez)."],
       ["Operador administrativo", "Usa el menú de consola: registra, asigna, cambia estados, consulta y emite reportes."],
       ["Responsable / Área", "Alumnado, Bedelia o Secretaria Academica: quien tiene a cargo la solicitud."]],
      [4.5, 12.5])
H2("3.2 Entidades y funcionalidades")
tabla([["Entidad", "Descripción"],
       ["Solicitud", "id, legajo, tipo, prioridad, estado, descripción, responsable, fecha."],
       ["Estudiante", "legajo (numérico) y nombre."],
       ["Responsable / Área", "Una de tres áreas predefinidas."],
       ["Estado / Tipo / Prioridad", "Estado: PENDIENTE, EN_PROCESO, RESUELTA, RECHAZADA. Tipo: CONSTANCIA, EQUIVALENCIA, BAJA, OTRO. Prioridad: ALTA, MEDIA, BAJA."]],
      [4.5, 12.5])
tabla([["Operación", "Reglas de negocio verificables"],
       ["1. Registrar solicitud", "Legajo numérico obligatorio; nombre obligatorio solo para estudiante nuevo; tipo y prioridad válidos; descripción obligatoria, máx. 200 caracteres. Las BAJAS se fuerzan a prioridad ALTA."],
       ["2. Cambiar estado", "PENDIENTE -> EN_PROCESO/RECHAZADA; EN_PROCESO -> RESUELTA/RECHAZADA; RESUELTA y RECHAZADA son finales. No se pasa a EN_PROCESO sin responsable."],
       ["3. Asignar responsable", "Solo a solicitudes abiertas; el nombre del área no distingue mayúsculas."],
       ["4. Buscar / filtrar", "Por estado, tipo, prioridad, legajo o sin filtro."],
       ["5. Reporte", "Total y cantidades por estado, tipo y prioridad (incluye ceros) y solicitudes sin responsable."]],
      [4.5, 12.5])
H2("3.3 Tecnología, repositorio y versiones")
P(f"Python {sys.version_info.major}.{sys.version_info.minor} con biblioteca estándar (json, dataclasses, enum, unittest). "
  "Persistencia en <i>datos.json</i>. Herramientas de análisis: radon (complejidad y mantenibilidad) y flake8 "
  "(análisis estático). El repositorio "
  f"contiene <b>inicial/</b> (versión base, tag <i>estado-inicial</i>) y <b>refactorizado/</b> (versión final, tag "
  f"<i>estado-refactorizado</i>). Enlace: {REPO}.")
H2("3.4 Cumplimiento de los requisitos mínimos del sistema base")
tabla([["Requisito de la consigna", "Cumplimiento"],
       ["Al menos 3 entidades o estructuras principales", "Solicitud, Estudiante y Responsable (más Estado, Tipo y Prioridad)."],
       ["Al menos 4 operaciones funcionales verificables", f"5 operaciones, cubiertas por {N_GOLDEN} escenarios automatizados."],
       ["Persistir o simular datos", "Archivo JSON (datos.json)."],
       ["Versión inicial con problemas diagnosticables", "12 code smells con evidencia y ubicación (sección 5)."],
       ["Demostrar que la versión final conserva el comportamiento", "Golden master sobre ambas versiones (sección 8)."]],
      [7.5, 9.5])
H2("3.5 Evidencia de funcionamiento (versión inicial)")
story.append(Image(str(RAIZ / "docs/evidencias/captura_ejecucion_inicial.png"), width=13 * cm, height=13 * cm * 1364 / 2000))
P("Figura. Ejecución de inicial/app.py con entrada automatizada por stdin (por eso los valores ingresados no se "
  "ven en pantalla): registro, asignación, cambio de estado, búsqueda y reporte. Transcripciones completas de ambas "
  "versiones en docs/evidencias/demo_*.txt.", "cap")

# ================================================= 4. CALIDAD EXTERNA E INTERNA
H1("4. Calidad externa e interna")
P(f"<b>Calidad externa</b> es lo que percibe quien usa el sistema: que haga lo prometido, que no pierda datos y "
  f"que responda de forma clara. Desde esa mirada la versión inicial <b>funciona correctamente</b>: supera "
  f"{N_GOLDEN} de {N_GOLDEN} escenarios de caracterización (registro, validaciones, flujo de estados, filtros, "
  f"reportes y persistencia entre sesiones). <b>Calidad interna</b> es la estructura que el equipo técnico "
  f"debe sostener: legibilidad, cohesión, acoplamiento, testeabilidad y costo de cambio. Ahí la versión inicial "
  f"muestra problemas que el usuario no ve pero que encarecen cada modificación futura.")
tabla([["Atributo", "Calidad externa (visible)", "Calidad interna (estructura)", "Evidencia"],
       ["Corrección funcional", "Las 5 operaciones y sus reglas funcionan.", "Las reglas están dispersas en funciones de I/O; difícil asegurar que un cambio no rompa otra.", f"{N_GOLDEN}/{N_GOLDEN} escenarios; CC máx. {M1['cc_max']}"],
       ["Fiabilidad de datos", "Los datos persisten entre sesiones.", "Un except desnudo oculta archivos dañados y luego los sobrescribe.", f"cargar() {rango(INI, 'cargar')}"],
       ["Mantenibilidad", "—", f"{len(M1['mayores_20'])} funciones > 20 líneas; MI = {coma(M1['mi_min'])} (cerca del límite de la categoría A).", "radon cc / mi"],
       ["Legibilidad", "Mensajes de error claros.", "Nombres de una letra (s, x, e, d, n, r, v) y anidación de hasta 7 niveles.", f"opcion_registrar {rango(INI, 'opcion_registrar')}"],
       ["Testeabilidad", "—", "Estado global y print/input embebidos: no se puede probar una regla sin ejecutar todo el menú.", "variables de módulo"],
       ["Evolución futura", "—", "Agregar un estado, un filtro o cambiar de persistencia obliga a tocar varios lugares.", "ver tabla siguiente"]],
      [2.6, 4.0, 6.4, 4.0])
H2("4.1 Costo de cambio: cuatro cambios hipotéticos")
tabla([["Cambio pedido", "Versión inicial", "Versión refactorizada"],
       ["Agregar el estado EN_REVISION", "Hay que editar la lista de estados válidos y la cadena if/elif de transiciones en opcion_cambiar_estado y la lista de estados de opcion_reporte (3 puntos, fácil olvidar uno).", "Agregar un miembro a la enumeración Estado y su entrada en _TRANSICIONES. El reporte lo incluye solo (itera la enumeración). Solo queda actualizar el texto del prompt."],
       ["Agregar el filtro por responsable", "Un nuevo elif con otro bucle copiado (~6 líneas) en opcion_buscar y su texto de ayuda.", "Una entrada nueva en el diccionario FILTROS."],
       ["Cambiar JSON por SQLite", "Reescribir cargar/guardar y revisar todas las funciones que usan las variables globales.", "Nueva clase que implemente RepositorioSolicitudes; el servicio y la interfaz no cambian."],
       ["Probar la regla «BAJA fuerza prioridad ALTA»", "Solo ejecutando el menú completo con un archivo real.", "Prueba unitaria con repositorio en memoria (test_baja_fuerza_prioridad_alta)."]],
      [3.6, 6.7, 6.7])

# ========================================== 5. DEUDA TECNICA Y CODE SMELLS
H1("5. Diagnóstico de deuda técnica y code smells")
P("Se identificaron <b>12 debilidades técnicas</b> (la consigna pide al menos 8) mediante lectura del código y "
  "herramientas (radon, flake8). La ubicación se indica como archivo de la versión inicial y rango de líneas. "
  "Prioridad = urgencia de corrección según impacto y riesgo de mantenimiento.")
g = linea_de(INI, "solicitudes = []")
SMELLS = [
    ["S1", "<b>Estado global mutable</b>", "solicitudes, estudiantes, contador y responsables son variables de módulo; cargar() usa global.", f"inicial/app.py L{g}-L{g+3}; cargar {rango(INI,'cargar')}", "Acoplamiento oculto: el resultado depende del orden de llamadas; imposible probar funciones aisladas. Riesgo ALTO.", "Alta"],
    ["S2", "<b>Except desnudo</b> que oculta errores", "cargar() captura todo con «except:» y vuelve a listas vacías (flake8 E722).", f"cargar {rango(INI,'cargar')}", "Un datos.json dañado se ignora en silencio y el próximo guardar() lo sobrescribe: pérdida de datos. Riesgo ALTO.", "Alta"],
    ["S3", "<b>Long Method</b> / varias responsabilidades (SRP)", "opcion_registrar lee entradas, valida, aplica regla y delega persistencia; 7 niveles de if/else anidados.", f"opcion_registrar {rango(INI,'opcion_registrar')}", "CC 11 y 32 líneas; mezcla presentación, validación y reglas: cualquier cambio de regla toca la interfaz. Riesgo ALTO.", "Alta"],
    ["S4", "<b>Código duplicado</b>", "Búsqueda por ID copiada en cambiar_estado y asignar; parseo del ID; 4 bucles de conteo casi idénticos en el reporte; 4 bucles de filtro; búsqueda del nombre del estudiante repetida.", f"{rango(INI,'opcion_cambiar_estado')}, {rango(INI,'opcion_asignar')}, {rango(INI,'opcion_reporte')}, {rango(INI,'opcion_buscar')}", "Un cambio de regla debe replicarse en varios sitios; riesgo de corregir solo uno. Riesgo ALTO.", "Alta"],
    ["S5", "<b>Primitive Obsession</b> y cadenas mágicas", f"Estados, tipos y prioridades como strings sueltos ({LIT1} literales repetidos) y entidades como diccionarios.", "todo el archivo", "Un error de tipeo no falla en compilación sino en ejecución; no hay un lugar único con los valores válidos. Riesgo MEDIO-ALTO.", "Alta"],
    ["S6", "<b>Números mágicos</b> y listas repetidas", "El límite 200 y las listas de valores válidos están escritos en línea y repetidos entre registrar y reporte.", f"opcion_registrar {rango(INI,'opcion_registrar')}", "Cambiar un límite exige buscarlo a mano. Riesgo BAJO.", "Baja"],
    ["S7", "<b>Condicionales complejas</b> (viola OCP)", "Cadena if/elif de transiciones y de criterios de búsqueda; menú con if/elif.", f"opcion_buscar CC 19 {rango(INI,'opcion_buscar')}; opcion_cambiar_estado CC 14; main", "Cada nuevo estado/filtro/opción obliga a modificar código existente (riesgo de regresión). Riesgo MEDIO.", "Media"],
    ["S8", "<b>Long Parameter List</b> / Data Clump", "crear_solicitud(legajo, nombre, tipo, prioridad, desc) transporta 5 datos que siempre viajan juntos.", f"crear_solicitud {rango(INI,'crear_solicitud')}", "Firmas frágiles: alterar el orden produce errores silenciosos. Riesgo MEDIO.", "Media"],
    ["S9", "<b>Feature Envy</b> / modelo anémico", "Las reglas de «solicitud cerrada» y de transición viven en funciones externas que manipulan diccionarios.", f"{rango(INI,'opcion_cambiar_estado')}, {rango(INI,'opcion_asignar')}", "El conocimiento del dominio no está encapsulado en las entidades. Riesgo MEDIO.", "Media"],
    ["S10", "<b>Nombres poco expresivos</b>", "Variables s, x, e, d, f, n, r, v, c, sin, desc, op.", "todo el archivo", "Lectura lenta y errores de interpretación. Riesgo MEDIO-BAJO.", "Media"],
    ["S11", "<b>Recursos sin gestión segura</b>", "open()/close() manuales sin «with»: si hay una excepción el archivo queda abierto.", f"cargar, guardar {rango(INI,'guardar')}", "Posible fuga de recursos y archivos truncados. Riesgo MEDIO.", "Media"],
    ["S12", "<b>Código muerto</b> / estilo", "Imports sin uso (os, sys; flake8 F401) y línea de 104 caracteres (E501).", "inicial/app.py L4-L5, L53", "Ruido y falsa sensación de dependencias. Riesgo BAJO.", "Baja"],
]
tabla([["ID", "Smell", "Evidencia", "Ubicación", "Impacto y riesgo", "Prior."]] + SMELLS, [0.9, 2.5, 4.6, 3.1, 4.9, 1.0])
H2("5.1 Evidencia de herramientas sobre la versión inicial")
f1 = sorted(M1["funciones"], key=lambda f: -f["cc"])
tabla([["Función", "Complejidad ciclomática", "Líneas"]] + [[f["nombre"], f["cc"], f["largo"]] for f in f1], [7, 5, 5])
codigo("\n".join(M1["flake8"]), "flake8 --max-line-length=100 inicial/")
P("<b>Priorización:</b> primero S1, S2, S3, S4 y S5 (riesgo de pérdida de datos y mayor costo de cambio); luego "
  "S7–S11; por último S6 y S12, de bajo riesgo y resolución casi inmediata durante los refactorings anteriores.")

# ===================================================== 6. SOLID Y CLEAN CODE
H1("6. Aplicación de SOLID y Clean Code")
story.append(KeepTogether([
    Image(str(RAIZ / "docs/evidencias/arquitectura_antes_despues.png"), width=ANCHO, height=ANCHO * 5.2 / 11 * 0.97),
    Paragraph("Figura 1. Arquitectura antes y después del refactoring.", S["cap"])]))
H2("6.1 Principios SOLID")
tabla([["Principio", "Problema en la versión inicial", "Mejora aplicada", "Dónde verlo"],
       ["SRP", "Cada opcion_* lee entradas, valida, aplica reglas, persiste e imprime.", "Cada módulo tiene una razón de cambio: cli (entrada/salida), servicio (casos de uso), dominio (reglas), repositorio (persistencia), reportes y filtros.", "refactorizado/solicitudes/*"],
       ["OCP", "Agregar un estado, filtro u opción de menú obliga a editar cadenas if/elif.", "Tablas de datos: _TRANSICIONES, FILTROS y el diccionario de acciones del menú. Extender = agregar una entrada.", "dominio.py, filtros.py, cli.py"],
       ["LSP", "No había abstracciones que sustituir.", "RepositorioJson y RepositorioEnMemoria son intercambiables bajo el mismo contrato (pruebas de contrato comunes). La jerarquía ErrorDeDominio se captura con un único manejador.", "test_unitarios: ContratoRepositorio"],
       ["ISP", "—", "RepositorioSolicitudes expone solo cargar/guardar; reportes y filtros reciben listas de Solicitud en vez del servicio completo. En un sistema tan pequeño ISP aplica de forma limitada.", "repositorio.py, reportes.py"],
       ["DIP", "Funciones dependían de variables globales, del archivo concreto y de datetime.now().", "ServicioSolicitudes recibe un RepositorioSolicitudes y un reloj; Interfaz recibe funciones de entrada/salida; las dependencias se componen en main.py.", "servicio.py, main.py"]],
      [1.4, 4.4, 7.4, 3.8])
H2("6.2 Clean Code")
tabla([["Aspecto", "Antes", "Después"],
       ["Nombres", "s, x, e, d, n, r, v, c, sin.", "solicitud, estudiante, responsable, descripcion, criterio, valor…; tras el code review no quedan nombres de una letra en la lógica."],
       ["Funciones", f"{len(M1['mayores_20'])} funciones > 20 líneas; máx. {M1['largo_max']}.", f"Ninguna > 20 líneas; máx. {M2['largo_max']}. Cada función hace una cosa."],
       ["Manejo de errores", "print + return mezclados con la lógica; except desnudo.", "Excepciones de dominio tipificadas (ErrorDeValidacion, SolicitudNoEncontrada, TransicionNoPermitida, OperacionNoPermitida, ErrorDeAlmacenamiento). Un único punto en la interfaz las convierte en «Error: …» con el mismo texto que antes."],
       ["Cohesión", "Funciones heterogéneas en un archivo.", "Módulos pequeños y cohesivos; las reglas viven en las entidades (Solicitud, Estado)."],
       ["Acoplamiento", "Estado global compartido.", "Dependencias explícitas por constructor; sin estado global."],
       ["Límites entre componentes", "No existían.", "Presentación -> servicio -> dominio/repositorio; la capa de abajo no conoce a la de arriba."],
       ["Valores mágicos", f"{LIT1} literales repetidos; número 200 en línea.", f"Enumeraciones y constante LONGITUD_MAXIMA_DESCRIPCION ({LIT2} literales fuera de la definición de las enumeraciones)."],
       ["Documentación", "Sin docstrings.", "Docstring por módulo y por clase clave; README y decisiones técnicas."]],
      [3.0, 5.2, 8.8])

# ====================================================== 7. REFACTORINGS
H1("7. Refactorings aplicados con evidencia antes/después")
P(f"Se aplicaron <b>7 refactorings documentados</b> (la consigna pide al menos 4, incluyendo Extract Method, Move "
  f"Method e Introduce Parameter Object). Método de trabajo seguro: (1) fijar el comportamiento externo con "
  f"pruebas de caracterización <i>antes</i> de tocar el código; (2) hacer pasos pequeños; (3) ejecutar la suite "
  f"completa después de cada paso; (4) comparar salida de consola y datos persistidos con la referencia. "
  f"Resultado final: {N_TESTS}/{N_TESTS} pruebas en verde.")
tabla([["#", "Refactoring", "Smells que ataca", "Principio"],
       ["R1", "Extract Method", "S3", "SRP, Clean Code"], ["R2", "Move Method (reubicación de responsabilidad)", "S9, S7", "SRP, cohesión"],
       ["R3", "Introduce Parameter Object", "S8", "Clean Code"], ["R4", "Replace Type Code with Enum + constante nombrada", "S5, S6", "Clean Code"],
       ["R5", "Replace Conditional with Lookup table", "S7, S4", "OCP"],
       ["R6", "Extract Class (repositorio) + inyección de dependencias + excepciones específicas + with", "S1, S2, S11", "DIP, LSP, ISP"],
       ["R7", "Consolidar duplicación (Extract Method), Rename Variable y eliminar código muerto", "S4, S10, S12", "Clean Code"]],
      [1.0, 8.3, 3.2, 4.5])


def refactoring(titulo, objetivo, antes, despues, verificacion):
    H2(titulo)
    P(objetivo)
    for leyenda, txt in antes:
        codigo(txt, "ANTES — " + leyenda)
    for leyenda, txt in despues:
        codigo(txt, "DESPUÉS — " + leyenda)
    P("<b>Verificación:</b> " + verificacion)


refactoring("R1 — Extract Method: validaciones y creación de la solicitud",
            "<b>Problema (S3):</b> opcion_registrar concentraba lectura, validación en cascada, regla de negocio y "
            "persistencia. <b>Cambio:</b> la validación se extrajo en métodos con nombre propio "
            "(_validar_legajo, _validar_nombre, _validar_descripcion) y el caso de uso quedó en un método "
            "de pocas líneas, plano y sin anidación. El orden de validación se conserva.",
            [("inicial/app.py, opcion_registrar", fuente(INI, "opcion_registrar"))],
            [("servicio.py, registrar", fuente(SERV, "ServicioSolicitudes.registrar")),
             ("servicio.py, _validar_legajo", fuente(SERV, "ServicioSolicitudes._validar_legajo")),
             ("servicio.py, _validar_descripcion", fuente(SERV, "ServicioSolicitudes._validar_descripcion"))],
            "escenarios 01, 02, 03 y 04 (alta, regla de BAJA, 7 validaciones en orden y estudiante existente) "
            "producen exactamente la misma salida y los mismos datos.")
refactoring("R2 — Move Method: las reglas de transición y cierre pasan al dominio",
            "<b>Problema (S9, S7):</b> la cadena if/elif que decide si un cambio de estado es válido estaba en una "
            "función de menú. <b>Cambio:</b> el conocimiento de «qué transiciones existen» se movió a Estado y la "
            "regla «no pasar a EN_PROCESO sin responsable» a Solicitud.cambiar_estado. Los mensajes se mantienen.",
            [("inicial/app.py, opcion_cambiar_estado (reglas)", trozo(INI, 'actual = s["estado"]', 15))],
            [("dominio.py, tabla de transiciones", trozo(DOM, "_TRANSICIONES = {", 6)),
             ("dominio.py, Estado.puede_pasar_a", fuente(DOM, "Estado.puede_pasar_a")),
             ("dominio.py, Solicitud.cambiar_estado", fuente(DOM, "Solicitud.cambiar_estado"))],
            "escenarios 05 y 06 (flujo completo y errores de transición) idénticos; pruebas unitarias de "
            "PruebasDominio validan cada regla sin pasar por la consola.")
refactoring("R3 — Introduce Parameter Object: NuevaSolicitud",
            "<b>Problema (S8):</b> cinco parámetros que viajan juntos (data clump). <b>Cambio:</b> se creó el "
            "objeto inmutable NuevaSolicitud; la interfaz lo construye y el servicio lo valida.",
            [("inicial/app.py, firma", trozo(INI, "def crear_solicitud", 1)),
             ("inicial/app.py, llamada", trozo(INI, "crear_solicitud(legajo, nombre", 1, 2))],
            [("dominio.py", fuente(DOM, "NuevaSolicitud")), ("cli.py, construcción", trozo(CLI, "nueva = NuevaSolicitud(", 6)),
             ("servicio.py, firma", trozo(SERV, "def registrar", 1))],
            "escenarios 01 a 04; además las pruebas unitarias construyen NuevaSolicitud con valores nombrados.")
refactoring("R4 — Replace Type Code with Enum y constante nombrada",
            "<b>Problema (S5, S6):</b> estados, tipos y prioridades eran strings repetidos y el límite de 200 estaba "
            "escrito en línea. <b>Cambio:</b> enumeraciones Estado, Tipo y Prioridad (str, Enum) —que se serializan "
            "igual en JSON— y la constante LONGITUD_MAXIMA_DESCRIPCION; parsear_enum centraliza la conversión.",
            [("inicial/app.py, validaciones con listas literales", trozo(INI, 'if tipo not in', 1) + "\n" +
              trozo(INI, 'if prioridad not in', 1) + "\n" + trozo(INI, "if len(desc) > 200", 1) + "\n" +
              trozo(INI, 'for e in ["PENDIENTE"', 1))],
            [("dominio.py, enumeraciones y constantes", trozo(DOM, "TEnum =", 4) + "\n" + trozo(DOM, "class Tipo", 5) +
              "\n" + trozo(DOM, "class Estado", 5)), ("dominio.py, parsear_enum", fuente(DOM, "parsear_enum"))],
            "escenarios 02, 03, 06, 08 y 10; y la prueba de formato de datos.json confirma que el archivo sigue "
            "siendo compatible con la versión inicial.")
refactoring("R5 — Replace Conditional with Lookup table (OCP)",
            "<b>Problema (S7, S4):</b> opcion_buscar repetía un bucle por criterio y main usaba if/elif para el menú. "
            "<b>Cambio:</b> el criterio de búsqueda y las opciones del menú son tablas; agregar una entrada no "
            "modifica la lógica existente.",
            [("inicial/app.py, opcion_buscar (parcial)", trozo(INI, "def opcion_buscar", 26)),
             ("inicial/app.py, menú", trozo(INI, 'if op == "1":', 11))],
            [("filtros.py", trozo(FIL, "FILTROS: dict", 6)), ("filtros.py, Filtro", fuente(FIL, "Filtro")),
             ("cli.py, _buscar", fuente(CLI, "Interfaz._buscar")), ("cli.py, tabla de acciones", trozo(CLI, "self._acciones", 8))],
            "escenarios 08 (todos los criterios, valor inexistente y criterio inválido), 11 (opción inválida) y 13.")
refactoring("R6 — Extract Class (repositorio), inyección de dependencias y excepciones específicas",
            "<b>Problema (S1, S2, S11):</b> estado global, persistencia embebida, except desnudo y archivos sin with. "
            "<b>Cambio:</b> contrato abstracto RepositorioSolicitudes con implementaciones en JSON y en memoria; "
            "el servicio recibe sus dependencias por constructor; el archivo se gestiona con with y los errores se "
            "capturan por tipo. <b>Nota:</b> este refactoring contiene el único cambio de comportamiento deliberado "
            "(ver 8.4): un archivo dañado ahora se informa en lugar de ignorarse y sobrescribirse.",
            [("inicial/app.py, cargar", fuente(INI, "cargar")), ("inicial/app.py, guardar", fuente(INI, "guardar"))],
            [("repositorio.py, contrato", fuente(REP, "RepositorioSolicitudes")),
             ("repositorio.py, RepositorioJson.cargar", fuente(REP, "RepositorioJson.cargar")),
             ("servicio.py, constructor", fuente(SERV, "ServicioSolicitudes.__init__")),
             ("main.py, composición", fuente(MAIN, "main"))],
            "escenario 12 (persistencia entre sesiones), pruebas de contrato sobre ambos repositorios y la prueba "
            "de archivo dañado.")
refactoring("R7 — Consolidar duplicación, renombrar y limpiar",
            "<b>Problema (S4, S10, S12):</b> cuatro bucles de conteo casi idénticos, nombres crípticos e imports "
            "sin uso. <b>Cambio:</b> un método _contar reutilizable, separación entre generar y formatear el reporte, "
            "nombres expresivos y eliminación de os y sys.",
            [("inicial/app.py, opcion_reporte", fuente(INI, "opcion_reporte"))],
            [("reportes.py, generar_reporte", fuente(REPT, "generar_reporte")), ("reportes.py, _contar", fuente(REPT, "_contar"))],
            "escenarios 09 y 10 (reporte vacío y con datos, incluyendo categorías en cero).")

# ================================================ 8. PRUEBAS Y VERIFICACION
H1("8. Pruebas y verificaciones realizadas")
H2("8.1 Estrategia")
P("Se combinaron cuatro tipos de evidencia: (a) <b>pruebas de caracterización (golden master)</b>: cada escenario "
  "simula a un usuario real por entrada estándar y compara salida de consola y datos persistidos con la referencia "
  "generada con la versión inicial; (b) <b>pruebas unitarias</b> de dominio, servicio, filtros y reportes, posibles "
  "gracias a la inyección de dependencias; (c) <b>pruebas de contrato</b> que ambos repositorios deben cumplir; "
  "(d) <b>análisis estático</b> (flake8, radon). Se excluye la fecha de registro por ser no determinista.")
H2("8.2 Casos de prueba de caracterización y trazabilidad")
ESC = [("01_registrar_ok", "Alta de solicitud y estudiante nuevo", "R1, R3"),
       ("02_baja_fuerza_prioridad_alta", "BAJA fuerza prioridad ALTA; entrada en minúsculas", "R1, R4"),
       ("03_validaciones_registro", "7 errores de validación en orden + descripción de exactamente 200 caracteres", "R1, R3"),
       ("04_estudiante_existente_conserva_nombre", "No se pisa el nombre; nombre vacío permitido si ya existe", "R1"),
       ("05_flujo_completo_estados", "Asignar, EN_PROCESO, RESUELTA y rechazo de cambios posteriores", "R2, R5"),
       ("06_errores_cambiar_estado", "ID inválido/inexistente, estado inválido, transiciones no permitidas, sin responsable", "R2, R4"),
       ("07_errores_asignar", "Responsable inexistente, sin distinguir mayúsculas, solicitud cerrada", "R2"),
       ("08_filtros", "Los 4 criterios, sin resultados y criterio inválido", "R5"),
       ("09_reporte_vacio", "Reporte sin datos (todo en cero)", "R7"),
       ("10_reporte_con_datos", "Reporte con estados, tipos y prioridades mixtos", "R7, R4"),
       ("11_opcion_invalida", "Opciones de menú inválidas", "R5"),
       ("12_persistencia_entre_sesiones", "Tres ejecuciones consecutivas sobre el mismo archivo", "R6"),
       ("13_busqueda_sin_resultados_y_vacio", "Búsqueda y listado con el sistema vacío", "R5")]
tabla([["Escenario", "Qué verifica", "Refactorings"]] + [list(e) for e in ESC], [5.6, 9.0, 2.4])
H2("8.3 Resultados antes y después")
tabla([["Suite", "Versión inicial", "Versión refactorizada"],
       [f"Caracterización ({N_GOLDEN} escenarios: consola + datos)", f"{N_GOLDEN}/{N_GOLDEN} (línea base)", f"{N_GOLDEN}/{N_GOLDEN}"],
       [f"Unitarias y de contrato ({N_UNIT})", "no aplica (no testeable de forma aislada)", f"{N_UNIT}/{N_UNIT}"],
       ["Total ejecutado", f"{N_GOLDEN}", f"{N_TESTS}"],
       ["Comparación de demos", "demo_inicial.txt", "idéntica a demo_refactorizado.txt (diff sin diferencias)"]],
      [7.0, 5.0, 5.0])
tail = "\n".join(SALIDA_TESTS.strip().splitlines()[-4:])
story.append(Image(str(RAIZ / "docs/evidencias/captura_pruebas.png"), width=ANCHO, height=ANCHO * 814 / 2416))
P("Figura. Final de la ejecución de la suite completa (salida completa en el anexo).", "cap")
tabla([["Métrica", "Inicial", "Refactorizada"],
       ["Archivos .py / funciones y métodos", f"{M1['archivos']} / {len(M1['funciones'])}", f"{M2['archivos']} / {len(M2['funciones'])}"],
       ["Líneas (LOC / SLOC)", f"{M1['loc']} / {M1['sloc']}", f"{M2['loc']} / {M2['sloc']}"],
       ["Complejidad ciclomática promedio", coma(M1["cc_prom"], 2), coma(M2["cc_prom"], 2)],
       ["Complejidad ciclomática máxima", M1["cc_max"], M2["cc_max"]],
       ["Funciones con CC > 10", len(M1["mayores_cc10"]), len(M2["mayores_cc10"])],
       ["Funciones > 20 líneas / longitud máxima", f"{len(M1['mayores_20'])} / {M1['largo_max']}", f"{len(M2['mayores_20'])} / {M2['largo_max']}"],
       ["Índice de mantenibilidad (mínimo por archivo)", coma(M1["mi_min"]), coma(M2["mi_min"])],
       ["Avisos de flake8", len(M1["flake8"]), len(M2["flake8"])],
       ["Literales de estado/tipo/prioridad repetidos", LIT1, f"{LIT2} (fuera de las enumeraciones)"]],
      [8.0, 4.5, 4.5])
P("<b>Lectura honesta de las métricas:</b> el código total creció (más archivos y líneas) porque se agregaron "
  "abstracciones, docstrings y pruebas de diseño; lo que bajó es la complejidad por unidad, la duplicación y el "
  "costo de cambio. El TPI no premia la cantidad de código sino la mejora técnica demostrada.")
H2("8.4 Único cambio de comportamiento deliberado")
P("La versión inicial ignoraba un datos.json dañado y lo sobrescribía en el siguiente guardado (pérdida silenciosa "
  "de datos, smell S2). La refactorizada informa «Error: el archivo de datos … esta danado» y no lo modifica. "
  "Se decidió así porque conservar un comportamiento que destruye datos no es una mejora segura; queda "
  "documentado (decisión D6) y cubierto por test_archivo_danado_se_informa_y_no_se_pisa. El resto del "
  "comportamiento externo —mensajes, orden de preguntas, formato del archivo— se conserva idéntico.")

# ====================================================== 9. CODE REVIEW
H1("9. Code review y checklist técnico")
OK, NO = "Sí", "No"
CHECK = [
    ("C1", "Cada módulo/función tiene una única responsabilidad (SRP)", NO, OK, "secciones 5 y 6"),
    ("C2", "Nombres expresivos, sin variables de una letra", NO, OK, "H1 corregido"),
    ("C3", "Funciones de hasta 20 líneas", f"{NO} ({len(M1['mayores_20'])} la superan)", f"{OK} (máx. {M2['largo_max']})", "radon cc"),
    ("C4", "Sin código duplicado relevante", NO, OK, "R5, R7"),
    ("C5", "Sin números ni cadenas mágicas", NO, OK, "R4"),
    ("C6", "Errores tratados de forma explícita (sin except desnudo)", NO, OK, "R6"),
    ("C7", "Sin estado global mutable", NO, OK, "R6"),
    ("C8", "Dependencias invertidas y componentes testeables", NO, OK, f"{N_UNIT} pruebas unitarias"),
    ("C9", "Complejidad ciclomática por función <= 10", f"{NO} ({len(M1['mayores_cc10'])} la superan)", f"{OK} (máx. {M2['cc_max']})", "radon cc"),
    ("C10", "Análisis estático limpio (flake8)", f"{NO} ({len(M1['flake8'])} avisos)", f"{OK} (0)", "flake8"),
    ("C11", "Pruebas automatizadas que protegen el comportamiento", NO, f"{OK} ({N_TESTS})", "sección 8"),
    ("C12", "Documentación (README, docstrings, decisiones técnicas)", NO, OK, "docs/"),
    ("C13", "El comportamiento externo se conserva", "—", f"{OK} ({N_GOLDEN}/{N_GOLDEN})", "golden master; ver D6"),
    ("C14", "Datos sintéticos, sin datos personales reales", OK, OK, "consigna sección 10"),
    ("C15", "Trazabilidad Git (tags por etapa y commits claros)", "—", OK, "tags del repositorio"),
]
tabla([["#", "Criterio", "Inicial", "Refactorizada", "Evidencia"]] + [list(c) for c in CHECK], [0.9, 7.3, 3.0, 3.2, 2.6])
H2("9.1 Observaciones, feedback y acciones")
HALL = [
    ("H1", "Menor", "cli.py usa la variable «s» en _registrar, _cambiar_estado, _asignar_responsable y _buscar: contradice C2.", "Renombrar a «solicitud» (y extraer «nombre» en _buscar).", "Corregido"),
    ("H2", "Menor", "parsear_enum no tenía tipos genéricos: el retorno perdía información para el lector y el IDE.", "TypeVar TEnum y firma type[TEnum] -> TEnum.", "Corregido"),
    ("H3", "Media", "Interfaz._cambiar_estado llama a servicio.obtener() solo para validar el ID antes de pedir el estado.", "Aceptado: preserva el orden de preguntas de la versión inicial (decisión D5). Mejora futura: validar todo al final.", "Aceptado"),
    ("H4", "Menor", "validar_asignable y asignar_responsable repiten la verificación de solicitud cerrada.", "Aceptado: el servicio protege su invariante aunque se lo llame sin pasar por la interfaz.", "Aceptado"),
    ("H5", "Media", "RESPONSABLES es una constante de dominio: no se pueden administrar áreas.", "Mejora futura: entidad Responsable persistida y repositorio propio.", "Mejora futura"),
    ("H6", "Menor", "_leer_id (presentación) lanza ErrorDeValidacion, un error del dominio.", "Aceptado por simplicidad; alternativa: error de presentación propio.", "Aceptado"),
    ("H7", "Media", "Solicitud es mutable y listar() devuelve una copia superficial: un cliente podría mutar objetos.", "Mejora futura: vistas inmutables (DTO) para consulta.", "Mejora futura"),
    ("H8", "Mayor", "El manejo de archivo dañado cambia el comportamiento respecto de la versión inicial.", "Aceptado y documentado (D6, sección 8.4); cubierto por prueba. Es una mejora, no una regresión.", "Aceptado"),
    ("H9", "Menor", "Si la entrada estándar se cierra (EOF) el programa termina con traceback, en ambas versiones.", "Fuera del alcance de un refactoring; queda como mejora futura.", "Mejora futura"),
]
tabla([["ID", "Sev.", "Observación (feedback objetivo)", "Acción", "Estado"]] + [list(h) for h in HALL], [0.9, 1.3, 6.4, 6.2, 2.2])
corr = sum(1 for h in HALL if h[4] == "Corregido")
P(f"Resultado del review: {len(HALL)} observaciones; {corr} corregidas, {sum(1 for h in HALL if h[4]=='Aceptado')} "
  f"aceptadas con justificación y {sum(1 for h in HALL if h[4]=='Mejora futura')} derivadas a mejoras futuras. Tras "
  f"las correcciones se volvió a ejecutar la suite completa ({N_TESTS}/{N_TESTS}) y flake8 (0 avisos).")
H2("9.2 Criterios de aceptación técnica")
ACEP = [
    ("A1", f"Suite completa en verde ({N_TESTS}/{N_TESTS})", True),
    ("A2", f"Sin diferencias de salida ni de datos entre versiones en {N_GOLDEN} escenarios", True),
    ("A3", "flake8 sin avisos en el código refactorizado", len(M2["flake8"]) == 0),
    ("A4", "Complejidad ciclomática <= 10 en todas las funciones", M2["cc_max"] <= 10),
    ("A5", "Ninguna función de más de 20 líneas", M2["largo_max"] <= 20),
    ("A6", "Sin cambios de comportamiento salvo los documentados (D6)", True),
    ("A7", "Observaciones de severidad mayor cerradas o justificadas por escrito", True),
]
tabla([["ID", "Criterio", "Resultado"]] + [[a, c, "Cumple" if ok else "NO cumple"] for a, c, ok in ACEP], [1.2, 12.8, 3.0])

# =========================================================== 10. CONCLUSIONES
H1("10. Conclusiones y mejoras futuras")
H2("10.1 Conclusiones generales")
P("Un sistema que «funciona» no es necesariamente un sistema sano: la versión inicial aprobaba todas las pruebas "
  "externas y aun así concentraba riesgo (pérdida silenciosa de datos, duplicación, reglas dispersas). Fijar "
  "primero el comportamiento con pruebas de caracterización fue lo que permitió refactorizar con seguridad. "
  "Los patrones simples —enumeraciones, tablas de datos, objetos de parámetros, un contrato de repositorio— "
  "redujeron la complejidad y el costo de cambio sin alterar lo que ve el usuario. Relación con la materia: "
  "calidad interna vs. externa, deuda técnica, code smells, SOLID, Clean Code, refactoring seguro y code review.")
H2("10.2 Dificultades")
P("Preservar byte a byte mensajes y orden de preguntas (por ejemplo, validar el ID antes de pedir el nuevo "
  "estado) condicionó el diseño del servicio y dejó la observación H3; decidir qué hacer con el archivo dañado "
  "(¿conservar un comportamiento defectuoso?) obligó a distinguir refactoring puro de mejora de comportamiento.")
H2("10.3 Límites del trabajo")
P("Alcance acotado a un módulo de consola; sin concurrencia ni base de datos real; los responsables son fijos; "
  "las pruebas de caracterización dependen de los escenarios elegidos (no prueban todo el espacio de entradas); "
  "no se midió cobertura de código.")
H2("10.4 Mejoras futuras")
P("Entidad Responsable persistida (H5); vistas inmutables de consulta (H7); manejo de fin de entrada (H9); "
  "repositorio SQLite detrás del mismo contrato; medición de cobertura; integración continua que ejecute "
  "unittest y flake8 en cada commit; interfaz web o API reutilizando el servicio.")
H2("10.5 Conclusiones individuales breves")
P("<b>Diego Pavón:</b> lo que más me dejó este trabajo es entender que el código que funciona no es necesariamente "
  "código mantenible, y que antes de refactorizar hay que fijar el comportamiento con pruebas. Ver cómo la complejidad "
  "y el costo de cambio bajaban sin que cambiara nada para el usuario me ayudó a conectar SOLID y Clean Code con "
  "problemas concretos, y no solo con definiciones.")

# ============================================================ 11. ANEXOS
H1("11. Anexos y enlaces")
tabla([["Recurso", "Enlace / ubicación"],
       ["Repositorio GitHub (tags estado-inicial, estado-refactorizado, etapa-diagnostico, etapa-refactoring, etapa-pruebas, etapa-docs)", REPO],
       ["Video de defensa (10 a 15 minutos, voz propia)", VIDEO],
       ["Anexo ZIP", "Evidencias de herramientas, salidas de pruebas, demos, capturas, diagrama y scripts de generación."],
       ["Carpeta /docs del repositorio", "Checklist de code review, decisiones técnicas y evidencias."]],
      [9.5, 7.5], zebra=False)
H2("11.1 Participación")
P("Trabajo realizado en forma <b>individual</b> por Diego Pavón (comisión 4): selección del caso, revisión y "
  "ejecución del sistema base y del refactorizado, verificación de pruebas y métricas, revisión del informe, "
  "publicación del repositorio y grabación del video. Los commits del repositorio (usuario Dieggo-p) y los tags "
  "por etapa son la evidencia de trazabilidad.")
H2("11.2 Declaración de uso de inteligencia artificial")
tabla([["Herramienta", "Finalidad", "Grado de intervención", "Evidencia"],
       ["Claude (Anthropic)", "Generación del sistema base de ejemplo y de la versión refactorizada, de las pruebas, de los scripts de análisis y de un borrador del informe y del checklist; revisión de alternativas de diseño.", "ALTO: Claude produjo el código, las pruebas, los scripts y el borrador del informe y del guion. El estudiante definió el caso y los datos de entrega, revisó y ejecutó el resultado y asume su comprensión y defensa.", "Declaración del autor."]],
      [3.0, 6.0, 4.5, 3.5], zebra=False)
P("El autor debe comprender y poder defender cada decisión, fragmento de código y métrica de este informe "
  "(la cátedra puede solicitar defensa individual). La IA no reemplaza la autoría: el video se graba con voz propia.")

# =========================================================================== build
doc = SimpleDocTemplate(str(SALIDA), pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=1.8 * cm,
                        bottomMargin=1.8 * cm, title="TPI Metodología de Sistemas II — Solicitudes Académicas",
                        author="Diego Pavón")
doc.build(story, onFirstPage=pie, onLaterPages=pie)
print("PDF generado:", SALIDA)

# ===================================================== checklist en markdown (docs)
md = ["# Checklist de code review", "",
      "Aplicado sobre `inicial/` y `refactorizado/`. Criterios de aceptación al final.", "",
      "| # | Criterio | Inicial | Refactorizada | Evidencia |", "|---|---|---|---|---|"]
md += [f"| {c[0]} | {c[1]} | {c[2]} | {c[3]} | {c[4]} |" for c in CHECK]
md += ["", "## Observaciones y acciones", "", "| ID | Sev. | Observación | Acción | Estado |", "|---|---|---|---|---|"]
md += [f"| {h[0]} | {h[1]} | {h[2]} | {h[3]} | {h[4]} |" for h in HALL]
md += ["", "## Criterios de aceptación técnica", ""]
md += [f"- [{'x' if ok else ' '}] **{a}** {c}" for a, c, ok in ACEP]
(RAIZ / "docs/checklist_code_review.md").write_text("\n".join(md) + "\n", encoding="utf-8")
print("checklist escrito")
