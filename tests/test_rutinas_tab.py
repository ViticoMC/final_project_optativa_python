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
        self.assertEqual(self.tab.combo_grupo.count(), 15)
        self.assertEqual(self.tab.combo_nivel.count(), 4)
        self.assertEqual(self.tab.combo_horario.count(), 10)

        placeholders = (
            (self.tab.combo_dia, "Todos los días"),
            (self.tab.combo_grupo, "Todos los grupos"),
            (self.tab.combo_nivel, "Todos los niveles"),
            (self.tab.combo_horario, "Todos los horarios"),
        )
        for combo, placeholder in placeholders:
            self.assertEqual(combo.currentData(), "")
            self.assertEqual(combo.itemText(0), placeholder)

        self.assertEqual(self.tab.combo_horario.itemData(1), "06:30-07:30")
        self.assertEqual(
            self.tab.combo_horario.itemData(self.tab.combo_horario.count() - 1),
            "Descanso",
        )

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

        self.assertEqual(self.tab.modelo.rowCount(), 10)
        self.assertEqual(
            self.tab.etiqueta_estado.text(),
            "Mostrando 10 de 60 rutinas.",
        )

    def test_filtro_por_nivel(self) -> None:
        self.seleccionar(self.tab.combo_nivel, "Intermedio")

        self.assertEqual(self.tab.modelo.rowCount(), 27)
        ids = {
            self.tab.modelo.registro_en(fila).id_rutina
            for fila in range(self.tab.modelo.rowCount())
        }
        self.assertIn("R001", ids)
        self.assertIn("R057", ids)
        self.assertTrue(
            all(
                self.tab.modelo.registro_en(fila).nivel == "Intermedio"
                for fila in range(self.tab.modelo.rowCount())
            )
        )

    def test_filtro_por_grupo_y_horario(self) -> None:
        self.seleccionar(self.tab.combo_grupo, "Pecho")
        self.assertEqual(self.tab.modelo.rowCount(), 6)

        self.seleccionar(self.tab.combo_grupo, "")
        self.seleccionar(self.tab.combo_horario, "18:00-19:00")
        ids = [
            self.tab.modelo.registro_en(fila).id_rutina
            for fila in range(self.tab.modelo.rowCount())
        ]
        self.assertEqual(
            ids,
            ["R002", "R004", "R036", "R037", "R038", "R058", "R059", "R060"],
        )

    def test_busqueda_libre(self) -> None:
        self.tab.busqueda.setText("triceps")

        self.assertEqual(self.tab.modelo.rowCount(), 2)
        self.assertIn(
            "R002",
            {
                self.tab.modelo.registro_en(fila).id_rutina
                for fila in range(self.tab.modelo.rowCount())
            },
        )

        self.tab.busqueda.setText("press banca")
        self.assertEqual(self.tab.modelo.rowCount(), 8)
        self.assertIn(
            "R001",
            {
                self.tab.modelo.registro_en(fila).id_rutina
                for fila in range(self.tab.modelo.rowCount())
            },
        )

    def test_busqueda_sin_resultados(self) -> None:
        self.tab.busqueda.setText("no existe")

        self.assertEqual(self.tab.modelo.rowCount(), 0)
        self.assertEqual(
            self.tab.etiqueta_estado.text(),
            "Sin coincidencias. 0 de 60 rutinas.",
        )

    def test_filtros_combinados(self) -> None:
        self.seleccionar(self.tab.combo_dia, "Lunes")
        self.seleccionar(self.tab.combo_nivel, "Intermedio")

        self.assertEqual(self.tab.modelo.rowCount(), 5)
        self.assertIn(
            "R001",
            {
                self.tab.modelo.registro_en(fila).id_rutina
                for fila in range(self.tab.modelo.rowCount())
            },
        )

        self.seleccionar(self.tab.combo_grupo, "Piernas")
        self.assertEqual(self.tab.modelo.rowCount(), 0)

    def test_limpiar_filtros(self) -> None:
        self.seleccionar(self.tab.combo_dia, "Lunes")
        self.seleccionar(self.tab.combo_nivel, "Intermedio")
        self.tab.busqueda.setText("press")

        self.tab.boton_limpiar.click()

        self.assertEqual(self.tab.modelo.rowCount(), 60)
        self.assertEqual(self.tab.combo_dia.currentIndex(), 0)
        self.assertEqual(self.tab.combo_nivel.currentIndex(), 0)
        self.assertEqual(self.tab.busqueda.text(), "")
        self.assertEqual(
            self.tab.etiqueta_estado.text(),
            "60 rutinas cargadas.",
        )

    def test_orden_se_conserva_al_filtrar(self) -> None:
        self.tab.tabla.sortByColumn(5, Qt.DescendingOrder)
        self.seleccionar(self.tab.combo_dia, "Miércoles")

        ids = [
            self.tab.modelo.registro_en(fila).id_rutina
            for fila in range(self.tab.modelo.rowCount())
        ]
        self.assertEqual(
            ids,
            ["R023", "R015", "R005", "R016", "R031", "R050", "R058", "R010", "R046"],
        )

    def test_atajos_de_busqueda_y_filtros(self) -> None:
        self.assertEqual(self.tab.atajo_buscar.key().toString(), "Ctrl+F")
        self.assertEqual(self.tab.atajo_limpiar.key().toString(), "Ctrl+L")

    def test_exportar_emite_senal_y_respeta_filtros(self) -> None:
        self.seleccionar(self.tab.combo_dia, "Lunes")
        recibido: list[bool] = []
        self.tab.exportar_solicitado.connect(lambda: recibido.append(True))

        self.tab.boton_exportar.click()

        self.assertEqual(recibido, [True])
        visibles = self.tab.registros_visibles()
        self.assertEqual(len(visibles), 10)
        self.assertEqual({rutina.dia for rutina in visibles}, {"Lunes"})

    def test_refrescar_datos_reinicia_filtros(self) -> None:
        self.seleccionar(self.tab.combo_dia, "Lunes")
        self.tab.busqueda.setText("press")

        self.tab.refrescar_datos(reiniciar_filtros=True)

        self.assertEqual(self.tab.modelo.rowCount(), 60)
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
