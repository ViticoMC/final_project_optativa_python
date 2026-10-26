import unittest

from app.config import CATALOGO_PATH, NUTRICION_PATH, RUTINAS_PATH
from services.csv_service import CsvService
from services.ejercicio_service import EjercicioService
from services.estadistica_service import EstadisticaService
from services.nutricion_service import NutricionService
from services.rutina_service import RutinaService
from tests.qt_test_case import QtTestCase
from ui.widgets.estadisticas_tab import EstadisticasTab


class EstadisticasTabTests(QtTestCase):
    def setUp(self) -> None:
        csv_service = CsvService()
        self.rutinas = RutinaService(csv_service, RUTINAS_PATH)
        self.rutinas.cargar()
        self.ejercicios = EjercicioService(csv_service, CATALOGO_PATH)
        self.ejercicios.cargar()
        self.comidas = NutricionService(csv_service, NUTRICION_PATH)
        self.comidas.cargar()

        self.tab = EstadisticasTab(
            EstadisticaService(),
            self.rutinas,
            self.ejercicios,
            self.comidas,
        )
        self.addCleanup(self.tab.close)
        self.addCleanup(self.tab.deleteLater)

    def test_tarjetas_resumen(self) -> None:
        self.assertEqual(self.tab.valor_rutinas.text(), "10")
        self.assertEqual(
            self.tab.detalle_rutinas.text(),
            "6 días activos · 1 de descanso",
        )
        self.assertEqual(self.tab.valor_series.text(), "26")
        self.assertEqual(
            self.tab.detalle_series.text(),
            "2.6 series por rutina",
        )
        self.assertEqual(self.tab.valor_catalogo.text(), "13")
        self.assertEqual(
            self.tab.detalle_catalogo.text(),
            "12/28 de las rutinas cubiertos (42.9 %)",
        )
        self.assertEqual(self.tab.valor_nutricion.text(), "7")
        self.assertEqual(
            self.tab.detalle_nutricion.text(),
            "16 alimentos únicos · 17 sugerencias",
        )

    def test_modelos_poblados(self) -> None:
        self.assertEqual(self.tab.modelo_dias.rowCount(), 7)
        self.assertEqual(self.tab.modelo_grupos.rowCount(), 10)
        self.assertEqual(self.tab.modelo_niveles.rowCount(), 2)
        self.assertEqual(self.tab.modelo_series.rowCount(), 9)
        self.assertEqual(self.tab.modelo_catalogo.rowCount(), 9)
        self.assertEqual(self.tab.modelo_comidas.rowCount(), 7)
        self.assertEqual(self.tab.modelo_ejercicios.rowCount(), 28)

    def test_contenido_de_tablas(self) -> None:
        primer_dia = self.tab.modelo_dias.registro_en(0)
        self.assertEqual(primer_dia.categoria, "Lunes")
        self.assertEqual(primer_dia.valor, 2)
        self.assertAlmostEqual(primer_dia.porcentaje, 20.0)

        primer_ejercicio = self.tab.modelo_ejercicios.registro_en(0)
        self.assertEqual(primer_ejercicio.nombre, "Plancha")
        self.assertEqual(primer_ejercicio.menciones, 2)
        self.assertTrue(primer_ejercicio.en_catalogo)

    def test_exportar_emite_senal(self) -> None:
        recibido: list[bool] = []
        self.tab.exportar_solicitado.connect(lambda: recibido.append(True))

        self.tab.boton_exportar.click()

        self.assertEqual(recibido, [True])

    def test_tablas_sin_ordenamiento(self) -> None:
        self.assertFalse(self.tab.tabla_dias.isSortingEnabled())
        self.assertFalse(self.tab.tabla_ejercicios.isSortingEnabled())

    def test_actualizar_recalcula(self) -> None:
        csv_service = CsvService()
        rutinas = RutinaService(csv_service, RUTINAS_PATH)
        ejercicios = EjercicioService(csv_service, CATALOGO_PATH)
        comidas = NutricionService(csv_service, NUTRICION_PATH)
        tab = EstadisticasTab(
            EstadisticaService(),
            rutinas,
            ejercicios,
            comidas,
        )
        self.addCleanup(tab.close)
        self.addCleanup(tab.deleteLater)

        self.assertEqual(tab.valor_rutinas.text(), "0")
        self.assertEqual(tab.modelo_dias.rowCount(), 0)

        rutinas.cargar()
        ejercicios.cargar()
        comidas.cargar()
        tab.boton_actualizar.click()

        self.assertEqual(tab.valor_rutinas.text(), "10")
        self.assertEqual(tab.valor_series.text(), "26")
        self.assertEqual(tab.modelo_dias.rowCount(), 7)
        self.assertEqual(tab.modelo_ejercicios.rowCount(), 28)

    def test_tab_sin_datos(self) -> None:
        csv_service = CsvService()
        tab = EstadisticasTab(
            EstadisticaService(),
            RutinaService(csv_service, RUTINAS_PATH),
            EjercicioService(csv_service, CATALOGO_PATH),
            NutricionService(csv_service, NUTRICION_PATH),
        )
        self.addCleanup(tab.close)
        self.addCleanup(tab.deleteLater)

        self.assertEqual(tab.valor_rutinas.text(), "0")
        self.assertEqual(tab.valor_series.text(), "0")
        self.assertEqual(tab.valor_catalogo.text(), "0")
        self.assertEqual(tab.valor_nutricion.text(), "0")
        self.assertEqual(
            tab.detalle_catalogo.text(),
            "Sin ejercicios en las rutinas",
        )
        self.assertEqual(
            tab.detalle_nutricion.text(),
            "0 alimentos únicos · 0 sugerencias",
        )
        self.assertEqual(tab.modelo_dias.rowCount(), 0)
        self.assertEqual(tab.modelo_ejercicios.rowCount(), 0)


if __name__ == "__main__":
    unittest.main()
