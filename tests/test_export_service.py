import tempfile
import unittest
from pathlib import Path

from app.config import (
    CATALOGO_PATH,
    COLUMNAS_EJERCICIO,
    COLUMNAS_NUTRICION,
    COLUMNAS_RUTINA,
    NUTRICION_PATH,
    RUTINAS_PATH,
)
from app.exceptions import ExportError
from services.csv_service import CsvService
from services.ejercicio_service import EjercicioService
from services.estadistica_service import EstadisticaService
from services.export_service import COLUMNAS_ESTADISTICA, ExportService
from services.nutricion_service import NutricionService
from services.rutina_service import RutinaService


class ExportServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.csv_service = CsvService()
        self.servicio = ExportService(self.csv_service)
        self.temporal = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporal.cleanup)
        self.directorio = Path(self.temporal.name)

        self.rutinas = RutinaService(CsvService(), RUTINAS_PATH)
        self.rutinas.cargar()
        self.ejercicios = EjercicioService(CsvService(), CATALOGO_PATH)
        self.ejercicios.cargar()
        self.comidas = NutricionService(CsvService(), NUTRICION_PATH)
        self.comidas.cargar()

    def test_exportar_rutinas_conserva_datos(self) -> None:
        seleccion = self.rutinas.todas()[:2]
        destino = self.servicio.exportar_rutinas(
            self.directorio / "rutinas.csv",
            seleccion,
        )

        self.assertTrue(destino.exists())
        leidas = self.csv_service.leer(
            destino,
            COLUMNAS_RUTINA,
            columna_id="id_rutina",
        )
        self.assertEqual(leidas, [rutina.to_row() for rutina in seleccion])

    def test_exportar_ejercicios_y_comidas(self) -> None:
        destino_ejercicios = self.servicio.exportar_ejercicios(
            self.directorio / "ejercicios.csv",
            self.ejercicios.todos(),
        )
        destino_comidas = self.servicio.exportar_comidas(
            self.directorio / "comidas.csv",
            self.comidas.todos(),
        )

        ejercicios = self.csv_service.leer(
            destino_ejercicios,
            COLUMNAS_EJERCICIO,
            columna_id="id_ejercicio",
        )
        comidas = self.csv_service.leer(
            destino_comidas,
            COLUMNAS_NUTRICION,
            columna_id="id_plan",
        )

        self.assertEqual(len(ejercicios), 13)
        self.assertEqual(len(comidas), 7)
        self.assertEqual(ejercicios[0]["nombre"], "Press de banca")
        self.assertEqual(comidas[0]["comida"], "Desayuno")

    def test_agrega_extension_csv(self) -> None:
        destino = self.servicio.exportar_rutinas(
            self.directorio / "rutinas_sin_extension",
            (),
        )

        self.assertEqual(destino.name, "rutinas_sin_extension.csv")
        self.assertTrue(destino.exists())

    def test_reemplaza_extension_distinta(self) -> None:
        destino = self.servicio.exportar_rutinas(
            self.directorio / "rutinas.txt",
            (),
        )

        self.assertEqual(destino.name, "rutinas.csv")
        self.assertTrue(destino.exists())

    def test_exporta_solo_encabezado_sin_registros(self) -> None:
        destino = self.servicio.exportar_rutinas(
            self.directorio / "vacias.csv",
            (),
        )

        leidas = self.csv_service.leer(
            destino,
            COLUMNAS_RUTINA,
            columna_id="id_rutina",
        )
        self.assertEqual(leidas, [])

    def test_ruta_vacia_falla(self) -> None:
        with self.assertRaises(ExportError):
            self.servicio.exportar_rutinas("   ", ())

    def test_exportar_estadisticas_genera_secciones(self) -> None:
        estadisticas = EstadisticaService().calcular(
            self.rutinas.todas(),
            self.ejercicios.todos(),
            self.comidas.todos(),
        )
        destino = self.servicio.exportar_estadisticas(
            self.directorio / "estadisticas.csv",
            estadisticas,
        )

        filas = self.csv_service.leer(destino, COLUMNAS_ESTADISTICA)
        secciones = {fila["seccion"] for fila in filas}
        resumen = next(
            fila
            for fila in filas
            if fila["seccion"] == "Resumen" and fila["categoria"] == "Rutinas"
        )
        cobertura = next(
            fila
            for fila in filas
            if fila["seccion"] == "Cobertura"
            and fila["categoria"] == "Encontrados"
        )
        plancha = next(
            fila for fila in filas if fila["categoria"] == "Plancha"
        )

        self.assertIn("Rutinas por día", secciones)
        self.assertIn("Ejercicios en rutinas", secciones)
        self.assertEqual(resumen["valor"], "10")
        self.assertEqual(cobertura["valor"], "12")
        self.assertEqual(cobertura["porcentaje"], "42.9")
        self.assertEqual(cobertura["detalle"], "de 28")
        self.assertEqual(plancha["valor"], "2")
        self.assertEqual(plancha["detalle"], "En catálogo")

    def test_estadisticas_sin_datos(self) -> None:
        estadisticas = EstadisticaService().calcular((), (), ())
        destino = self.servicio.exportar_estadisticas(
            self.directorio / "estadisticas_vacias.csv",
            estadisticas,
        )

        filas = self.csv_service.leer(destino, COLUMNAS_ESTADISTICA)
        self.assertEqual(len(filas), 9)
        self.assertNotIn("Cobertura", {fila["seccion"] for fila in filas})
        self.assertNotIn(
            "Ejercicios en rutinas",
            {fila["seccion"] for fila in filas},
        )


if __name__ == "__main__":
    unittest.main()
