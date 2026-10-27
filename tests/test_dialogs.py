import unittest

from app.exceptions import CsvFormatError, FitPlanError
from ui.dialogs import detalle_error, resumen_error


class DialogHelpersTests(unittest.TestCase):
    def test_resumen_csv_usa_solo_el_mensaje(self) -> None:
        error = CsvFormatError(
            "Falta una columna obligatoria.",
            "datos.csv",
            4,
        )

        self.assertEqual(
            resumen_error(error),
            "Falta una columna obligatoria.",
        )

    def test_resumen_usa_mensaje_de_dominio(self) -> None:
        self.assertEqual(
            resumen_error(FitPlanError("No se pudo cargar.")),
            "No se pudo cargar.",
        )

    def test_resumen_de_error_sin_mensaje(self) -> None:
        self.assertEqual(resumen_error(ValueError()), "ValueError")

    def test_detalle_csv_incluye_archivo_y_linea(self) -> None:
        error = CsvFormatError("Encabezado inválido.", "datos.csv", 2)

        detalle = detalle_error(error)

        self.assertIn("Encabezado inválido.", detalle)
        self.assertIn("datos.csv", detalle)
        self.assertIn("línea: 2", detalle)

    def test_detalle_generico_incluye_tipo(self) -> None:
        self.assertEqual(
            detalle_error(ValueError("valor inválido")),
            "ValueError: valor inválido",
        )


if __name__ == "__main__":
    unittest.main()
