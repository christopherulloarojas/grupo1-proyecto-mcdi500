"""Configuración del preprocesamiento: las reglas de la Fase 2 declaradas como datos."""

ORDEN_GRUPOS = ["SNSS", "No SNSS"]
ORDEN_COMPLEJIDAD = ["Baja", "Mediana", "Alta"]
COLUMNAS_NECESARIAS = ["EstablecimientoCodigo", "EstadoFuncionamiento",
                       "TipoPertenenciaEstabGlosa", "NivelComplejidadEstabGlosa"]

# Normalización: columna original -> columna normalizada (espacios y mayúsculas)
NORMALIZACIONES = [("EstablecimientoCodigo", "codigo_establecimiento"),
                   ("EstadoFuncionamiento", "estado_normalizado"),
                   ("TipoPertenenciaEstabGlosa", "pertenencia_original_normalizada"),
                   ("NivelComplejidadEstabGlosa", "complejidad_original_normalizada")]

# Traducción a categorías analíticas: lo que no está en el mapa queda sin correspondencia
MAPA_PERTENENCIA = {"perteneciente al sistema nacional de servicios de salud": "SNSS",
                    "no perteneciente al sistema nacional de servicios de salud": "No SNSS"}
MAPA_COMPLEJIDAD = {"baja complejidad": "Baja", "mediana complejidad": "Mediana",
                    "alta complejidad": "Alta"}
MAPEOS = [("pertenencia_original_normalizada", "pertenencia_snss", MAPA_PERTENENCIA),
          ("complejidad_original_normalizada", "complejidad", MAPA_COMPLEJIDAD)]
ESTADOS_VIGENTES = ["vigente en operación habitual", "vigente en operación transitoria"]

# Reglas de la población: las mismas de la Fase 2, en el mismo orden
REGLAS_POBLACION = [
    {"paso": "F01", "tipo": "permitidos", "columna": "estado_normalizado",
     "valores": ESTADOS_VIGENTES, "motivo": "Conservar estado vigente"},
    {"paso": "F02", "tipo": "informado", "columna": "codigo_establecimiento",
     "motivo": "Código informado"},
    {"paso": "F03", "tipo": "duplicados_exactos",
     "motivo": "Una copia de filas exactamente repetidas"},
    {"paso": "F04", "tipo": "codigos_en_conflicto", "columna": "codigo_establecimiento",
     "motivo": "Excluir códigos con registros distintos en conflicto"},
    {"paso": "F05", "tipo": "permitidos", "columna": "pertenencia_snss", "valores": ORDEN_GRUPOS,
     "motivo": "Pertenencia clasificable: excluir No Aplica, vacíos o no reconocidos"},
    {"paso": "F06", "tipo": "informado", "columna": "complejidad_original_normalizada",
     "motivo": "Complejidad informada: excluir vacíos"},
    {"paso": "F07", "tipo": "excluir_valor", "columna": "complejidad_original_normalizada",
     "valor": "no aplica", "motivo": "Complejidad aplicable: excluir No Aplica"},
    {"paso": "F08", "tipo": "permitidos", "columna": "complejidad", "valores": ORDEN_COMPLEJIDAD,
     "motivo": "Complejidad reconocida: Baja, Mediana o Alta"},
]
PASOS_COMPLEJIDAD = ["F06", "F07", "F08"]        # para medir la retención por grupo

COLUMNAS_POBLACION = ["fila_origen", "codigo_establecimiento", "estado_normalizado",
                      "pertenencia_snss", "complejidad"]
CODIFICACIONES = [("pertenencia_snss", {"SNSS": "snss_perteneciente", "No SNSS": "snss_no_perteneciente"}),
                  ("complejidad", {"Baja": "complejidad_baja", "Mediana": "complejidad_mediana",
                                   "Alta": "complejidad_alta"})]
COLUMNAS_NUMERICAS = [nombre for _, nombres in CODIFICACIONES for nombre in nombres.values()]
COLUMNAS_AUDITORIA = ["fila_origen", "codigo_establecimiento", "EstadoFuncionamiento", "TipoPertenenciaEstabGlosa",
                      "NivelComplejidadEstabGlosa", "paso_exclusion", "motivo_exclusion"]


def crear_configuracion(columnas_originales, normalizaciones=NORMALIZACIONES, columnas_poblacion=COLUMNAS_POBLACION):
    """Reúne la configuración que recibe el preprocesador para un registro dado."""
    return {"normalizaciones": list(normalizaciones), "mapeos": MAPEOS, "reglas": REGLAS_POBLACION,
            "columnas_originales": list(columnas_originales), "columnas_poblacion": list(columnas_poblacion),
            "codificaciones": CODIFICACIONES, "columnas_numericas": COLUMNAS_NUMERICAS}
