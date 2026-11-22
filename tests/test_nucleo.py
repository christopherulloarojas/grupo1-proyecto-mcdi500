"""Pruebas del núcleo algorítmico con tablas pequeñas construidas a mano.

Se ejecutan desde la raíz del proyecto con un solo comando:

    python -m unittest -v
"""
import gc
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.carga import cargar_registro
from src.configuracion import (CODIFICACIONES, COLUMNAS_NECESARIAS, COLUMNAS_NUMERICAS, ESTADOS_VIGENTES,
                               MAPA_PERTENENCIA, crear_configuracion)
from src.conflictos import conflictos_con_diccionario, conflictos_con_lista, conflictos_vectorizado
from src.estructura import aplanar, recorrer_jerarquia
from src.fabrica import construir_codificacion, crear_filtro
from src.funciones import normalizar_columna, seleccionar_columnas
from src.observadores import BitacoraFiltros
from src.pipeline import Pipeline, PipelineObservable
from src.preprocesador import PreprocesadorRegistro
from src.referencia_f2 import flujo_f2
from src.transformadores import (CodificadorBinario, Filtro, FiltroCodigosEnConflicto, FiltroInformado,
                                 FiltroValoresPermitidos, MapeadorCategorias, PasoFuncion, Transformador)

RAIZ = Path(__file__).resolve().parent.parent
SNSS = "Perteneciente al Sistema Nacional de Servicios de Salud"
NO_SNSS = "No Perteneciente al Sistema Nacional de Servicios de Salud"


def registro_pequeno():
    """Seis establecimientos cuyo destino se conoce de antemano."""
    return pd.DataFrame({
        "EstablecimientoCodigo": ["101", "102", "103", "104", "105", "106"],
        "EstadoFuncionamiento": ["Vigente en Operación Habitual", "Vigente en operación habitual", "Cerrado",
                                 "Vigente en Operación Habitual", "Vigente en Operación Habitual",
                                 "Vigente en Operación Habitual"],
        "TipoPertenenciaEstabGlosa": [SNSS, NO_SNSS, SNSS, "No Aplica", SNSS, NO_SNSS],
        "NivelComplejidadEstabGlosa": ["Baja Complejidad", "Alta Complejidad", "Baja Complejidad",
                                       "Baja Complejidad", "", "No Aplica"],
    }, dtype="string")


def preprocesador_pequeno():
    datos = registro_pequeno()
    return PreprocesadorRegistro(crear_configuracion(datos.columns)), datos


class TestCasosNormales(unittest.TestCase):
    """Datos típicos con su resultado esperado."""

    def test_normalizar_columna(self):
        """Normalizar unifica espacios y mayúsculas sin modificar la tabla de entrada."""
        datos = pd.DataFrame({"estado": ["  Vigente   EN Operación  ", "Cerrado"]}, dtype="string")
        salida = normalizar_columna(datos, "estado", "estado_normalizado")
        self.assertEqual(salida["estado_normalizado"].tolist(), ["vigente en operación", "cerrado"])
        self.assertNotIn("estado_normalizado", datos.columns)

    def test_mapeador_aprende_valores_sin_correspondencia(self):
        """El mapeador traduce las categorías y recuerda cuáles no tienen correspondencia."""
        datos = pd.DataFrame({"origen": list(MAPA_PERTENENCIA) + ["no aplica"]}, dtype="string")
        mapeador = MapeadorCategorias("origen", "destino", MAPA_PERTENENCIA)
        salida = mapeador.ajustar_transformar(datos)
        self.assertEqual(salida["destino"].tolist()[:2], ["SNSS", "No SNSS"])
        self.assertTrue(pd.isna(salida["destino"].iloc[2]))
        self.assertEqual(mapeador.parametros["sin_correspondencia"], ["no aplica"])

    def test_filtro_recuerda_los_excluidos(self):
        """El filtro conserva las filas válidas y guarda las excluidas con su paso y motivo."""
        datos = pd.DataFrame({"estado": ["vigente en operación habitual", "cerrado"]})
        filtro = FiltroValoresPermitidos("estado", ESTADOS_VIGENTES, "F01", "Conservar estado vigente")
        salida = filtro.ajustar_transformar(datos)
        self.assertEqual(len(salida), 1)
        self.assertEqual(filtro.excluidos["paso_exclusion"].tolist(), ["F01"])
        self.assertEqual(filtro.excluidos["motivo_exclusion"].tolist(), ["Conservar estado vigente"])

    def test_codificador_genera_indicadores(self):
        """El codificador crea una columna 0/1 por categoría declarada."""
        datos = pd.DataFrame({"complejidad": ["Baja", "Alta", "Mediana"]})
        salida = CodificadorBinario(*CODIFICACIONES[1]).ajustar_transformar(datos)
        self.assertEqual(salida["complejidad_baja"].tolist(), [1, 0, 0])
        self.assertEqual(salida["complejidad_alta"].tolist(), [0, 1, 0])

    def test_pipeline_encadena_funciones_y_clases(self):
        """El pipeline recorre por igual una función adaptada y una clase."""
        datos = pd.DataFrame({"origen": ["  SÍ ", "no", ""]}, dtype="string")
        pipeline = Pipeline([PasoFuncion(normalizar_columna, columna="origen", destino="limpio"),
                             FiltroInformado("limpio", "P1", "Valor informado")])
        salida = pipeline.ajustar_transformar(datos)
        self.assertEqual(salida["limpio"].tolist(), ["sí", "no"])

    def test_bitacora_se_genera_al_ejecutar(self):
        """La bitácora registra antes, excluidos y restantes de cada filtro sin que el filtro la conozca."""
        datos = pd.DataFrame({"valor": ["a", "", "c"]}, dtype="string")
        bitacora = BitacoraFiltros()
        pipeline = PipelineObservable([FiltroInformado("valor", "P1", "Valor informado")]).suscribir(bitacora)
        pipeline.ajustar_transformar(datos)
        self.assertEqual(bitacora.a_dataframe().iloc[0].to_dict(),
                         {"paso": "P1", "regla": "Valor informado", "antes": 3, "excluidos": 1, "restantes": 2})

    def test_preprocesador_sobre_registro_pequeno(self):
        """De seis establecimientos quedan dos; los otros cuatro salen en F01, F05, F06 y F07."""
        preprocesador, datos = preprocesador_pequeno()
        resultado = preprocesador.ajustar_transformar(datos)
        self.assertEqual(resultado["poblacion"]["codigo_establecimiento"].tolist(), ["101", "102"])
        self.assertEqual(resultado["matriz"].values.tolist(), [[1, 0, 1, 0, 0], [0, 1, 0, 0, 1]])
        excluidos = preprocesador.exclusiones.set_index("EstablecimientoCodigo")["paso_exclusion"].to_dict()
        self.assertEqual(excluidos, {"103": "F01", "104": "F05", "105": "F06", "106": "F07"})

    def test_una_pasada_equivale_a_dos(self):
        """Aprender y aplicar en una pasada da lo mismo que ajustar y luego transformar."""
        preprocesador, datos = preprocesador_pequeno()
        una = preprocesador.ajustar_transformar(datos)
        dos = PreprocesadorRegistro(crear_configuracion(datos.columns)).ajustar(datos).transformar(datos)
        pd.testing.assert_frame_equal(una["poblacion"], dos["poblacion"])
        pd.testing.assert_frame_equal(una["matriz"], dos["matriz"])

    def test_clases_equivalen_al_flujo_de_f2(self):
        """El pipeline con clases produce la misma población y matriz que el flujo de la Fase 2."""
        preprocesador, datos = preprocesador_pequeno()
        resultado, referencia = preprocesador.ajustar_transformar(datos), flujo_f2(datos)
        pd.testing.assert_frame_equal(resultado["poblacion"], referencia["poblacion"])
        pd.testing.assert_frame_equal(resultado["matriz"], referencia["matriz"])
        pd.testing.assert_frame_equal(preprocesador.tabla_filtros, referencia["tabla_filtros"])

    def test_versiones_de_conflictos_coinciden(self):
        """Las tres implementaciones detectan los mismos códigos repetidos."""
        codigos = pd.Series(["a", "b", "a", "c", "b", "d"], dtype="string")
        esperado = ["a", "b"]
        self.assertEqual(conflictos_con_lista(codigos), esperado)
        self.assertEqual(conflictos_con_diccionario(codigos), esperado)
        self.assertEqual(conflictos_vectorizado(codigos), esperado)

    def test_recursion_recorre_niveles_variables(self):
        """Las funciones recursivas recorren la jerarquía de clases y una configuración anidada."""
        clases = [fila["clase"] for fila in recorrer_jerarquia(Transformador)]
        self.assertIn("FiltroCodigosEnConflicto", clases)
        self.assertEqual(aplanar({"a": {"b": [{"c": 1}, {"c": 2}]}, "d": [1, 2]}),
                         {"a.b.0.c": 1, "a.b.1.c": 2, "d": [1, 2]})


class TestCasosLimite(unittest.TestCase):
    """Situaciones extremas pero válidas."""

    def test_columna_sin_faltantes(self):
        """Una columna sin vacíos no pierde filas en el filtro de valor informado."""
        datos = pd.DataFrame({"codigo": ["a1", "b2", "c3"]}, dtype="string")
        salida = FiltroInformado("codigo", "L1", "Prueba").ajustar_transformar(datos)
        pd.testing.assert_frame_equal(salida, datos)

    def test_una_sola_fila(self):
        """Un registro de una sola fila válida produce una población y una matriz de una fila."""
        preprocesador, datos = preprocesador_pequeno()
        resultado = preprocesador.ajustar_transformar(datos.head(1))
        self.assertEqual(resultado["matriz"].shape, (1, 5))

    def test_filtro_que_excluye_todo(self):
        """Si un filtro excluye todo, queda una tabla vacía con su esquema y una matriz de 0 × 5."""
        datos = pd.DataFrame({"pertenencia_snss": ["SNSS"], "complejidad": ["Baja"]})
        vacia = FiltroValoresPermitidos("complejidad", ["Inexistente"], "L2", "Prueba").ajustar_transformar(datos)
        matriz = construir_codificacion(CODIFICACIONES, COLUMNAS_NUMERICAS).ajustar_transformar(vacia)
        self.assertEqual(list(vacia.columns), list(datos.columns))
        self.assertEqual(matriz.shape, (0, 5))

    def test_una_sola_categoria(self):
        """Una categoría ausente genera una columna de ceros, no una columna faltante."""
        datos = pd.DataFrame({"pertenencia_snss": ["SNSS", "SNSS"]})
        salida = CodificadorBinario(*CODIFICACIONES[0]).ajustar_transformar(datos)
        self.assertEqual(salida["snss_no_perteneciente"].tolist(), [0, 0])

    def test_codigo_en_conflicto_se_excluye_completo(self):
        """Dos registros con el mismo código se excluyen ambos, sin elegir uno."""
        datos = pd.DataFrame({"codigo": ["100", "100", "200"]}, dtype="string")
        filtro = FiltroCodigosEnConflicto("codigo", "L4", "Prueba")
        self.assertEqual(filtro.ajustar_transformar(datos)["codigo"].tolist(), ["200"])
        self.assertEqual(filtro.parametros["codigos_en_conflicto"], ["100"])

    def test_categoria_nueva_en_otro_corte(self):
        """Una pertenencia desconocida en un corte nuevo no se imputa: se excluye en F05."""
        preprocesador, datos = preprocesador_pequeno()
        preprocesador.ajustar(datos)
        nuevo_corte = datos.head(2).copy()
        nuevo_corte.loc[0, "TipoPertenenciaEstabGlosa"] = "En proceso de traspaso"
        resultado = preprocesador.transformar(nuevo_corte)
        self.assertEqual(resultado["poblacion"]["codigo_establecimiento"].tolist(), ["102"])
        self.assertEqual(preprocesador.exclusiones["paso_exclusion"].tolist(), ["F05"])

    def test_seleccion_conserva_el_orden_pedido(self):
        """Seleccionar columnas respeta el orden indicado y reinicia el índice."""
        datos = pd.DataFrame({"a": [1, 2], "b": [3, 4]}, index=[7, 9])
        salida = seleccionar_columnas(datos, ["b", "a"])
        self.assertEqual(list(salida.columns), ["b", "a"])
        self.assertEqual(list(salida.index), [0, 1])


class TestExcepciones(unittest.TestCase):
    """Entradas inválidas que deben fallar con un error claro."""

    def setUp(self):
        self.datos = registro_pequeno()

    # --- CAMBIO (Fase 4): dos pruebas nuevas para la clase base abstracta (módulo abc) ---
    def test_clase_base_abstracta(self):
        """Transformador y Filtro son abstractos: crearlos directamente produce TypeError."""
        with self.assertRaises(TypeError):
            Transformador("EstadoFuncionamiento")
        with self.assertRaises(TypeError):
            Filtro("EstadoFuncionamiento", "E0", "Prueba")

    def test_hija_incompleta_no_se_instancia(self):
        """Una clase hija que no implementa aplicar no se puede crear: TypeError."""
        class SoloAprende(Transformador):
            def aprender(self, df):
                return {}
        with self.assertRaisesRegex(TypeError, "aplicar"):
            SoloAprende("EstadoFuncionamiento")
        # La clase de prueba se elimina para que no quede registrada como subclase de Transformador:
        # si quedara, recorrer_jerarquia la contaría en el cuaderno F3 después de ejecutar las pruebas.
        del SoloAprende
        gc.collect()

    def test_transformar_sin_ajustar(self):
        """Transformar antes de ajustar produce RuntimeError."""
        with self.assertRaises(RuntimeError):
            MapeadorCategorias("EstadoFuncionamiento", "destino", {}).transformar(self.datos)

    def test_columna_inexistente(self):
        """Una columna que no existe produce KeyError con su nombre."""
        with self.assertRaisesRegex(KeyError, "no_existe"):
            FiltroInformado("no_existe", "E1", "Prueba").ajustar(self.datos)

    def test_paso_que_no_es_transformador(self):
        """El pipeline rechaza con TypeError un paso que no cumple el contrato."""
        with self.assertRaises(TypeError):
            Pipeline().agregar("texto")

    def test_pipeline_sin_ajustar(self):
        """Un pipeline sin ajustar no puede transformar: RuntimeError."""
        with self.assertRaises(RuntimeError):
            Pipeline([FiltroInformado("EstablecimientoCodigo", "E2", "Prueba")]).transformar(self.datos)

    def test_categoria_no_reconocida(self):
        """Una categoría fuera del vocabulario detiene la codificación con ValueError."""
        datos = pd.DataFrame({"complejidad": ["Baja", "Desconocida"]})
        with self.assertRaisesRegex(ValueError, "Desconocida"):
            CodificadorBinario(*CODIFICACIONES[1]).ajustar(datos)

    def test_faltante_en_variable_analitica(self):
        """Un faltante en una variable analítica produce ValueError: no se codifica en silencio."""
        datos = pd.DataFrame({"complejidad": ["Baja", None]})
        with self.assertRaises(ValueError):
            CodificadorBinario(*CODIFICACIONES[1]).ajustar(datos)

    def test_tipo_de_filtro_desconocido(self):
        """La fábrica rechaza un tipo de regla no declarado y enumera los válidos."""
        with self.assertRaisesRegex(ValueError, "Tipos válidos"):
            crear_filtro({"paso": "X", "tipo": "geografico", "motivo": "-"})

    def test_preprocesador_sin_ajustar(self):
        """El preprocesador no transforma si no se ajustó antes: RuntimeError."""
        with self.assertRaises(RuntimeError):
            PreprocesadorRegistro(crear_configuracion(self.datos.columns)).transformar(self.datos)

    def test_archivo_inexistente(self):
        """Cargar un archivo que no existe produce FileNotFoundError."""
        with self.assertRaises(FileNotFoundError):
            cargar_registro(RAIZ / "data/raw/no_existe.csv", COLUMNAS_NECESARIAS)

    def test_huella_y_esquema_del_archivo(self):
        """Una huella distinta produce ValueError y una columna ausente, KeyError."""
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = Path(carpeta) / "registro.csv"
            self.datos.to_csv(ruta, sep=";", index=False, encoding="utf-8")
            with self.assertRaises(ValueError):
                cargar_registro(ruta, COLUMNAS_NECESARIAS, huella_esperada="0" * 64)
            with self.assertRaises(KeyError):
                cargar_registro(ruta, COLUMNAS_NECESARIAS + ["ColumnaAusente"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
