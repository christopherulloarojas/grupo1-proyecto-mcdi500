"""Transformación: variables derivadas, codificación por rol y escalamiento."""

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler, OneHotEncoder, OrdinalEncoder, RobustScaler, StandardScaler

from src import ProyectoError
from src.geo import distancia_minima_km

# Agrupación por código de región, declarada por el equipo: de norte a sur. No es una
# división oficial; ordena la lectura territorial y se documenta como supuesto.
MACROZONAS = {"15": "Norte", "01": "Norte", "02": "Norte", "03": "Norte", "04": "Norte",
              "05": "Centro", "13": "Centro", "06": "Centro", "07": "Centro", "16": "Centro",
              "08": "Sur", "09": "Sur", "14": "Sur", "10": "Sur",
              "11": "Austral", "12": "Austral"}
ORDEN_MACROZONAS = ["Norte", "Centro", "Sur", "Austral"]
# Alternativa para medir sensibilidad: otra agrupación defendible de las mismas regiones.
MACROZONAS_ALTERNATIVA = {**MACROZONAS, "10": "Austral", "04": "Centro"}

# Orden declarado por el equipo según el diccionario oficial. Nunca alfabético: «Alta» no
# es menor que «Baja», y «Primer» no es mayor que «Tercer» por la inicial.
ORDEN_NIVEL_ATENCION = ["Primer Nivel", "Segundo Nivel", "Tercer Nivel"]
ORDEN_COMPLEJIDAD = ["Baja Complejidad", "Mediana Complejidad", "Alta Complejidad"]
FUERA_DE_ESCALA = ("No Aplica", "Sin dato")

GRUPOS_DEPENDENCIA = {
    "Armada de Chile": "FF. AA. y de Orden", "Ejército de Chile": "FF. AA. y de Orden",
    "Fuerza Aérea de Chile": "FF. AA. y de Orden", "Carabineros": "FF. AA. y de Orden",
    "PDI": "FF. AA. y de Orden", "Gendarmería": "Otra", "Otra Institución": "Otra",
    "SEREMI de Salud": "Otra", "Delegado": "Otra",
}

USO_MATRIZ = {
    "uso": ("Entrada para exploración multivariada y modelos descriptivos de la Fase 3. No sirve para calcular "
        "distancias ni para el análisis descriptivo, que usan el conjunto limpio."),
    "variable_objetivo": ("No hay una variable objetivo definida en F2. Si F3 modela la lejanía, el objetivo debe "
        "ser dist_urgencia_km_esc o una versión en kilómetros tomada del conjunto limpio."),
    "prohibidas_si_el_objetivo_es_la_distancia": [
        "Latitud_esc", "Longitud_esc", "es_referencia_urgencia", "tiene_servicio_urgencia",
            "n_establecimientos_comuna_esc",
        "coordenada_imputada", "EstablecimientoCodigo"],
    "advertencia_geometria": ("Latitud y Longitud se escalan por separado, con rangos distintos: una unidad "
        "escalada no equivale a la misma distancia en ambos ejes. Las distancias se calculan siempre en kilómetros "
            "con las coordenadas sin escalar del conjunto limpio."),
}

# Tipos de urgencia que se aceptan como atención general. Quedan fuera, por no prestarla,
# «Hospitalaria Especializada», «Otro» y «SAPU Dental».
UEH = "Urgencia Hospitalaria (UEH)"
SUR = "Urgencia Ambulatoria (SUR)"
SAPU = "Urgencia Ambulatoria (SAPU)"
URGENCIAS_GENERALES = {UEH, SAPU, SUR, "Urgencia Ambulatoria (SAR)", "Urgencia Ambulatoria Privada"}
# Un establecimiento puede declarar UEH y ser especializado por su nombre.
PATRON_ESPECIALIZADA = r"(?i)psiqui|oncol|geri[aá]tr|rehabilit"
SAPU_ESTACIONAL = "Verano"
SAPU_CORTO = "Corto"

# Nivel de referencia -> columna booleana, distancia derivada y definición que usa el informe.
NIVELES_REFERENCIA = {
    "1. Cualquier urgencia general": {
        "columna": "es_referencia_urgencia", "distancia": "dist_urgencia_km",
        "definicion": "UEH, SAPU, SAR, SUR y ambulatoria privada; sin especializadas, Otro, dental ni SAPU de verano"},
    "2. Sin SUR": {
        "columna": "ref_sin_sur", "distancia": "dist_sin_sur_km", "definicion": "Nivel 1 sin servicios de urgencia "
            "rural"},
    "3. Solo UEH": {
        "columna": "ref_ueh", "distancia": "dist_ueh_km", "definicion": "Nivel 1 restringido a unidades de "
            "emergencia hospitalaria"},
    "4. UEH pública, alta o mediana": {
        "columna": "ref_ueh_pub_am", "distancia": "dist_ueh_pub_am_km",
        "definicion": "UEH del sistema público con complejidad alta o mediana"},
    "5. UEH pública, alta": {
        "columna": "ref_ueh_pub_a", "distancia": "dist_ueh_pub_a_km",
            "definicion": "UEH del sistema público con complejidad alta"},
}


def asignar_macrozona(codigos, mapa=None):
    """Asigna macrozona desde el código de región; exige que todos los códigos estén mapeados."""
    mapa = MACROZONAS if mapa is None else mapa
    resultado = codigos.map(mapa)
    if resultado.isna().any():
        raise ProyectoError(f"Códigos de región sin macrozona: {sorted(codigos[resultado.isna()].unique())}")
    return resultado


def calcular_antiguedad(inicio, fecha_corte):
    """Antigüedad en años a la fecha de corte; lo faltante permanece faltante."""
    return (pd.to_datetime(fecha_corte, dayfirst=True) - inicio).dt.days / 365.25


def contar_por_grupo(serie_grupo):
    """Devuelve, para cada fila, cuántas filas comparten su grupo."""
    return serie_grupo.map(serie_grupo.value_counts()).astype(int)


def marcar_referencia_urgencia(datos):
    """Identifica los servicios de urgencia general que operan todo el año (nivel 1).

    Exige urgencia declarada y un tipo general; excluye SAPU estacionales y los establecimientos
    psiquiátricos, oncológicos, geriátricos y de rehabilitación aunque declaren UEH.
    """
    return (datos["TieneServicioUrgencia"].eq("SI")
            & datos["TipoUrgencia"].isin(URGENCIAS_GENERALES)
            & datos["ClasificacionTipoSapu"].ne(SAPU_ESTACIONAL)
            & ~datos["EstablecimientoGlosa"].str.contains(PATRON_ESPECIALIZADA, regex=True))


def marcar_niveles_referencia(datos):
    """Devuelve una columna booleana por nivel, más la variante sin SAPU de horario corto."""
    base = marcar_referencia_urgencia(datos)
    publica_ueh = base & datos["TipoUrgencia"].eq(UEH) & datos["TipoSistemaSaludGlosa"].eq("Público")
    complejidad = datos["NivelComplejidadEstabGlosa"]
    return pd.DataFrame({
        "es_referencia_urgencia": base,
        "ref_sin_sur": base & datos["TipoUrgencia"].ne(SUR),
        "ref_ueh": base & datos["TipoUrgencia"].eq(UEH),
        "ref_ueh_pub_am": publica_ueh & complejidad.isin(["Alta Complejidad", "Mediana Complejidad"]),
        "ref_ueh_pub_a": publica_ueh & complejidad.eq("Alta Complejidad"),
        "ref_sin_sapu_corto": base & ~(datos["TipoUrgencia"].eq(SAPU) & datos["ClasificacionTipoSapu"].eq(SAPU_CORTO)),
    }, index=datos.index)


def calcular_distancia_urgencia(datos, lat="Latitud", lon="Longitud", referencia="es_referencia_urgencia"):
    """Distancia en línea recta de cada fila al servicio de referencia más cercano."""
    ref = datos[datos[referencia]]
    return pd.Series(distancia_minima_km(datos[lat], datos[lon], ref[lat], ref[lon]),
                     index=datos.index, name="dist_urgencia_km")


def agrupar_categorias_raras(serie, umbral=0.01, etiqueta="Otros tipos"):
    """Agrupa categorías con frecuencia relativa menor que ``umbral``; devuelve serie y lista."""
    if not 0 <= umbral < 1:
        raise ProyectoError("El umbral debe estar en [0, 1).")
    frecuencias = serie.value_counts(normalize=True)
    raras = frecuencias[frecuencias < umbral].index.tolist()
    return serie.where(~serie.isin(raras), etiqueta), raras


def codificar_ordinal(serie, orden, fuera_de_escala=FUERA_DE_ESCALA, nombre=None):
    """Codifica con el orden declarado: 1, 2, 3... y 0 para lo que está fuera de la escala.

    Devuelve un DataFrame con la columna ordinal y la bandera ``*_fuera_escala``. El 0 no
    es un peldaño de la escala: la bandera permite excluirlo en el análisis. Una categoría
    no declarada detiene la ejecución, en vez de convertirse en un nulo silencioso.
    """
    nombre = nombre or serie.name
    if serie.isna().any():
        raise ProyectoError(f"'{nombre}' tiene nulos: resuélvalos antes de codificar.")
    en_escala = ~serie.isin(fuera_de_escala)
    codificador = OrdinalEncoder(categories=[list(orden)], handle_unknown="error", dtype=int)
    salida = pd.Series(0, index=serie.index, name=nombre, dtype=int)
    if en_escala.any():
        try:
            valores = codificador.fit_transform(serie[en_escala].to_frame())
        except ValueError as error:
            raise ProyectoError(f"Categoría no declarada en '{nombre}': {error}") from error
        salida.loc[en_escala] = valores.ravel() + 1
    return pd.DataFrame({nombre: salida, f"{nombre}_fuera_escala": (~en_escala).astype(int)})


def codificar_one_hot(datos, columnas, prefijos=None):
    """Aplica one-hot y devuelve ``(matriz, grupos)``.

    Se conservan todas las categorías (sin ``drop``) para validar que cada grupo sume 1.
    ``handle_unknown='error'`` detiene el flujo ante una categoría que no se vio al ajustar.
    """
    prefijos = prefijos or {c: c for c in columnas}
    partes, grupos = [], {}
    for columna in columnas:
        if datos[columna].isna().any():
            raise ProyectoError(f"'{columna}' tiene nulos: resuélvalos antes de codificar.")
        codificador = OneHotEncoder(sparse_output=False, handle_unknown="error", dtype=int)
        matriz = codificador.fit_transform(datos[[columna]])
        nombres = [f"{prefijos[columna]}__{normalizar_categoria(c)}" for c in codificador.categories_[0]]
        partes.append(pd.DataFrame(matriz, columns=nombres, index=datos.index))
        grupos[columna] = nombres
    return pd.concat(partes, axis=1), grupos


def normalizar_categoria(texto):
    """Convierte una categoría en un sufijo de columna sin espacios ni tildes."""
    import re
    import unicodedata
    plano = unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "_", plano).strip("_")


_ESCALADORES = {"estandar": StandardScaler, "minmax": MinMaxScaler, "robusto": RobustScaler}


def verificar_propiedad_escalador(valores, metodo, tolerancia=1e-9):
    """Comprueba la propiedad que el método garantiza; devuelve ``True`` o lanza error."""
    valores = np.asarray(valores, dtype=float)
    valores = valores[~np.isnan(valores)]
    if metodo == "estandar":
        cumple = abs(valores.mean()) < tolerancia and abs(valores.std() - 1) < 1e-6
    elif metodo == "minmax":
        cumple = abs(valores.min()) < tolerancia and abs(valores.max() - 1) < tolerancia
    elif metodo == "robusto":
        q1, mediana, q3 = np.percentile(valores, [25, 50, 75])
        cumple = abs(mediana) < tolerancia and abs((q3 - q1) - 1) < 1e-6
    else:
        raise ProyectoError(f"Escalador desconocido: {metodo}")
    if not cumple:
        raise AssertionError(f"El escalador '{metodo}' no cumple su propiedad.")
    return True


def comparar_escaladores(datos, columnas):
    """Mide cómo deja cada escalador a cada variable.

    ``rango_p1_p99`` muestra cuánto espacio ocupa el 98 % central de los datos: si es muy
    pequeño frente al rango total, un extremo está comprimiendo a todos los demás.
    """
    filas = []
    for columna in columnas:
        valores = datos[[columna]].to_numpy(dtype=float)
        for nombre, clase in _ESCALADORES.items():
            escalado = clase().fit_transform(valores).ravel()
            limpios = escalado[~np.isnan(escalado)]
            verificar_propiedad_escalador(escalado, nombre)
            filas.append({"variable": columna, "escalador": nombre, "min": limpios.min(), "max": limpios.max(),
                          "propiedad_verificada": True})
    return pd.DataFrame(filas)


def _centro_y_escala(valores, metodo):
    """Parámetros que usa cada escalador: centro y escala."""
    if metodo == "estandar":
        return valores.mean(), valores.std()
    if metodo == "minmax":
        return valores.min(), valores.max() - valores.min()
    q1, mediana, q3 = np.percentile(valores, [25, 50, 75])
    return mediana, q3 - q1


def estabilidad_escaladores(datos, columnas, recorte=0.01):
    """Mide cuánto cambian centro y escala de cada escalador al quitar los extremos.

    Un porcentaje de rango no sirve para compararlos: todos son transformaciones lineales y dejan
    igual la forma de la variable. Lo que sí los distingue es de qué valores dependen sus parámetros.
    ``recorte`` es la fracción que se quita en cada cola.
    """
    filas = []
    for columna in columnas:
        valores = datos[columna].dropna().to_numpy(dtype=float)
        inferior, superior = np.quantile(valores, [recorte, 1 - recorte])
        recortados = valores[(valores >= inferior) & (valores <= superior)]
        for nombre in _ESCALADORES:
            centro, escala = _centro_y_escala(valores, nombre)
            centro_r, escala_r = _centro_y_escala(recortados, nombre)
            filas.append({"variable": columna, "escalador": nombre, "centro": centro, "escala": escala,
                          "cambio_escala_pct": 100 * (escala_r - escala) / escala if escala else 0.0,
                          "desplaza_centro_en_escalas": abs(centro_r - centro) / escala if escala else 0.0})
    return pd.DataFrame(filas)


def escalar_robusto(datos, columnas, sufijo="_esc"):
    """Aplica ``RobustScaler`` y devuelve las columnas nuevas y sus parámetros."""
    escalador = RobustScaler()
    matriz = escalador.fit_transform(datos[columnas].to_numpy(dtype=float))
    nombres = [f"{c}{sufijo}" for c in columnas]
    parametros = {c: {"mediana": float(m), "rango_intercuartilico": float(e)}
                  for c, m, e in zip(columnas, escalador.center_, escalador.scale_)}
    return pd.DataFrame(matriz, columns=nombres, index=datos.index), parametros
