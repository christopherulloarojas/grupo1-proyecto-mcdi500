"""Ejecuta los notebooks del proyecto en orden (F1, F2 y F3) y guarda sus salidas.

Uso, con el entorno virtual activo y desde la raíz del proyecto:

    python ejecutar_proyecto.py
"""
import sys
import time
from pathlib import Path

import nbformat
from nbclient import NotebookClient
from nbclient.exceptions import CellExecutionError

RAIZ = Path(__file__).resolve().parent
NOTEBOOKS = ["F1/Grupo1_F1_Definicion.ipynb",
             "F2/Grupo1_F2_Preprocesamiento.ipynb",
             "F3/S2_F3_NucleoAlgoritmico_Eficiencia_POO.ipynb"]


def ejecutar_notebook(ruta):
    """Ejecuta un notebook desde un kernel limpio, en su carpeta, y guarda las salidas."""
    notebook = nbformat.read(ruta, as_version=4)
    cliente = NotebookClient(notebook, timeout=900, kernel_name="python3",
                             resources={"metadata": {"path": str(ruta.parent)}})
    inicio = time.perf_counter()
    cliente.execute()
    nbformat.write(notebook, ruta)
    return time.perf_counter() - inicio


def main():
    for nombre in NOTEBOOKS:
        ruta = RAIZ / nombre
        if not ruta.is_file():
            print(f"No se encontró el notebook: {nombre}")
            return 1
        print(f"Ejecutando {nombre} ...", flush=True)
        try:
            segundos = ejecutar_notebook(ruta)
        except CellExecutionError as error:
            print(f"  ERROR en {nombre}: la ejecución se detuvo.")
            print("  " + str(error).strip().splitlines()[-1])
            return 1
        print(f"  correcto ({segundos:.0f} s)")
    print("Proyecto ejecutado completo: F1, F2 y F3 sin errores.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
