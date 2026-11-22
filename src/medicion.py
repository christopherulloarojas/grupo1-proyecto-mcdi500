"""Medición de tiempo y memoria de cualquier función."""
import time
import timeit
import tracemalloc


def medir(funcion, *args, **kwargs):
    """Ejecuta la función una vez y devuelve resultado, segundos y memoria pico en MB."""
    tracemalloc.start()
    inicio = time.perf_counter()
    resultado = funcion(*args, **kwargs)
    transcurrido = time.perf_counter() - inicio
    _, pico = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return resultado, transcurrido, pico / 1024 / 1024


def tiempo_minimo(funcion, repeticiones=5, numero=1):
    """Menor tiempo por ejecución entre varias repeticiones de timeit."""
    return min(timeit.repeat(funcion, repeat=repeticiones, number=numero)) / numero
