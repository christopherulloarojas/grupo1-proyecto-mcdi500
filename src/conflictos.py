"""Tres implementaciones de una misma operación: detectar códigos repetidos.

Las tres devuelven la lista ordenada de códigos que aparecen más de una vez. Se
conservan juntas porque el cuaderno de la Fase 3 las compara en tiempo y memoria;
el filtro F04 usa la versión vectorizada, elegida a partir de esa medición.
"""


def conflictos_con_lista(codigos):
    """Versión A: cuenta cada código recorriendo la lista completa. Costo O(n²)."""
    lista = list(codigos)
    return sorted({codigo for codigo in lista if lista.count(codigo) > 1})


def conflictos_con_diccionario(codigos):
    """Versión B: una pasada, acumulando conteos en un diccionario. Costo O(n)."""
    conteo = {}
    for codigo in codigos:
        conteo[codigo] = conteo.get(codigo, 0) + 1
    return sorted(codigo for codigo, veces in conteo.items() if veces > 1)


def conflictos_vectorizado(codigos):
    """Versión C: operación vectorizada de pandas sobre la columna completa. Costo O(n)."""
    return sorted(codigos[codigos.duplicated(keep=False)].unique())
