"""Funciones sencillas compartidas por las fases del proyecto."""
from pathlib import Path
import pandas as pd

def localizar_raiz(inicio=None):
    """Localiza el proyecto desde su raíz o desde las carpetas F1 y F2."""
    carpeta = Path.cwd() if inicio is None else Path(inicio)
    return carpeta.parent if carpeta.name in {"F1", "F2"} else carpeta

def normalizar_texto(serie):
    """Unifica espacios y mayúsculas; conserva los faltantes como faltantes."""
    return serie.astype("string").str.strip().str.replace(r"\s+", " ", regex=True).str.casefold()

def cargar_datos(ruta):
    """Lee el CSV como texto para preservar códigos y categorías originales."""
    ruta = Path(ruta)
    if not ruta.is_file():
        raise FileNotFoundError(f"No se encontró el archivo: {ruta}")
    datos = pd.read_csv(ruta, sep=";", encoding="utf-8", dtype="string", keep_default_na=False)
    if datos.empty:
        raise ValueError("El archivo no contiene registros.")
    return datos
