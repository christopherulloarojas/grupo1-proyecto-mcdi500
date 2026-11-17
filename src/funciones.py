"""Operaciones sin estado del pipeline.

No aprenden nada de los datos ni recuerdan nada entre llamadas: reciben una tabla y
devuelven otra. Por eso son funciones y no clases. Ninguna modifica su entrada.
"""
import numpy as np

from src.utilidades import normalizar_texto


def agregar_fila_origen(df, destino="fila_origen", primera_fila=2):
    """Agrega el número de fila del CSV (la fila 1 es el encabezado) para rastrear cada registro."""
    return df.assign(**{destino: np.arange(primera_fila, len(df) + primera_fila)})


def normalizar_columna(df, columna, destino):
    """Unifica espacios y mayúsculas de una columna y guarda el resultado en otra."""
    return df.assign(**{destino: normalizar_texto(df[columna])})


def seleccionar_columnas(df, columnas):
    """Conserva las columnas indicadas, en ese orden, y reinicia el índice."""
    return df[list(columnas)].reset_index(drop=True)
