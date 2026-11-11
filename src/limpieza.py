"""Limpieza: texto, categorías, tipos, anomalías e imputación categórica por regla."""

import re
import unicodedata

import numpy as np
import pandas as pd

from src import ProyectoError
from src.geo import haversine_km

COLUMNAS_FECHA = ["FechaInicioFuncionamientoEstab", "FechaIncorporacion", "FechaCierre"]
FORMATO_FECHA = "%d-%m-%Y"  # formato declarado en el diccionario oficial
ETIQUETA_SIN_DATO = "Sin dato"

# Variantes de escritura confirmadas en la exploración. Se declaran una a una: una
# corrección automática podría fundir categorías distintas sin que nadie lo advierta.
MAPEOS_CATEGORIAS = {
    "TipoPertenenciaEstabGlosa": {
        "No perteneciente al Sistema Nacional de Servicios de Salud":
            "No Perteneciente al Sistema Nacional de Servicios de Salud"},
    "TieneServicioUrgencia": {"No": "NO"},
    "EstadoFuncionamiento": {"Vigente en operación habitual": "Vigente en Operación Habitual"},
    "TipoAtencionEstabGlosa": {"Atención Abierta-Ambu": "Atención Abierta-Ambulatoria"},
    "DependenciaAdministrativa": {"Gendamería": "Gendarmería"},
    "TipoSistemaSaludGlosa": {"Gendamería": "Gendarmería"},
    "TipoEstablecimientoGlosa": {"Centro Terapeútico": "Centro Terapéutico"},
    "TipoUrgencia": {"Urgencia ambulatoria privada": "Urgencia Ambulatoria Privada"},
}

PSEUDONULOS = {"-", "--", ".", "s/i", "si dato", "sin dato", "n/a", "na", "null", "none", "nan"}


def normalizar_texto(serie):
    """Quita espacios en los extremos y colapsa los repetidos; respeta los nulos."""
    if not pd.api.types.is_string_dtype(serie):
        raise ProyectoError(f"'{serie.name}' no es una columna de texto.")
    return serie.str.strip().str.replace(r"\s+", " ", regex=True)


def _clave_comparacion(texto):
    """Reduce un texto a minúsculas sin tildes ni signos para comparar variantes."""
    sin_tildes = unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", " ", sin_tildes.lower()).strip()


def detectar_variantes(datos, columnas):
    """Encuentra valores que solo difieren en mayúsculas, tildes o signos."""
    filas = []
    for columna in columnas:
        conteo = datos[columna].value_counts()
        claves = pd.Series({v: _clave_comparacion(v) for v in conteo.index}, dtype=object)
        for _, grupo in claves.groupby(claves):
            if len(grupo) > 1:
                filas.append({"variable": columna, "variantes": " | ".join(grupo.index),
                              "conteos": " | ".join(str(int(conteo[v])) for v in grupo.index)})
    return pd.DataFrame(filas, columns=["variable", "variantes", "conteos"])


def detectar_pseudonulos(datos):
    """Cuenta valores que parecen ausencia escrita como texto en lugar de celda vacía."""
    filas = []
    for columna in datos.columns:
        minusculas = datos[columna].dropna().str.strip().str.lower()
        for valor, cantidad in minusculas[minusculas.isin(PSEUDONULOS)].value_counts().items():
            filas.append({"variable": columna, "valor": valor, "cantidad": int(cantidad)})
    return pd.DataFrame(filas, columns=["variable", "valor", "cantidad"])


def aplicar_mapeos(datos, mapeos=None):
    """Aplica los reemplazos declarados y devuelve ``(copia, tabla de cambios)``."""
    mapeos = MAPEOS_CATEGORIAS if mapeos is None else mapeos
    salida = datos.copy()
    cambios = []
    for columna, mapa in mapeos.items():
        if columna not in salida.columns:
            raise ProyectoError(f"Mapeo sobre una columna inexistente: {columna}")
        for original, canonico in mapa.items():
            n = int((salida[columna] == original).sum())
            salida[columna] = salida[columna].replace(original, canonico)
            cambios.append({"variable": columna, "original": original,
                            "canonico": canonico, "filas": n})
    return salida, pd.DataFrame(cambios)


def _fecha_chilena(fecha):
    """Muestra una fecha como día-mes-año; una fecha faltante queda vacía."""
    return fecha.strftime("%d-%m-%Y") if pd.notna(fecha) else None


def convertir_fechas(datos, columnas=None, formato=FORMATO_FECHA):
    """Convierte fechas con formato explícito y devuelve ``(copia, tabla de resultados)``.

    El formato explícito evita que pandas intercambie día y mes. Lo que no se pueda
    convertir queda como ``NaT`` y se informa en ``no_convertidas``.
    """
    columnas = COLUMNAS_FECHA if columnas is None else columnas
    salida = datos.copy()
    filas = []
    for columna in columnas:
        original = salida[columna]
        salida[columna] = pd.to_datetime(original, format=formato, errors="coerce")
        filas.append({"variable": columna, "con_valor": int(original.notna().sum()),
                      "no_convertidas": int((original.notna() & salida[columna].isna()).sum()),
                      "minima": _fecha_chilena(salida[columna].min()), "maxima": _fecha_chilena(salida[columna].max())})
    return salida, pd.DataFrame(filas)


def convertir_numericas(datos, columnas):
    """Convierte a ``float`` admitiendo coma decimal; devuelve ``(copia, no_convertidos)``."""
    salida = datos.copy()
    no_convertidos = {}
    for columna in columnas:
        original = salida[columna]
        salida[columna] = pd.to_numeric(original.str.replace(",", ".", regex=False),
                                        errors="coerce").astype(float)
        no_convertidos[columna] = int((original.notna() & salida[columna].isna()).sum())
    return salida, no_convertidos


def atipicos_iqr(serie, factor=1.5):
    """Devuelve máscara de atípicos y límites según el rango intercuartílico."""
    q1, q3 = serie.quantile([0.25, 0.75])
    rango = q3 - q1
    inferior, superior = q1 - factor * rango, q3 + factor * rango
    return (serie < inferior) | (serie > superior), inferior, superior


def resumen_atipicos(datos, columnas, factor=1.5):
    """Tabla de atípicos IQR: justifica qué centro y qué escala corresponden."""
    filas = []
    for columna in columnas:
        serie = datos[columna].dropna()
        mascara, inferior, superior = atipicos_iqr(serie, factor)
        filas.append({"variable": columna, "n": int(serie.size), "media": serie.mean(),
                      "mediana": serie.median(), "desv_est": serie.std(),
                      "asimetria": serie.skew(), "lim_inf": inferior, "lim_sup": superior,
                      "atipicos": int(mascara.sum()),
                      "pct_atipicos": 100 * mascara.mean() if serie.size else np.nan,
                      "min": serie.min(), "max": serie.max()})
    return pd.DataFrame(filas)


def distancia_a_mediana_comunal(datos, lat="Latitud", lon="Longitud", comuna="ComunaCodigo"):
    """Distancia de cada punto a la mediana de las coordenadas de su comuna."""
    medianas = datos.groupby(comuna)[[lat, lon]].transform("median")
    return pd.Series(haversine_km(datos[lat], datos[lon], medianas[lat], medianas[lon]),
                     index=datos.index, name="km_a_mediana_comunal")


def anular_coordenadas_erroneas(datos, umbral_km, lat="Latitud", lon="Longitud",
                                comuna="ComunaCodigo"):
    """Anula coordenadas a más de ``umbral_km`` de su comuna; devuelve copia y máscara."""
    salida = datos.copy()
    errores = distancia_a_mediana_comunal(salida, lat, lon, comuna) > umbral_km
    salida.loc[errores, [lat, lon]] = np.nan
    return salida, errores


def marcar_coordenadas_relativas(datos, factor=10, minimo_km=50, minimo_puntos=5, lat="Latitud", lon="Longitud",
                                 comuna="ComunaCodigo"):
    """Marca puntos muy alejados en relación con la dispersión de su propia comuna.

    Complementa al umbral absoluto: en una comuna compacta, 60 km ya es anómalo. Se exige superar
    ``factor`` veces el percentil 90 de la comuna y ``minimo_km``. Devuelve una máscara para revisar,
    no para corregir: un campamento minero remoto puede cumplir la regla y ser real.
    """
    km = distancia_a_mediana_comunal(datos, lat, lon, comuna)
    por_comuna = km.groupby(datos[comuna])
    p90 = por_comuna.transform(lambda s: s.quantile(0.9))
    puntos = por_comuna.transform("count")
    return (km > factor * p90) & (km > minimo_km) & (puntos >= minimo_puntos)


def depurar_fechas(datos, fecha_corte, col_inicio="FechaInicioFuncionamientoEstab",
                   col_cierre="FechaCierre"):
    """Anula inicios imposibles: posteriores al corte o posteriores al cierre.

    Devuelve ``(copia, conteos)``. No se corrige el valor porque no hay información para
    saber cuál es el correcto; solo se evita que entre al cálculo de antigüedad.
    """
    salida = datos.copy()
    corte = pd.to_datetime(fecha_corte, dayfirst=True)   # admite día-mes-año
    futuras = salida[col_inicio] > corte
    invertidas = salida[col_cierre].notna() & (salida[col_inicio] > salida[col_cierre])
    salida.loc[futuras | invertidas, col_inicio] = pd.NaT
    return salida, {"inicio_posterior_al_corte": int(futuras.sum()),
                    "inicio_posterior_al_cierre": int(invertidas.sum())}


def completar_por_condicion(datos, columna, condicion, valor):
    """Asigna ``valor`` donde hay nulo y se cumple ``condicion``; devuelve copia y conteo.

    Se usa para los faltantes estructurales que el diccionario oficial explica.
    """
    salida = datos.copy()
    mascara = salida[columna].isna() & condicion
    salida.loc[mascara, columna] = valor
    return salida, int(mascara.sum())


def imputar_categorica_por_grupo(datos, columna, grupo, pureza_minima=0.95,
                                 sin_dato=ETIQUETA_SIN_DATO):
    """Imputa la moda del grupo solo si ese grupo es casi homogéneo.

    La pureza es la proporción de la moda dentro del grupo. Bajo ``pureza_minima`` la moda
    sería una suposición, así que el nulo pasa a ``sin_dato``. Devuelve copia y conteos.
    """
    if not 0 < pureza_minima <= 1:
        raise ProyectoError("pureza_minima debe estar en (0, 1].")
    salida = datos.copy()
    conteos = salida.groupby(grupo)[columna].value_counts()
    imputados = etiquetados = 0
    for clave, indice in salida[salida[columna].isna()].groupby(grupo).groups.items():
        modas = conteos.loc[clave] if clave in conteos.index.get_level_values(0) else pd.Series(dtype=int)
        if len(modas) and modas.iloc[0] / modas.sum() >= pureza_minima:
            salida.loc[indice, columna] = modas.index[0]
            imputados += len(indice)
        else:
            salida.loc[indice, columna] = sin_dato
            etiquetados += len(indice)
    # Los nulos cuyo grupo también es nulo no entran a groupby: se etiquetan aparte.
    restantes = salida[columna].isna()
    salida.loc[restantes, columna] = sin_dato
    etiquetados += int(restantes.sum())
    return salida, {"imputados_moda_grupo": imputados, "etiquetados_sin_dato": etiquetados}


def evaluar_imputacion_categorica(datos, columna, grupo, pureza_minima=0.95,
                                  fraccion=0.10, semilla=42):
    """Oculta valores conocidos y mide el acierto de tres alternativas de imputación.

    Retorna una tabla con el acierto sobre los valores ocultos y la cobertura, es decir,
    qué parte de esos valores recibe una categoría real y no ``Sin dato``.
    """
    conocidos = datos[datos[columna].notna()]
    generador = np.random.default_rng(semilla)
    ocultos = generador.choice(conocidos.index.to_numpy(),
                               size=max(1, int(fraccion * len(conocidos))), replace=False)
    verdad = conocidos.loc[ocultos, columna]
    entrenamiento = conocidos.drop(index=ocultos)

    moda_global = entrenamiento[columna].mode().iloc[0]
    moda_grupo = entrenamiento.groupby(grupo)[columna].agg(lambda s: s.mode().iloc[0])
    pureza = entrenamiento.groupby(grupo)[columna].agg(lambda s: s.value_counts(normalize=True).iloc[0])
    claves = conocidos.loc[ocultos, grupo]
    pred_grupo = claves.map(moda_grupo)
    pred_pura = pred_grupo.where(claves.map(pureza) >= pureza_minima)

    filas = [("moda global", pd.Series(moda_global, index=verdad.index)),
             ("moda por grupo", pred_grupo),
             (f"moda por grupo con pureza >= {pureza_minima:.0%}", pred_pura)]
    return pd.DataFrame([
        {"metodo": nombre, "ocultos": int(verdad.size),
         "cobertura_pct": round(100 * pred.notna().mean(), 1),
         "acierto_sobre_cubiertos_pct": round(100 * (pred[pred.notna()] == verdad[pred.notna()]).mean(), 1)}
        for nombre, pred in filas])


def marcar_posibles_duplicados(datos, claves):
    """Marca filas con igual nombre, comuna y dirección, aunque su código sea distinto."""
    completas = datos[claves].notna().all(axis=1)
    return completas & datos.duplicated(subset=claves, keep=False)
