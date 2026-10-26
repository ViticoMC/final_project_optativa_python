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
from app.exceptions import CsvFormatError, ExportError
from services.csv_service import CsvService

FIXTURES = Path(__file__).resolve().parent / "fixtures"


class CsvServiceLecturaTests(unittest.TestCase):
    def setUp(self) -> None:
        self.servicio = CsvService()
        self.temporal = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporal.cleanup)
        self.directorio = Path(self.temporal.name)

    def crear_csv(
        self,
        nombre: str,
        contenido: str,
        encoding: str = "utf-8-sig",
    ) -> Path:
        ruta = self.directorio / nombre
        with ruta.open("w", encoding=encoding, newline="") as fh:
            fh.write(contenido)
        return ruta

    def test_lee_los_tres_archivos_reales(self) -> None:
        rutinas = self.servicio.leer(
            RUTINAS_PATH, COLUMNAS_RUTINA, columna_id="id_rutina"
        )
        ejercicios = self.servicio.leer(
            CATALOGO_PATH,
            COLUMNAS_EJERCICIO,
            columna_id="id_ejercicio",
        )
        comidas = self.servicio.leer(
            NUTRICION_PATH, COLUMNAS_NUTRICION, columna_id="id_plan"
        )

        self.assertEqual(len(rutinas), 10)
        self.assertEqual(len(ejercicios), 13)
        self.assertEqual(len(comidas), 7)
        self.assertEqual(rutinas[0]["id_rutina"], "R001")
        self.assertEqual(len(rutinas[0]), 9)

    def test_conserva_comas_internas_y_bom(self) -> None:
        comidas = self.servicio.leer(
            NUTRICION_PATH, COLUMNAS_NUTRICION, columna_id="id_plan"
        )
        d003 = next(fila for fila in comidas if fila["id_plan"] == "D003")

        self.assertEqual(
            d003["alimentos_sugeridos"],
            "Arroz o vianda; pollo, pescado, huevo o legumbres; verduras",
        )
        self.assertEqual(
            d003["observaciones"],
            "Elegir alimentos disponibles y variar fuentes",
        )

    def test_lee_utf8_sin_bom(self) -> None:
        ruta = self.crear_csv(
            "sin_bom.csv",
            "id_rutina,dia,series\nR001,Lunes,3\n",
            encoding="utf-8",
        )
        registros = self.servicio.leer(
            ruta, ("id_rutina", "dia", "series"), columna_id="id_rutina"
        )

        self.assertEqual(registros, [{"id_rutina": "R001", "dia": "Lunes", "series": "3"}])

    def test_ignora_lineas_vacias(self) -> None:
        ruta = self.crear_csv(
            "con_vacias.csv",
            "id_rutina,dia,series\nR001,Lunes,3\n\n   \nR002,Martes,3\n",
        )
        registros = self.servicio.leer(ruta, ("id_rutina", "dia", "series"))

        self.assertEqual(len(registros), 2)
        self.assertEqual([fila["id_rutina"] for fila in registros], ["R001", "R002"])

    def test_archivo_inexistente(self) -> None:
        ruta = self.directorio / "no_existe.csv"

        with self.assertRaises(CsvFormatError) as contexto:
            self.servicio.leer(ruta)

        self.assertIn("no existe", str(contexto.exception).lower())
        self.assertEqual(contexto.exception.ruta, ruta)

    def test_archivo_vacio(self) -> None:
        ruta = self.directorio / "vacio.csv"
        ruta.write_text("", encoding="utf-8-sig")

        with self.assertRaises(CsvFormatError) as contexto:
            self.servicio.leer(ruta)

        self.assertIn("vacío", str(contexto.exception).lower())

    def test_columna_requerida_faltante(self) -> None:
        with self.assertRaises(CsvFormatError) as contexto:
            self.servicio.leer(
                FIXTURES / "csv_sin_columna.csv",
                ("id_rutina", "dia", "series"),
            )

        self.assertIn("series", str(contexto.exception))
        self.assertIn("Faltan columnas", str(contexto.exception))

    def test_encabezado_duplicado(self) -> None:
        ruta = self.crear_csv(
            "duplicado.csv",
            "id_rutina,dia,dia\nR001,Lunes,3\n",
        )

        with self.assertRaises(CsvFormatError) as contexto:
            self.servicio.leer(ruta)

        self.assertIn("duplicadas", str(contexto.exception).lower())

    def test_fila_con_columnas_incorrectas(self) -> None:
        with self.assertRaises(CsvFormatError) as contexto:
            self.servicio.leer(
                FIXTURES / "csv_fila_mal_formada.csv",
                ("id_rutina", "dia", "series"),
            )

        self.assertEqual(contexto.exception.linea, 3)
        self.assertIn("2 columnas", str(contexto.exception))

    def test_identificador_duplicado(self) -> None:
        with self.assertRaises(CsvFormatError) as contexto:
            self.servicio.leer(
                FIXTURES / "csv_id_duplicado.csv",
                ("id_rutina", "dia", "series"),
                columna_id="id_rutina",
            )

        self.assertEqual(contexto.exception.linea, 3)
        self.assertIn("duplicado", str(contexto.exception).lower())
        self.assertIn("R001", str(contexto.exception))

    def test_identificador_vacio(self) -> None:
        ruta = self.crear_csv(
            "id_vacio.csv",
            "id_rutina,dia,series\n,Lunes,3\n",
        )

        with self.assertRaises(CsvFormatError) as contexto:
            self.servicio.leer(
                ruta, ("id_rutina", "dia", "series"), columna_id="id_rutina"
            )

        self.assertEqual(contexto.exception.linea, 2)
        self.assertIn("no puede estar vacío", str(contexto.exception))

    def test_columna_id_inexistente(self) -> None:
        ruta = self.crear_csv(
            "sin_id.csv",
            "dia,series\nLunes,3\n",
        )

        with self.assertRaises(CsvFormatError) as contexto:
            self.servicio.leer(ruta, columna_id="id_rutina")

        self.assertIn("id_rutina", str(contexto.exception))

    def test_delimitador_invalido(self) -> None:
        with self.assertRaises(ValueError):
            CsvService(delimiter=";;")


class CsvServiceEscrituraTests(unittest.TestCase):
    def setUp(self) -> None:
        self.servicio = CsvService()
        self.temporal = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporal.cleanup)
        self.directorio = Path(self.temporal.name)

    def test_escribir_y_releer(self) -> None:
        ruta = self.directorio / "salida.csv"
        filas = [
            {
                "id": "1",
                "nombre": "Press, banca",
                "etiquetas": ["fuerza", "pecho"],
            }
        ]

        resultado = self.servicio.escribir(
            ruta, ("id", "nombre", "etiquetas"), filas
        )

        self.assertEqual(resultado, ruta)
        self.assertTrue(ruta.read_bytes().startswith(b"\xef\xbb\xbf"))
        self.assertIn(b'"Press, banca"', ruta.read_bytes())

        registros = self.servicio.leer(
            ruta, ("id", "nombre", "etiquetas"), columna_id="id"
        )
        self.assertEqual(registros[0]["nombre"], "Press, banca")
        self.assertEqual(registros[0]["etiquetas"], "fuerza; pecho")

    def test_escribir_crea_directorios(self) -> None:
        ruta = self.directorio / "nuevo" / "sub" / "salida.csv"

        self.servicio.escribir(ruta, ("id",), [{"id": "1"}])

        self.assertTrue(ruta.is_file())

    def test_escribir_reemplaza_archivo_existente(self) -> None:
        ruta = self.directorio / "salida.csv"
        ruta.write_text("contenido anterior", encoding="utf-8-sig")

        self.servicio.escribir(ruta, ("id",), [{"id": "nuevo"}])

        self.assertNotIn("contenido anterior", ruta.read_text(encoding="utf-8-sig"))
        self.assertIn("nuevo", ruta.read_text(encoding="utf-8-sig"))

    def test_escribir_solo_encabezado(self) -> None:
        ruta = self.directorio / "vacio.csv"

        self.servicio.escribir(ruta, ("id", "nombre"), [])

        self.assertEqual(self.servicio.leer(ruta, ("id", "nombre")), [])

    def test_columnas_duplicadas(self) -> None:
        with self.assertRaises(ExportError):
            self.servicio.escribir(
                self.directorio / "salida.csv", ("id", "id"), [{"id": "1"}]
            )

    def test_columnas_vacias(self) -> None:
        with self.assertRaises(ExportError):
            self.servicio.escribir(
                self.directorio / "salida.csv", (), []
            )

    def test_fila_sin_columna(self) -> None:
        with self.assertRaises(ExportError) as contexto:
            self.servicio.escribir(
                self.directorio / "salida.csv",
                ("id", "nombre"),
                [{"id": "1"}],
            )

        self.assertIn("nombre", str(contexto.exception))

    def test_fila_no_es_diccionario(self) -> None:
        with self.assertRaises(ExportError):
            self.servicio.escribir(
                self.directorio / "salida.csv", ("id",), ["no-es-dict"]
            )


if __name__ == "__main__":
    unittest.main()
