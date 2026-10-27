from PyQt5.QtWidgets import QMessageBox, QWidget

from app.config import APP_NAME, APP_VERSION
from app.exceptions import CsvFormatError


def resumen_error(error: Exception) -> str:
    if isinstance(error, CsvFormatError):
        return error.mensaje
    mensaje = str(error).strip()
    return mensaje or type(error).__name__


def detalle_error(error: Exception) -> str:
    if isinstance(error, CsvFormatError):
        return str(error)
    return f"{type(error).__name__}: {error}"


def mostrar_error(
    parent: QWidget | None,
    titulo: str,
    error: Exception,
) -> None:
    caja = QMessageBox(parent)
    caja.setWindowTitle(APP_NAME)
    caja.setIcon(QMessageBox.Critical)
    caja.setText(titulo)
    caja.setInformativeText(resumen_error(error))
    caja.setDetailedText(detalle_error(error))
    caja.setStandardButtons(QMessageBox.Ok)
    caja.exec_()


def mostrar_acerca_de(parent: QWidget | None) -> None:
    QMessageBox.about(
        parent,
        f"Acerca de {APP_NAME}",
        (
            f"<h3>{APP_NAME} {APP_VERSION}</h3>"
            "<p>Gestor de rutinas de entrenamiento, catálogo de ejercicios "
            "y planificación nutricional.</p>"
            "<p>Incluye filtros, cobertura del catálogo, estadísticas y "
            "exportación CSV.</p>"
            "<p>Desarrollado en Python con PyQt5.</p>"
        ),
    )
