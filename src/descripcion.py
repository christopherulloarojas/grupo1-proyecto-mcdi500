"""Funciones descriptivas: no guardan estado, por eso son funciones y no clases."""
import pandas as pd

from src.utilidades import normalizar_texto


def perfilar(df, columnas):
    """Una fila por columna: vacíos, «No Aplica» y variantes antes y después de normalizar."""
    filas = []
    for columna in columnas:
        normalizada = normalizar_texto(df[columna])
        filas.append({"columna": columna,
                      "vacios": int(normalizada.eq("").sum()),
                      "no_aplica": int(normalizada.eq("no aplica").sum()),
                      "variantes_originales": int(df[columna].nunique()),
                      "variantes_normalizadas": int(normalizada.nunique())})
    return pd.DataFrame(filas)


def construir_contingencia(poblacion, orden_filas, orden_columnas):
    """Tabla de contingencia y porcentajes por fila con un orden declarado."""
    tabla = pd.crosstab(poblacion["pertenencia_snss"], poblacion["complejidad"])
    tabla = tabla.reindex(index=orden_filas, columns=orden_columnas, fill_value=0)
    porcentajes = tabla.div(tabla.sum(axis=1), axis=0) * 100
    return tabla, porcentajes


def calcular_retencion(poblacion, exclusiones, pasos_complejidad, orden_grupos):
    """Retención por grupo: vigentes con pertenencia válida frente a incluidos."""
    excluidos = exclusiones.loc[exclusiones["paso_exclusion"].isin(pasos_complejidad), "pertenencia_snss"]
    incluidos = poblacion["pertenencia_snss"].value_counts()
    vigentes = incluidos.add(excluidos.value_counts(), fill_value=0).astype(int)
    retencion = pd.DataFrame({"vigentes_con_pertenencia": vigentes, "incluidos": incluidos}).reindex(orden_grupos)
    retencion["excluidos_por_complejidad"] = retencion["vigentes_con_pertenencia"] - retencion["incluidos"]
    retencion["porcentaje_retenido"] = retencion["incluidos"] / retencion["vigentes_con_pertenencia"] * 100
    return retencion


def tabla_correspondencias(trabajo, pares):
    """Cuenta cuántos registros de cada categoría original fueron a cada categoría analítica."""
    bloques = []
    for original, nueva in pares:
        tabla = trabajo.groupby([original, nueva], dropna=False).size().reset_index(name="cantidad")
        tabla.columns = ["categoria_original", "categoria_analitica", "cantidad"]
        tabla.insert(0, "variable", original)
        bloques.append(tabla)
    return pd.concat(bloques, ignore_index=True)
