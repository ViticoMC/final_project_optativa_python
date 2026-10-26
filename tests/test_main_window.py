import unittest

from app.config import CATALOGO_PATH, RUTINAS_PATH
from services.container import AppServices
from services.csv_service import CsvService
from services.ejercicio_service import EjercicioService
from services.rutina_service import RutinaService
from tests.qt_test_case import QtTestCase
from ui.main_window import MainWindow


class MainWindowTests(QtTestCase):
    def crear_ventana(self) -> MainWindow:
        csv_service = CsvService()
        servicios = AppServices(
            rutinas=RutinaService(csv_service, RUTINAS_PATH),
            ejercicios=EjercicioService(csv_service, CATALOGO_PATH),
        )
        ventana = MainWindow(servicios)
        self.addCleanup(ventana.close)
        self.addCleanup(ventana.deleteLater)
        return ventana

    def test_carga_inicial_de_datos(self) -> None:
        ventana = self.crear_ventana()

        self.assertEqual(ventana.tabs.count(), 2)
        self.assertEqual(ventana.tabs.tabText(0), "Rutinas")
        self.assertEqual(ventana.tabs.tabText(1), "Ejercicios")
        self.assertEqual(ventana.rutinas_tab.modelo.rowCount(), 10)
        self.assertEqual(ventana.ejercicios_tab.modelo.rowCount(), 13)
        self.assertEqual(
            ventana.etiqueta_estado.text(),
            "10 rutinas · 13 ejercicios",
        )
        self.assertIn("12/28", ventana.ejercicios_tab.etiqueta_cobertura.text())
        self.assertEqual(
            ventana.ejercicios_tab.detalle_titulo.text(),
            "Press de banca",
        )

    def test_acciones_de_menu(self) -> None:
        ventana = self.crear_ventana()

        self.assertEqual(ventana.accion_importar.shortcut().toString(), "Ctrl+O")
        self.assertEqual(
            ventana.accion_importar_ejercicios.shortcut().toString(),
            "Ctrl+Shift+O",
        )
        self.assertEqual(ventana.accion_salir.shortcut().toString(), "Ctrl+Q")
        self.assertIn("Importar", ventana.accion_importar.text())
        self.assertIn("catálogo", ventana.accion_importar_ejercicios.text())
        self.assertIn("Acerca de", ventana.accion_acerca.text())

    def test_botones_importar(self) -> None:
        ventana = self.crear_ventana()

        self.assertEqual(ventana.rutinas_tab.boton_importar.text(), "Importar CSV")
        self.assertTrue(ventana.rutinas_tab.boton_importar.isEnabled())
        self.assertEqual(
            ventana.ejercicios_tab.boton_importar.text(),
            "Importar catálogo CSV",
        )
        self.assertTrue(ventana.ejercicios_tab.boton_importar.isEnabled())

    def test_tablas_configuradas(self) -> None:
        ventana = self.crear_ventana()

        self.assertTrue(ventana.rutinas_tab.tabla.isSortingEnabled())
        self.assertFalse(ventana.rutinas_tab.tabla.verticalHeader().isVisible())
        self.assertTrue(ventana.ejercicios_tab.tabla.isSortingEnabled())
        self.assertFalse(
            ventana.ejercicios_tab.tabla.verticalHeader().isVisible()
        )


if __name__ == "__main__":
    unittest.main()
