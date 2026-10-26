import unittest

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QComboBox

from app.config import RUTINAS_PATH
from services.csv_service import CsvService
from services.rutina_service import RutinaService
from tests.qt_test_case import QtTestCase
from ui.widgets.rutinas_tab import RutinasTab


class RutinasTabTests(QtTestCase):
    def setUp(self) -> None:
        self.servicio = RutinaService(CsvService(), RUTINAS_PATH)
        self.servicio.cargar()
        self.tab = RutinasTab(self.servicio)
        self.addCleanup(self.tab.close)
        self.addCleanup(self.tab.deleteLater)

    def seleccionar(self, combo: QComboBox, valor: str) -> None:
        indice = combo.findData(valor)
        self.assertGreaterEqual(indice, 0, f"No se encontró el valor {valor!r}")
        combo.setCurrentIndex(indice)

    def test_combos_poblados(self) -> None:
        self.assertEqual(self.tab.combo_dia.count(), 8)
        self.assertEqual(self.tab.combo_grupo.count(), 11)
        self.assertEqual(self.tab.combo_nivel.count(), 3)
        self.assertEqual(self.tab.combo_horario.count(), 6)

        placeholders = (
            (self.tab.combo_dia, "Todos los días"),
            (self.tab.combo_grupo, "Todos los grupos"),
            (self.tab.combo_nivel, "Todos los niveles"),
            (self.tab.combo_horario, "Todos los horarios"),
        )
        for combo, placeholder in placeholders:
            self.assertEqual(combo.currentData(), "")
            self.assertEqual(combo.itemText(0), placeholder)

        self.assertEqual(self.tab.combo_horario.itemData(1), "07:00-08:00")
        self.assertEqual(self.tab.combo_horario.itemData(5), "Descanso")

    def test_niveles_dinamicos_sin_duplicar_placeholder(self) -> None:
        textos = [
            self.tab.combo_nivel.itemText(indice)
            for indice in range(self.tab.combo_nivel.count())
        ]

        self.assertEqual(textos[0], "Todos los niveles")
        self.assertNotIn("Todos los niveles", textos[1:])
        self.assertEqual(len(textos), len(set(textos)))
        for nivel in self.servicio.niveles():
            self.assertEqual(textos.count(nivel), 1)

    def test_filtro_por_dia(self) -> None:
        self.seleccionar(self.tab.combo_dia, "Lunes")

        self.assertEqual(self.tab.modelo.rowCount(), 2)
        self.assertEqual(
            self.tab.etiqueta_estado.text(),
            "Mostrando 2 de 10 rutinas.",
        )

    def test_filtro_por_nivel(self) -> None:
        self.seleccionar(self.tab.combo_nivel, "Intermedio")

        self.assertEqual(self.tab.modelo.rowCount(), 3)
        ids = [
            self.tab.modelo.registro_en(fila).id_rutina
            for fila in range(self.tab.modelo.rowCount())
        ]
        self.assertEqual(ids, ["R001", "R003", "R006"])

    def test_filtro_por_grupo_y_horario(self) -> None:
        self.seleccionar(self.tab.combo_grupo, "Pecho")
        self.assertEqual(self.tab.modelo.rowCount(), 1)

        self.seleccionar(self.tab.combo_grupo, "")
        self.seleccionar(self.tab.combo_horario, "18:00-19:00")
        ids = [
            self.tab.modelo.registro_en(fila).id_rutina
            for fila in range(self.tab.modelo.rowCount())
        ]
        self.assertEqual(ids, ["R002", "R004"])

    def test_busqueda_libre(self) -> None:
        self.tab.busqueda.setText("triceps")

        self.assertEqual(self.tab.modelo.rowCount(), 1)
        self.assertEqual(self.tab.modelo.registro_en(0).id_rutina, "R002")

        self.tab.busqueda.setText("press banca")
        self.assertEqual(self.tab.modelo.rowCount(), 1)
        self.assertEqual(self.tab.modelo.registro_en(0).id_rutina, "R001")

    def test_busqueda_sin_resultados(self) -> None:
        self.tab.busqueda.setText("no existe")

        self.assertEqual(self.tab.modelo.rowCount(), 0)
        self.assertEqual(
            self.tab.etiqueta_estado.text(),
            "Sin coincidencias. 0 de 10 rutinas.",
        )

    def test_filtros_combinados(self) -> None:
        self.seleccionar(self.tab.combo_dia, "Lunes")
        self.seleccionar(self.tab.combo_nivel, "Intermedio")

        self.assertEqual(self.tab.modelo.rowCount(), 1)
        self.assertEqual(self.tab.modelo.registro_en(0).id_rutina, "R001")

        self.seleccionar(self.tab.combo_grupo, "Piernas")
        self.assertEqual(self.tab.modelo.rowCount(), 0)

    def test_limpiar_filtros(self) -> None:
        self.seleccionar(self.tab.combo_dia, "Lunes")
        self.seleccionar(self.tab.combo_nivel, "Intermedio")
        self.tab.busqueda.setText("press")

        self.tab.boton_limpiar.click()

        self.assertEqual(self.tab.modelo.rowCount(), 10)
        self.assertEqual(self.tab.combo_dia.currentIndex(), 0)
        self.assertEqual(self.tab.combo_nivel.currentIndex(), 0)
        self.assertEqual(self.tab.busqueda.text(), "")
        self.assertEqual(
            self.tab.etiqueta_estado.text(),
            "10 rutinas cargadas.",
        )

    def test_orden_se_conserva_al_filtrar(self) -> None:
        self.tab.tabla.sortByColumn(5, Qt.DescendingOrder)
        self.seleccionar(self.tab.combo_dia, "Miércoles")

        ids = [
            self.tab.modelo.registro_en(fila).id_rutina
            for fila in range(self.tab.modelo.rowCount())
        ]
        self.assertEqual(ids, ["R005", "R010"])

    def test_refrescar_datos_reinicia_filtros(self) -> None:
        self.seleccionar(self.tab.combo_dia, "Lunes")
        self.tab.busqueda.setText("press")

        self.tab.refrescar_datos(reiniciar_filtros=True)

        self.assertEqual(self.tab.modelo.rowCount(), 10)
        self.assertEqual(self.tab.combo_dia.currentIndex(), 0)
        self.assertEqual(self.tab.busqueda.text(), "")

    def test_tab_sin_datos(self) -> None:
        servicio_vacio = RutinaService(CsvService(), RUTINAS_PATH)
        tab = RutinasTab(servicio_vacio)
        self.addCleanup(tab.close)
        self.addCleanup(tab.deleteLater)

        self.assertEqual(tab.modelo.rowCount(), 0)
        self.assertEqual(tab.combo_dia.count(), 1)
        self.assertIn("No hay rutinas cargadas", tab.etiqueta_estado.text())


if __name__ == "__main__":
    unittest.main()
