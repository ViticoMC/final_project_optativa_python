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
from ui.dialogs_personal import (
    DialogoComidaPersonal,
    DialogoPlantillaRutina,
)


class PersonalDialogsTests(QtTestCase):
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
        self.ruta_plantillas = Path(self.temporal.name) / "mis_rutinas.csv"
        self.ruta_comidas = Path(self.temporal.name) / "mis_comidas.csv"
        self.plantillas = PlantillaService(
            self.csv_service,
            self.catalogo,
            self.rutinas,
            self.ruta_plantillas,
        )
        self.plantillas.cargar()
        self.comidas = ComidaPersonalService(
            self.csv_service,
            self.nutricion,
            self.ruta_comidas,
        )
        self.comidas.cargar()

    def test_plantilla_desde_rutina_estandar(self) -> None:
        dialogo = DialogoPlantillaRutina(self.plantillas)
        self.addCleanup(dialogo.deleteLater)

        indice = dialogo.combo_base.findData("R001")
        dialogo.combo_base.setCurrentIndex(indice)

        self.assertIn("Press de banca", dialogo.selector.seleccionados())
        self.assertIn("Aperturas", dialogo.selector.seleccionados())
        self.assertNotIn("Aperturas", dialogo.etiqueta_aviso.text())
        self.assertEqual(dialogo.datos_actuales()["series"], 3)
        self.assertEqual(
            dialogo.datos_actuales()["repeticiones"],
            "12-Aug",
        )
        self.assertEqual(
            dialogo.datos_actuales()["descanso"],
            "60-90 s",
        )

        dialogo.accept()

        self.assertEqual(dialogo.result(), QDialog.Accepted)
        self.assertEqual(dialogo.resultado.id_plantilla, "MR001")
        self.assertEqual(self.plantillas.total(), 1)

    def test_plantilla_valida_y_edita(self) -> None:
        dialogo = DialogoPlantillaRutina(self.plantillas)
        self.addCleanup(dialogo.deleteLater)
        dialogo.selector.set_seleccionados(("Plancha", "Dead bug"))
        dialogo.combo_series.setCurrentIndex(
            dialogo.combo_series.findData(
                self.plantillas.opciones_series()[0]
            )
        )
        dialogo._seleccionar_por_texto(
            dialogo.combo_repeticiones,
            self.plantillas.opciones_repeticiones()[0],
        )
        dialogo._seleccionar_por_texto(
            dialogo.combo_descanso,
            self.plantillas.opciones_descanso()[0],
        )
        dialogo._seleccionar_por_texto(
            dialogo.combo_nivel_plantilla,
            self.plantillas.opciones_nivel()[0],
        )
        dialogo.accept()
        plantilla = dialogo.resultado
        self.assertIsNotNone(plantilla)

        edicion = DialogoPlantillaRutina(
            self.plantillas,
            plantilla=plantilla,
        )
        self.addCleanup(edicion.deleteLater)
        self.assertFalse(edicion.grupo_base.isVisible())
        self.assertEqual(
            edicion.selector.seleccionados(),
            ("Plancha", "Dead bug"),
        )

        edicion.selector.agregar_valor("Plancha")
        edicion.accept()

        self.assertEqual(edicion.result(), QDialog.Accepted)
        self.assertEqual(self.plantillas.total(), 1)
        self.assertEqual(
            edicion.resultado.ejercicios,
            ("Plancha", "Dead bug"),
        )

    def test_plantilla_sin_ejercicios_no_guarda(self) -> None:
        dialogo = DialogoPlantillaRutina(self.plantillas)
        self.addCleanup(dialogo.deleteLater)

        with patch("ui.dialogs_personal.mostrar_error") as mostrar:
            dialogo.accept()

        self.assertIsNone(dialogo.resultado)
        self.assertEqual(dialogo.result(), 0)
        self.assertEqual(self.plantillas.total(), 0)
        mostrar.assert_called_once()

    def test_comida_desde_plan_estandar(self) -> None:
        dialogo = DialogoComidaPersonal(self.comidas)
        self.addCleanup(dialogo.deleteLater)

        indice = dialogo.combo_base.findData("D001")
        dialogo.combo_base.setCurrentIndex(indice)

        self.assertEqual(dialogo.datos_actuales()["comida"], "Desayuno")
        self.assertEqual(dialogo.datos_actuales()["horario"], "07:30")
        self.assertIn("huevo", dialogo.selector.seleccionados())

        dialogo.accept()

        self.assertEqual(dialogo.result(), QDialog.Accepted)
        self.assertEqual(dialogo.resultado.id_plan, "MC001")
        self.assertEqual(self.comidas.total(), 1)

    def test_comida_valida_edita_y_filtra(self) -> None:
        dialogo = DialogoComidaPersonal(self.comidas)
        self.addCleanup(dialogo.deleteLater)
        dialogo._seleccionar_por_texto(dialogo.combo_comida, "Desayuno")
        dialogo._seleccionar_por_texto(dialogo.combo_horario, "07:30")
        dialogo._seleccionar_por_texto(
            dialogo.combo_objetivo,
            "Energía y proteína",
        )
        dialogo.selector.set_seleccionados(("huevo", "plátano"))

        indice = dialogo.combo_origen.findData("Desayuno")
        dialogo.combo_origen.setCurrentIndex(indice)
        self.assertNotIn("Arroz o vianda", dialogo.selector.disponibles())
        self.assertIn(
            "Avena con leche o bebida vegetal",
            dialogo.selector.disponibles(),
        )

        dialogo.accept()
        comida = dialogo.resultado
        self.assertIsNotNone(comida)

        edicion = DialogoComidaPersonal(self.comidas, comida=comida)
        self.addCleanup(edicion.deleteLater)
        self.assertFalse(edicion.grupo_base.isVisible())
        self.assertEqual(edicion.selector.seleccionados(), ("huevo", "plátano"))

        edicion.selector.agregar_valor("huevo")
        edicion.accept()

        self.assertEqual(edicion.result(), QDialog.Accepted)
        self.assertEqual(self.comidas.total(), 1)
        self.assertEqual(edicion.resultado.alimentos, ("huevo", "plátano"))

    def test_comida_sin_alimentos_no_guarda(self) -> None:
        dialogo = DialogoComidaPersonal(self.comidas)
        self.addCleanup(dialogo.deleteLater)
        dialogo._seleccionar_por_texto(dialogo.combo_comida, "Desayuno")
        dialogo._seleccionar_por_texto(dialogo.combo_horario, "07:30")
        dialogo._seleccionar_por_texto(
            dialogo.combo_objetivo,
            "Energía y proteína",
        )

        with patch("ui.dialogs_personal.mostrar_error") as mostrar:
            dialogo.accept()

        self.assertIsNone(dialogo.resultado)
        self.assertEqual(dialogo.result(), 0)
        self.assertEqual(self.comidas.total(), 0)
        mostrar.assert_called_once()


if __name__ == "__main__":
    unittest.main()
