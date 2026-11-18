# Pertenencia al SNSS y nivel de complejidad de los establecimientos de salud en Chile

**Universidad:** Universidad Andrés Bello (UNAB)  
**Programa:** Magíster en Ciencia de Datos e Inteligencia Artificial
**Asignatura:** MCDI500 — Programación para la Ciencia de Datos  
**Equipo:** Grupo 1  
**Docente:** Omar Salinas  
**Año:** 2026

**Integrantes:** Brian Cerda, Kattia Espinoza, Karla Martínez y Christopher Ulloa.

## 1. Descripción del proyecto

Este proyecto estudia la distribución de los establecimientos de salud de Chile según dos características: su pertenencia al Sistema Nacional de Servicios de Salud (SNSS) y su nivel de complejidad asistencial. El trabajo utiliza un registro de establecimientos de salud y desarrolla tres fases: la definición del problema y del entorno (F1), la exploración y preparación de los datos (F2) y la reorganización del pipeline en un núcleo algorítmico orientado a objetos, con su costo medido (F3).

El procesamiento se realiza en Python, con criterios documentados de selección de registros, normalización de categorías y generación de archivos para el análisis descriptivo.

La fuente original de los datos trabajados en este proyecto se encuentran en: https://datos.gob.cl/dataset/establecimientos-de-salud-vigentes/resource/2c44d782-3365-44e3-aefb-2c8b8363a1bc 
La fuente original se actualiza de forma periodica (sin versionamiento). Para este trabajo se utilizó la base actualizada hasta el 06 de noviembre del 2026.

## 2. Objetivo y pregunta de análisis

**Objetivo general:** Evaluar la asociación entre la pertenencia al SNSS y el nivel de complejidad de los establecimientos de salud vigentes con código único y ambas variables informadas.

**Pregunta de análisis:** ¿Existe asociación entre la pertenencia al SNSS y el nivel de complejidad en los establecimientos de salud vigentes con código único y con ambas variables informadas en la base?

Para abordar esta pregunta se consideran dos dimensiones principales:

| Dimensión | Variable de origen | Variable analítica | Categorías |
|---|---|---|---|
| Administrativa | `TipoPertenenciaEstabGlosa` | `pertenencia_snss` | SNSS / No SNSS |
| Asistencial | `NivelComplejidadEstabGlosa` | `complejidad` | Baja / Mediana / Alta |

La unidad de análisis es el establecimiento identificado por su código vigente. Las demás columnas del registro (territoriales, de urgencia, de dirección y de jerarquía institucional) se documentan en el diccionario analítico, pero no forman parte del cruce principal.

### Estado de las fases

| Fase | Contenido | Estado |
|---|---|---|
| F1 | Definición del problema, objetivos, entorno reproducible y diccionario analítico | Desarrollada |
| F2 | Obtención, exploración, limpieza, transformación y validación del dataset | Desarrollada |
| F3 | Núcleo algorítmico: el pipeline de F2 encapsulado en clases, verificado contra F2 y con mediciones de tiempo y memoria | Desarrollada |

La evaluación estadística de la asociación no forma parte de esta entrega.

## 3. Datos utilizados

El archivo de entrada es `establecimientos_20261103.csv`, que contiene **5.837 registros** de establecimientos de salud. Se utiliza el diccionario de datos del registro para interpretar sus variables y categorías.

| Característica | Descripción |
|---|---|
| Archivo de entrada | `establecimientos_20261103.csv` |
| Registros originales | 5.837 |
| Formato | CSV |
| Separador | Punto y coma (`;`) |
| Codificación | UTF-8 |
| Diccionario de origen | `docs/diccionario_fuente.txt` |

La fecha **03-11-2026** proviene del nombre del archivo y no constituye, por sí sola, evidencia de la fecha exacta de descarga o del corte de actualización del registro.

## 4. Metodología de preparación

### 4.1. Selección de la población de análisis

Se incluyen establecimientos con estado de funcionamiento vigente, código único, pertenencia al SNSS clasificable y nivel de complejidad registrado como bajo, mediano o alto.

Los filtros documentados en el proyecto producen las siguientes exclusiones:

| Motivo de exclusión | Registros excluidos |
|---|---:|
| Establecimientos cerrados | 431 |
| Pertenencia clasificada como «No Aplica» | 41 |
| Nivel de complejidad sin dato | 59 |
| Nivel de complejidad clasificado como «No Aplica» | 703 |
| **Total de exclusiones** | **1.234** |

De los **5.837 registros originales**, se excluyen **1.234** y se obtiene una población de **4.603 establecimientos**. La secuencia y el detalle de los filtros se encuentran en `docs/tabla_filtros.csv`.

La población de análisis corresponde, por tanto, a **4.603 establecimientos vigentes con pertenencia y complejidad aplicables y registradas**. Los resultados no deben interpretarse como representativos de todos los registros del archivo original.

### 4.2. Limpieza y transformación

La preparación comprende la lectura de los datos como texto para conservar códigos y categorías, la normalización de espacios y mayúsculas, la clasificación de las variables seleccionadas y la construcción de archivos para el análisis.

No se imputan los valores de complejidad ausentes ni las categorías «No Aplica». Los indicadores de la matriz numérica se representan mediante valores binarios (0 y 1), por lo que no se aplica un escalador adicional.

## 5. Resultados descriptivos

La población seleccionada se distribuye de la siguiente manera:

| Pertenencia | Establecimientos | Complejidad baja | Complejidad mediana | Complejidad alta |
|---|---:|---:|---:|---:|
| SNSS | 3.065 | 91,7 % | 6,0 % | 2,3 % |
| No SNSS | 1.538 | 29,9 % | 66,5 % | 3,6 % |
| **Total** | **4.603** | | | |

Los porcentajes se calculan **por fila**, utilizando como denominador el total de establecimientos de cada grupo de pertenencia. De este modo, reflejan la distribución de los niveles de complejidad *dentro* del SNSS y *dentro* del grupo no perteneciente al SNSS.

En el grupo SNSS predomina la baja complejidad (91,7 %), mientras que en el grupo no SNSS predomina la mediana complejidad (66,5 %). La fase F2 también presenta porcentajes por columna como información complementaria.

Estas cifras describen los registros seleccionados y no establecen relaciones causales ni diferencias estadísticamente significativas. La evaluación estadística de la asociación no forma parte de esta entrega.

## 6. Organización del proyecto

```
grupo1-proyecto-mcdi500/
├── F1/                      notebook de la fase 1 (definición y entorno)
├── F2/                      notebook de la fase 2 (preprocesamiento)
├── F3/                      notebook de la fase 3 (núcleo algorítmico, eficiencia y POO)
├── src/                     código del proyecto: los notebooks lo importan, no lo copian
├── tests/                   pruebas de casos normales, límite y excepciones
├── data/raw/                archivo de origen, sin modificaciones
├── data/processed/          salidas de F2 y, en f3/, salidas de F3
├── docs/                    documentación de F1 y F2 y, en f3/, la de F3
├── ejecutar_proyecto.py     ejecuta F1, F2 y F3 en orden
├── requirements.txt         dependencias con versión fija
└── README.md
```

### 6.1. Notebooks

| Ruta | Contenido |
|---|---|
| `F1/Grupo1_F1_Definicion.ipynb` | Definición del problema, entorno y diccionario analítico |
| `F2/Grupo1_F2_Preprocesamiento.ipynb` | Exploración, limpieza, transformación y validación del dataset |
| `F3/Grupo1_S2_F3_NucleoAlgoritmico_Eficiencia_POO.ipynb` | Núcleo algorítmico: clases, patrones, verificación contra F2, pruebas y mediciones |

Cada notebook se entrega ejecutado y con su exportación `.html` en la misma carpeta.

### 6.2. Código (`src/`)

Cada módulo tiene una sola responsabilidad. El notebook de F3 importa todo desde aquí.

| Módulo | Responsabilidad |
|---|---|
| `src/utilidades.py` | Funciones compartidas por las tres fases: normalizar texto y leer el CSV |
| `src/configuracion.py` | Reglas F01–F08, mapeos y columnas, declarados como datos |
| `src/carga.py` | Lectura del archivo y verificación de su huella y su esquema |
| `src/funciones.py` | Operaciones sin estado del pipeline (fila de origen, normalización, selección) |
| `src/transformadores.py` | Clase base `Transformador`, adaptador `PasoFuncion`, clase intermedia `Filtro` y las clases que aprenden algo de los datos |
| `src/conflictos.py` | Tres implementaciones de la detección de códigos repetidos, comparadas en la medición |
| `src/pipeline.py` | `Pipeline` y `PipelineObservable`, que encadenan los pasos y notifican a los observadores |
| `src/observadores.py` | Bitácora de filtros, registro de exclusiones y tiempos por paso |
| `src/fabrica.py` | Construcción de filtros y pipelines desde la configuración |
| `src/preprocesador.py` | `PreprocesadorRegistro`: el preprocesamiento completo en una llamada |
| `src/descripcion.py` | Perfil, tabla de contingencia, retención y correspondencias |
| `src/estructura.py` | Funciones recursivas para la jerarquía de clases y la configuración anidada |
| `src/medicion.py` | Medición de tiempo (`timeit`) y memoria (`tracemalloc`) |
| `src/referencia_f2.py` | El flujo de F2 conservado como línea base para verificar y medir |

### 6.3. Pruebas (`tests/`)

`tests/test_nucleo.py` contiene 28 pruebas con tablas pequeñas construidas a mano: 11 casos normales, 7 casos límite y 10 excepciones.

### 6.4. Datos y documentación

| Ruta | Contenido |
|---|---|
| `data/raw/` | Archivo de origen, sin modificaciones de sus valores |
| `data/processed/poblacion_analisis.csv` | Población seleccionada de 4.603 establecimientos, con códigos y etiquetas (F2) |
| `data/processed/matriz_numerica_0_1.csv` | Matriz de cinco columnas binarias, sin identificadores (F2) |
| `data/processed/clave_filas.csv` | Correspondencia entre las filas de la matriz y los establecimientos (F2) |
| `data/processed/tabla_contingencia.csv` | Tabla de frecuencias de 2 × 3 (F2) |
| `data/processed/f3/` | Resultados de F3: población, matriz, clave de filas, contingencia y porcentajes, idénticos a los de F2 |
| `docs/` | Diccionarios, decisiones, filtros, exclusiones, perfiles y metadatos de F1 y F2 |
| `docs/diccionario_fuente.txt` | Extracción textual del diccionario de origen |
| `docs/reporte_descriptivo.html` | Perfil descriptivo del archivo de entrada |
| `docs/figuras/` | Seis gráficos del análisis de F2 |
| `docs/f3/` | Bitácora de filtros, exclusiones, parámetros aprendidos, bitácora de decisiones de diseño, arquitectura y mediciones de F3 |
| `docs/f3/figuras/` | Dos gráficos de la medición de eficiencia |

El diccionario analítico documenta las **33 columnas** del conjunto de datos y las decisiones adoptadas para su tratamiento.

## 7. Dependencias y ejecución

El proyecto está preparado para utilizar **Python 3.13**. Las dependencias se especifican en `requirements.txt`, todas con versión fija:

| Biblioteca | Versión | Uso |
|---|---|---|
| pandas | 3.0.5 | Lectura, transformación y tablas |
| NumPy | 2.5.2 | Operaciones numéricas |
| Matplotlib | 3.11.1 | Gráficos |
| nbformat, nbclient, ipykernel | 5.11.1, 0.11.0, 7.4.0 | Ejecución de los notebooks |

Ese archivo es la fuente de verdad del entorno: el notebook F1 lo compara con el entorno activo y se detiene si encuentra diferencias, sin modificarlo. La fase F3 no agrega dependencias: además de las anteriores usa solo la biblioteca estándar (`timeit`, `tracemalloc`, `unittest`, `inspect`).

### 7.1. Preparación del entorno

Descomprimir o clonar el proyecto conservando la estructura de carpetas. Desde la raíz del proyecto, crear el entorno virtual:

```bash
python -m venv .venv
```

Activarlo según el sistema operativo.

**Windows (PowerShell):**

```powershell
.venv\Scripts\Activate.ps1
```

**Linux o macOS:**

```bash
source .venv/bin/activate
```

Instalar las dependencias:

```bash
python -m pip install -r requirements.txt
```

Los notebooks pueden abrirse en Visual Studio Code o Jupyter. Si se necesita JupyterLab, se puede instalar adicionalmente:

```bash
python -m pip install jupyterlab
```

### 7.2. Ejecución del proyecto completo

Los notebooks se ejecutan siempre en este orden, porque cada fase lee lo que guardó la anterior: **F1 → F2 → F3**.

**Opción A: todo el proyecto con un comando.** Con el entorno virtual activo, desde la raíz:

```bash
python ejecutar_proyecto.py
```

El script ejecuta los tres notebooks desde un kernel limpio, guarda sus salidas y se detiene con un mensaje si alguno falla.

**Opción B: notebook por notebook** (Visual Studio Code o Jupyter, con el kernel de `.venv`):

1. Reiniciar el kernel y ejecutar todas las celdas de `F1/Grupo1_F1_Definicion.ipynb`.
2. Reiniciar el kernel y ejecutar todas las celdas de `F2/Grupo1_F2_Preprocesamiento.ipynb`.
3. Reiniciar el kernel y ejecutar todas las celdas de `F3/Grupo1_S2_F3_NucleoAlgoritmico_Eficiencia_POO.ipynb`.

Las rutas se resuelven tanto desde la raíz del proyecto como desde las carpetas `F1/`, `F2/` y `F3/`.

El CSV de entrada utiliza separador `;` y codificación UTF-8. Los CSV de salida se generan con separador coma y codificación UTF-8 con BOM.

### 7.3. Ejecución del notebook de la Fase 3

El notebook `F3/Grupo1_S2_F3_NucleoAlgoritmico_Eficiencia_POO.ipynb` necesita que F1 y F2 se hayan ejecutado antes, porque lee `docs/proyecto.json`, `docs/metadatos_f1.json` y las salidas de F2 con las que se compara.

1. Activar el entorno virtual e instalar las dependencias (sección 7.1).
2. Abrir el notebook y seleccionar el kernel de `.venv`.
3. Ejecutar **Kernel → Restart Kernel and Run All Cells**.

El notebook tarda menos de un minuto. Al terminar deja sus resultados en `data/processed/f3/` y `docs/f3/`, sin modificar los archivos de F2, y se detiene con un error si alguna salida difiere de las de F2. Los tiempos que muestra la sección 15 dependen del equipo; las razones entre versiones se mantienen.

### 7.4. Ejecución de las pruebas

Desde la raíz del proyecto, con el entorno virtual activo:

```bash
python -m unittest -v
```

El comando descubre y ejecuta las 28 pruebas de `tests/`. Las mismas pruebas se ejecutan dentro del notebook de F3 (sección 13).

## 8. Fase 3: núcleo algorítmico

La fase F3 no cambia los datos ni las reglas: reorganiza el pipeline de F2 en módulos y clases, y mide su costo.

| Aspecto | Cómo se resuelve |
|---|---|
| Código en una sola versión | La lógica vive en `src/`; el notebook la importa y la muestra sin copiarla |
| Programación orientada a objetos | Se usan clases solo en los componentes que recuerdan algo entre llamadas: clase base `Transformador`, clase intermedia `Filtro` y ocho clases hijas. Encapsulamiento con atributos internos y propiedades de solo lectura; el `Pipeline` recorre los pasos sin preguntar su tipo |
| Patrones de diseño | *Observer* para la bitácora, las exclusiones y los tiempos; *Factory* para construir el pipeline desde las reglas F01–F08 declaradas en la configuración |
| Pipeline en una llamada | `PreprocesadorRegistro(configuracion).ajustar_transformar(datos)` |
| Verificación | Las nueve salidas de F2 se reproducen de forma idéntica (secciones 11 y 18 del notebook) |
| Validación | Caso normal sobre el registro real y 28 pruebas de casos normales, límite y excepciones (sección 13 y carpeta `tests/`) |
| Recursividad | Recorrido de la jerarquía de clases y aplanado de la configuración anidada (sección 14) |
| Eficiencia | Tres implementaciones de una operación del pipeline comparadas con `timeit` y `tracemalloc`, curva de crecimiento, tiempo por paso y costo del pipeline antes y después, con dos gráficos (sección 15) |
| Decisiones | Bitácora con cada decisión, su motivo, la alternativa descartada y su efecto (sección 16 y `docs/f3/bitacora_decisiones_f3.csv`) |

Ejemplo de uso del núcleo desde cualquier script o notebook ubicado en la raíz:

```python
from src.carga import cargar_registro
from src.configuracion import COLUMNAS_NECESARIAS, crear_configuracion
from src.preprocesador import PreprocesadorRegistro

datos = cargar_registro("data/raw/establecimientos_20261103.csv", COLUMNAS_NECESARIAS)
resultado = PreprocesadorRegistro(crear_configuracion(datos.columns)).ajustar_transformar(datos)
poblacion, matriz = resultado["poblacion"], resultado["matriz"]
```

Las mediciones y sus decisiones quedan visibles en el notebook y se guardan en `docs/f3/mediciones_resumen_f3.csv`. Los tiempos absolutos dependen del equipo; las decisiones se apoyan en las razones entre versiones.

## 9. Alcance y limitaciones

El estudio se limita al análisis descriptivo de la pertenencia al SNSS y el nivel de complejidad. En estas fases no se desarrollan análisis territoriales, de servicios de urgencia, de calidad asistencial ni de causalidad, y la inferencia estadística no forma parte de esta entrega.

Aunque el archivo de origen comprende 5.837 registros, contiene establecimientos cerrados y categorías que no cumplen los criterios de selección. Por ese motivo, el denominador empleado en los resultados principales es de 4.603 establecimientos.

La disponibilidad de la complejidad no es homogénea: se retuvo el 99,00 % de los establecimientos SNSS vigentes, pero solo el 67,78 % de los No SNSS (`docs/retencion_por_grupo.csv`). Las conclusiones se limitan a la población con complejidad informada.

La fecha exacta de descarga, la fecha de corte del registro y la licencia específica de uso de los datos no están acreditadas en los archivos disponibles.

## 10. Control de versiones

Las fases 1 y 2 se organizaron en ramas temáticas (`parte1-datos`, `parte2-definicion`, `parte3-limpieza`, `parte4-descriptivo`, `parte5-integracion`, `limpieza-final` y `actualiza-limpieza`) integradas en `main` mediante *pull requests*. La Fase 3 sigue el mismo flujo: una rama por componente, integrada en `main` mediante un *pull request* revisado por otro integrante. El historial y los aportes por integrante pueden consultarse con:

```bash
git log --graph --oneline --all
git shortlog -sne
```

## 11. Documentación de respaldo

La carpeta `docs/` reúne los diccionarios, criterios de transformación, tablas de filtros, registros de exclusión y productos descriptivos utilizados en el proyecto. Estos archivos permiten consultar las decisiones metodológicas y reconstruir la preparación de los datos. La subcarpeta `docs/f3/` reúne la documentación de la Fase 3: arquitectura, bitácora de decisiones y mediciones.

---

**Grupo 1 · MCDI500 · Universidad Andrés Bello · 2026**
