"""Comparación medida de alternativas de imputación numérica."""

import numpy as np
import pandas as pd

from src import ProyectoError


def _rellenar(serie, metodo, grupo=None):
    """Devuelve la serie imputada según ``metodo``; ``grupo`` se exige en la variante grupal."""
    if metodo == "media":
        return serie.fillna(serie.mean())
    if metodo == "mediana":
        return serie.fillna(serie.median())
    if metodo == "mediana_grupo":
        if grupo is None:
            raise ProyectoError("La mediana por grupo requiere el parámetro 'grupo'.")
        # La mediana global es el respaldo para grupos sin ningún valor observado.
        return serie.fillna(serie.groupby(grupo).transform("median")).fillna(serie.median())
    raise ProyectoError(f"Método de imputación desconocido: {metodo}")


def comparar_imputaciones(serie, grupo=None):
    """Compara eliminar, media, mediana y mediana por grupo sobre una variable numérica.

    ``cambio_desv_pct`` mide el efecto en la variabilidad respecto de lo observado: toda
    imputación por un valor central concentra los datos y reduce la desviación estándar.
    """
    if not pd.api.types.is_numeric_dtype(serie):
        raise ProyectoError(f"'{serie.name}' debe ser numérica para compararla.")
    observada = serie.dropna()
    if observada.empty:
        raise ProyectoError(f"'{serie.name}' no tiene valores observados.")
    desv_base = observada.std()
    alternativas = {"eliminar filas": observada}
    for metodo in ("media", "mediana"):
        alternativas[metodo] = _rellenar(serie, metodo)
    if grupo is not None:
        alternativas["mediana por grupo"] = _rellenar(serie, "mediana_grupo", grupo)

    filas = []
    for nombre, resultado in alternativas.items():
        desv = resultado.std()
        filas.append({"metodo": nombre, "n": int(resultado.size),
                      "filas_perdidas": int(serie.size - resultado.size),
                      "media": resultado.mean(), "mediana": resultado.median(), "desv_est": desv,
                      "cambio_desv_pct": 100 * (desv - desv_base) / desv_base if desv_base else 0.0})
    return pd.DataFrame(filas)


def error_oculto_escalar(serie, grupo, fraccion=0.10, semilla=42):
    """Oculta valores conocidos y mide el error absoluto medio de cada alternativa."""
    conocidos = serie.dropna()
    generador = np.random.default_rng(semilla)
    ocultos = generador.choice(conocidos.index.to_numpy(),
                               size=max(1, int(fraccion * conocidos.size)), replace=False)
    prueba = serie.copy()
    prueba.loc[ocultos] = np.nan
    filas = []
    for metodo, parametro in (("media", None), ("mediana", None), ("mediana_grupo", grupo)):
        relleno = _rellenar(prueba, metodo, parametro)
        filas.append({"metodo": metodo.replace("_", " por "), "ocultos": int(ocultos.size),
                      "error_absoluto_medio": (relleno.loc[ocultos] - serie.loc[ocultos]).abs().mean()})
    return pd.DataFrame(filas)


def error_oculto_coordenadas(datos, grupo, lat="Latitud", lon="Longitud",
                             fraccion=0.10, semilla=42):
    """Mide el error geográfico en kilómetros al ocultar pares de coordenadas conocidos."""
    from src.geo import haversine_km  # importación local: evita cargar geo si no se usa

    conocidos = datos[datos[lat].notna() & datos[lon].notna()]
    generador = np.random.default_rng(semilla)
    ocultos = generador.choice(conocidos.index.to_numpy(),
                               size=max(1, int(fraccion * len(conocidos))), replace=False)
    prueba = datos.copy()
    prueba.loc[ocultos, [lat, lon]] = np.nan
    filas = []
    for metodo, parametro in (("media", None), ("mediana", None),
                              ("mediana_grupo", prueba[grupo])):
        relleno_lat = _rellenar(prueba[lat], metodo, parametro)
        relleno_lon = _rellenar(prueba[lon], metodo, parametro)
        km = haversine_km(relleno_lat.loc[ocultos], relleno_lon.loc[ocultos],
                          datos.loc[ocultos, lat], datos.loc[ocultos, lon])
        filas.append({"metodo": metodo.replace("_grupo", " por comuna"), "ocultos": int(ocultos.size),
                      "error_medio_km": float(np.mean(km)), "error_mediano_km": float(np.median(km))})
    return pd.DataFrame(filas)


def error_dejando_uno_fuera(datos, grupo, respaldo, lat="Latitud", lon="Longitud"):
    """Error en km de imputar cada punto conocido con la mediana de su grupo sin ese punto.

    No depende del azar y da un error por fila, de modo que se puede resumir por tipo. Los grupos
    con un solo punto usan la mediana de ``respaldo``.
    """
    from src.geo import haversine_km

    conocidos = datos[datos[lat].notna() & datos[lon].notna()]
    estimado = pd.DataFrame(index=conocidos.index, columns=[lat, lon], dtype=float)
    for _, indice in conocidos.groupby(grupo).groups.items():
        miembros = conocidos.loc[indice, [lat, lon]]
        if len(miembros) < 2:
            continue
        for fila in indice:
            estimado.loc[fila] = miembros.drop(index=fila).median().to_numpy()
    solos = estimado[lat].isna()
    medianas = conocidos.groupby(respaldo)[[lat, lon]].median()
    estimado.loc[solos, [lat, lon]] = medianas.loc[conocidos.loc[solos, respaldo]].to_numpy()
    km = haversine_km(conocidos[lat], conocidos[lon], estimado[lat], estimado[lon])
    return pd.Series(km, index=conocidos.index, name="error_km")


def resumir_error_por_estrato(error_km, estrato):
    """Resume el error por estrato: registros, mediana, percentil 90 y media."""
    return (error_km.groupby(estrato.loc[error_km.index]).agg(
        n="size", mediana_km="median", p90_km=lambda s: s.quantile(0.9), media_km="mean").sort_values("n",
            ascending=False))


def error_ponderado_como_faltantes(error_km, estrato, estrato_faltantes):
    """Pondera el error por estrato con la composición real de los faltantes.

    El ocultamiento al azar se parece a los datos conocidos. Esta medida responde otra pregunta:
    cuál sería el error si los puntos ocultos se parecieran a los que de verdad faltan.
    """
    pesos = estrato_faltantes.value_counts(normalize=True)
    por_estrato = resumir_error_por_estrato(error_km, estrato)
    comunes = pesos.index.intersection(por_estrato.index)
    peso_cubierto = float(pesos.loc[comunes].sum())
    if peso_cubierto == 0:
        raise ProyectoError("Los faltantes no comparten estratos con los datos conocidos.")
    return {"media_km": float((por_estrato.loc[comunes, "media_km"] * pesos.loc[comunes]).sum() / peso_cubierto),
            "mediana_km": float((por_estrato.loc[comunes, "mediana_km"] * pesos.loc[comunes]).sum() / peso_cubierto),
            "peso_cubierto_pct": 100 * peso_cubierto}


def imputar_por_grupo(datos, columnas, grupo, grupo_respaldo=None, sufijo_bandera=None):
    """Imputa con la mediana del grupo y agrega una bandera de filas imputadas.

    Si un grupo no tiene valores observados se usa ``grupo_respaldo``. Devuelve copia y
    conteos por nivel. La bandera es obligatoria para no confundir dato con estimación.
    """
    salida = datos.copy()
    conteos = {}
    for columna in columnas:
        faltantes = salida[columna].isna()
        if sufijo_bandera:
            salida[f"{columna}{sufijo_bandera}"] = faltantes.astype(int)
        por_grupo = salida[columna].groupby(salida[grupo]).transform("median")
        salida[columna] = salida[columna].fillna(por_grupo)
        tras_grupo = int(salida[columna].isna().sum())
        if grupo_respaldo and tras_grupo:
            por_respaldo = salida[columna].groupby(salida[grupo_respaldo]).transform("median")
            salida[columna] = salida[columna].fillna(por_respaldo)
        conteos[columna] = {"por_grupo": int(faltantes.sum()) - tras_grupo, "por_respaldo": tras_grupo}
    return salida, conteos
