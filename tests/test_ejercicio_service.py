import tempfile
import unittest
from pathlib import Path

from app.config import CATALOGO_PATH, COLUMNAS_EJERCICIO, RUTINAS_PATH
from app.exceptions import DataValidationError
from app.utils import normalizar_texto
from services.csv_service import CsvService
from services.ejercicio_service import EjercicioService
from services.rutina_service import RutinaService


def fila_ejercicio(
    id_ejercicio: str,
    nombre: str = "Press de banca",
    grupo: str = "Pecho",
    nivel: str = "Principiante",
) -> dict[str, str]:
    return {
        "id_ejercicio": id_ejercicio,
        "nombre": nombre,
        "grupo_muscular": grupo,
        "patron_movimiento": "Empuje horizontal",
        "equipamiento": "Barra o mancuernas",
        "nivel_sugerido": nivel,
        "nota_tecnica": "Usar carga controlable",
    }


class EjercicioServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.csv_service = CsvService()
        self.servicio = EjercicioService(self.csv_service, CATALOGO_PATH)
        self.temporal = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporal.cleanup)
        self.directorio = Path(self.temporal.name)

    def crear_csv(self, nombre: str, filas: list[dict[str, str]]) -> Path:
        ruta = self.directorio / nombre
        self.csv_service.escribir(ruta, COLUMNAS_EJERCICIO, filas)
        return ruta

    def test_carga_datos_reales(self) -> None:
        total = self.servicio.cargar()

        self.assertEqual(total, 13)
        self.assertEqual(self.servicio.total(), 13)
        self.assertEqual(len(self.servicio.todos()), 13)
        self.assertEqual(self.servicio.ruta, CATALOGO_PATH)
        self.assertEqual(
            self.servicio.por_id("E001").nombre,
            "Press de banca",
        )
        self.assertIsNone(self.servicio.por_id("E999"))

    def test_busqueda_por_nombre_sin_tildes(self) -> None:
        self.servicio.cargar()

        self.assertEqual(
            self.servicio.por_nombre("jalon al pecho").id_ejercicio,
            "E003",
        )
        self.assertEqual(
            self.servicio.por_nombre("PRESS DE BANCA").id_ejercicio,
            "E001",
        )
        self.assertIsNone(self.servicio.por_nombre("No existe"))

    def test_grupos_niveles_patrones_y_equipos(self) -> None:
        self.servicio.cargar()

        for valores in (
            self.servicio.grupos(),
            self.servicio.niveles(),
            self.servicio.patrones(),
            self.servicio.equipamientos(),
        ):
            self.assertTrue(valores)
            self.assertEqual(valores, sorted(valores, key=normalizar_texto))
            self.assertEqual(len(valores), len(set(valores)))

        self.assertIn("Core", self.servicio.grupos())
        self.assertIn("Polea", self.servicio.equipamientos())

    def _contar(self, atributo: str, valor: str) -> int:
        return sum(
            1
            for ejercicio in self.servicio.todos()
            if normalizar_texto(getattr(ejercicio, atributo))
            == normalizar_texto(valor)
        )

    def test_filtros_simples(self) -> None:
        self.servicio.cargar()

        casos = (
            ({}, self.servicio.total()),
            ({"grupo": "Pecho"}, self._contar("grupo_muscular", "Pecho")),
            ({"grupo": "Piernas"}, self._contar("grupo_muscular", "Piernas")),
            ({"grupo": "Core"}, self._contar("grupo_muscular", "Core")),
            (
                {"nivel": "Principiante"},
                self._contar("nivel_sugerido", "Principiante"),
            ),
            (
                {"nivel": "Principiante-intermedio"},
                self._contar("nivel_sugerido", "Principiante-intermedio"),
            ),
            (
                {"nivel": "Todos"},
                self._contar("nivel_sugerido", "Todos"),
            ),
            (
                {"patron": "Empuje horizontal"},
                self._contar("patron_movimiento", "Empuje horizontal"),
            ),
            (
                {"equipo": "Polea"},
                self._contar("equipamiento", "Polea"),
            ),
            (
                {"equipo": "Colchoneta"},
                self._contar("equipamiento", "Colchoneta"),
            ),
        )
        for filtros, esperado in casos:
            with self.subTest(filtros=filtros):
                self.assertEqual(
                    len(self.servicio.filtrar(**filtros)),
                    esperado,
                )

    def test_filtros_combinados(self) -> None:
        self.servicio.cargar()

        self.assertEqual(
            [
                e.id_ejercicio
                for e in self.servicio.filtrar(
                    grupo="Pecho",
                    nivel="Principiante-intermedio",
                )
            ],
            ["E001", "E002"],
        )
        self.assertEqual(
            [
                e.id_ejercicio
                for e in self.servicio.filtrar(
                    grupo="Pecho",
                    nivel="Principiante",
                )
            ],
            [],
        )

    def test_busqueda_texto(self) -> None:
        self.servicio.cargar()

        casos = (
            ("empuje", ["E001", "E002", "E007"]),
            ("core", ["E010", "E011"]),
            ("lumbar", ["E011"]),
            ("biceps", ["E008"]),
            ("polea", ["E003", "E009"]),
            ("no existe", []),
        )
        for texto, esperados in casos:
            with self.subTest(texto=texto):
                encontrados = [
                    e.id_ejercicio
                    for e in self.servicio.filtrar(texto=texto)
                ]
                self.assertEqual(encontrados, esperados)

    def test_filtros_sin_tildes_ni_mayusculas(self) -> None:
        self.servicio.cargar()

        self.assertEqual(
            [e.id_ejercicio for e in self.servicio.filtrar(grupo="BICEPS")],
            ["E008"],
        )
        self.assertEqual(
            [
                e.id_ejercicio
                for e in self.servicio.filtrar(patron="extension de codo")
            ],
            ["E009"],
        )

    def test_cobertura_con_rutinas_reales(self) -> None:
        self.servicio.cargar()
        rutinas = RutinaService(self.csv_service, RUTINAS_PATH)
        rutinas.cargar()

        cobertura = self.servicio.cobertura(rutinas.todas())

        self.assertEqual(cobertura.total, 28)
        self.assertEqual(len(cobertura.encontrados), 12)
        self.assertEqual(len(cobertura.faltantes), 16)
        self.assertAlmostEqual(cobertura.porcentaje, 42.857, places=3)
        self.assertIn("Press de banca", cobertura.encontrados)
        self.assertIn("Prensa", cobertura.faltantes)
        self.assertEqual(
            set(cobertura.encontrados) | set(cobertura.faltantes),
            set(cobertura.usados),
        )
        self.assertEqual(
            len(set(cobertura.usados)),
            len(cobertura.usados),
        )

    def test_cobertura_sin_rutinas(self) -> None:
        self.servicio.cargar()

        cobertura = self.servicio.cobertura([])

        self.assertEqual(cobertura.total, 0)
        self.assertEqual(cobertura.faltantes, ())
        self.assertEqual(cobertura.porcentaje, 100.0)

    def test_error_semantico_conserva_datos_anteriores(self) -> None:
        self.servicio.cargar()
        ruta = self.crear_csv(
            "invalido.csv",
            [fila_ejercicio("E200", nombre="", grupo="Pecho")],
        )

        with self.assertRaises(DataValidationError) as contexto:
            self.servicio.cargar(ruta)

        self.assertIn("nombre", str(contexto.exception))
        self.assertEqual(self.servicio.total(), 13)
        self.assertEqual(self.servicio.ruta, CATALOGO_PATH)

    def test_cargar_archivo_sin_registros(self) -> None:
        ruta = self.crear_csv("vacio.csv", [])

        total = self.servicio.cargar(ruta)

        self.assertEqual(total, 0)
        self.assertEqual(self.servicio.todos(), ())
        self.assertEqual(self.servicio.grupos(), [])


if __name__ == "__main__":
    unittest.main()
