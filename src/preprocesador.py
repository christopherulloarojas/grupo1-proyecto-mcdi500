"""Fachada que encapsula el pipeline completo de la Fase 2 en un solo objeto."""
import pandas as pd

from src.fabrica import construir_codificacion, construir_poblacion, construir_preparacion
from src.observadores import BitacoraFiltros, RegistroExclusiones, RegistroTiempos


class PreprocesadorRegistro:
    """Prepara el registro, construye la población y genera la matriz 0/1.

    Compone tres pipelines (preparación, población y codificación) y sus
    observadores: bitácora de filtros, registro de exclusiones y tiempos por paso.
    """

    def __init__(self, configuracion):
        self._configuracion = configuracion
        self._preparacion = construir_preparacion(configuracion["normalizaciones"], configuracion["mapeos"])
        self._poblacion = construir_poblacion(configuracion["reglas"], configuracion["columnas_originales"],
                                              configuracion["columnas_poblacion"])
        self._codificacion = construir_codificacion(configuracion["codificaciones"],
                                                    configuracion["columnas_numericas"])
        self._bitacora = BitacoraFiltros()
        self._exclusiones = RegistroExclusiones()
        self._poblacion.suscribir(self._bitacora).suscribir(self._exclusiones)
        self._tiempos = {}                      # un registro de tiempos por etapa
        for etapa, pipeline in self.pipelines().items():
            self._tiempos[etapa] = RegistroTiempos()
            pipeline.suscribir(self._tiempos[etapa])
        self._ajustado = False

    def ajustar_transformar(self, datos):
        """Una sola pasada: aprende y aplica sobre el mismo registro."""
        trabajo = self._preparacion.ajustar_transformar(datos)
        poblacion = self._poblacion.ajustar_transformar(trabajo)
        matriz = self._codificacion.ajustar_transformar(poblacion)
        self._ajustado = True
        return {"trabajo": trabajo, "poblacion": poblacion, "matriz": matriz}

    def ajustar(self, datos):
        self.ajustar_transformar(datos)
        return self

    def transformar(self, datos):
        """Aplica lo aprendido, por ejemplo sobre un nuevo corte del registro."""
        if not self._ajustado:
            raise RuntimeError("PreprocesadorRegistro: hay que ajustar antes de transformar.")
        trabajo = self._preparacion.transformar(datos)
        poblacion = self._poblacion.transformar(trabajo)
        matriz = self._codificacion.transformar(poblacion)
        return {"trabajo": trabajo, "poblacion": poblacion, "matriz": matriz}

    @property
    def tabla_filtros(self):
        return self._bitacora.a_dataframe()

    @property
    def exclusiones(self):
        return self._exclusiones.a_dataframe()

    @property
    def tiempos(self):
        """Tiempo de cada paso en la última ejecución, con su etapa."""
        return pd.concat([registro.a_dataframe().assign(etapa=etapa)
                          for etapa, registro in self._tiempos.items()], ignore_index=True)

    def parametros(self):
        """Una fila por paso con lo que aprendió en el ajuste."""
        filas = []
        for etapa, pipeline in self.pipelines().items():
            for orden, paso in enumerate(pipeline.pasos_ejecutados(), start=1):
                filas.append({"etapa": etapa, "orden": orden, "paso": paso.nombre, "parametros": str(paso.parametros)})
        return pd.DataFrame(filas)

    def pipelines(self):
        return {"preparación": self._preparacion, "población": self._poblacion,
                "codificación": self._codificacion}
