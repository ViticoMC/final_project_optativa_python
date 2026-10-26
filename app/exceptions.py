from pathlib import Path


class FitPlanError(Exception):
    """Error base de la aplicación."""


class CsvFormatError(FitPlanError):
    """Error de estructura, codificación o contenido de un archivo CSV."""

    def __init__(
        self,
        mensaje: str,
        ruta: str | Path | None = None,
        linea: int | None = None,
    ) -> None:
        self.mensaje = mensaje
        self.ruta = Path(ruta) if ruta is not None else None
        self.linea = linea
        detalles = [mensaje]
        if self.ruta is not None:
            detalles.append(f"archivo: {self.ruta}")
        if self.linea is not None:
            detalles.append(f"línea: {self.linea}")
        super().__init__(" | ".join(detalles))


class DataValidationError(FitPlanError):
    """Error de validación de un registro de dominio."""


class ExportError(FitPlanError):
    """Error al escribir un archivo de resultados."""
