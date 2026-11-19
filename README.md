# Gestión de Solicitudes Académicas — TPI Metodología de Sistemas II (UTN TUP)

Módulo de consola para registrar y gestionar solicitudes académicas de estudiantes
(constancias, equivalencias, bajas). El repositorio contiene **dos versiones del mismo sistema**
para demostrar una evolución profesional: calidad interna, deuda técnica, refactoring seguro y code review.

| Carpeta | Contenido |
|---|---|
| `inicial/` | Versión base (`app.py`, un solo archivo) con deuda técnica real y diagnosticable. Tag `estado-inicial`. |
| `refactorizado/` | Misma funcionalidad, rediseñada en capas (dominio, servicio, repositorio, filtros, reportes, CLI). Tag `estado-refactorizado`. |
| `tests/` | Pruebas de caracterización (golden master, corren contra **ambas** versiones) y pruebas unitarias/contrato de la refactorizada. |
| `docs/` | Checklist de code review, decisiones técnicas, evidencias (métricas, salidas de pruebas, demos, capturas) |
| `scripts/` | `generar_informe.py`: genera el informe PDF y el checklist a partir del repositorio real. |

## Funcionalidades
1. Registrar solicitud (tipo, prioridad, descripción; alta automática del estudiante; las **bajas** se fuerzan a prioridad ALTA).
2. Cambiar estado: `PENDIENTE → EN_PROCESO → RESUELTA`, o `→ RECHAZADA`. No se puede pasar a `EN_PROCESO` sin responsable.
3. Asignar responsable (Alumnado, Bedelia, Secretaria Academica); no se puede en solicitudes cerradas.
4. Buscar / filtrar por estado, tipo, prioridad o legajo.
5. Reporte: totales por estado, tipo, prioridad y solicitudes sin responsable.

Persistencia en `datos.json` (se crea en el directorio desde donde se ejecuta). **Todos los datos son sintéticos.**

## Tecnologías
Python 3.10+ (solo biblioteca estándar: `json`, `dataclasses`, `enum`, `unittest`). Herramientas de análisis: `radon`, `flake8`.

## Uso
```bash
python inicial/app.py            # versión inicial
python refactorizado/main.py     # versión refactorizada (mismo comportamiento)
```

## Pruebas
```bash
python -m unittest discover -s tests -v        # 47 pruebas (Python 3.10+)
python tests/generar_golden.py                  # (solo histórico) regenera la referencia con la versión inicial
```
Análisis estático:
```bash
pip install radon flake8
radon cc -s -a inicial/app.py refactorizado/
radon mi -s inicial/app.py refactorizado/
flake8 --max-line-length=100 inicial/ refactorizado/
```

## Tags de entrega
`estado-inicial`, `estado-refactorizado`, `etapa-diagnostico`, `etapa-refactoring`, `etapa-pruebas`, `etapa-docs`


## Autor
Diego Pavón — Comisión 4 — entrega individual.

## Declaración de uso de IA
Ver sección "Uso de inteligencia artificial" del informe PDF y la carpeta `docs/evidencias/` / anexo ZIP.
