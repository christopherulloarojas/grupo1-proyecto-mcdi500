"""Funciones recursivas para estructuras de profundidad variable."""


def recorrer_jerarquia(clase, nivel=0):
    """Devuelve la clase y todas sus descendientes, con su nivel en la jerarquía."""
    filas = [{"nivel": nivel, "clase": clase.__name__,
              "descripcion": (clase.__doc__ or "").strip().split("\n")[0]}]
    for hija in clase.__subclasses__():          # caso base: una clase sin hijas no entra al bucle
        filas += recorrer_jerarquia(hija, nivel + 1)   # caso recursivo: un nivel más abajo
    return filas


def aplanar(estructura, prefijo=""):
    """Convierte diccionarios y listas anidados en pares de ruta y valor."""
    if isinstance(estructura, dict):
        elementos = estructura.items()
    elif isinstance(estructura, list) and any(isinstance(valor, (dict, list)) for valor in estructura):
        elementos = enumerate(estructura)
    else:                                        # caso base: un valor simple o una lista de valores simples
        return {prefijo: estructura}
    plano = {}
    for clave, valor in elementos:
        ruta = f"{prefijo}.{clave}" if prefijo else str(clave)
        plano.update(aplanar(valor, ruta))       # caso recursivo
    return plano
