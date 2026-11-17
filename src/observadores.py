"""Observadores del pipeline: registran lo ocurrido sin que el pipeline sepa quién anota."""
import pandas as pd


class Observador:
    """Contrato de los observadores: reiniciar() y notificar()."""

    def reiniciar(self):
        pass

    def notificar(self, paso, antes, resultado, segundos):
        raise NotImplementedError


class BitacoraFiltros(Observador):
    """Construye la tabla secuencial de filtros (paso, regla, antes, excluidos, restantes)."""

    def __init__(self):
        self._filas = []

    def reiniciar(self):
        self._filas = []

    def notificar(self, paso, antes, resultado, segundos):
        if hasattr(paso, "paso"):                     # solo los filtros tienen código de paso
            self._filas.append({"paso": paso.paso, "regla": paso.motivo, "antes": antes,
                                "excluidos": antes - len(resultado), "restantes": len(resultado)})

    def a_dataframe(self):
        return pd.DataFrame(self._filas, columns=["paso", "regla", "antes", "excluidos", "restantes"])


class RegistroExclusiones(Observador):
    """Acumula las filas excluidas por cada filtro, con su paso y motivo."""

    def __init__(self):
        self._bloques = []

    def reiniciar(self):
        self._bloques = []

    def notificar(self, paso, antes, resultado, segundos):
        excluidos = getattr(paso, "excluidos", None)
        if excluidos is not None:
            self._bloques.append(excluidos)

    def a_dataframe(self):
        return pd.concat(self._bloques, ignore_index=True)


class RegistroTiempos(Observador):
    """Anota cuánto tardó cada paso, para saber dónde se concentra el costo."""

    def __init__(self):
        self._filas = []

    def reiniciar(self):
        self._filas = []

    def notificar(self, paso, antes, resultado, segundos):
        self._filas.append({"paso": paso.nombre, "filas_entrada": antes,
                            "milisegundos": round(segundos * 1000, 3)})

    def a_dataframe(self):
        return pd.DataFrame(self._filas, columns=["paso", "filas_entrada", "milisegundos"])


class ReporteConsola(Observador):
    """Imprime el avance mientras ocurre."""

    def notificar(self, paso, antes, resultado, segundos):
        print(f"  {paso.nombre:<44} {antes:>6} -> {len(resultado):>6} filas  [{segundos:.4f} s]")
