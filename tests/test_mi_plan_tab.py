import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PyQt5.QtWidgets import QDialog

from app.config import CATALOGO_PATH, NUTRICION_PATH, RUTINAS_PATH
from services.comida_personal_service import ComidaPersonalService
from services.csv_service import CsvService
from services.ejercicio_service import EjercicioService
from services.nutricion_service import NutricionService
from services.plantilla_service import PlantillaService
from services.rutina_service import RutinaService
from tests.qt_test_case import QtTestCase
from ui.widgets.mi_plan_tab import MiPlanTab


class MiPlanTabTests(QtTestCase):
    def setUp(self) -> None:
        self.csv_service = CsvService()
        self.rutinas = RutinaService(self.csv_service, RUTINAS_PATH)
        self.rutinas.cargar()
        self.catalogo = EjercicioService(self.csv_service, CATALOGO_PATH)
        self.catalogo.cargar()
        self.nutricion = NutricionService(self.csv_service, NUTRICION_PATH)
        self.nutricion.cargar()

        self.temporal = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporal.cleanup)
        self.plantillas = PlantillaService(
            self.csv_service,
            self.catalogo,
            self.rutinas,
            Path(self.temporal.name) / "mis_rutinas.csv",
        )
        self.plantillas.cargar()
        self.comidas = ComidaPersonalService(
            self.csv_service,
            self.nutricion,
            Path(self.temporal.name) / "mis_comidas.csv",
        )
        self.comidas.cargar()

        self.tab = MiPlanTab(self.plantillas, self.comidas)
        self.addCleanup(self.tab.deleteLater)

    def crear_plantilla(self):
        return self.plantillas.crear(
            ("Plancha",),
            self.plantillas.opciones_series()[0],
            self.plantillas.opciones_repeticiones()[0],
            self.plantillas.opciones_nivel()[0],
            self.plantillas.opciones_descanso()[0],
        )

    def crear_comida(self):
        return self.comidas.crear(
            self.comidas.tipos_comida()[0],
            self.comidas.horarios()[0],
            ("huevo", "plátano"),
            self.comidas.objetivos()[0],
        )

    def test_estado_inicial_vacio(self) -> None:
        self.assertEqual(self.tab.tabla_plantillas.model().rowCount(), 0)
        self.assertEqual(self.tab.tabla_comidas.model().rowCount(), 0)
        self.assertFalse(self.tab.plantillas_panel.boton_editar.isEnabled())
        self.assertFalse(self.tab.plantillas_panel.boton_eliminar.isEnabled())
        self.assertFalse(self.tab.comidas_panel.boton_editar.isEnabled())
        self.assertFalse(self.tab.comidas_panel.boton_eliminar.isEnabled())
        self.assertIn(
            "Aún no hay plantillas",
            self.tab.plantillas_panel.etiqueta_estado.text(),
        )
        self.assertIn(
            "Aún no hay comidas",
            self.tab.comidas_panel.etiqueta_estado.text(),
        )

    def test_muestra_datos_y_habilita_acciones(self) -> None:
        self.crear_plantilla()
        self.crear_comida()
        self.tab.refrescar_datos()

        self.assertEqual(self.tab.tabla_plantillas.model().rowCount(), 1)
        self.assertEqual(self.tab.tabla_comidas.model().rowCount(), 1)
        self.assertEqual(len(self.tab.plantillas_visibles()), 1)
        self.assertEqual(len(self.tab.comidas_visibles()), 1)
        self.assertIn("1 plantilla", self.tab.plantillas_panel.etiqueta_estado.text())
        self.assertIn("1 comida", self.tab.comidas_panel.etiqueta_estado.text())

        self.tab.tabla_plantillas.selectRow(0)
        self.tab.tabla_comidas.selectRow(0)
        self.tab.plantillas_panel._actualizar_botones()
        self.tab.comidas_panel._actualizar_botones()

        self.assertTrue(self.tab.plantillas_panel.boton_editar.isEnabled())
        self.assertTrue(self.tab.plantillas_panel.boton_eliminar.isEnabled())
        self.assertTrue(self.tab.comidas_panel.boton_editar.isEnabled())
        self.assertTrue(self.tab.comidas_panel.boton_eliminar.isEnabled())

    def test_eliminar_con_confirmacion(self) -> None:
        self.crear_plantilla()
        self.crear_comida()
        self.tab.refrescar_datos()
        self.tab.tabla_plantillas.selectRow(0)
        self.tab.tabla_comidas.selectRow(0)

        cambios = []
        self.tab.datos_cambiados.connect(lambda: cambios.append(True))

        with patch(
            "ui.widgets.mi_plan_tab.QMessageBox.question",
            return_value=__import__("PyQt5.QtWidgets", fromlist=["QMessageBox"]).QMessageBox.Yes,
        ):
            self.tab.plantillas_panel.eliminar()
            self.tab.comidas_panel.eliminar()

        self.assertEqual(self.tab.tabla_plantillas.model().rowCount(), 0)
        self.assertEqual(self.tab.tabla_comidas.model().rowCount(), 0)
        self.assertEqual(cambios, [True, True])

    def test_botones_exportar_emiten_senales(self) -> None:
        plantillas = []
        comidas = []
        self.tab.exportar_plantillas_solicitado.connect(
            lambda: plantillas.append(True)
        )
        self.tab.exportar_comidas_solicitado.connect(
            lambda: comidas.append(True)
        )

        self.tab.plantillas_panel.boton_exportar.click()
        self.tab.comidas_panel.boton_exportar.click()

        self.assertEqual(plantillas, [True])
        self.assertEqual(comidas, [True])

    def test_crear_desde_panel_usa_dialogo_y_refresca(self) -> None:
        class DialogoFalso:
            Accepted = QDialog.Accepted

            def __init__(self, servicio, plantilla=None, parent=None) -> None:
                self.servicio = servicio

            def exec_(self):
                self.servicio.crear(
                    ("Plancha",),
                    self.servicio.opciones_series()[0],
                    self.servicio.opciones_repeticiones()[0],
                    self.servicio.opciones_nivel()[0],
                    self.servicio.opciones_descanso()[0],
                )
                return QDialog.Accepted

        with patch(
            "ui.widgets.mi_plan_tab.DialogoPlantillaRutina",
            DialogoFalso,
        ):
            self.tab.plantillas_panel.crear()

        self.assertEqual(self.tab.tabla_plantillas.model().rowCount(), 1)


if __name__ == "__main__":
    unittest.main()
