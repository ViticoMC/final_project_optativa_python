import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.config import (
    CATALOGO_PATH,
    COLUMNAS_RUTINA,
    NUTRICION_PATH,
    RUTINAS_PATH,
)
from services.container import AppServices
from services.csv_service import CsvService
from services.ejercicio_service import EjercicioService
from services.estadistica_service import EstadisticaService
from services.export_service import ExportService
from services.nutricion_service import NutricionService
from services.rutina_service import RutinaService
from tests.qt_test_case import QtTestCase
from ui.main_window import MainWindow


class MainWindowTests(QtTestCase):
    def crear_ventana(self) -> MainWindow:
        csv_service = CsvService()
        servicios = AppServices(
            rutinas=RutinaService(csv_service, RUTINAS_PATH),
            ejercicios=EjercicioService(csv_service, CATALOGO_PATH),
            nutricion=NutricionService(csv_service, NUTRICION_PATH),
            estadisticas=EstadisticaService(),
            exportacion=ExportService(csv_service),
        )
        ventana = MainWindow(servicios)
        self.addCleanup(ventana.close)
        self.addCleanup(ventana.deleteLater)
        return ventana

    def test_carga_inicial_de_datos(self) -> None:
        ventana = self.crear_ventana()

        self.assertEqual(ventana.tabs.count(), 4)
        self.assertEqual(ventana.tabs.tabText(0), "Rutinas")
        self.assertEqual(ventana.tabs.tabText(1), "Ejercicios")
        self.assertEqual(ventana.tabs.tabText(2), "Nutrición")
        self.assertEqual(ventana.tabs.tabText(3), "Estadísticas")
        self.assertEqual(ventana.rutinas_tab.modelo.rowCount(), 10)
        self.assertEqual(ventana.ejercicios_tab.modelo.rowCount(), 13)
        self.assertEqual(ventana.nutricion_tab.modelo.rowCount(), 7)
        self.assertEqual(ventana.estadisticas_tab.modelo_dias.rowCount(), 7)
        self.assertEqual(
            ventana.estadisticas_tab.valor_rutinas.text(),
            "10",
        )
        self.assertEqual(
            ventana.estadisticas_tab.valor_series.text(),
            "26",
        )
        self.assertEqual(
            ventana.estadisticas_tab.valor_catalogo.text(),
            "13",
        )
        self.assertEqual(
            ventana.estadisticas_tab.valor_nutricion.text(),
            "7",
        )
        self.assertEqual(
            ventana.etiqueta_estado.text(),
            "10 rutinas · 13 ejercicios · 7 comidas",
        )
        self.assertIn("12/28", ventana.ejercicios_tab.etiqueta_cobertura.text())
        self.assertEqual(
            ventana.ejercicios_tab.detalle_titulo.text(),
            "Press de banca",
        )
        self.assertEqual(
            ventana.nutricion_tab.detalle_titulo.text(),
            "Desayuno",
        )

    def test_acciones_de_menu(self) -> None:
        ventana = self.crear_ventana()

        self.assertEqual(ventana.accion_importar.shortcut().toString(), "Ctrl+O")
        self.assertEqual(
            ventana.accion_importar_ejercicios.shortcut().toString(),
            "Ctrl+Shift+O",
        )
        self.assertEqual(
            ventana.accion_importar_nutricion.shortcut().toString(),
            "Ctrl+Shift+N",
        )
        self.assertEqual(ventana.accion_salir.shortcut().toString(), "Ctrl+Q")
        self.assertIn("Importar", ventana.accion_importar.text())
        self.assertIn("catálogo", ventana.accion_importar_ejercicios.text())
        self.assertIn(
            "nutricional",
            ventana.accion_importar_nutricion.text(),
        )
        self.assertIn("Acerca de", ventana.accion_acerca.text())
        self.assertIn(
            "rutinas visibles",
            ventana.accion_exportar_rutinas.text(),
        )
        self.assertIn(
            "catálogo visible",
            ventana.accion_exportar_ejercicios.text(),
        )
        self.assertIn(
            "plan visible",
            ventana.accion_exportar_nutricion.text(),
        )
        self.assertIn(
            "estadísticas",
            ventana.accion_exportar_estadisticas.text(),
        )

    def test_botones_importar(self) -> None:
        ventana = self.crear_ventana()

        self.assertEqual(ventana.rutinas_tab.boton_importar.text(), "Importar CSV")
        self.assertTrue(ventana.rutinas_tab.boton_importar.isEnabled())
        self.assertEqual(
            ventana.ejercicios_tab.boton_importar.text(),
            "Importar catálogo CSV",
        )
        self.assertTrue(ventana.ejercicios_tab.boton_importar.isEnabled())
        self.assertEqual(
            ventana.nutricion_tab.boton_importar.text(),
            "Importar plan CSV",
        )
        self.assertTrue(ventana.nutricion_tab.boton_importar.isEnabled())
        self.assertEqual(
            ventana.rutinas_tab.boton_exportar.text(),
            "Exportar vista CSV",
        )
        self.assertEqual(
            ventana.ejercicios_tab.boton_exportar.text(),
            "Exportar vista CSV",
        )
        self.assertEqual(
            ventana.nutricion_tab.boton_exportar.text(),
            "Exportar vista CSV",
        )
        self.assertEqual(
            ventana.estadisticas_tab.boton_exportar.text(),
            "Exportar estadísticas CSV",
        )

    def test_exportar_rutinas_desde_vista_filtrada(self) -> None:
        ventana = self.crear_ventana()
        temporal = tempfile.TemporaryDirectory()
        self.addCleanup(temporal.cleanup)
        destino = Path(temporal.name) / "salida.csv"

        indice = ventana.rutinas_tab.combo_dia.findData("Lunes")
        ventana.rutinas_tab.combo_dia.setCurrentIndex(indice)

        with patch(
            "ui.main_window.QFileDialog.getSaveFileName",
            return_value=(str(destino), ""),
        ):
            ventana._exportar_rutinas()

        self.assertTrue(destino.exists())
        filas = CsvService().leer(
            destino,
            COLUMNAS_RUTINA,
            columna_id="id_rutina",
        )
        self.assertEqual(len(filas), 2)
        self.assertEqual({fila["dia"] for fila in filas}, {"Lunes"})
        self.assertIn("2 rutinas", ventana.statusBar().currentMessage())

    def test_tablas_configuradas(self) -> None:
        ventana = self.crear_ventana()

        self.assertTrue(ventana.rutinas_tab.tabla.isSortingEnabled())
        self.assertFalse(ventana.rutinas_tab.tabla.verticalHeader().isVisible())
        self.assertTrue(ventana.ejercicios_tab.tabla.isSortingEnabled())
        self.assertFalse(
            ventana.ejercicios_tab.tabla.verticalHeader().isVisible()
        )
        self.assertTrue(ventana.nutricion_tab.tabla.isSortingEnabled())
        self.assertFalse(
            ventana.nutricion_tab.tabla.verticalHeader().isVisible()
        )
        self.assertFalse(
            ventana.estadisticas_tab.tabla_dias.isSortingEnabled()
        )
        self.assertFalse(
            ventana.estadisticas_tab.tabla_dias.verticalHeader().isVisible()
        )


if __name__ == "__main__":
    unittest.main()
