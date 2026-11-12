# Pertenencia al SNSS y nivel de complejidad de los establecimientos de salud en Chile

**Universidad:** Universidad Andrés Bello (UNAB)  
**Programa:** Magíster en Ciencia de Datos e Inteligencia Artificial
**Asignatura:** MCDI500 — Programación para la Ciencia  
**Equipo:** Grupo 1  - mcdi500
**Año:** 2026

**Integrantes:** Brian Cerda, Kattia Espinoza, Karla Martínez y Christopher Ulloa.

## 1. Descripción del proyecto

Este proyecto estudia la distribución de los establecimientos de salud de Chile según dos características: su pertenencia al Sistema Nacional de Servicios de Salud (SNSS) y su nivel de complejidad asistencial. El trabajo utiliza un registro de establecimientos de salud y desarrolla las etapas de definición, exploración y preparación de datos correspondientes a las fases F1 y F2 de la asignatura.

El procesamiento se realiza en Python, con criterios documentados de selección de registros, normalización de categorías y generación de archivos para el análisis descriptivo y las fases posteriores.

## 2. Objetivo y pregunta de análisis

**Objetivo general:** Evaluar la asociación entre la pertenencia al SNSS y el nivel de complejidad de los establecimientos de salud vigentes con código único y ambas variables informadas.

**Pregunta de análisis:** ¿Existe asociación entre la pertenencia al SNSS y el nivel de complejidad en los establecimientos de salud vigentes con código único y con ambas variables informadas en la base?

Para abordar esta pregunta se consideran dos dimensiones principales:

| Dimensión | Variable de origen | Variable analítica | Categorías |
|---|---|---|---|
| Administrativa | `TipoPertenenciaEstabGlosa` | `pertenencia_snss` | SNSS / No SNSS |
| Asistencial | `NivelComplejidadEstabGlosa` | `complejidad` | Baja / Mediana / Alta |

Las dimensiones geográfica (macrozona) y de servicios se conservan como contexto, pero no forman parte del cruce principal de esta etapa.

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

Estas cifras describen los registros seleccionados y no establecen relaciones causales ni diferencias estadísticamente significativas. Los análisis inferenciales corresponden a las fases F3 y F4.

## 6. Estructura del proyecto

| Ruta | Contenido |
|---|---|
| `F1/Grupo1_F1_Definicion.ipynb` | Definición y desarrollo de la fase F1 |
| `F2/Grupo1_F2_Preprocesamiento.ipynb` | Preparación y procesamiento de datos de la fase F2 |
| `data/raw/` | Archivo de origen, sin modificaciones de sus valores |
| `data/processed/poblacion_analisis.csv` | Población seleccionada de 4.603 establecimientos, con códigos y etiquetas |
| `data/processed/matriz_numerica_0_1.csv` | Matriz de cinco columnas binarias, sin identificadores |
| `data/processed/clave_filas.csv` | Correspondencia entre las filas de la matriz y los establecimientos |
| `data/processed/tabla_contingencia.csv` | Tabla de frecuencias de 2 × 3 para F3 y F4 |
| `docs/` | Diccionarios, decisiones, filtros, exclusiones, perfiles y metadatos |
| `docs/diccionario_fuente.txt` | Extracción textual del diccionario de origen |
| `docs/reporte_descriptivo.html` | Perfil descriptivo del archivo de entrada |
| `docs/figuras/` | Seis gráficos del análisis |
| `src/utilidades.py` | Funciones compartidas de lectura y normalización |
| `requirements.txt` | Dependencias del entorno de ejecución |

El diccionario analítico documenta las **33 columnas** del conjunto de datos y las decisiones adoptadas para su tratamiento.

## 7. Requisitos y ejecución

El proyecto está preparado para utilizar **Python 3.13**. Las dependencias se especifican en `requirements.txt`, incluyendo Pandas, NumPy, Matplotlib y componentes para ejecutar notebooks.

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

### 7.2. Orden de ejecución

1. Reiniciar el kernel y ejecutar todas las celdas de `F1/Grupo1_F1_Definicion.ipynb`.
2. Reiniciar el kernel y ejecutar todas las celdas de `F2/Grupo1_F2_Preprocesamiento.ipynb`.

Las rutas se resuelven tanto desde la raíz del proyecto como desde las carpetas `F1/` y `F2/`.

El CSV de entrada utiliza separador `;` y codificación UTF-8. Los CSV de salida se generan con separador coma y codificación UTF-8 con BOM.

## 8. Alcance y limitaciones

El estudio se limita al análisis descriptivo de la pertenencia al SNSS y el nivel de complejidad. En estas fases no se desarrollan análisis territoriales, de servicios de urgencia, de calidad asistencial ni de causalidad. La inferencia estadística se reserva para F3 y F4.

Aunque el archivo de origen comprende 5.837 registros, contiene establecimientos cerrados y categorías que no cumplen los criterios de selección. Por ese motivo, el denominador empleado en los resultados principales es de 4.603 establecimientos.

La fecha exacta de descarga, la fecha de corte del registro, la licencia específica de uso de los datos, el respaldo del mapa conceptual previo y la identificación de contribuciones individuales en Git quedan sujetos a la documentación y verificación del grupo.

## 9. Documentación de respaldo

La carpeta `docs/` reúne los diccionarios, criterios de transformación, tablas de filtros, registros de exclusión y productos descriptivos utilizados en el proyecto. Estos archivos permiten consultar las decisiones metodológicas y reconstruir la preparación de los datos.

---

**Grupo 1 · MCDI500 · Universidad Andrés Bello · 2026**
