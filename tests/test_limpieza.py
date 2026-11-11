"""Pruebas de la limpieza, la imputación, las distancias y la transformación.

Ejecución desde la raíz del proyecto:
    python -m unittest tests.test_limpieza -v
"""

import unittest

import numpy as np
import pandas as pd

from src import ProyectoError, limpieza as modulo_limpieza
from src.geo import distancia_minima_km, haversine_km, vecino_mas_cercano
from src.imputacion import (comparar_imputaciones, error_dejando_uno_fuera, error_oculto_coordenadas,
                            error_oculto_escalar, error_ponderado_como_faltantes, imputar_por_grupo,
                            resumir_error_por_estrato)
from src.limpieza import (anular_coordenadas_erroneas, aplicar_mapeos, atipicos_iqr, completar_por_condicion,
                          convertir_fechas, convertir_numericas, depurar_fechas, detectar_pseudonulos,
                          detectar_variantes, imputar_categorica_por_grupo, marcar_posibles_duplicados,
                          marcar_coordenadas_relativas, normalizar_texto)
from src.transformacion import (MACROZONAS, MACROZONAS_ALTERNATIVA, ORDEN_COMPLEJIDAD, ORDEN_NIVEL_ATENCION,
                                agrupar_categorias_raras, asignar_macrozona, calcular_antiguedad, codificar_one_hot,
                                codificar_ordinal, comparar_escaladores, contar_por_grupo, escalar_robusto,
                                estabilidad_escaladores, marcar_niveles_referencia, marcar_referencia_urgencia,
                                verificar_propiedad_escalador)


class TestLimpieza(unittest.TestCase):
    def test_normalizar_texto(self):
        self.assertEqual(normalizar_texto(pd.Series(["  Sala   Externa "])).iloc[0], "Sala Externa")
        with self.assertRaises(ProyectoError):
            normalizar_texto(pd.Series([1, 2]))

    def test_detectar_variantes_y_pseudonulos(self):
        datos = pd.DataFrame({"c": ["NO", "No", "SI"], "d": ["-", "x", None]})
        self.assertEqual(len(detectar_variantes(datos, ["c"])), 1)
        self.assertEqual(detectar_pseudonulos(datos)["cantidad"].sum(), 1)

    def test_mapeos_no_modifican_el_original(self):
        original = pd.DataFrame({"c": ["No"]})
        salida, cambios = aplicar_mapeos(original, {"c": {"No": "NO"}})
        self.assertEqual(original["c"].iloc[0], "No")
        self.assertEqual(salida["c"].iloc[0], "NO")
        self.assertEqual(cambios["filas"].iloc[0], 1)

    def test_fechas_con_formato_explicito(self):
        salida, tabla = convertir_fechas(pd.DataFrame({"f": ["01-02-2020", None, "99-99-2020"]}), ["f"])
        self.assertEqual(salida["f"].iloc[0], pd.Timestamp("2020-02-01"))
        self.assertEqual(tabla["no_convertidas"].iloc[0], 1)

    def test_numericas_admiten_coma_decimal(self):
        salida, malos = convertir_numericas(pd.DataFrame({"x": ["-33,5", "abc", None]}), ["x"])
        self.assertEqual(salida["x"].iloc[0], -33.5)
        self.assertEqual(malos["x"], 1)

    def test_atipicos_iqr(self):
        mascara, _, _ = atipicos_iqr(pd.Series([1.0, 2.0, 3.0, 4.0, 100.0]))
        self.assertEqual(int(mascara.sum()), 1)

    def test_coordenadas_erroneas(self):
        datos = pd.DataFrame({"Latitud": [-33.0, -33.01, -33.02, -39.0], "Longitud": [-70.0] * 4,
            "ComunaCodigo": ["13101"] * 4})
        salida, errores = anular_coordenadas_erroneas(datos, 400)
        self.assertEqual(int(errores.sum()), 1)
        self.assertTrue(np.isnan(salida["Latitud"].iloc[3]))

    def test_depurar_fechas(self):
        datos = pd.DataFrame({"FechaInicioFuncionamientoEstab": pd.to_datetime(["2030-01-01", "2020-01-01",
            "2010-01-01"]),
                              "FechaCierre": pd.to_datetime([None, "2019-01-01", "2015-01-01"])})
        salida, conteos = depurar_fechas(datos, "03-11-2026")
        self.assertEqual(conteos, {"inicio_posterior_al_corte": 1, "inicio_posterior_al_cierre": 1})
        self.assertEqual(int(salida["FechaInicioFuncionamientoEstab"].isna().sum()), 2)

    def test_completar_por_condicion(self):
        datos = pd.DataFrame({"a": [None, None, "x"], "b": [True, False, True]})
        salida, n = completar_por_condicion(datos, "a", datos["b"], "No Aplica")
        self.assertEqual(n, 1)
        self.assertEqual(salida["a"].iloc[0], "No Aplica")
        self.assertTrue(pd.isna(salida["a"].iloc[1]))

    def test_imputar_categorica_con_grupo_nulo(self):
        datos = pd.DataFrame({"g": ["a", "a", None], "v": ["x", None, None]})
        salida, conteos = imputar_categorica_por_grupo(datos, "v", "g")
        self.assertEqual(salida["v"].tolist(), ["x", "x", "Sin dato"])
        self.assertEqual(conteos, {"imputados_moda_grupo": 1, "etiquetados_sin_dato": 1})

    def test_duplicados_ignoran_claves_incompletas(self):
        datos = pd.DataFrame({"n": ["a", "a", "b", "b"], "v": ["x", "x", None, None]})
        self.assertEqual(marcar_posibles_duplicados(datos, ["n", "v"]).tolist(), [True, True, False, False])


class TestImputacion(unittest.TestCase):
    def test_efecto_en_variabilidad(self):
        tabla = comparar_imputaciones(pd.Series([1.0, 2.0, 9.0, np.nan, np.nan], name="v"))
        self.assertEqual(tabla.loc[0, "filas_perdidas"], 2)
        self.assertLess(tabla.loc[tabla["metodo"].eq("mediana"), "cambio_desv_pct"].iloc[0], 0)

    def test_mediana_por_grupo_y_bandera(self):
        datos = pd.DataFrame({"x": [1.0, np.nan, 10.0, np.nan], "g": ["a", "a", "b", "c"], "r": ["R", "R", "S", "S"]})
        salida, conteos = imputar_por_grupo(datos, ["x"], "g", "r", "_imputada")
        self.assertEqual(salida["x"].tolist(), [1.0, 1.0, 10.0, 10.0])
        self.assertEqual(salida["x_imputada"].tolist(), [0, 1, 0, 1])
        self.assertEqual(conteos["x"], {"por_grupo": 1, "por_respaldo": 1})

    def test_error_oculto_es_reproducible(self):
        datos = pd.DataFrame({"Latitud": np.linspace(-40, -30, 100), "Longitud": np.linspace(-72, -70, 100),
            "c": ["a", "b"] * 50})
        pd.testing.assert_frame_equal(error_oculto_coordenadas(datos, "c", semilla=42),
            error_oculto_coordenadas(datos, "c", semilla=42))


class TestGeo(unittest.TestCase):
    def test_distancia_conocida(self):
        self.assertAlmostEqual(float(haversine_km(0, 0, 0, 1)), 111.195, places=2)

    def test_minimo_entre_referencias(self):
        salida = distancia_minima_km([-33.0, np.nan], [-70.0, -70.0], [-33.0, -40.0], [-70.0, -70.0])
        self.assertEqual(salida[0], 0.0)
        self.assertTrue(np.isnan(salida[1]))

    def test_sin_referencias(self):
        with self.assertRaises(ProyectoError):
            distancia_minima_km([-33.0], [-70.0], [], [])


class TestTransformacion(unittest.TestCase):
    def test_macrozona_y_conteo(self):
        self.assertEqual(asignar_macrozona(pd.Series(["11"])).iloc[0], "Austral")
        self.assertEqual(contar_por_grupo(pd.Series(["a", "a", "b"])).tolist(), [2, 2, 1])

    def test_antiguedad_conserva_faltantes(self):
        salida = calcular_antiguedad(pd.Series(pd.to_datetime(["2016-11-03", None])), "03-11-2026")
        self.assertAlmostEqual(salida.iloc[0], 10.0, places=2)
        self.assertTrue(np.isnan(salida.iloc[1]))

    def test_referencia_excluye_dental_y_estacional(self):
        datos = pd.DataFrame({"TieneServicioUrgencia": ["SI", "SI", "SI", "NO", "SI", "SI", "SI"],
                              "TipoUrgencia": ["Urgencia Hospitalaria (UEH)", "SAPU Dental",
                                  "Urgencia Ambulatoria (SAPU)",
                                               "No Aplica", "Hospitalaria Especializada", "Otro",
                                                   "Urgencia Hospitalaria (UEH)"],
                              "ClasificacionTipoSapu": ["No Aplica", "Corto", "Verano", "No Aplica", "No Aplica",
                                  "No Aplica", "No Aplica"],
                              "EstablecimientoGlosa": ["Hospital", "SAPU D", "SAPU V", "Posta", "Instituto", "Centro",
                                                       "Hospital Psiquiátrico"]})
        self.assertEqual(marcar_referencia_urgencia(datos).tolist(), [True, False, False, False, False, False, False])

    def test_agrupar_raras(self):
        salida, raras = agrupar_categorias_raras(pd.Series(["a"] * 99 + ["b"]), umbral=0.05)
        self.assertEqual(raras, ["b"])
        self.assertEqual(salida.iloc[-1], "Otros tipos")

    def test_ordinal_no_es_alfabetico(self):
        orden = ["Baja Complejidad", "Mediana Complejidad", "Alta Complejidad"]
        salida = codificar_ordinal(pd.Series(["Alta Complejidad", "Baja Complejidad", "No Aplica"], name="c"), orden)
        self.assertEqual(salida["c"].tolist(), [3, 1, 0])
        self.assertEqual(salida["c_fuera_escala"].tolist(), [0, 0, 1])

    def test_ordinal_rechaza_nulos_y_desconocidos(self):
        with self.assertRaises(ProyectoError):
            codificar_ordinal(pd.Series(["x", None], name="c"), ["x"])
        with self.assertRaises(ProyectoError):
            codificar_ordinal(pd.Series(["z"], name="c"), ["x"])

    def test_one_hot_nombres_y_suma(self):
        matriz, grupos = codificar_one_hot(pd.DataFrame({"c": ["Público", "Privado"]}), ["c"], {"c": "sis"})
        self.assertEqual(grupos["c"], ["sis__privado", "sis__publico"])
        self.assertTrue(matriz.sum(axis=1).eq(1).all())

    def test_escaladores_cumplen_su_propiedad(self):
        datos = pd.DataFrame({"x": np.arange(100, dtype=float) ** 2})
        self.assertEqual(len(comparar_escaladores(datos, ["x"])), 3)
        self.assertEqual(len(estabilidad_escaladores(datos, ["x"])), 3)
        salida, parametros = escalar_robusto(datos, ["x"])
        self.assertTrue(verificar_propiedad_escalador(salida["x_esc"], "robusto"))
        self.assertIn("mediana", parametros["x"])
        with self.assertRaises(ProyectoError):
            verificar_propiedad_escalador([1.0, 2.0], "desconocido")


class TestDefinicionesDeclaradas(unittest.TestCase):
    """Fijan decisiones que, si cambian por error, alteran resultados sin lanzar excepciones."""

    def test_macrozonas_exactas(self):
        esperado = {"Norte": {"15", "01", "02", "03", "04"}, "Centro": {"05", "13", "06", "07", "16"},
                    "Sur": {"08", "09", "14", "10"}, "Austral": {"11", "12"}}
        for zona, regiones in esperado.items():
            self.assertEqual({r for r, z in MACROZONAS.items() if z == zona}, regiones, zona)
        self.assertEqual(MACROZONAS["10"], "Sur")
        self.assertEqual(MACROZONAS["04"], "Norte")

    def test_macrozona_alternativa(self):
        self.assertEqual(MACROZONAS_ALTERNATIVA["10"], "Austral")
        self.assertEqual(MACROZONAS_ALTERNATIVA["04"], "Centro")
        distintas = {r for r in MACROZONAS if MACROZONAS[r] != MACROZONAS_ALTERNATIVA[r]}
        self.assertEqual(distintas, {"10", "04"})

    def test_orden_de_las_escalas(self):
        self.assertEqual(ORDEN_COMPLEJIDAD, ["Baja Complejidad", "Mediana Complejidad", "Alta Complejidad"])
        self.assertEqual(ORDEN_NIVEL_ATENCION, ["Primer Nivel", "Segundo Nivel", "Tercer Nivel"])

    def test_mapeo_gendarmeria(self):
        for columna in ("DependenciaAdministrativa", "TipoSistemaSaludGlosa"):
            self.assertEqual(modulo_limpieza.MAPEOS_CATEGORIAS[columna], {"Gendamería": "Gendarmería"})
        salida, _ = aplicar_mapeos(pd.DataFrame({"TipoSistemaSaludGlosa": ["Gendamería"]}),
                                   {"TipoSistemaSaludGlosa":
                                    modulo_limpieza.MAPEOS_CATEGORIAS["TipoSistemaSaludGlosa"]})
        self.assertEqual(salida.iloc[0, 0], "Gendarmería")


class TestImputacionExacta(unittest.TestCase):
    def test_usa_mediana_y_no_media(self):
        # La media del grupo es 40 y la mediana, 10: el extremo no debe arrastrar el valor.
        datos = pd.DataFrame({"x": [10.0, 10.0, 100.0, np.nan], "g": ["a"] * 4})
        salida, _ = imputar_por_grupo(datos, ["x"], "g")
        self.assertEqual(salida["x"].iloc[3], 10.0)

    def test_fraccion_oculta_coordenadas(self):
        datos = pd.DataFrame({"Latitud": np.linspace(-40, -30, 200), "Longitud": np.linspace(-72, -70, 200),
            "c": ["a", "b"] * 100})
        self.assertEqual(error_oculto_coordenadas(datos, "c")["ocultos"].iloc[0], 20)
        self.assertEqual(error_oculto_coordenadas(datos, "c", fraccion=0.25)["ocultos"].iloc[0], 50)

    def test_fraccion_oculta_escalar(self):
        serie = pd.Series(np.arange(200, dtype=float), name="v")
        grupo = pd.Series(["a", "b"] * 100)
        self.assertEqual(error_oculto_escalar(serie, grupo)["ocultos"].iloc[0], 20)

    def test_dejando_uno_fuera(self):
        datos = pd.DataFrame({"Latitud": [-33.0, -33.0, -33.0, -40.0], "Longitud": [-70.0] * 4,
                              "c": ["a", "a", "a", "b"], "r": ["R"] * 4})
        km = error_dejando_uno_fuera(datos, "c", "r")
        self.assertEqual(km.iloc[0], 0.0)
        self.assertGreater(km.iloc[3], 500)  # comuna con un solo punto: usa la mediana de la región

    def test_ponderado_usa_composicion_de_faltantes(self):
        error = pd.Series([1.0, 1.0, 9.0, 9.0])
        estrato = pd.Series(["a", "a", "b", "b"])
        resultado = error_ponderado_como_faltantes(error, estrato, pd.Series(["b", "b", "b", "a"]))
        self.assertAlmostEqual(resultado["media_km"], 7.0)
        self.assertEqual(resumir_error_por_estrato(error, estrato).loc["a", "n"], 2)
        with self.assertRaises(ProyectoError):
            error_ponderado_como_faltantes(error, estrato, pd.Series(["z"]))


class TestCoordenadasRelativas(unittest.TestCase):
    def test_marca_punto_lejano_en_comuna_compacta(self):
        latitudes = [-33.0 - i / 1000 for i in range(30)] + [-34.0]
        datos = pd.DataFrame({"Latitud": latitudes, "Longitud": [-70.0] * 31, "ComunaCodigo": ["1"] * 31})
        self.assertEqual(marcar_coordenadas_relativas(datos).tolist(), [False] * 30 + [True])

    def test_comuna_pequena_no_se_marca(self):
        datos = pd.DataFrame({"Latitud": [-33.0, -34.0], "Longitud": [-70.0, -70.0], "ComunaCodigo": ["1", "1"]})
        self.assertFalse(marcar_coordenadas_relativas(datos).any())


class TestGeoAdicional(unittest.TestCase):
    def test_vecino_devuelve_posicion_original(self):
        km, indice = vecino_mas_cercano([-33.0], [-70.0], [np.nan, -40.0, -33.1], [np.nan, -70.0, -70.0])
        self.assertEqual(indice[0], 2)
        self.assertAlmostEqual(km[0], 11.12, places=1)


class TestNiveles(unittest.TestCase):
    def test_niveles_son_anidados(self):
        datos = pd.DataFrame({
            "TieneServicioUrgencia": ["SI"] * 6,
            "TipoUrgencia": ["Urgencia Hospitalaria (UEH)"] * 3 + ["Urgencia Ambulatoria (SUR)",
                "Urgencia Ambulatoria (SAPU)", "Urgencia Hospitalaria (UEH)"],
            "ClasificacionTipoSapu": ["No Aplica"] * 4 + ["Corto", "No Aplica"],
            "EstablecimientoGlosa": list("abcdef"),
            "TipoSistemaSaludGlosa": ["Público", "Público", "Público", "Público", "Público", "Privado"],
            "NivelComplejidadEstabGlosa": ["Alta Complejidad", "Mediana Complejidad", "Baja Complejidad",
                "Baja Complejidad", "Baja Complejidad", "Alta Complejidad"]})
        niveles = marcar_niveles_referencia(datos)
        self.assertEqual(niveles.sum().to_dict(), {"es_referencia_urgencia": 6, "ref_sin_sur": 5, "ref_ueh": 4,
            "ref_ueh_pub_am": 2,
                                                   "ref_ueh_pub_a": 1, "ref_sin_sapu_corto": 5})


if __name__ == "__main__":
    unittest.main()
