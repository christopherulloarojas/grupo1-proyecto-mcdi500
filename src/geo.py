"""Distancias geodésicas vectorizadas con NumPy."""

import numpy as np

from src import ProyectoError

RADIO_TIERRA_KM = 6371.0088  # radio medio terrestre


def haversine_km(lat1, lon1, lat2, lon2):
    """Distancia del gran círculo en kilómetros. Admite escalares y arreglos."""
    lat1, lon1, lat2, lon2 = (np.radians(np.asarray(v, dtype=float))
                              for v in (lat1, lon1, lat2, lon2))
    a = (np.sin((lat2 - lat1) / 2) ** 2
         + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2)
    return 2 * RADIO_TIERRA_KM * np.arcsin(np.sqrt(np.clip(a, 0.0, 1.0)))


def vecino_mas_cercano(lat, lon, lat_ref, lon_ref, bloque=512):
    """Para cada punto, distancia a la referencia más cercana y posición de esa referencia.

    Es una búsqueda exhaustiva con costo O(n·m); se procesa por bloques para acotar la
    memoria de la matriz de distancias. Los puntos con coordenada faltante devuelven
    ``NaN`` y posición -1. La posición se refiere a las referencias tal como se entregaron.
    Lanza ``ProyectoError`` si no hay referencias válidas.
    """
    lat, lon = np.asarray(lat, dtype=float), np.asarray(lon, dtype=float)
    lat_ref, lon_ref = np.asarray(lat_ref, dtype=float), np.asarray(lon_ref, dtype=float)
    validas = ~(np.isnan(lat_ref) | np.isnan(lon_ref))
    if not validas.any():
        raise ProyectoError("No hay puntos de referencia con coordenadas válidas.")
    posiciones_validas = np.flatnonzero(validas)
    lat_ref, lon_ref = lat_ref[validas], lon_ref[validas]

    salida = np.full(lat.shape, np.nan)
    indices = np.full(lat.shape, -1, dtype=int)
    for inicio in range(0, lat.size, bloque):
        fin = inicio + bloque
        # Una dimensión extra por punto: la difusión compara cada punto con cada referencia.
        distancias = haversine_km(lat[inicio:fin, None], lon[inicio:fin, None], lat_ref, lon_ref)
        fila_valida = ~np.isnan(lat[inicio:fin]) & ~np.isnan(lon[inicio:fin])
        minimos = np.full(distancias.shape[0], np.nan)
        minimos[fila_valida] = distancias[fila_valida].min(axis=1)
        salida[inicio:fin] = minimos
        cercanos = np.full(distancias.shape[0], -1, dtype=int)
        cercanos[fila_valida] = posiciones_validas[distancias[fila_valida].argmin(axis=1)]
        indices[inicio:fin] = cercanos
    return salida, indices


def distancia_minima_km(lat, lon, lat_ref, lon_ref, bloque=512):
    """Para cada punto, distancia a la referencia más cercana; ver ``vecino_mas_cercano``."""
    return vecino_mas_cercano(lat, lon, lat_ref, lon_ref, bloque)[0]
