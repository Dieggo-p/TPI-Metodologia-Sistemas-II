# Decisiones técnicas

| # | Decisión | Alternativas | Justificación |
|---|---|---|---|
| D1 | Python con biblioteca estándar | Java/Spring, FastAPI | Sin dependencias: cualquier integrante lo ejecuta; el foco es el diseño, no el framework. |
| D2 | Persistencia en JSON | SQLite | Formato legible y fácil de comparar antes/después. Detrás de `RepositorioSolicitudes` se puede cambiar por SQLite sin tocar el servicio (DIP). |
| D3 | Pruebas de caracterización (golden master) | Solo unitarias | Fijan el comportamiento **externo** (consola + datos persistidos) antes de tocar el código; son la red de seguridad de todo refactoring. |
| D4 | Mismo formato de `datos.json` en ambas versiones | Nuevo esquema | Compatibilidad hacia atrás: un archivo creado con la versión inicial se abre con la refactorizada. |
| D5 | Se conservan mensajes, prompts y orden de preguntas | Mejorar la UX durante el refactoring | Refactoring = no cambiar comportamiento externo. Las mejoras de UX quedan como trabajo futuro. |
| D6 | **Único cambio de comportamiento deliberado:** archivo de datos dañado | Replicar el `except:` silencioso | La versión inicial lo ignoraba y lo sobrescribía al guardar (pérdida de datos). La refactorizada informa el error y no pisa el archivo. Cubierto por `test_archivo_danado_se_informa_y_no_se_pisa`. |
| D7 | Reloj inyectable (`reloj`) | `datetime.now()` directo | Permite pruebas deterministas (DIP). |
| D8 | `RESPONSABLES` como constante de dominio | Entidad persistida | Fuera de alcance; queda como mejora futura. |
