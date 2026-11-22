"""Orquestadores: encadenan transformadores sin conocer el detalle de cada paso."""
import time

import pandas as pd

from src.transformadores import Transformador


class Pipeline:
    """Encadena transformadores y los ejecuta en orden."""

    def __init__(self, pasos=None):
        self._pasos = []
        self._ajustado = False
        for paso in pasos or []:
            self.agregar(paso)

    def agregar(self, transformador):
        if not isinstance(transformador, Transformador):
            raise TypeError(f"Se esperaba un Transformador y se recibió {type(transformador).__name__}.")
        self._pasos.append(transformador)
        self._ajustado = False
        return self

    def _ejecutar_paso(self, paso, df, aprender):
        """Un paso: aprende y aplica, o solo aplica lo ya aprendido."""
        return paso.ajustar_transformar(df) if aprender else paso.transformar(df)

    def _recorrer(self, df, aprender):
        resultado = df.copy()
        for paso in self._pasos:                     # polimorfismo: la misma llamada
            resultado = self._ejecutar_paso(paso, resultado, aprender)
        return resultado

    def ajustar_transformar(self, df):
        """Una sola pasada: cada paso aprende sobre la salida del anterior y la transforma."""
        resultado = self._recorrer(df, aprender=True)
        self._ajustado = True
        return resultado

    def ajustar(self, df):
        self.ajustar_transformar(df)
        return self

    def transformar(self, df):
        """Aplica lo aprendido, por ejemplo sobre un nuevo corte del registro."""
        if not self._ajustado:
            raise RuntimeError("Pipeline: hay que ajustar antes de transformar.")
        return self._recorrer(df, aprender=False)

    def pasos_ejecutados(self):
        return tuple(self._pasos)

    def resumen(self):
        return pd.DataFrame([{"orden": i, "paso": p.nombre, "clase": type(p).__name__}
                             for i, p in enumerate(self._pasos, start=1)])

    def __len__(self):
        return len(self._pasos)

    def __repr__(self):
        estado = "ajustado" if self._ajustado else "sin ajustar"
        return f"{type(self).__name__}({len(self._pasos)} pasos, {estado})"


class PipelineObservable(Pipeline):
    """Pipeline que avisa a sus observadores cada vez que termina un paso (Observer)."""

    def __init__(self, pasos=None):
        super().__init__(pasos)
        self._observadores = []

    def suscribir(self, observador):
        self._observadores.append(observador)
        return self

    def _recorrer(self, df, aprender):
        for observador in self._observadores:        # cada recorrido parte con registros limpios
            observador.reiniciar()
        return super()._recorrer(df, aprender)

    def _ejecutar_paso(self, paso, df, aprender):
        inicio = time.perf_counter()
        resultado = super()._ejecutar_paso(paso, df, aprender)
        segundos = time.perf_counter() - inicio
        for observador in self._observadores:
            observador.notificar(paso, len(df), resultado, segundos)
        return resultado
