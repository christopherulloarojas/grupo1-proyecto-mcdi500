"""Comunicación de resultados: de las salidas de la Fase 3 a la figura que responde.

La Fase 4 no vuelve a limpiar ni a transformar. Lee lo que dejó la Fase 3, construye
una copia interpretable (con las categorías como texto y no como columnas 0/1) y
calcula las tablas que se grafican y la prueba de independencia comprometida en la
Fase 1.

El módulo sigue el contrato del proyecto modelo del curso (mismos nombres de función),
adaptado a este proyecto: las variables son categóricas, no hay escalamiento ni
partición en entrenamiento y prueba, y la codificación la hizo CodificadorBinario.
"""

import ast
import math
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats


# Salidas de la Fase 3 que usa la Fase 4, con su ruta relativa a la raíz del proyecto
ARTEFACTOS_F3 = {
    "poblacion": "data/processed/f3/poblacion_f3.csv",
    "matriz": "data/processed/f3/matriz_f3.csv",
    "clave_filas": "data/processed/f3/clave_filas_f3.csv",
    "contingencia": "data/processed/f3/contingencia_f3.csv",
    "porcentajes": "data/processed/f3/porcentajes_f3.csv",
    "parametros": "docs/f3/parametros_f3.csv",
    "exclusiones": "docs/f3/exclusiones_f3.csv",
}
# Tablas que se leen con la primera columna como índice (filas = grupo)
CON_INDICE = {"contingencia", "porcentajes"}
# Columnas que deben leerse como texto para no perder ceros a la izquierda
COMO_TEXTO = {"codigo_establecimiento": str}


def cargar_artefactos(raiz, artefactos=ARTEFACTOS_F3):
    """Lee las salidas de la Fase 3.

    Si falta alguna, se detiene y dice qué hacer: la Fase 4 no inventa datos
    para poder seguir. Los archivos se escribieron con BOM (utf-8-sig) para que
    Excel muestre bien las tildes, así que se leen con esa misma codificación.
    """
    raiz = Path(raiz)
    faltantes = [ruta for ruta in artefactos.values() if not (raiz / ruta).is_file()]
    if faltantes:
        raise FileNotFoundError(
            f"Faltan salidas de la Fase 3 en {raiz}: {faltantes}. "
            "Ejecuten primero el cuaderno de F3, que las escribe en data/processed/f3 y docs/f3."
        )
    leidos = {}
    for nombre, ruta in artefactos.items():
        opciones = {"encoding": "utf-8-sig", "dtype": COMO_TEXTO}
        if nombre in CON_INDICE:
            opciones["index_col"] = 0
        leidos[nombre] = pd.read_csv(raiz / ruta, **opciones)
    return leidos


def leer_parametros(tabla_parametros):
    """Convierte la tabla de parámetros de la Fase 3 en un diccionario por paso.

    La Fase 3 guardó cada diccionario como texto. ast.literal_eval lo convierte
    de vuelta sin ejecutar código, a diferencia de eval, que sí lo haría. Si un
    paso se repite (por ejemplo, seleccionar columnas en dos etapas), se agrega la
    etapa al nombre para que ninguno se sobrescriba en silencio.
    """
    repetidos = tabla_parametros["paso"].duplicated(keep=False)
    parametros = {}
    for (_, fila), repetido in zip(tabla_parametros.iterrows(), repetidos):
        clave = f"{fila['etapa']}: {fila['paso']}" if repetido else fila["paso"]
        try:
            parametros[clave] = ast.literal_eval(fila["parametros"])
        except (ValueError, SyntaxError) as error:
            raise ValueError(
                f"Parámetros ilegibles en el paso {fila['paso']}: {fila['parametros']!r}"
            ) from error
    return parametros


def reconstruir_categorias(matriz, codificaciones, parametros=None):
    """Vuelve a juntar las columnas 0/1 en una columna con la categoría.

    `codificaciones` es la misma lista que usó la Fase 3: (variable, {categoría:
    columna}). La correspondencia se hace por nombre y no por posición: en los
    parámetros, las categorías aparecen ordenadas alfabéticamente y las columnas
    en el orden de la matriz, y unirlas por posición intercambiaría SNSS con No SNSS.
    Si se entregan los parámetros, se comprueba además que la Fase 3 generó
    exactamente esas columnas.
    """
    resultado = pd.DataFrame(index=matriz.index)
    for variable, columnas_por_categoria in codificaciones:
        columnas = list(columnas_por_categoria.values())
        faltan = [c for c in columnas if c not in matriz.columns]
        if faltan:
            raise KeyError(f"Faltan columnas indicadoras de {variable}: {faltan}")
        if parametros is not None:
            registradas = parametros[f"CodificadorBinario({variable})"]["columnas_generadas"]
            if registradas != columnas:
                raise ValueError(f"{variable}: la Fase 3 generó {registradas}, se esperaban {columnas}.")
        bloque = matriz[columnas].to_numpy()
        if not ((bloque == 0) | (bloque == 1)).all():
            raise ValueError(f"{variable}: las columnas indicadoras deben contener solo 0 y 1.")
        if not (bloque.sum(axis=1) == 1).all():
            raise ValueError(f"{variable}: hay filas sin exactamente una categoría activa.")
        # Posición del 1 en cada fila: como las columnas se tomaron en el orden del vocabulario,
        # la posición es directamente el código de la categoría. La Fase 4 midió esta versión
        # contra idxmax y contra un bucle de Python (sección 8 del cuaderno F4).
        posiciones = bloque.argmax(axis=1)
        resultado[variable] = pd.Categorical.from_codes(posiciones, categories=list(columnas_por_categoria))
    return resultado


def copia_interpretable(artefactos, codificaciones, parametros=None):
    """Matriz 0/1 de la Fase 3 convertida en una tabla legible, con su fila de origen.

    La clave de filas une cada fila de la matriz con su registro en el archivo
    original; se comprueba que esté completa y en orden antes de usarla.
    """
    matriz = artefactos["matriz"]
    clave = artefactos["clave_filas"]
    if len(clave) != len(matriz) or not (clave["fila_matriz"].to_numpy() == np.arange(1, len(matriz) + 1)).all():
        raise ValueError("La clave de filas no corresponde fila a fila con la matriz.")
    categorias = reconstruir_categorias(matriz, codificaciones, parametros)
    return pd.concat([clave[["fila_origen", "codigo_establecimiento"]].reset_index(drop=True),
                      categorias.reset_index(drop=True)], axis=1)


def agrupar_tipos(serie, agrupacion):
    """Asigna a cada tipo de establecimiento su grupo, según una agrupación declarada.

    Antes de buscar, colapsa los espacios repetidos: el registro escribe, por
    ejemplo, «Salud Mental  (COSAM)» con dos espacios. Un tipo sin grupo detiene la
    ejecución, para que un tipo nuevo del registro no quede fuera sin aviso.
    """
    grupo_por_tipo = {" ".join(tipo.split()): grupo for grupo, tipos in agrupacion.items() for tipo in tipos}
    normalizada = serie.astype(str).map(lambda texto: " ".join(texto.split()))
    sin_grupo = sorted(set(normalizada) - set(grupo_por_tipo))
    if sin_grupo:
        raise KeyError(f"Tipos de establecimiento sin grupo asignado: {sin_grupo}")
    return pd.Categorical(normalizada.map(grupo_por_tipo), categories=list(agrupacion))


def intervalo_wilson(exitos, total, z=1.96):
    """Intervalo de confianza de Wilson para una proporción.

    Se prefiere al intervalo normal porque no da límites negativos ni mayores
    que 1 cuando la proporción es pequeña o el grupo tiene pocos casos.
    """
    if total <= 0:
        raise ValueError("No se puede estimar una proporción sin observaciones.")
    if not 0 <= exitos <= total:
        raise ValueError(f"Los casos ({exitos}) deben estar entre 0 y el total ({total}).")
    p = exitos / total
    denominador = 1 + z ** 2 / total
    centro = (p + z ** 2 / (2 * total)) / denominador
    margen = z * math.sqrt(p * (1 - p) / total + z ** 2 / (4 * total ** 2)) / denominador
    # Con 0 casos o con todos, el límite es exacto: se fija para que el redondeo
    # de punto flotante no deje un 1e-17 donde debe haber un cero
    inferior = 0.0 if exitos == 0 else max(0.0, centro - margen)
    superior = 1.0 if exitos == total else min(1.0, centro + margen)
    return inferior, superior


def tasa_por_grupo(df, grupo, objetivo):
    """Proporción de un indicador 0/1 por grupo, con tamaño e intervalo al 95 %."""
    filas = []
    for valor, sub in df.groupby(grupo, observed=True):
        n = len(sub)
        casos = int(sub[objetivo].sum())
        inferior, superior = intervalo_wilson(casos, n)
        filas.append({grupo: valor, "n": n, "casos": casos, "tasa": casos / n,
                      "ic_inferior": inferior, "ic_superior": superior})
    return pd.DataFrame(filas)


def distribucion_por_grupo(df, grupo, variable):
    """Proporción de cada categoría de `variable` dentro de cada grupo, con su intervalo.

    Generaliza tasa_por_grupo a una variable con más de dos categorías: cada fila
    es una combinación grupo-categoría, y la proporción se calcula sobre el total
    del grupo.
    """
    filas = []
    for valor, sub in df.groupby(grupo, observed=True):
        n = len(sub)
        conteo = sub[variable].value_counts()
        categorias = sub[variable].cat.categories if hasattr(sub[variable], "cat") else sorted(conteo.index)
        for categoria in categorias:
            casos = int(conteo.get(categoria, 0))
            inferior, superior = intervalo_wilson(casos, n)
            filas.append({grupo: valor, variable: categoria, "n": n, "casos": casos,
                          "proporcion": casos / n, "ic_inferior": inferior, "ic_superior": superior})
    return pd.DataFrame(filas)


def v_cramer(chi2, n, filas, columnas):
    """Magnitud de la asociación entre 0 (independencia) y 1 (asociación perfecta)."""
    return math.sqrt(chi2 / (n * (min(filas, columnas) - 1)))


def residuos_ajustados(observadas, esperadas):
    """Residuos estandarizados ajustados de cada celda.

    Indican qué celdas se apartan de la independencia y en qué dirección: un valor
    mayor que 2 en valor absoluto señala una celda con más (o menos) casos de los
    esperados si no hubiera asociación.
    """
    obs = np.asarray(observadas, dtype=float)
    esp = np.asarray(esperadas, dtype=float)
    n = obs.sum()
    prop_filas = obs.sum(axis=1, keepdims=True) / n
    prop_columnas = obs.sum(axis=0, keepdims=True) / n
    return (obs - esp) / np.sqrt(esp * (1 - prop_filas) * (1 - prop_columnas))


def log10_valor_p(chi2, gl):
    """Logaritmo en base 10 del valor p de una chi-cuadrado, aun cuando el valor p es ínfimo.

    Con estadísticos muy grandes, SciPy devuelve p = 0 y su logaritmo -inf, porque el
    número es menor que el mínimo representable. En ese caso se usa la expansión
    asintótica de la función gamma incompleta superior, Q(s, x) con s = gl/2 y
    x = chi2/2:  ln Q ≈ (s - 1) ln x - x - ln Γ(s) + ln(1 + (s-1)/x + (s-1)(s-2)/x² + ...).
    Con 2 grados de libertad la serie termina en el primer término y el resultado es
    exacto: ln p = -chi2 / 2.
    """
    logaritmo = stats.chi2.logsf(chi2, gl)
    if np.isfinite(logaritmo):
        return float(logaritmo / math.log(10))
    s, x = gl / 2, chi2 / 2
    termino, serie = 1.0, 1.0
    for k in range(1, 30):
        termino *= (s - k) / x
        serie += termino
        if abs(termino) < 1e-16:
            break
    ln_q = (s - 1) * math.log(x) - x - math.lgamma(s) + math.log(serie)
    return ln_q / math.log(10)


def prueba_independencia(tabla):
    """Prueba chi-cuadrado de independencia y V de Cramér para una tabla de contingencia.

    Revisa antes la condición de aplicación: todas las frecuencias esperadas
    deberían ser al menos 5. No la impone; la informa, para que la lectura del
    resultado la considere. Devuelve un diccionario con el estadístico, los grados
    de libertad, el logaritmo en base 10 del valor p (el valor p puede ser tan
    pequeño que se redondea a cero), las esperadas y los residuos ajustados.
    """
    tabla = pd.DataFrame(tabla)
    if tabla.shape[0] < 2 or tabla.shape[1] < 2:
        raise ValueError("La prueba requiere al menos dos filas y dos columnas.")
    if (tabla.sum(axis=1) == 0).any() or (tabla.sum(axis=0) == 0).any():
        raise ValueError("La tabla tiene una fila o una columna sin casos: elimínela antes de probar.")
    chi2, p, gl, esperadas = stats.chi2_contingency(tabla.to_numpy(), correction=False)
    n = int(tabla.to_numpy().sum())
    esperadas = pd.DataFrame(esperadas, index=tabla.index, columns=tabla.columns)
    return {
        "n": n,
        "chi2": float(chi2),
        "gl": int(gl),
        "p": float(p),
        "log10_p": log10_valor_p(chi2, gl),
        "v_cramer": v_cramer(chi2, n, *tabla.shape),
        "esperada_minima": float(esperadas.to_numpy().min()),
        "celdas_esperada_menor_5": int((esperadas.to_numpy() < 5).sum()),
        "esperadas": esperadas,
        "residuos": pd.DataFrame(residuos_ajustados(tabla, esperadas), index=tabla.index, columns=tabla.columns),
    }


# --- AGREGADO (Fase 4: comparación dentro de los tipos presentes en ambos grupos) ---
# Para controlar el tipo de establecimiento como variable de confusión, la comparación se repite solo en los tipos
# que tienen establecimientos de los dos grupos: en un tipo con un solo grupo no hay nada que comparar.
def estratos_compartidos(df, estrato, grupo):
    """Devuelve, ordenados de mayor a menor tamaño, los valores de `estrato` en que aparecen todos los grupos."""
    conteo = pd.crosstab(df[estrato], df[grupo])
    compartidos = conteo[(conteo > 0).all(axis=1)]
    return compartidos.sum(axis=1).sort_values(ascending=False, kind="stable").index.tolist()


def resumir_estrato(sub, nombre, grupo, variable, orden_grupos, orden_niveles):
    """Compara la distribución de `variable` entre los grupos dentro de un estrato.

    Devuelve un diccionario con el tamaño del estrato y de cada grupo, la proporción de cada nivel
    dentro de cada grupo (porcentaje por fila), la V de Cramér, la esperada mínima y una lectura:
    - «sin comparación posible» si falta alguno de los grupos (V sin valor);
    - «sin diferencia: un solo nivel» si todos los establecimientos tienen el mismo nivel (V = 0);
    - «comparable» o «esperadas < 5: leer con cautela», según la condición de la prueba chi-cuadrado.
    """
    tabla = (pd.crosstab(sub[grupo], sub[variable])
             .reindex(index=orden_grupos, columns=orden_niveles, fill_value=0))
    fila = {"estrato": nombre, "n": int(tabla.to_numpy().sum())}
    for g in orden_grupos:
        fila[f"n_{g}"] = int(tabla.loc[g].sum())
    for g in orden_grupos:
        total = tabla.loc[g].sum()
        for nivel in orden_niveles:
            fila[f"{nivel}_{g}"] = tabla.loc[g, nivel] / total if total else np.nan
    if (tabla.sum(axis=1) == 0).any():
        fila.update({"v_cramer": np.nan, "esperada_minima": np.nan, "lectura": "sin comparación posible"})
        return fila
    util = tabla.loc[:, tabla.sum(axis=0) > 0]
    if util.shape[1] < 2:
        fila.update({"v_cramer": 0.0, "esperada_minima": np.nan, "lectura": "sin diferencia: un solo nivel"})
        return fila
    resultado = prueba_independencia(util)
    fila.update({"v_cramer": resultado["v_cramer"], "esperada_minima": resultado["esperada_minima"],
                 "lectura": "comparable" if resultado["celdas_esperada_menor_5"] == 0
                            else "esperadas < 5: leer con cautela"})
    return fila


def guardar_figura(figura, carpeta, nombre, dpi=200):
    """Guarda la figura en PNG con resolución de impresión y devuelve la ruta."""
    carpeta = Path(carpeta)
    carpeta.mkdir(parents=True, exist_ok=True)
    ruta = carpeta / f"{nombre}.png"
    figura.savefig(ruta, dpi=dpi, bbox_inches="tight")
    return ruta
