import tempfile
import unittest
from pathlib import Path

from app.config import COLUMNAS_RUTINA, DIAS, NIVELES, RUTINAS_PATH
from app.exceptions import CsvFormatError, DataValidationError
from app.utils import normalizar_texto
from services.csv_service import CsvService
from services.rutina_service import RutinaService


def fila_rutina(
    id_rutina: str,
    dia: str = "Lunes",
    series: str = "3",
    nivel: str = "Intermedio",
    grupo_muscular: str = "Pecho",
) -> dict[str, str]:
    return {
        "id_rutina": id_rutina,
        "dia": dia,
        "horario": "07:00-08:00",
        "grupo_muscular": grupo_muscular,
        "ejercicios": "Press de banca; Plancha",
        "series": series,
        "repeticiones_o_duracion": "8-12",
        "nivel": nivel,
        "descanso": "60-90 s",
    }


class RutinaServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.csv_service = CsvService()
        self.servicio = RutinaService(self.csv_service, RUTINAS_PATH)
        self.temporal = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporal.cleanup)
        self.directorio = Path(self.temporal.name)

    def crear_csv(self, nombre: str, filas: list[dict[str, str]]) -> Path:
        ruta = self.directorio / nombre
        self.csv_service.escribir(ruta, COLUMNAS_RUTINA, filas)
        return ruta

    def test_carga_datos_reales(self) -> None:
        total = self.servicio.cargar()

        self.assertEqual(total, 10)
        self.assertEqual(self.servicio.total(), 10)
        self.assertEqual(len(self.servicio.todas()), 10)
        self.assertEqual(self.servicio.ruta, RUTINAS_PATH)
        self.assertEqual(self.servicio.por_id("R001").grupo_muscular, "Pecho")
        self.assertIsNone(self.servicio.por_id("R999"))

    def test_dias_niveles_y_grupos(self) -> None:
        self.servicio.cargar()

        self.assertEqual(self.servicio.dias(), list(DIAS))
        self.assertEqual(self.servicio.niveles(), list(NIVELES))
        self.assertIn("Bíceps", self.servicio.grupos())
        self.assertIn("Movilidad", self.servicio.grupos())
        self.assertEqual(
            self.servicio.grupos(),
            sorted(self.servicio.grupos(), key=normalizar_texto),
        )

    def test_valores_unicos(self) -> None:
        self.servicio.cargar()

        valores = self.servicio.valores_unicos("nivel")

        self.assertEqual(valores, sorted(set(valores), key=normalizar_texto))
        self.assertEqual(set(valores), {"Principiante", "Intermedio", "Todos"})

    def test_campo_desconocido(self) -> None:
        with self.assertRaises(ValueError):
            self.servicio.valores_unicos("no_existe")

    def test_filtros_simples(self) -> None:
        self.servicio.cargar()

        casos = (
            ({}, 10),
            ({"dia": "Lunes"}, 2),
            ({"grupo": "Pecho"}, 1),
            ({"nivel": "Intermedio"}, 3),
            ({"nivel": "Principiante"}, 5),
            ({"nivel": "Todos"}, 2),
            ({"horario": "18:00-19:00"}, 2),
            ({"dia": "Domingo"}, 1),
        )
        for filtros, esperado in casos:
            with self.subTest(filtros=filtros):
                self.assertEqual(
                    len(self.servicio.filtrar(**filtros)),
                    esperado,
                )

    def test_busqueda_texto(self) -> None:
        self.servicio.cargar()

        casos = (
            ("triceps", ["R002"]),
            ("press banca", ["R001"]),
            ("lunes pecho", ["R001"]),
            ("R010", ["R010"]),
            ("plancha", ["R007", "R008"]),
            ("no existe", []),
        )
        for texto, esperados in casos:
            with self.subTest(texto=texto):
                encontrados = [
                    rutina.id_rutina
                    for rutina in self.servicio.filtrar(texto=texto)
                ]
                self.assertEqual(encontrados, esperados)

    def test_filtros_combinados(self) -> None:
        self.servicio.cargar()

        self.assertEqual(
            [r.id_rutina for r in self.servicio.filtrar(dia="Lunes", nivel="Intermedio")],
            ["R001"],
        )
        self.assertEqual(
            [r.id_rutina for r in self.servicio.filtrar(dia="Lunes", nivel="Principiante")],
            ["R002"],
        )
        self.assertEqual(
            [r.id_rutina for r in self.servicio.filtrar(dia="Martes", grupo="Espalda")],
            ["R003"],
        )
        self.assertEqual(
            [r.id_rutina for r in self.servicio.filtrar(dia="Lunes", horario="18:00-19:00")],
            ["R002"],
        )
        self.assertEqual(
            self.servicio.filtrar(dia="Lunes", grupo="Piernas"),
            (),
        )

    def test_filtros_sin_tildes_ni_mayusculas(self) -> None:
        self.servicio.cargar()

        self.assertEqual(
            [r.id_rutina for r in self.servicio.filtrar(dia="miercoles")],
            ["R005", "R010"],
        )
        self.assertEqual(
            [r.id_rutina for r in self.servicio.filtrar(grupo="BICEPS")],
            ["R004"],
        )

    def test_horarios_ordenados(self) -> None:
        self.servicio.cargar()

        self.assertEqual(
            self.servicio.horarios(),
            [
                "07:00-08:00",
                "09:00-09:45",
                "18:00-18:30",
                "18:00-19:00",
                "Descanso",
            ],
        )

    def test_cargar_otro_archivo(self) -> None:
        ruta = self.crear_csv(
            "personalizado.csv",
            [
                fila_rutina("R100", dia="Sábado", nivel="Principiante"),
                fila_rutina("R101", dia="Domingo", nivel="Todos"),
            ],
        )

        total = self.servicio.cargar(ruta)

        self.assertEqual(total, 2)
        self.assertEqual(self.servicio.ruta, ruta)
        self.assertEqual(self.servicio.por_id("R100").dia, "Sábado")
        self.assertEqual(self.servicio.dias(), ["Sábado", "Domingo"])
        self.assertEqual(self.servicio.niveles(), ["Principiante", "Todos"])

    def test_error_semantico_conserva_datos_anteriores(self) -> None:
        self.servicio.cargar()
        ruta = self.crear_csv(
            "series_invalidas.csv",
            [fila_rutina("R200", series="tres")],
        )

        with self.assertRaises(DataValidationError) as contexto:
            self.servicio.cargar(ruta)

        self.assertIn("series", str(contexto.exception))
        self.assertIn("series_invalidas.csv", str(contexto.exception))
        self.assertEqual(self.servicio.total(), 10)
        self.assertEqual(self.servicio.ruta, RUTINAS_PATH)

    def test_archivo_inexistente_conserva_datos_anteriores(self) -> None:
        self.servicio.cargar()

        with self.assertRaises(CsvFormatError):
            self.servicio.cargar(self.directorio / "no_existe.csv")

        self.assertEqual(self.servicio.total(), 10)
        self.assertEqual(self.servicio.ruta, RUTINAS_PATH)

    def test_cargar_archivo_sin_registros(self) -> None:
        ruta = self.crear_csv("vacio.csv", [])

        total = self.servicio.cargar(ruta)

        self.assertEqual(total, 0)
        self.assertEqual(self.servicio.todas(), ())
        self.assertEqual(self.servicio.dias(), [])


if __name__ == "__main__":
    unittest.main()
