# Registro de cambios · Grupo 1 · MCDI500

Cada entrada indica la fecha, la descripción del cambio, los commits que lo contienen (verificables con `git show <commit>`), el *pull request* (PR) con que se integró a `main` y la justificación técnica. Orden cronológico. Fechas de 2026.

| Fecha | Descripción | Commits (PR) | Justificación técnica |
|---|---|---|---|
| 11-11 | Estructura inicial del repositorio y README con el grupo | `d50a53f`, `b1ce9e3` (#1, #3) | Punto de partida común para los cuatro integrantes |
| 11-11 | Datos procesados y notebook F2 de preprocesamiento | `704b251` (#4) | Construir la población con reglas auditables |
| 11-11 | Versión exploratoria del análisis (descartada después) | `b19c038`, `5fff822` (#5, #7) | Explorar el registro antes de fijar el alcance |
| 11-11 | Notebook F1 de definición del problema y del entorno | `5e0af12` (#6) | Fijar pregunta, objetivos y dependencias |
| 11-11 | Integración de F1 y F2; retiro de archivos de la versión exploratoria | `0f16fd2`, `0e97a09`, `f93a016` (#8–#10) | Dejar en `main` solo lo que usa el proyecto |
| 15-11 | F1 deja de reescribir `requirements.txt` y lo compara con el entorno | `aae2e4d` (#11) | Retroalimentación S1: el archivo de dependencias debe ser la fuente de verdad |
| 15-11 | F1 y F2 ubican la prueba de independencia en F4 | `07cd782` (#12) | Retroalimentación S1: articular F3 como núcleo algorítmico |
| 16-11 | Jerarquía de clases, pipeline, Observer y Factory en `src/` | `466a5cf`, `fe5ce54` (#13, #14) | Separar responsabilidades y probar cada paso por separado |
| 16-11 | Pruebas automatizadas y mediciones con `timeit` y `tracemalloc` | `9347558` (#15) | Demostrar equivalencia con F2 y justificar la eficiencia |
| 16-11 | Notebook F3 ejecutado, salidas y README | `fc6713e` (#16) | Entrega de la Fase 3 |
| 17-11 | Archivo de origen excluido en `.gitignore`; nombres normalizados | `49aaa16`, `c95a912`, `ddcb4ab` (#17, #18) | Formativa 3: el archivo contiene teléfonos y el repositorio es público |
| 17-11 | Fuente de los datos y vínculo con el foro de la Semana 1 | `8a5ed95`, `78f2f4c`, `8fb222a`, `6a6d4a2` (#19, #20, #22, #23) | Formativa 3: trazabilidad de la fuente y de la retroalimentación |
| 17-11 | `verificar_fuente.py` comprueba tamaño y huella SHA-256 | `9d5d937`, `9fcdab2`, `a1029c7` (#24–#26) | Garantizar que el archivo descargado es el mismo que se analizó |
| 17-11 | Controles de F1 actualizados | `d6e3c00` (#21) | Coherencia entre el entorno declarado y el activo |
| 18-11 | Retiro de archivos del sistema (`.DS_Store`) | `5b014fd` (#27) | Repositorio limpio |
| 20-11 | SciPy fijado en `requirements.txt`; F1 nombra la biblioteca que falta | `e12ea16` (#28) | Retroalimentación S2: la prueba de independencia requiere SciPy |
| 20-11 | Módulo `src/comunicacion.py` y sus pruebas | `3caee16` (#29) | Funciones de la F4 importables y probadas |
| 20-11 | Tablas de exclusiones, prueba de independencia, residuos ajustados y sus figuras | `4b4f938`, `e471cd3`, `e8d849e`, `d92d5cf` (#30) | Retroalimentación S2: esperadas, V de Cramér y residuos |
| 20-11 | Notebook F4, figuras, hallazgos, metadatos y `ejecutar_proyecto.py` | `d9418eb`, `b7f1464`, `9d9d9e1`, `fdab63c`, `bcb9f7f`, `c8fd698` (#31) | Comunicar con una sola fuente de cifras y ejecutar todo desde la terminal |
| 22-11 | Restauración de 56 archivos borrados por error en el PR #29 | `c59a9fc`, `3457ea6`, `77e5c8c` (#32) | `main` no se ejecutaba desde un clon limpio |
| 22-11 | `Transformador` como clase abstracta; referencia en datos.gob.cl | `c15066f`, `5c518ca`, `6548434` (#33) | Retroalimentación S2: contrato explícito y fuente verificable |
| 22-11 | Comparación dentro de los 5 tipos compartidos (562 establecimientos) y nueva Figura 7 | `a1c3ff0`, `8b37937`, `b9bbafc` (#34) | Retroalimentación S1 y S2: controlar el tipo de establecimiento |
| 22-11 | README con las correcciones de la Fase 4 | `e0e4c56` (#35) | Coherencia entre repositorio e informe |
| 22-11 | `changelog.md` y `.mailmap` | este commit | Retroalimentación S2: trazabilidad de mejoras e identidades unificadas |

S1 y S2: retroalimentación de las Sumativas 1 y 2.
