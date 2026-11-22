"""Pruebas de src/comunicacion.py con tablas pequeñas cuyo resultado se conoce de antemano.

Se ejecutan junto con las del núcleo desde la raíz del proyecto:

    python -m unittest -v
"""
import math
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from src import comunicacion as com
from src.configuracion import AGRUPACION_TIPOS, CODIFICACIONES

RAIZ = Path(__file__).resolve().parent.parent


def matriz_pequena():
    """Tres establecimientos: SNSS-Baja, No SNSS-Mediana y No SNSS-Alta."""
    return pd.DataFrame({"snss_perteneciente": [1, 0, 0], "snss_no_perteneciente": [0, 1, 1],
                         "complejidad_baja": [1, 0, 0], "complejidad_mediana": [0, 1, 0],
                         "complejidad_alta": [0, 0, 1]})


class TestReconstruccion(unittest.TestCase):
    def test_caso_normal_recupera_las_categorias(self):
        resultado = com.reconstruir_categorias(matriz_pequena(), CODIFICACIONES)
        self.assertEqual(list(resultado["pertenencia_snss"]), ["SNSS", "No SNSS", "No SNSS"])
        self.assertEqual(list(resultado["complejidad"]), ["Baja", "Mediana", "Alta"])

    def test_correspondencia_por_nombre_y_no_por_posicion(self):
        # Mismo contenido con las columnas en otro orden: el resultado no cambia
        desordenada = matriz_pequena()[["complejidad_alta", "snss_no_perteneciente", "complejidad_baja",
                                        "snss_perteneciente", "complejidad_mediana"]]
        resultado = com.reconstruir_categorias(desordenada, CODIFICACIONES)
        self.assertEqual(list(resultado["pertenencia_snss"]), ["SNSS", "No SNSS", "No SNSS"])

    def test_limite_categoria_sin_casos_se_conserva(self):
        solo_snss = matriz_pequena().iloc[[0]]
        resultado = com.reconstruir_categorias(solo_snss, CODIFICACIONES)
        self.assertEqual(list(resultado["complejidad"].cat.categories), ["Baja", "Mediana", "Alta"])

    def test_excepcion_fila_sin_categoria_activa(self):
        matriz = matriz_pequena()
        matriz.loc[0, "complejidad_baja"] = 0
        with self.assertRaises(ValueError):
            com.reconstruir_categorias(matriz, CODIFICACIONES)

    def test_excepcion_columna_faltante(self):
        with self.assertRaises(KeyError):
            com.reconstruir_categorias(matriz_pequena().drop(columns="complejidad_alta"), CODIFICACIONES)

    def test_excepcion_parametros_desalineados(self):
        parametros = {"CodificadorBinario(pertenencia_snss)":
                      {"columnas_generadas": ["snss_no_perteneciente", "snss_perteneciente"]}}
        with self.assertRaises(ValueError):
            com.reconstruir_categorias(matriz_pequena(), CODIFICACIONES[:1], parametros)


class TestParametrosYCarga(unittest.TestCase):
    def test_pasos_repetidos_no_se_sobrescriben(self):
        tabla = pd.DataFrame({"etapa": ["población", "codificación"], "orden": [9, 3],
                              "paso": ["seleccionar_columnas(5 columnas)"] * 2, "parametros": ["{}", "{}"]})
        self.assertEqual(len(com.leer_parametros(tabla)), 2)

    def test_excepcion_parametros_ilegibles(self):
        tabla = pd.DataFrame({"etapa": ["x"], "orden": [1], "paso": ["p"], "parametros": ["media=1"]})
        with self.assertRaises(ValueError):
            com.leer_parametros(tabla)

    def test_excepcion_faltan_salidas_de_f3(self):
        with tempfile.TemporaryDirectory() as carpeta:
            with self.assertRaises(FileNotFoundError):
                com.cargar_artefactos(carpeta)


class TestProporciones(unittest.TestCase):
    def test_wilson_contiene_la_proporcion(self):
        inferior, superior = com.intervalo_wilson(30, 100)
        self.assertLess(inferior, 0.30)
        self.assertGreater(superior, 0.30)

    def test_limite_wilson_sin_casos_y_con_todos(self):
        self.assertEqual(com.intervalo_wilson(0, 22)[0], 0.0)
        self.assertEqual(com.intervalo_wilson(10, 10)[1], 1.0)

    def test_excepcion_wilson_sin_observaciones(self):
        with self.assertRaises(ValueError):
            com.intervalo_wilson(0, 0)

    def test_distribucion_suma_uno_por_grupo(self):
        datos = com.reconstruir_categorias(matriz_pequena(), CODIFICACIONES)
        tabla = com.distribucion_por_grupo(datos, "pertenencia_snss", "complejidad")
        self.assertTrue(np.allclose(tabla.groupby("pertenencia_snss", observed=True)["proporcion"].sum(), 1))


class TestIndependencia(unittest.TestCase):
    def test_tabla_independiente_da_v_cero(self):
        tabla = pd.DataFrame([[10, 20, 30], [20, 40, 60]], index=["A", "B"], columns=["x", "y", "z"])
        resultado = com.prueba_independencia(tabla)
        self.assertAlmostEqual(resultado["chi2"], 0.0)
        self.assertAlmostEqual(resultado["v_cramer"], 0.0)

    def test_tabla_perfecta_da_v_uno(self):
        tabla = pd.DataFrame([[50, 0], [0, 50]])
        self.assertAlmostEqual(com.prueba_independencia(tabla)["v_cramer"], 1.0)

    def test_estadistico_coincide_con_la_formula(self):
        tabla = pd.DataFrame([[30, 10, 5], [10, 30, 15]])
        observadas = tabla.to_numpy()
        esperadas = np.outer(observadas.sum(1), observadas.sum(0)) / observadas.sum()
        chi2_manual = ((observadas - esperadas) ** 2 / esperadas).sum()
        resultado = com.prueba_independencia(tabla)
        self.assertAlmostEqual(resultado["chi2"], chi2_manual)
        # Con dos grados de libertad, el valor p es exactamente exp(-chi2 / 2)
        self.assertAlmostEqual(resultado["log10_p"], -chi2_manual / 2 / math.log(10))

    def test_limite_valor_p_infimo_no_se_pierde(self):
        # SciPy redondea este valor p a cero; el logaritmo debe seguir siendo exacto
        self.assertAlmostEqual(com.log10_valor_p(2000.0, 2), -1000 / math.log(10))
        self.assertTrue(math.isfinite(com.log10_valor_p(3000.0, 4)))

    def test_excepcion_columna_sin_casos(self):
        with self.assertRaises(ValueError):
            com.prueba_independencia(pd.DataFrame([[10, 0], [5, 0]]))


class TestAgrupacionTipos(unittest.TestCase):
    def test_espacios_repetidos_no_impiden_agrupar(self):
        serie = pd.Series(["Centro Comunitario de Salud Mental  (COSAM)", "Hospital"])
        self.assertEqual(list(com.agrupar_tipos(serie, AGRUPACION_TIPOS)),
                         ["Centros ambulatorios y de especialidad", "Hospitales y clínicas"])

    def test_excepcion_tipo_sin_grupo(self):
        with self.assertRaises(KeyError):
            com.agrupar_tipos(pd.Series(["Tipo inventado"]), AGRUPACION_TIPOS)


# --- AGREGADO (Fase 4): pruebas de la comparación dentro de los tipos presentes en ambos grupos ---
class TestEstratos(unittest.TestCase):
    GRUPOS, NIVELES = ["SNSS", "No SNSS"], ["Baja", "Mediana", "Alta"]

    def datos(self):
        """Tipo A con los dos grupos y niveles distintos; tipo B solo SNSS; tipo C con los dos grupos y un solo nivel."""
        return pd.DataFrame({
            "tipo": ["A"] * 6 + ["B"] * 3 + ["C"] * 4,
            "grupo": ["SNSS", "SNSS", "SNSS", "No SNSS", "No SNSS", "No SNSS"] + ["SNSS"] * 3
                     + ["SNSS", "SNSS", "No SNSS", "No SNSS"],
            "nivel": ["Baja", "Baja", "Baja", "Mediana", "Mediana", "Mediana"] + ["Baja"] * 3 + ["Baja"] * 4})

    def test_estratos_compartidos_excluye_tipos_de_un_solo_grupo(self):
        self.assertEqual(com.estratos_compartidos(self.datos(), "tipo", "grupo"), ["A", "C"])

    def test_resumen_con_asociacion_perfecta(self):
        sub = self.datos().query("tipo == 'A'")
        fila = com.resumir_estrato(sub, "A", "grupo", "nivel", self.GRUPOS, self.NIVELES)
        self.assertEqual((fila["n"], fila["n_SNSS"], fila["n_No SNSS"]), (6, 3, 3))
        self.assertAlmostEqual(fila["Baja_SNSS"], 1.0)
        self.assertAlmostEqual(fila["v_cramer"], 1.0)

    def test_limite_un_solo_nivel_y_un_solo_grupo(self):
        datos = self.datos()
        un_nivel = com.resumir_estrato(datos.query("tipo == 'C'"), "C", "grupo", "nivel", self.GRUPOS, self.NIVELES)
        un_grupo = com.resumir_estrato(datos.query("tipo == 'B'"), "B", "grupo", "nivel", self.GRUPOS, self.NIVELES)
        self.assertEqual((un_nivel["v_cramer"], un_nivel["lectura"]), (0.0, "sin diferencia: un solo nivel"))
        self.assertTrue(math.isnan(un_grupo["v_cramer"]))
        self.assertEqual(un_grupo["lectura"], "sin comparación posible")


if __name__ == "__main__":
    unittest.main()
