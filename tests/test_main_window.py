import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PyQt5.QtCore import QSettings

from app.config import (
    CATALOGO_PATH,
    COLUMNAS_NUTRICION,
    COLUMNAS_PLANTILLA,
    COLUMNAS_RUTINA,
    NUTRICION_PATH,
    RUTINAS_PATH,
)
from services.comida_personal_service import ComidaPersonalService
from services.container import AppServices
from services.csv_service import CsvService
from services.ejercicio_service import EjercicioService
from services.estadistica_service import EstadisticaService
from services.export_service import ExportService
from services.nutricion_service import NutricionService
from services.plantilla_service import PlantillaService
from services.rutina_service import RutinaService
from tests.qt_test_case import QtTestCase
from ui.main_window import MainWindow


class MainWindowTests(QtTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.temporal_datos = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporal_datos.cleanup)
        self.ruta_plantillas = (
            Path(self.temporal_datos.name) / "mis_rutinas.csv"
        )
        self.ruta_comidas = (
            Path(self.temporal_datos.name) / "mis_comidas.csv"
        )

    def crear_ventana(
        self,
        settings: QSettings | None = None,
    ) -> MainWindow:
        csv_service = CsvService()
        rutinas = RutinaService(csv_service, RUTINAS_PATH)
        ejercicios = EjercicioService(csv_service, CATALOGO_PATH)
        nutricion = NutricionService(csv_service, NUTRICION_PATH)
        servicios = AppServices(
            rutinas=rutinas,
            ejercicios=ejercicios,
            nutricion=nutricion,
            estadisticas=EstadisticaService(),
            exportacion=ExportService(csv_service),
            plantillas=PlantillaService(
                csv_service,
                ejercicios,
                rutinas,
                self.ruta_plantillas,
            ),
            comidas_personales=ComidaPersonalService(
                csv_service,
                nutricion,
                self.ruta_comidas,
            ),
        )
        ventana = MainWindow(servicios, settings=settings)
        self.addCleanup(ventana.close)
        self.addCleanup(ventana.deleteLater)
        return ventana

    def test_carga_inicial_de_datos(self) -> None:
        ventana = self.crear_ventana()

        self.assertEqual(ventana.tabs.count(), 5)
        self.assertEqual(ventana.tabs.tabText(0), "Rutinas")
        self.assertEqual(ventana.tabs.tabText(1), "Ejercicios")
        self.assertEqual(ventana.tabs.tabText(2), "Nutrición")
        self.assertEqual(ventana.tabs.tabText(3), "Estadísticas")
        self.assertEqual(ventana.tabs.tabText(4), "Mi plan")
        self.assertEqual(ventana.rutinas_tab.modelo.rowCount(), 60)
        self.assertEqual(ventana.ejercicios_tab.modelo.rowCount(), 100)
        self.assertEqual(ventana.nutricion_tab.modelo.rowCount(), 42)
        self.assertEqual(ventana.estadisticas_tab.modelo_dias.rowCount(), 7)
        self.assertEqual(
            ventana.estadisticas_tab.valor_rutinas.text(),
            "60",
        )
        self.assertEqual(
            ventana.estadisticas_tab.valor_series.text(),
            "196",
        )
        self.assertEqual(
            ventana.estadisticas_tab.valor_catalogo.text(),
            "100",
        )
        self.assertEqual(
            ventana.estadisticas_tab.valor_nutricion.text(),
            "42",
        )
        self.assertEqual(
            ventana.etiqueta_estado.text(),
            "60 rutinas · 100 ejercicios · 42 comidas · 0 plantillas · 0 mis comidas",
        )
        self.assertIn("100/100", ventana.ejercicios_tab.etiqueta_cobertura.text())
        self.assertEqual(
            ventana.ejercicios_tab.detalle_titulo.text(),
            "Press de banca",
        )
        self.assertEqual(
            ventana.nutricion_tab.detalle_titulo.text(),
            "Desayuno",
        )

    def crear_datos_personales(self) -> None:
        csv_service = CsvService()
        csv_service.escribir(
            self.ruta_plantillas,
            COLUMNAS_PLANTILLA,
            [
                {
                    "id_plantilla": "MR001",
                    "grupo_muscular": "Core",
                    "ejercicios": "Plancha; Dead bug",
                    "series": "3",
                    "repeticiones_o_duracion": "20-30 s por ejercicio",
                    "nivel": "Principiante",
                    "descanso": "30 s",
                }
            ],
        )
        csv_service.escribir(
            self.ruta_comidas,
            COLUMNAS_NUTRICION,
            [
                {
                    "id_plan": "MC001",
                    "comida": "Desayuno",
                    "horario": "07:30",
                    "alimentos_sugeridos": "huevo; plátano",
                    "objetivo_general": "Energía y proteína",
                    "observaciones": "Selección personal.",
                }
            ],
        )

    def test_carga_datos_personales(self) -> None:
        self.crear_datos_personales()

        ventana = self.crear_ventana()

        self.assertEqual(ventana.plantilla_service.total(), 1)
        self.assertEqual(ventana.comida_personal_service.total(), 1)
        self.assertEqual(ventana.mi_plan_tab.tabla_plantillas.model().rowCount(), 1)
        self.assertEqual(ventana.mi_plan_tab.tabla_comidas.model().rowCount(), 1)
        self.assertIn("1 plantillas", ventana.etiqueta_estado.text())
        self.assertIn("1 mis comidas", ventana.etiqueta_estado.text())

    def test_exportar_datos_personales(self) -> None:
        self.crear_datos_personales()
        ventana = self.crear_ventana()
        temporal = tempfile.TemporaryDirectory()
        self.addCleanup(temporal.cleanup)
        destino_plantillas = Path(temporal.name) / "mis_rutinas.csv"
        destino_comidas = Path(temporal.name) / "mis_comidas.csv"

        with patch(
            "ui.main_window.QFileDialog.getSaveFileName",
            return_value=(str(destino_plantillas), ""),
        ):
            ventana._exportar_plantillas()
        with patch(
            "ui.main_window.QFileDialog.getSaveFileName",
            return_value=(str(destino_comidas), ""),
        ):
            ventana._exportar_comidas_personales()

        self.assertTrue(destino_plantillas.exists())
        self.assertTrue(destino_comidas.exists())
        self.assertEqual(
            len(CsvService().leer(destino_plantillas, COLUMNAS_PLANTILLA)),
            1,
        )
        self.assertEqual(
            len(CsvService().leer(destino_comidas, COLUMNAS_NUTRICION)),
            1,
        )

    def test_recargar_detecta_datos_personales_nuevos(self) -> None:
        ventana = self.crear_ventana()
        self.assertEqual(ventana.mi_plan_tab.tabla_plantillas.model().rowCount(), 0)

        self.crear_datos_personales()
        ventana.accion_recargar.trigger()

        self.assertEqual(ventana.mi_plan_tab.tabla_plantillas.model().rowCount(), 1)
        self.assertEqual(ventana.mi_plan_tab.tabla_comidas.model().rowCount(), 1)

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
        self.assertEqual(ventana.accion_recargar.shortcut().toString(), "F5")
        self.assertEqual(
            ventana.accion_ver_rutinas.shortcut().toString(),
            "Ctrl+1",
        )
        self.assertEqual(
            ventana.accion_ver_ejercicios.shortcut().toString(),
            "Ctrl+2",
        )
        self.assertEqual(
            ventana.accion_ver_nutricion.shortcut().toString(),
            "Ctrl+3",
        )
        self.assertEqual(
            ventana.accion_ver_estadisticas.shortcut().toString(),
            "Ctrl+4",
        )
        self.assertEqual(
            ventana.accion_ver_mi_plan.shortcut().toString(),
            "Ctrl+5",
        )
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
        self.assertIn(
            "rutinas",
            ventana.accion_exportar_plantillas.text(),
        )
        self.assertIn(
            "comidas",
            ventana.accion_exportar_comidas_personales.text(),
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
        self.assertEqual(len(filas), 10)
        self.assertEqual({fila["dia"] for fila in filas}, {"Lunes"})
        self.assertIn("10 rutinas", ventana.statusBar().currentMessage())

    def test_acciones_ver_cambian_de_pestana(self) -> None:
        ventana = self.crear_ventana()

        ventana.accion_ver_estadisticas.trigger()
        self.assertEqual(ventana.tabs.currentIndex(), 3)

        ventana.accion_ver_mi_plan.trigger()
        self.assertEqual(ventana.tabs.currentIndex(), 4)

        ventana.accion_ver_ejercicios.trigger()
        self.assertEqual(ventana.tabs.currentIndex(), 1)

    def test_recargar_datos_conserva_totales(self) -> None:
        ventana = self.crear_ventana()

        ventana.accion_recargar.trigger()

        self.assertEqual(ventana.rutinas_tab.modelo.rowCount(), 60)
        self.assertEqual(ventana.ejercicios_tab.modelo.rowCount(), 100)
        self.assertEqual(ventana.nutricion_tab.modelo.rowCount(), 42)
        self.assertEqual(ventana.estadisticas_tab.valor_series.text(), "196")
        self.assertEqual(
            ventana.statusBar().currentMessage(),
            "Datos recargados correctamente",
        )
        self.assertEqual(ventana.mi_plan_tab.plantillas_visibles(), ())
        self.assertEqual(ventana.mi_plan_tab.comidas_visibles(), ())

    def test_persistencia_de_pestana_y_carpetas(self) -> None:
        temporal = tempfile.TemporaryDirectory()
        self.addCleanup(temporal.cleanup)
        ruta_config = str(Path(temporal.name) / "config.ini")
        settings = QSettings(ruta_config, QSettings.IniFormat)

        ventana = self.crear_ventana(settings=settings)
        ventana.resize(1111, 777)
        ventana.tabs.setCurrentIndex(2)
        ventana._ultima_carpeta = Path(temporal.name)
        ventana._carpeta_exportacion = Path(temporal.name)
        ventana.close()

        nueva = self.crear_ventana(
            settings=QSettings(ruta_config, QSettings.IniFormat)
        )

        self.assertEqual(nueva.tabs.currentIndex(), 2)
        self.assertEqual(nueva.size().width(), 1111)
        self.assertEqual(nueva.size().height(), 777)
        self.assertEqual(nueva._ultima_carpeta, Path(temporal.name))
        self.assertEqual(nueva._carpeta_exportacion, Path(temporal.name))

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
        self.assertTrue(ventana.mi_plan_tab.tabla_plantillas.isSortingEnabled())
        self.assertTrue(ventana.mi_plan_tab.tabla_comidas.isSortingEnabled())


if __name__ == "__main__":
    unittest.main()
