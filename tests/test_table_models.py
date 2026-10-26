import unittest

from PyQt5.QtCore import Qt

from app.models import Ejercicio, Rutina
from tests.qt_test_case import QtTestCase
from ui.models.table_models import EjercicioTableModel, RutinaTableModel


def crear_ejercicio(
    id_ejercicio: str,
    nombre: str,
    grupo: str = "Pecho",
) -> Ejercicio:
    return Ejercicio.from_row(
        {
            "id_ejercicio": id_ejercicio,
            "nombre": nombre,
            "grupo_muscular": grupo,
            "patron_movimiento": "Empuje horizontal",
            "equipamiento": "Barra o mancuernas",
            "nivel_sugerido": "Principiante",
            "nota_tecnica": "Usar carga controlable",
        }
    )


def crear_rutina(
    id_rutina: str,
    dia: str = "Lunes",
    series: int = 3,
) -> Rutina:
    return Rutina.from_row(
        {
            "id_rutina": id_rutina,
            "dia": dia,
            "horario": "07:00-08:00",
            "grupo_muscular": "Pecho",
            "ejercicios": "Press de banca; Plancha",
            "series": str(series),
            "repeticiones_o_duracion": "8-12",
            "nivel": "Intermedio",
            "descanso": "60-90 s",
        }
    )


class RutinaTableModelTests(QtTestCase):
    def setUp(self) -> None:
        self.rutinas = [
            crear_rutina("R001", dia="Lunes", series=3),
            crear_rutina("R002", dia="Miércoles", series=10),
            crear_rutina("R003", dia="Sábado", series=2),
        ]
        self.modelo = RutinaTableModel(self.rutinas)

    def test_dimensiones_y_cabeceras(self) -> None:
        self.assertEqual(self.modelo.rowCount(), 3)
        self.assertEqual(self.modelo.columnCount(), 9)
        self.assertEqual(
            self.modelo.headerData(0, Qt.Horizontal, Qt.DisplayRole), "ID"
        )
        self.assertEqual(
            self.modelo.headerData(0, Qt.Vertical, Qt.DisplayRole), 1
        )
        self.assertIsNone(
            self.modelo.headerData(99, Qt.Horizontal, Qt.DisplayRole)
        )

    def test_datos_visibles(self) -> None:
        self.assertEqual(
            self.modelo.data(self.modelo.index(0, 0), Qt.DisplayRole), "R001"
        )
        self.assertEqual(
            self.modelo.data(self.modelo.index(0, 4), Qt.DisplayRole),
            "Press de banca; Plancha",
        )
        self.assertEqual(
            self.modelo.data(self.modelo.index(1, 5), Qt.DisplayRole), "10"
        )
        self.assertEqual(
            self.modelo.data(self.modelo.index(0, 5), Qt.TextAlignmentRole),
            int(Qt.AlignCenter),
        )
        self.assertEqual(
            self.modelo.data(self.modelo.index(0, 4), Qt.ToolTipRole),
            "Press de banca; Plancha",
        )

    def test_rol_usuario_devuelve_registro(self) -> None:
        registro = self.modelo.data(self.modelo.index(0, 0), Qt.UserRole)

        self.assertIsInstance(registro, Rutina)
        self.assertEqual(registro.id_rutina, "R001")

    def test_indice_invalido(self) -> None:
        self.assertIsNone(self.modelo.data(self.modelo.index(99, 0)))
        self.assertIsNone(self.modelo.registro_en(99))
        self.assertIsNone(self.modelo.registro_en(-1))

    def test_sort_numerico_de_series(self) -> None:
        self.modelo.sort(5, Qt.AscendingOrder)

        series = [
            self.modelo.registro_en(fila).series
            for fila in range(self.modelo.rowCount())
        ]
        self.assertEqual(series, [2, 3, 10])

    def test_sort_descendente(self) -> None:
        self.modelo.sort(5, Qt.DescendingOrder)

        series = [
            self.modelo.registro_en(fila).series
            for fila in range(self.modelo.rowCount())
        ]
        self.assertEqual(series, [10, 3, 2])

    def test_sort_texto_sin_tildes(self) -> None:
        self.modelo.sort(1, Qt.AscendingOrder)

        dias = [
            self.modelo.registro_en(fila).dia
            for fila in range(self.modelo.rowCount())
        ]
        self.assertEqual(dias, ["Lunes", "Miércoles", "Sábado"])

    def test_set_registros(self) -> None:
        self.modelo.set_registros([])
        self.assertEqual(self.modelo.rowCount(), 0)

        self.modelo.set_registros([crear_rutina("R100")])
        self.assertEqual(self.modelo.rowCount(), 1)
        self.assertEqual(self.modelo.registro_en(0).id_rutina, "R100")

    def test_registros_devuelve_copia(self) -> None:
        registros = self.modelo.registros()

        self.assertIsInstance(registros, tuple)
        self.assertEqual(len(registros), 3)
        self.assertEqual(self.modelo.rowCount(), 3)


class EjercicioTableModelTests(QtTestCase):
    def setUp(self) -> None:
        self.ejercicios = [
            crear_ejercicio("E001", "Press de banca"),
            crear_ejercicio("E002", "Jalón al pecho", grupo="Espalda"),
            crear_ejercicio("E003", "Curl con mancuernas", grupo="Bíceps"),
        ]
        self.modelo = EjercicioTableModel(self.ejercicios)

    def test_dimensiones_y_datos(self) -> None:
        self.assertEqual(self.modelo.rowCount(), 3)
        self.assertEqual(self.modelo.columnCount(), 6)
        self.assertEqual(
            self.modelo.headerData(1, Qt.Horizontal, Qt.DisplayRole),
            "Nombre",
        )
        self.assertEqual(
            self.modelo.data(self.modelo.index(0, 1), Qt.DisplayRole),
            "Press de banca",
        )
        self.assertIsInstance(
            self.modelo.data(self.modelo.index(0, 0), Qt.UserRole),
            Ejercicio,
        )
        self.assertEqual(
            self.modelo.data(self.modelo.index(0, 1), Qt.ToolTipRole),
            "Press de banca",
        )

    def test_sort_por_nombre_sin_tildes(self) -> None:
        self.modelo.sort(1, Qt.AscendingOrder)

        nombres = [
            self.modelo.registro_en(fila).nombre
            for fila in range(self.modelo.rowCount())
        ]
        self.assertEqual(
            nombres,
            ["Curl con mancuernas", "Jalón al pecho", "Press de banca"],
        )

    def test_set_registros(self) -> None:
        self.modelo.set_registros([])
        self.assertEqual(self.modelo.rowCount(), 0)

        self.modelo.set_registros([crear_ejercicio("E100", "Plancha")])
        self.assertEqual(self.modelo.rowCount(), 1)
        self.assertEqual(self.modelo.registro_en(0).id_ejercicio, "E100")


if __name__ == "__main__":
    unittest.main()
