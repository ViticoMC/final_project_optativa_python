import unittest

from app.config import RUTINAS_PATH
from services.csv_service import CsvService
from services.rutina_service import RutinaService
from tests.qt_test_case import QtTestCase
from ui.main_window import MainWindow


class MainWindowTests(QtTestCase):
    def crear_ventana(self) -> MainWindow:
        servicio = RutinaService(CsvService(), RUTINAS_PATH)
        ventana = MainWindow(servicio)
        self.addCleanup(ventana.close)
        self.addCleanup(ventana.deleteLater)
        return ventana

    def test_carga_inicial_de_rutinas(self) -> None:
        ventana = self.crear_ventana()

        self.assertEqual(ventana.tabs.count(), 1)
        self.assertEqual(ventana.tabs.tabText(0), "Rutinas")
        self.assertEqual(ventana.rutinas_tab.modelo.rowCount(), 10)
        self.assertIn("10 rutinas", ventana.etiqueta_estado.text())
        self.assertIn("rutinas_fitness.csv", ventana.etiqueta_estado.text())

    def test_acciones_de_menu(self) -> None:
        ventana = self.crear_ventana()

        self.assertEqual(ventana.accion_importar.shortcut().toString(), "Ctrl+O")
        self.assertEqual(ventana.accion_salir.shortcut().toString(), "Ctrl+Q")
        self.assertIn("Importar", ventana.accion_importar.text())
        self.assertIn("Acerca de", ventana.accion_acerca.text())

    def test_boton_importar_existe(self) -> None:
        ventana = self.crear_ventana()

        self.assertEqual(ventana.rutinas_tab.boton_importar.text(), "Importar CSV")
        self.assertTrue(ventana.rutinas_tab.boton_importar.isEnabled())

    def test_tabla_configurada(self) -> None:
        ventana = self.crear_ventana()

        self.assertTrue(ventana.rutinas_tab.tabla.isSortingEnabled())
        self.assertFalse(ventana.rutinas_tab.tabla.verticalHeader().isVisible())


if __name__ == "__main__":
    unittest.main()
