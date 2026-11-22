"""Flujo de la Fase 2 reunido en una función, tal como estaba antes de las clases.

Se conserva solo como línea base: sirve para comprobar que el núcleo algorítmico
produce el mismo resultado y para medir cuánto cuesta la nueva arquitectura. El
proyecto no lo usa para generar sus salidas.
"""
import numpy as np
import pandas as pd

from src.configuracion import (COLUMNAS_NUMERICAS, COLUMNAS_POBLACION, ESTADOS_VIGENTES,
                               MAPA_COMPLEJIDAD, MAPA_PERTENENCIA)
from src.utilidades import normalizar_texto


def aplicar_filtro(datos, condicion, paso, motivo, bitacora, exclusiones):
    """Filtra filas y registra su primer motivo de exclusión en las listas recibidas."""
    condicion = condicion.fillna(False)
    excluidos = datos.loc[~condicion].copy()
    excluidos["paso_exclusion"] = paso
    excluidos["motivo_exclusion"] = motivo
    exclusiones.append(excluidos)
    restantes = datos.loc[condicion].copy()
    bitacora.append({"paso": paso, "regla": motivo, "antes": len(datos),
                     "excluidos": len(excluidos), "restantes": len(restantes)})
    return restantes


def flujo_f2(datos_originales):
    """Ejecuta el preprocesamiento de la Fase 2 de principio a fin."""
    trabajo = datos_originales.copy()
    trabajo["fila_origen"] = np.arange(2, len(trabajo) + 2)
    trabajo["codigo_establecimiento"] = normalizar_texto(trabajo["EstablecimientoCodigo"])
    trabajo["estado_normalizado"] = normalizar_texto(trabajo["EstadoFuncionamiento"])
    trabajo["pertenencia_original_normalizada"] = normalizar_texto(trabajo["TipoPertenenciaEstabGlosa"])
    trabajo["complejidad_original_normalizada"] = normalizar_texto(trabajo["NivelComplejidadEstabGlosa"])
    trabajo["pertenencia_snss"] = trabajo["pertenencia_original_normalizada"].map(MAPA_PERTENENCIA)
    trabajo["complejidad"] = trabajo["complejidad_original_normalizada"].map(MAPA_COMPLEJIDAD)

    bitacora, exclusiones = [], []
    p = trabajo
    p = aplicar_filtro(p, p["estado_normalizado"].isin(ESTADOS_VIGENTES), "F01",
                       "Conservar estado vigente", bitacora, exclusiones)
    p = aplicar_filtro(p, p["codigo_establecimiento"].notna() & p["codigo_establecimiento"].ne(""), "F02",
                       "Código informado", bitacora, exclusiones)
    p = aplicar_filtro(p, ~p.duplicated(subset=list(datos_originales.columns)), "F03",
                       "Una copia de filas exactamente repetidas", bitacora, exclusiones)
    p = aplicar_filtro(p, ~p["codigo_establecimiento"].duplicated(keep=False), "F04",
                       "Excluir códigos con registros distintos en conflicto", bitacora, exclusiones)
    p = aplicar_filtro(p, p["pertenencia_snss"].notna(), "F05",
                       "Pertenencia clasificable: excluir No Aplica, vacíos o no reconocidos", bitacora, exclusiones)
    p = aplicar_filtro(p, p["complejidad_original_normalizada"].notna() & p["complejidad_original_normalizada"].ne(""),
                       "F06", "Complejidad informada: excluir vacíos", bitacora, exclusiones)
    p = aplicar_filtro(p, p["complejidad_original_normalizada"].ne("no aplica"), "F07",
                       "Complejidad aplicable: excluir No Aplica", bitacora, exclusiones)
    p = aplicar_filtro(p, p["complejidad"].notna(), "F08",
                       "Complejidad reconocida: Baja, Mediana o Alta", bitacora, exclusiones)

    poblacion = p[COLUMNAS_POBLACION].reset_index(drop=True)
    matriz = pd.get_dummies(poblacion[["pertenencia_snss", "complejidad"]], prefix=["snss", "complejidad"], dtype=int)
    matriz = matriz.rename(columns={"snss_SNSS": "snss_perteneciente", "snss_No SNSS": "snss_no_perteneciente",
                                    "complejidad_Baja": "complejidad_baja", "complejidad_Mediana": "complejidad_mediana",
                                    "complejidad_Alta": "complejidad_alta"}).reindex(columns=COLUMNAS_NUMERICAS, fill_value=0)
    return {"trabajo": trabajo, "poblacion": poblacion, "matriz": matriz,
            "tabla_filtros": pd.DataFrame(bitacora), "exclusiones": pd.concat(exclusiones, ignore_index=True)}
