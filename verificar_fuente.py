"""Verifica que el archivo de origen sea exactamente la versión usada en el proyecto.

El archivo no se guarda en el repositorio, así que cada integrante lo descarga por su
cuenta. El portal lo actualiza sin versiones y el archivo puede editarse por error, por
eso antes de ejecutar el proyecto se comprueba su tamaño y su huella SHA-256.

Uso, desde la raíz del proyecto:

    python verificar_fuente.py
"""
import hashlib
import sys
from pathlib import Path

RAIZ = Path(_file_).resolve().parent


def miles(numero):
    """Escribe un entero con punto de miles, como en el resto del proyecto."""
    return f"{numero:,}".replace(",", ".")


class ArchivoFuenteError(Exception):
    """El archivo de origen falta o no corresponde a la versión registrada."""


class VerificadorFuente:
    """Comprueba la presencia, el tamaño y la huella del archivo de origen."""

    NOMBRE = "establecimientos_20261103.csv"
    SHA256 = "febff55e3612fb60076df9279f1090240cd02a39e9c7b79b822119dfdef84c8d"
    TAMANO = 2_548_427
    URL = ("https://datos.gob.cl/dataset/3bf4cf7c-f638-4735-9a01-f65faae4beca/resource/"
           "2c44d782-3365-44e3-aefb-2c8b8363a1bc/download/establecimientos_20261110.csv")

    def _init_(self, raiz=RAIZ, nombre=NOMBRE, sha256=SHA256, tamano=TAMANO, url=URL):
        self._ruta = Path(raiz) / "data" / "raw" / nombre
        self._sha256 = sha256.lower()
        self._tamano = tamano
        self._url = url

    @property
    def ruta(self):
        return self._ruta

    def calcular_huella(self, bloque=1024 * 1024):
        """SHA-256 del archivo, leído por bloques para no cargarlo entero en memoria."""
        huella = hashlib.sha256()
        with self._ruta.open("rb") as archivo:
            for parte in iter(lambda: archivo.read(bloque), b""):
                huella.update(parte)
        return huella.hexdigest()

    def verificar(self):
        """Devuelve la huella si el archivo es el correcto; si no, se detiene explicando qué hacer."""
        if not self._ruta.is_file():
            raise ArchivoFuenteError(
                f"No se encontró el archivo de origen: {self._ruta}\n"
                f"  1. Descargarlo desde {self._url}\n"
                f"  2. Guardarlo como data/raw/{self._ruta.name} (el portal lo entrega con otro nombre).\n"
                f"  3. Volver a ejecutar.")

        tamano = self._ruta.stat().st_size
        huella = self.calcular_huella()
        if tamano != self._tamano or huella != self._sha256:
            raise ArchivoFuenteError(
                "El archivo de origen no es la versión utilizada por el proyecto.\n"
                f"  Tamaño esperado: {miles(self._tamano)} bytes · obtenido: {miles(tamano)} bytes\n"
                f"  SHA-256 esperado: {self._sha256}\n"
                f"  SHA-256 obtenido: {huella}\n"
                "Puede haberse descargado una actualización del portal o haberse modificado el archivo "
                "(por ejemplo, al abrirlo y guardarlo en Excel). Hay que volver a descargarlo; si el "
                "portal ya no publica esta versión, los resultados del proyecto no se pueden reproducir "
                "con el archivo nuevo.")
        return huella


def main():
    verificador = VerificadorFuente()
    try:
        huella = verificador.verificar()
    except ArchivoFuenteError as error:
        print(f"ERROR: {error}")
        return 1
    print(f"Archivo de origen correcto: {verificador.ruta.name} (SHA-256 {huella[:12]}…)")
    return 0


if _name_ == "_main_":
    sys.exit(main())