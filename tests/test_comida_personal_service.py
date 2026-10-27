import tempfile
import unittest
from pathlib import Path

from app.config import NUTRICION_PATH, OBSERVACION_COMIDA_PERSONAL
from app.exceptions import DataValidationError
from services.comida_personal_service import ComidaPersonalService
from services.csv_service import CsvService
from services.nutricion_service import NutricionService


class ComidaPersonalServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.csv_service = CsvService()
        self.nutricion = NutricionService(self.csv_service, NUTRICION_PATH)
        self.nutricion.cargar()
        self.temporal = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporal.cleanup)
        self.ruta = Path(self.temporal.name) / "mis_comidas.csv"
        self.servicio = ComidaPersonalService(
            self.csv_service,
            self.nutricion,
            self.ruta,
        )

    def crear(self, alimentos=("Avena con leche o bebida vegetal", "huevo")):
        return self.servicio.crear(
            self.servicio.tipos_comida()[0],
            self.servicio.horarios()[0],
            alimentos,
            self.servicio.objetivos()[0],
        )

    def test_archivo_inexistente_inicia_vacio(self) -> None:
        total = self.servicio.cargar()

        self.assertEqual(total, 0)
        self.assertEqual(self.servicio.todas(), ())
        self.assertEqual(self.servicio.ruta, self.ruta)
        self.assertFalse(self.ruta.exists())

    def test_crear_guarda_y_recarga(self) -> None:
        comida = self.crear()

        self.assertEqual(comida.id_plan, "MC001")
        self.assertEqual(
            comida.observaciones,
            OBSERVACION_COMIDA_PERSONAL,
        )
        self.assertTrue(self.ruta.exists())
        self.assertEqual(self.servicio.total(), 1)

        recargado = ComidaPersonalService(
            self.csv_service,
            self.nutricion,
            self.ruta,
        )
        self.assertEqual(recargado.cargar(), 1)
        self.assertEqual(recargado.por_id("MC001"), comida)

    def test_crear_varios_genera_ids_secuenciales(self) -> None:
        self.assertEqual(self.crear().id_plan, "MC001")
        self.assertEqual(self.crear().id_plan, "MC002")

    def test_deduplica_alimentos(self) -> None:
        comida = self.crear(("huevo", "HUEVO", "plátano"))

        self.assertEqual(comida.alimentos, ("huevo", "plátano"))

    def test_actualizar_y_eliminar(self) -> None:
        comida = self.crear()
        actualizada = self.servicio.actualizar(
            comida.id_plan,
            self.servicio.tipos_comida()[1],
            self.servicio.horarios()[1],
            ("plátano", "Yogur natural"),
            self.servicio.objetivos()[1],
        )

        self.assertEqual(actualizada.id_plan, "MC001")
        self.assertEqual(actualizada.alimentos, ("plátano", "Yogur natural"))
        self.assertTrue(self.servicio.eliminar("MC001"))
        self.assertFalse(self.servicio.eliminar("MC001"))
        self.assertEqual(self.servicio.total(), 0)
        self.assertEqual(self.csv_service.leer(self.ruta), [])

    def test_rechaza_datos_fuera_del_plan(self) -> None:
        base = {
            "comida": self.servicio.tipos_comida()[0],
            "horario": self.servicio.horarios()[0],
            "alimentos": ("huevo",),
            "objetivo": self.servicio.objetivos()[0],
        }
        casos = (
            ("sin alimentos", {**base, "alimentos": ()}),
            (
                "alimento desconocido",
                {**base, "alimentos": ("Comida inventada",)},
            ),
            ("comida inválida", {**base, "comida": "Brunch"}),
            ("horario inválido", {**base, "horario": "23:59"}),
            ("objetivo inválido", {**base, "objetivo": "Ganar músculo"}),
        )
        for nombre, datos in casos:
            with self.subTest(caso=nombre):
                with self.assertRaises(DataValidationError):
                    self.servicio.crear(
                        datos["comida"],
                        datos["horario"],
                        datos["alimentos"],
                        datos["objetivo"],
                    )
        self.assertEqual(self.servicio.total(), 0)

    def test_no_permite_actualizar_inexistente(self) -> None:
        with self.assertRaises(DataValidationError):
            self.servicio.actualizar(
                "MC999",
                self.servicio.tipos_comida()[0],
                self.servicio.horarios()[0],
                ("huevo",),
                self.servicio.objetivos()[0],
            )

    def test_alimentos_por_comida(self) -> None:
        desayuno = self.servicio.alimentos_por_comida("Desayuno")
        todas = self.servicio.alimentos_por_comida()

        self.assertIn("Avena con leche o bebida vegetal", desayuno)
        self.assertNotIn("Arroz o vianda", desayuno)
        self.assertEqual(
            len(todas),
            len(self.nutricion.alimentos_unicos()),
        )

    def test_listas_estandar(self) -> None:
        self.assertEqual(
            self.servicio.tipos_comida(),
            self.nutricion.comidas(),
        )
        self.assertEqual(self.servicio.horarios(), self.nutricion.horarios())
        self.assertEqual(self.servicio.objetivos(), self.nutricion.objetivos())
        self.assertEqual(
            self.servicio.comidas_estandar(),
            self.nutricion.todos(),
        )


if __name__ == "__main__":
    unittest.main()
