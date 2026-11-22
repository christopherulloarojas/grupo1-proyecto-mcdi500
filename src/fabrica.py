"""Fábrica: construye los pasos y los pipelines a partir de la configuración (Factory)."""
from src.pipeline import PipelineObservable
from src.funciones import agregar_fila_origen, normalizar_columna, seleccionar_columnas
from src.transformadores import (CodificadorBinario, FiltroCodigosEnConflicto, FiltroDuplicadosExactos,
                                 FiltroInformado, FiltroValorExcluido, FiltroValoresPermitidos,
                                 MapeadorCategorias, PasoFuncion)


def crear_filtro(regla, columnas_originales=None):
    """Devuelve el filtro que corresponde al tipo declarado en la regla."""
    tipo = regla["tipo"].strip().lower()
    paso, motivo = regla["paso"], regla["motivo"]
    if tipo == "permitidos":
        return FiltroValoresPermitidos(regla["columna"], regla["valores"], paso, motivo)
    if tipo == "informado":
        return FiltroInformado(regla["columna"], paso, motivo)
    if tipo == "excluir_valor":
        return FiltroValorExcluido(regla["columna"], regla["valor"], paso, motivo)
    if tipo == "duplicados_exactos":
        return FiltroDuplicadosExactos(columnas_originales, paso, motivo)
    if tipo == "codigos_en_conflicto":
        return FiltroCodigosEnConflicto(regla["columna"], paso, motivo)
    raise ValueError(f"Tipo de filtro desconocido: '{tipo}'. Tipos válidos: permitidos, informado, "
                     "excluir_valor, duplicados_exactos, codigos_en_conflicto.")


def construir_preparacion(normalizaciones, mapeos):
    """Funciones de preparación (fila de origen y normalización) y mapeadores de categorías."""
    pasos = [PasoFuncion(agregar_fila_origen)]
    pasos += [PasoFuncion(normalizar_columna, columna=origen, destino=destino) for origen, destino in normalizaciones]
    pasos += [MapeadorCategorias(origen, destino, mapa) for origen, destino, mapa in mapeos]
    return PipelineObservable(pasos)


def construir_poblacion(reglas, columnas_originales, columnas_salida):
    """Filtros en el orden declarado y selección final de columnas."""
    pasos = [crear_filtro(regla, columnas_originales) for regla in reglas]
    pasos.append(PasoFuncion(seleccionar_columnas, columnas=columnas_salida))
    return PipelineObservable(pasos)


def construir_codificacion(codificaciones, columnas_numericas):
    """Indicadores 0/1 de cada variable analítica y selección de la matriz."""
    pasos = [CodificadorBinario(columna, nombres) for columna, nombres in codificaciones]
    pasos.append(PasoFuncion(seleccionar_columnas, columnas=columnas_numericas))
    return PipelineObservable(pasos)
