import unittest

from PyQt5.QtWidgets import QComboBox

from app.config import NUTRICION_PATH
from services.csv_service import CsvService
from services.nutricion_service import NutricionService
from tests.qt_test_case import QtTestCase
from ui.widgets.nutricion_tab import NutricionTab


class NutricionTabTests(QtTestCase):
    def setUp(self) -> None:
        self.servicio = NutricionService(CsvService(), NUTRICION_PATH)
        self.servicio.cargar()
        self.tab = NutricionTab(self.servicio)
        self.addCleanup(self.tab.close)
        self.addCleanup(self.tab.deleteLater)

    def seleccionar(self, combo: QComboBox, valor: str) -> None:
        indice = combo.findData(valor)
        self.assertGreaterEqual(indice, 0, f"No se encontró el valor {valor!r}")
        combo.setCurrentIndex(indice)

    def test_combos_poblados(self) -> None:
        self.assertEqual(self.tab.combo_comida.count(), 8)
        self.assertEqual(self.tab.combo_horario.count(), 8)
        self.assertEqual(self.tab.combo_objetivo.count(), 8)

        placeholders = (
            (self.tab.combo_comida, "Todas las comidas"),
            (self.tab.combo_horario, "Todos los horarios"),
            (self.tab.combo_objetivo, "Todos los objetivos"),
        )
        for combo, placeholder in placeholders:
            self.assertEqual(combo.currentData(), "")
            self.assertEqual(combo.itemText(0), placeholder)

    def test_horarios_ordenados_cronologicamente(self) -> None:
        valores = [
            self.tab.combo_horario.itemData(indice)
            for indice in range(1, self.tab.combo_horario.count())
        ]

        self.assertEqual(
            valores,
            [
                "07:30",
                "10:30",
                "13:00",
                "16:30",
                "19:30",
                "Después de entrenar",
                "Durante el día",
            ],
        )

    def test_plan_inicial_y_detalle(self) -> None:
        self.assertEqual(self.tab.modelo.rowCount(), 7)
        self.assertEqual(self.tab.detalle_titulo.text(), "Desayuno")
        self.assertIn("D001", self.tab.detalle_info.text())
        self.assertIn("07:30", self.tab.detalle_info.text())
        self.assertIn("Avena", self.tab.detalle_alimentos.text())
        self.assertIn("hambre", self.tab.detalle_observaciones.text())

    def test_resumen_del_plan(self) -> None:
        texto = self.tab.etiqueta_resumen.text()

        self.assertIn("7 comidas", texto)
        self.assertIn("17 sugerencias", texto)
        self.assertIn("16 alimentos únicos", texto)
        self.assertIn("plátano", self.tab.etiqueta_resumen.toolTip())

    def test_filtro_por_comida(self) -> None:
        self.seleccionar(self.tab.combo_comida, "Almuerzo")

        self.assertEqual(self.tab.modelo.rowCount(), 1)
        self.assertEqual(
            self.tab.etiqueta_estado.text(),
            "Mostrando 1 de 7 comidas.",
        )
        self.assertEqual(self.tab.detalle_titulo.text(), "Almuerzo")

    def test_filtro_por_horario_especial(self) -> None:
        self.seleccionar(self.tab.combo_horario, "Durante el día")

        self.assertEqual(self.tab.modelo.rowCount(), 1)
        self.assertEqual(self.tab.modelo.registro_en(0).id_plan, "D006")

    def test_filtro_por_objetivo(self) -> None:
        self.seleccionar(self.tab.combo_objetivo, "Recuperación")

        self.assertEqual(self.tab.modelo.rowCount(), 1)
        self.assertEqual(self.tab.modelo.registro_en(0).id_plan, "D007")
        self.assertEqual(self.tab.detalle_titulo.text(), "Postentreno")

    def test_busqueda_por_alimento(self) -> None:
        self.tab.busqueda.setText("fruta")

        ids = [
            self.tab.modelo.registro_en(fila).id_plan
            for fila in range(self.tab.modelo.rowCount())
        ]
        self.assertEqual(ids, ["D002", "D004"])

        self.tab.busqueda.setText("avena")
        self.assertEqual(self.tab.modelo.rowCount(), 1)
        self.assertEqual(self.tab.modelo.registro_en(0).id_plan, "D001")

    def test_busqueda_sin_resultados(self) -> None:
        self.tab.busqueda.setText("no existe")

        self.assertEqual(self.tab.modelo.rowCount(), 0)
        self.assertEqual(
            self.tab.etiqueta_estado.text(),
            "Sin coincidencias. 0 de 7 comidas.",
        )
        self.assertEqual(
            self.tab.detalle_titulo.text(),
            "Sin comida seleccionada",
        )

    def test_filtros_combinados(self) -> None:
        self.seleccionar(self.tab.combo_comida, "Cena")
        self.seleccionar(
            self.tab.combo_objetivo,
            "Proteína y micronutrientes",
        )
        self.assertEqual(self.tab.modelo.rowCount(), 1)
        self.assertEqual(self.tab.modelo.registro_en(0).id_plan, "D005")

        self.seleccionar(self.tab.combo_objetivo, "Hidratación")
        self.assertEqual(self.tab.modelo.rowCount(), 0)

    def test_limpiar_filtros(self) -> None:
        self.seleccionar(self.tab.combo_comida, "Cena")
        self.tab.busqueda.setText("pollo")

        self.tab.boton_limpiar.click()

        self.assertEqual(self.tab.modelo.rowCount(), 7)
        self.assertEqual(self.tab.combo_comida.currentIndex(), 0)
        self.assertEqual(self.tab.busqueda.text(), "")
        self.assertEqual(
            self.tab.etiqueta_estado.text(),
            "7 comidas cargadas.",
        )

    def test_exportar_emite_senal_y_respeta_filtros(self) -> None:
        self.seleccionar(self.tab.combo_comida, "Cena")
        recibido: list[bool] = []
        self.tab.exportar_solicitado.connect(lambda: recibido.append(True))

        self.tab.boton_exportar.click()

        self.assertEqual(recibido, [True])
        visibles = self.tab.registros_visibles()
        self.assertEqual(len(visibles), 1)
        self.assertEqual(visibles[0].comida, "Cena")

    def test_refrescar_datos_reinicia_filtros(self) -> None:
        self.seleccionar(self.tab.combo_comida, "Cena")
        self.tab.busqueda.setText("pollo")

        self.tab.refrescar_datos(reiniciar_filtros=True)

        self.assertEqual(self.tab.modelo.rowCount(), 7)
        self.assertEqual(self.tab.combo_comida.currentIndex(), 0)
        self.assertEqual(self.tab.busqueda.text(), "")

    def test_tab_sin_plan(self) -> None:
        servicio_vacio = NutricionService(CsvService(), NUTRICION_PATH)
        tab = NutricionTab(servicio_vacio)
        self.addCleanup(tab.close)
        self.addCleanup(tab.deleteLater)

        self.assertEqual(tab.modelo.rowCount(), 0)
        self.assertEqual(tab.combo_comida.count(), 1)
        self.assertIn("no cargado", tab.etiqueta_resumen.text())
        self.assertIn("No hay comidas cargadas", tab.etiqueta_estado.text())


if __name__ == "__main__":
    unittest.main()
