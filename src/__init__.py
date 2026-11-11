"""Paquete del proyecto MCDI500: caracterización de los establecimientos de salud de Chile.

Los módulos separan las tareas del flujo reproducible:

- ``entorno``: rutas, semilla, verificación de dependencias y estado de Git.
- ``datos``: carga del archivo crudo y perfil de lectura.
- ``diccionario``: rol analítico declarado para cada variable.
- ``limpieza``: normalización, corrección de categorías y casting.
- ``imputacion``: comparación y aplicación de alternativas de imputación.
- ``geo``: distancias geodésicas con NumPy.
- ``transformacion``: variables derivadas, codificación y escalamiento.
- ``validacion``: comprobaciones de integridad del resultado.
- ``descriptivo``: análisis descriptivo por dimensión y por objetivo específico.
- ``bitacora``: registro de decisiones con sus cifras.
- ``graficos``: figuras de control y de resultados.
"""


class ProyectoError(Exception):
    """Error propio del proyecto: lo distingue de los errores de las librerías."""
