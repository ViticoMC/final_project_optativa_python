import tempfile
import unittest
from pathlib import Path

from app.config import CATALOGO_PATH, RUTINAS_PATH
from app.exceptions import DataValidationError
from services.csv_service import CsvService
from services.ejercicio_service import EjercicioService
from services.plantilla_service import PlantillaService
from services.rutina_service import RutinaService


class PlantillaServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.csv_service = CsvService()
        self.catalogo = EjercicioService(self.csv_service, CATALOGO_PATH)
        self.catalogo.cargar()
        self.rutinas = RutinaService(self.csv_service, RUTINAS_PATH)
        self.rutinas.cargar()

        self.temporal = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporal.cleanup)
        self.ruta = Path(self.temporal.name) / "mis_rutinas.csv"
        self.servicio = PlantillaService(
            self.csv_service,
            self.catalogo,
            self.rutinas,
            self.ruta,
        )

    def crear(self, ejercicios=("Press de banca",)):
        return self.servicio.crear(
            ejercicios,
            self.servicio.opciones_series()[-1],
            self.servicio.opciones_repeticiones()[0],
            self.servicio.opciones_nivel()[0],
            self.servicio.opciones_descanso()[0],
        )

    def test_archivo_inexistente_inicia_vacio(self) -> None:
        total = self.servicio.cargar()

        self.assertEqual(total, 0)
        self.assertEqual(self.servicio.todas(), ())
        self.assertEqual(self.servicio.ruta, self.ruta)
        self.assertFalse(self.ruta.exists())

    def test_crear_guarda_y_recarga(self) -> None:
        plantilla = self.crear(("Press de banca", "Plancha"))

        self.assertEqual(plantilla.id_plantilla, "MR001")
        self.assertEqual(plantilla.grupo_muscular, "Cuerpo completo")
        self.assertTrue(self.ruta.exists())
        self.assertEqual(self.servicio.total(), 1)

        recargado = PlantillaService(
            self.csv_service,
            self.catalogo,
            self.rutinas,
            self.ruta,
        )
        self.assertEqual(recargado.cargar(), 1)
        self.assertEqual(recargado.por_id("MR001"), plantilla)

    def test_grupo_automatico(self) -> None:
        misma_grupo = self.crear(("Sentadilla goblet", "Curl femoral"))
        mixto = self.crear(("Press de banca", "Remo con mancuerna"))

        self.assertEqual(misma_grupo.grupo_muscular, "Piernas")
        self.assertEqual(mixto.grupo_muscular, "Cuerpo completo")

    def test_deduplica_ejercicios_conservando_orden(self) -> None:
        plantilla = self.crear(
            ("Press de banca", "PRESS DE BANCA", "Plancha")
        )

        self.assertEqual(
            plantilla.ejercicios,
            ("Press de banca", "Plancha"),
        )

    def test_crear_varios_genera_ids_secuenciales(self) -> None:
        primera = self.crear()
        segunda = self.crear(("Plancha",))

        self.assertEqual(primera.id_plantilla, "MR001")
        self.assertEqual(segunda.id_plantilla, "MR002")

    def test_actualizar_y_eliminar(self) -> None:
        plantilla = self.crear()
        actualizada = self.servicio.actualizar(
            plantilla.id_plantilla,
            ("Plancha", "Dead bug"),
            self.servicio.opciones_series()[0],
            self.servicio.opciones_repeticiones()[0],
            self.servicio.opciones_nivel()[0],
            self.servicio.opciones_descanso()[0],
        )

        self.assertEqual(actualizada.id_plantilla, "MR001")
        self.assertEqual(actualizada.grupo_muscular, "Core")
        self.assertEqual(actualizada.ejercicios, ("Plancha", "Dead bug"))

        self.assertTrue(self.servicio.eliminar("MR001"))
        self.assertFalse(self.servicio.eliminar("MR001"))
        self.assertEqual(self.servicio.total(), 0)
        self.assertTrue(self.ruta.exists())
        self.assertEqual(self.csv_service.leer(self.ruta), [])

    def test_rechaza_datos_fuera_de_los_csv(self) -> None:
        base = {
            "ejercicios": ("Press de banca",),
            "series": self.servicio.opciones_series()[0],
            "repeticiones": self.servicio.opciones_repeticiones()[0],
            "nivel": self.servicio.opciones_nivel()[0],
            "descanso": self.servicio.opciones_descanso()[0],
        }
        casos = (
            ("sin ejercicios", {**base, "ejercicios": ()}),
            (
                "ejercicio desconocido",
                {**base, "ejercicios": ("Ejercicio inventado",)},
            ),
            ("series inválidas", {**base, "series": 99}),
            (
                "repeticiones inventadas",
                {**base, "repeticiones": "las que quiera"},
            ),
            ("nivel inventado", {**base, "nivel": "Experto"}),
            ("descanso inventado", {**base, "descanso": "lo que sea"}),
        )
        for nombre, datos in casos:
            with self.subTest(caso=nombre):
                with self.assertRaises(DataValidationError):
                    self.servicio.crear(
                        datos["ejercicios"],
                        datos["series"],
                        datos["repeticiones"],
                        datos["nivel"],
                        datos["descanso"],
                    )
        self.assertEqual(self.servicio.total(), 0)

    def test_no_permite_actualizar_inexistente(self) -> None:
        with self.assertRaises(DataValidationError):
            self.servicio.actualizar(
                "MR999",
                ("Plancha",),
                self.servicio.opciones_series()[0],
                self.servicio.opciones_repeticiones()[0],
                self.servicio.opciones_nivel()[0],
                self.servicio.opciones_descanso()[0],
            )

    def test_opciones_derivadas_de_rutinas_estandar(self) -> None:
        series = {rutina.series for rutina in self.rutinas.todas() if rutina.series}
        repeticiones = {
            rutina.repeticiones
            for rutina in self.rutinas.todas()
            if rutina.repeticiones.casefold() != "no aplica"
        }
        descansos = {
            rutina.descanso
            for rutina in self.rutinas.todas()
            if rutina.descanso.casefold() != "no aplica"
        }

        self.assertEqual(set(self.servicio.opciones_series()), series)
        self.assertEqual(
            set(self.servicio.opciones_repeticiones()),
            repeticiones,
        )
        self.assertEqual(
            set(self.servicio.opciones_descanso()),
            descansos,
        )
        self.assertEqual(
            self.servicio.opciones_nivel(),
            self.rutinas.niveles(),
        )

    def test_filtros_de_ejercicios_disponibles(self) -> None:
        ejercicios = self.servicio.ejercicios_disponibles(grupo="Pecho")

        self.assertEqual(len(ejercicios), 10)
        self.assertTrue(
            all(ejercicio.grupo_muscular == "Pecho" for ejercicio in ejercicios)
        )
        nombres = {ejercicio.nombre for ejercicio in ejercicios}
        self.assertIn("Press de banca", nombres)
        self.assertIn("Aperturas", nombres)

    def test_error_de_archivo_conserva_datos(self) -> None:
        self.crear()
        self.csv_service.escribir(
            self.ruta,
            (
                "id_plantilla",
                "grupo_muscular",
                "ejercicios",
                "series",
                "repeticiones_o_duracion",
                "nivel",
                "descanso",
            ),
            [
                {
                    "id_plantilla": "MR999",
                    "grupo_muscular": "Pecho",
                    "ejercicios": "Press de banca",
                    "series": "0",
                    "repeticiones_o_duracion": "8-12",
                    "nivel": "Intermedio",
                    "descanso": "60 s",
                }
            ],
        )

        with self.assertRaises(DataValidationError):
            self.servicio.cargar()

        self.assertEqual(self.servicio.total(), 1)


if __name__ == "__main__":
    unittest.main()
