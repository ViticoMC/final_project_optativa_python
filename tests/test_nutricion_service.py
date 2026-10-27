import tempfile
import unittest
from pathlib import Path

from app.config import COLUMNAS_NUTRICION, NUTRICION_PATH
from app.exceptions import DataValidationError
from app.utils import normalizar_texto
from services.csv_service import CsvService
from services.nutricion_service import NutricionService


def fila_comida(
    id_plan: str,
    comida: str = "Desayuno",
    horario: str = "07:30",
    objetivo: str = "Energía y proteína",
) -> dict[str, str]:
    return {
        "id_plan": id_plan,
        "comida": comida,
        "horario": horario,
        "alimentos_sugeridos": "Avena; plátano; huevo",
        "objetivo_general": objetivo,
        "observaciones": "Ajustar por hambre",
    }


class NutricionServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.csv_service = CsvService()
        self.servicio = NutricionService(self.csv_service, NUTRICION_PATH)
        self.temporal = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporal.cleanup)
        self.directorio = Path(self.temporal.name)

    def crear_csv(self, nombre: str, filas: list[dict[str, str]]) -> Path:
        ruta = self.directorio / nombre
        self.csv_service.escribir(ruta, COLUMNAS_NUTRICION, filas)
        return ruta

    def test_carga_datos_reales(self) -> None:
        total = self.servicio.cargar()

        self.assertEqual(total, 42)
        self.assertEqual(self.servicio.total(), 42)
        self.assertEqual(len(self.servicio.todos()), 42)
        self.assertEqual(self.servicio.ruta, NUTRICION_PATH)
        self.assertEqual(self.servicio.por_id("D001").comida, "Desayuno")
        self.assertIsNone(self.servicio.por_id("D999"))

    def test_comidas_horarios_y_objetivos(self) -> None:
        self.servicio.cargar()

        self.assertEqual(
            self.servicio.comidas(),
            [
                "Almuerzo",
                "Cena",
                "Desayuno",
                "Hidratación",
                "Media mañana",
                "Merienda",
                "Postentreno",
            ],
        )
        self.assertEqual(
            self.servicio.horarios(),
            [
                "07:30",
                "10:30",
                "13:00",
                "16:30",
                "19:30",
                "Después de entrenar",
                "Durante el día",
            ],
        )
        self.assertEqual(len(self.servicio.objetivos()), 25)
        self.assertIn("Hidratación", self.servicio.objetivos())
        self.assertIn("Recuperación", self.servicio.objetivos())

    def test_filtros_simples(self) -> None:
        self.servicio.cargar()

        casos = (
            ({}, 42),
            ({"comida": "Almuerzo"}, 6),
            ({"comida": "Cena"}, 6),
            ({"horario": "07:30"}, 6),
            ({"horario": "Durante el día"}, 6),
            ({"objetivo": "Hidratación"}, 3),
            ({"objetivo": "Recuperación"}, 1),
            ({"objetivo": "Proteína y micronutrientes"}, 2),
        )
        for filtros, esperado in casos:
            with self.subTest(filtros=filtros):
                self.assertEqual(
                    len(self.servicio.filtrar(**filtros)),
                    esperado,
                )

    def test_filtros_combinados(self) -> None:
        self.servicio.cargar()

        resultado = self.servicio.filtrar(
            comida="Cena",
            objetivo="Proteína y micronutrientes",
        )

        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado[0].id_plan, "D005")

        self.assertEqual(
            self.servicio.filtrar(comida="Cena", horario="07:30"),
            (),
        )

    def test_filtros_sin_tildes_ni_mayusculas(self) -> None:
        self.servicio.cargar()

        resultado = self.servicio.filtrar(
            comida="HIDRATACION",
            horario="durante el dia",
        )

        self.assertEqual(len(resultado), 6)
        self.assertEqual(resultado[0].id_plan, "D006")

    def test_busqueda_texto(self) -> None:
        self.servicio.cargar()

        casos = (
            ("avena", ["D001", "D011", "D017", "D039"]),
            ("avena platano", ["D001"]),
            ("hidratacion", ["D006", "D033", "D034", "D035", "D036", "D037"]),
            ("suplementos", ["D007"]),
            ("fruta", ["D002", "D004", "D010", "D014"]),
            ("no existe", []),
        )
        for texto, esperados in casos:
            with self.subTest(texto=texto):
                encontrados = [
                    comida.id_plan
                    for comida in self.servicio.filtrar(texto=texto)
                ]
                self.assertEqual(encontrados, esperados)

    def test_alimentos_unicos_y_sugerencias(self) -> None:
        self.servicio.cargar()

        alimentos = self.servicio.alimentos_unicos()

        self.assertEqual(len(alimentos), 93)
        self.assertEqual(self.servicio.total_sugerencias(), 132)
        self.assertEqual(
            sum(
                1
                for alimento in alimentos
                if normalizar_texto(alimento) == "arroz o vianda"
            ),
            1,
        )
        self.assertTrue(
            any(normalizar_texto(a) == "platano" for a in alimentos)
        )
        self.assertEqual(alimentos, sorted(alimentos, key=normalizar_texto))

    def test_error_semantico_conserva_datos_anteriores(self) -> None:
        self.servicio.cargar()
        ruta = self.crear_csv(
            "invalido.csv",
            [fila_comida("D200", comida="")],
        )

        with self.assertRaises(DataValidationError) as contexto:
            self.servicio.cargar(ruta)

        self.assertIn("comida", str(contexto.exception))
        self.assertEqual(self.servicio.total(), 42)
        self.assertEqual(self.servicio.ruta, NUTRICION_PATH)

    def test_cargar_archivo_sin_registros(self) -> None:
        ruta = self.crear_csv("vacio.csv", [])

        total = self.servicio.cargar(ruta)

        self.assertEqual(total, 0)
        self.assertEqual(self.servicio.todos(), ())
        self.assertEqual(self.servicio.comidas(), [])
        self.assertEqual(self.servicio.alimentos_unicos(), [])
        self.assertEqual(self.servicio.total_sugerencias(), 0)


if __name__ == "__main__":
    unittest.main()
