"""Clases de transformación del núcleo algorítmico (Fase 3).

Una clase base, Transformador, define el contrato y controla el estado. Las clases
hijas solo implementan qué aprenden del conjunto (aprender) y cómo lo aplican
(aplicar). Son clases los componentes que necesitan recordar algo entre una llamada
y otra; las operaciones sin estado son funciones (src/funciones.py) y entran al
pipeline mediante el adaptador PasoFuncion.
"""
from src.conflictos import conflictos_vectorizado


class Transformador:
    """Clase base: contrato común y control de estado de cada paso del pipeline."""

    def __init__(self, columnas=()):
        # Atributo público: las columnas sobre las que trabaja el paso
        self.columnas = [columnas] if isinstance(columnas, str) else list(columnas)
        # Atributos internos (guion bajo): se aprenden, no se asignan desde fuera
        self._parametros = {}
        self._ajustado = False

    @property
    def nombre(self):
        """Nombre legible del paso, con la clase real del objeto."""
        detalle = ", ".join(self.columnas[:2]) + ("…" if len(self.columnas) > 2 else "")
        return f"{type(self).__name__}({detalle})"

    @property
    def parametros(self):
        """Copia defensiva de lo aprendido: no permite modificar el estado interno."""
        return dict(self._parametros)

    @property
    def ajustado(self):
        """Solo lectura: indica si el paso ya aprendió sus parámetros."""
        return self._ajustado

    def _validar_columnas(self, df):
        faltantes = [c for c in self.columnas if c not in df.columns]
        if faltantes:
            raise KeyError(f"{self.nombre}: faltan columnas en el conjunto: {faltantes}")

    def ajustar(self, df):
        """Valida la entrada, aprende los parámetros y marca el paso como ajustado."""
        self._validar_columnas(df)
        self._parametros = self.aprender(df)
        self._ajustado = True
        return self

    def transformar(self, df):
        """Aplica lo aprendido sobre una copia: nunca modifica la entrada."""
        if not self._ajustado:
            raise RuntimeError(f"{self.nombre}: hay que ajustar antes de transformar.")
        self._validar_columnas(df)
        return self.aplicar(df.copy())

    def ajustar_transformar(self, df):
        """Atajo para aprender y aplicar sobre el mismo conjunto."""
        return self.ajustar(df).transformar(df)

    def aprender(self, df):
        raise NotImplementedError("Cada clase hija debe implementar aprender().")

    def aplicar(self, df):
        raise NotImplementedError("Cada clase hija debe implementar aplicar().")


class PasoFuncion(Transformador):
    """Adapta una función sin estado al contrato del pipeline.

    No aprende nada de los datos: solo guarda qué función aplicar y con qué
    argumentos, para que el pipeline trate igual a funciones y clases.
    """

    def __init__(self, funcion, **argumentos):
        super().__init__(argumentos.get("columna", ()))
        self.funcion = funcion
        self.argumentos = argumentos

    @property
    def nombre(self):
        if "columnas" in self.argumentos:
            detalle = f"{len(self.argumentos['columnas'])} columnas"
        else:
            detalle = self.argumentos.get("columna", "")
        return f"{self.funcion.__name__}({detalle})"

    def aprender(self, df):
        return {}

    def aplicar(self, df):
        return self.funcion(df, **self.argumentos)


class MapeadorCategorias(Transformador):
    """Traduce etiquetas normalizadas a categorías analíticas con un mapeo explícito.

    Aprende qué valores observó y cuáles no tienen correspondencia. Esos valores
    quedan como faltantes: no se imputan, los excluyen después los filtros con su motivo.
    """

    def __init__(self, columna, destino, correspondencias):
        super().__init__(columna)
        self.destino = destino
        self.correspondencias = dict(correspondencias)

    def aprender(self, df):
        observadas = sorted(df[self.columnas[0]].dropna().unique())
        return {"observadas": observadas,
                "sin_correspondencia": [v for v in observadas if v not in self.correspondencias]}

    def aplicar(self, df):
        df[self.destino] = df[self.columnas[0]].map(self.correspondencias)
        return df


class Filtro(Transformador):
    """Clase intermedia: conserva las filas que cumplen una condición.

    Las filas excluidas no se descartan en silencio: quedan en el atributo interno
    _excluidos, con el código del paso y su motivo, para que los observadores del
    pipeline las registren.
    """

    def __init__(self, columnas, paso, motivo):
        super().__init__(columnas)
        self.paso = paso
        self.motivo = motivo
        self._excluidos = None

    @property
    def nombre(self):
        return f"{self.paso} {type(self).__name__}"

    @property
    def excluidos(self):
        """Copia de las filas excluidas en la última transformación."""
        return None if self._excluidos is None else self._excluidos.copy()

    def aprender(self, df):
        condicion = self.condicion(df).fillna(False)
        return {"evaluadas": len(df), "excluiria": int((~condicion).sum())}

    def aplicar(self, df):
        condicion = self.condicion(df).fillna(False)
        excluidos = df.loc[~condicion].copy()
        excluidos["paso_exclusion"] = self.paso
        excluidos["motivo_exclusion"] = self.motivo
        self._excluidos = excluidos
        return df.loc[condicion].copy()

    def condicion(self, df):
        raise NotImplementedError("Cada filtro debe implementar condicion().")


class FiltroValoresPermitidos(Filtro):
    """Conserva las filas cuyo valor pertenece a un conjunto declarado."""

    def __init__(self, columna, permitidos, paso, motivo):
        super().__init__(columna, paso, motivo)
        self.permitidos = list(permitidos)

    def condicion(self, df):
        return df[self.columnas[0]].isin(self.permitidos)


class FiltroInformado(Filtro):
    """Conserva las filas con valor presente y no vacío."""

    def condicion(self, df):
        columna = df[self.columnas[0]]
        return columna.notna() & columna.ne("")


class FiltroValorExcluido(Filtro):
    """Excluye las filas que tienen un valor explícito, como «no aplica»."""

    def __init__(self, columna, valor, paso, motivo):
        super().__init__(columna, paso, motivo)
        self.valor = valor

    def condicion(self, df):
        return df[self.columnas[0]].ne(self.valor)


class FiltroDuplicadosExactos(Filtro):
    """Conserva una copia de las filas repetidas en todas las columnas indicadas."""

    def condicion(self, df):
        return ~df.duplicated(subset=self.columnas)


class FiltroCodigosEnConflicto(Filtro):
    """Excluye todos los registros de un código que aparece más de una vez.

    No elige una versión: los códigos en conflicto se aprenden en el ajuste y
    quedan documentados en los parámetros. Usa la detección vectorizada, la
    implementación elegida tras la medición de eficiencia.
    """

    def aprender(self, df):
        conflictos = conflictos_vectorizado(df[self.columnas[0]])
        return {**super().aprender(df), "codigos_en_conflicto": conflictos}

    def condicion(self, df):
        codigos = df[self.columnas[0]]
        return ~codigos.isin(conflictos_vectorizado(codigos))


class CodificadorBinario(Transformador):
    """Crea un indicador 0/1 por categoría declarada (codificación One-Hot).

    El vocabulario se declara en la configuración: una categoría ausente produce
    una columna de ceros y una categoría no reconocida detiene la ejecución.
    """

    def __init__(self, columna, nombres_columnas):
        super().__init__(columna)
        self.nombres_columnas = dict(nombres_columnas)    # categoría -> columna 0/1

    def _validar_valores(self, df):
        serie = df[self.columnas[0]]
        if serie.isna().any():
            raise ValueError(f"{self.nombre}: la variable contiene faltantes.")
        desconocidas = sorted(set(serie.unique()) - set(self.nombres_columnas))
        if desconocidas:
            raise ValueError(f"{self.nombre}: categorías no reconocidas {desconocidas}.")

    def aprender(self, df):
        self._validar_valores(df)
        return {"categorias_observadas": sorted(df[self.columnas[0]].unique()),
                "columnas_generadas": list(self.nombres_columnas.values())}

    def aplicar(self, df):
        self._validar_valores(df)
        for categoria, nombre_columna in self.nombres_columnas.items():
            df[nombre_columna] = (df[self.columnas[0]] == categoria).astype(int)
        return df
