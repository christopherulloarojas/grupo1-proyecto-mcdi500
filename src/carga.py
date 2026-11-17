"""Carga y verificación del archivo original."""
import hashlib
from pathlib import Path

from src.utilidades import cargar_datos


def huella_archivo(ruta):
    """SHA-256 del archivo, para comprobar que no cambió entre fases."""
    return hashlib.sha256(Path(ruta).read_bytes()).hexdigest()


def cargar_registro(ruta, columnas_esperadas, huella_esperada=None):
    """Lee el CSV como texto, verifica su huella y comprueba el esquema."""
    datos = cargar_datos(ruta)
    if huella_esperada is not None and huella_archivo(ruta) != huella_esperada:
        raise ValueError("La huella del archivo no coincide con la registrada en F1.")
    faltantes = [c for c in columnas_esperadas if c not in datos.columns]
    if faltantes:
        raise KeyError(f"Faltan columnas en el archivo: {faltantes}")
    return datos
