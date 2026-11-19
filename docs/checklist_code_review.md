# Checklist de code review

Aplicado sobre `inicial/` y `refactorizado/`. Criterios de aceptación al final.

| # | Criterio | Inicial | Refactorizada | Evidencia |
|---|---|---|---|---|
| C1 | Cada módulo/función tiene una única responsabilidad (SRP) | No | Sí | secciones 5 y 6 |
| C2 | Nombres expresivos, sin variables de una letra | No | Sí | H1 corregido |
| C3 | Funciones de hasta 20 líneas | No (6 la superan) | Sí (máx. 19) | radon cc |
| C4 | Sin código duplicado relevante | No | Sí | R5, R7 |
| C5 | Sin números ni cadenas mágicas | No | Sí | R4 |
| C6 | Errores tratados de forma explícita (sin except desnudo) | No | Sí | R6 |
| C7 | Sin estado global mutable | No | Sí | R6 |
| C8 | Dependencias invertidas y componentes testeables | No | Sí | 21 pruebas unitarias |
| C9 | Complejidad ciclomática por función <= 10 | No (4 la superan) | Sí (máx. 4) | radon cc |
| C10 | Análisis estático limpio (flake8) | No (4 avisos) | Sí (0) | flake8 |
| C11 | Pruebas automatizadas que protegen el comportamiento | No | Sí (47) | sección 8 |
| C12 | Documentación (README, docstrings, decisiones técnicas) | No | Sí | docs/ |
| C13 | El comportamiento externo se conserva | — | Sí (13/13) | golden master; ver D6 |
| C14 | Datos sintéticos, sin datos personales reales | Sí | Sí | consigna sección 10 |
| C15 | Trazabilidad Git (tags por etapa y commits claros) | — | Sí | tags del repositorio |

## Observaciones y acciones

| ID | Sev. | Observación | Acción | Estado |
|---|---|---|---|---|
| H1 | Menor | cli.py usa la variable «s» en _registrar, _cambiar_estado, _asignar_responsable y _buscar: contradice C2. | Renombrar a «solicitud» (y extraer «nombre» en _buscar). | Corregido |
| H2 | Menor | parsear_enum no tenía tipos genéricos: el retorno perdía información para el lector y el IDE. | TypeVar TEnum y firma type[TEnum] -> TEnum. | Corregido |
| H3 | Media | Interfaz._cambiar_estado llama a servicio.obtener() solo para validar el ID antes de pedir el estado. | Aceptado: preserva el orden de preguntas de la versión inicial (decisión D5). Mejora futura: validar todo al final. | Aceptado |
| H4 | Menor | validar_asignable y asignar_responsable repiten la verificación de solicitud cerrada. | Aceptado: el servicio protege su invariante aunque se lo llame sin pasar por la interfaz. | Aceptado |
| H5 | Media | RESPONSABLES es una constante de dominio: no se pueden administrar áreas. | Mejora futura: entidad Responsable persistida y repositorio propio. | Mejora futura |
| H6 | Menor | _leer_id (presentación) lanza ErrorDeValidacion, un error del dominio. | Aceptado por simplicidad; alternativa: error de presentación propio. | Aceptado |
| H7 | Media | Solicitud es mutable y listar() devuelve una copia superficial: un cliente podría mutar objetos. | Mejora futura: vistas inmutables (DTO) para consulta. | Mejora futura |
| H8 | Mayor | El manejo de archivo dañado cambia el comportamiento respecto de la versión inicial. | Aceptado y documentado (D6, sección 8.4); cubierto por prueba. Es una mejora, no una regresión. | Aceptado |
| H9 | Menor | Si la entrada estándar se cierra (EOF) el programa termina con traceback, en ambas versiones. | Fuera del alcance de un refactoring; queda como mejora futura. | Mejora futura |

## Criterios de aceptación técnica

- [x] **A1** Suite completa en verde (47/47)
- [x] **A2** Sin diferencias de salida ni de datos entre versiones en 13 escenarios
- [x] **A3** flake8 sin avisos en el código refactorizado
- [x] **A4** Complejidad ciclomática <= 10 en todas las funciones
- [x] **A5** Ninguna función de más de 20 líneas
- [x] **A6** Sin cambios de comportamiento salvo los documentados (D6)
- [x] **A7** Observaciones de severidad mayor cerradas o justificadas por escrito
