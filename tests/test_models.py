import unittest

from app.config import (
    CATALOGO_PATH,
    COLUMNAS_EJERCICIO,
    COLUMNAS_NUTRICION,
    COLUMNAS_RUTINA,
    NUTRICION_PATH,
    RUTINAS_PATH,
)
from app.exceptions import DataValidationError
from app.models import Cobertura, Comida, Ejercicio, Rutina
from services.csv_service import CsvService


def fila_rutina(**cambios: object) -> dict[str, object]:
    fila: dict[str, object] = {
        "id_rutina": "R001",
        "dia": "Lunes",
        "horario": "07:00-08:00",
        "grupo_muscular": "Pecho",
        "ejercicios": "Press de banca; Plancha",
        "series": "3",
        "repeticiones_o_duracion": "8-12",
        "nivel": "Intermedio",
        "descanso": "60-90 s",
    }
    fila.update(cambios)
    return fila


class RutinaTests(unittest.TestCase):
    def test_from_row_y_to_row(self) -> None:
        rutina = Rutina.from_row(fila_rutina())

        self.assertEqual(rutina.id_rutina, "R001")
        self.assertEqual(rutina.series, 3)
        self.assertEqual(rutina.ejercicios, ("Press de banca", "Plancha"))
        self.assertEqual(rutina.num_ejercicios, 2)
        self.assertFalse(rutina.es_descanso)
        self.assertEqual(
            rutina.to_row(),
            {
                "id_rutina": "R001",
                "dia": "Lunes",
                "horario": "07:00-08:00",
                "grupo_muscular": "Pecho",
                "ejercicios": "Press de banca; Plancha",
                "series": "3",
                "repeticiones_o_duracion": "8-12",
                "nivel": "Intermedio",
                "descanso": "60-90 s",
            },
        )

    def test_dia_de_descanso_por_series_cero(self) -> None:
        rutina = Rutina.from_row(
            fila_rutina(
                dia="Domingo",
                horario="Descanso",
                series="0",
                repeticiones="No aplica",
                descanso="No aplica",
            )
        )

        self.assertTrue(rutina.es_descanso)

    def test_dia_de_descanso_por_horario(self) -> None:
        rutina = Rutina.from_row(fila_rutina(horario="Descanso", series="2"))

        self.assertTrue(rutina.es_descanso)

    def test_series_invalidas(self) -> None:
        with self.assertRaises(DataValidationError) as contexto:
            Rutina.from_row(fila_rutina(series="tres"))

        self.assertIn("series", str(contexto.exception))

    def test_series_negativas(self) -> None:
        with self.assertRaises(DataValidationError):
            Rutina.from_row(fila_rutina(series="-1"))

    def test_campo_obligatorio_vacio(self) -> None:
        with self.assertRaises(DataValidationError) as contexto:
            Rutina.from_row(fila_rutina(dia="  "))

        self.assertIn("dia", str(contexto.exception))

    def test_ejercicios_vacios(self) -> None:
        with self.assertRaises(DataValidationError):
            Rutina.from_row(fila_rutina(ejercicios=" ; "))

    def test_todas_las_rutinas_reales(self) -> None:
        servicio = CsvService()
        filas = servicio.leer(
            RUTINAS_PATH, COLUMNAS_RUTINA, columna_id="id_rutina"
        )
        rutinas = [Rutina.from_row(fila) for fila in filas]

        self.assertEqual(len(rutinas), 10)
        self.assertEqual(rutinas[-2].series, 0)
        self.assertTrue(rutinas[-2].es_descanso)
        self.assertEqual(sum(rutina.series for rutina in rutinas), 26)


class EjercicioTests(unittest.TestCase):
    def test_from_row_y_to_row(self) -> None:
        fila = {
            "id_ejercicio": "E001",
            "nombre": "Press de banca",
            "grupo_muscular": "Pecho",
            "patron_movimiento": "Empuje horizontal",
            "equipamiento": "Barra o mancuernas",
            "nivel_sugerido": "Principiante-intermedio",
            "nota_tecnica": "Usar carga controlable",
        }

        ejercicio = Ejercicio.from_row(fila)

        self.assertEqual(ejercicio.nombre, "Press de banca")
        self.assertEqual(ejercicio.to_row(), fila)

    def test_catalogo_real(self) -> None:
        servicio = CsvService()
        filas = servicio.leer(
            CATALOGO_PATH,
            COLUMNAS_EJERCICIO,
            columna_id="id_ejercicio",
        )
        ejercicios = [Ejercicio.from_row(fila) for fila in filas]

        self.assertEqual(len(ejercicios), 13)
        self.assertEqual(ejercicios[0].nombre, "Press de banca")


class ComidaTests(unittest.TestCase):
    def test_from_row_y_to_row(self) -> None:
        fila = {
            "id_plan": "D001",
            "comida": "Desayuno",
            "horario": "07:30",
            "alimentos_sugeridos": "Avena; plátano; huevo",
            "objetivo_general": "Carbohidratos y proteína",
            "observaciones": "Ajustar por hambre",
        }

        comida = Comida.from_row(fila)

        self.assertEqual(comida.alimentos, ("Avena", "plátano", "huevo"))
        self.assertEqual(comida.to_row(), fila)

    def test_plan_real(self) -> None:
        servicio = CsvService()
        filas = servicio.leer(
            NUTRICION_PATH, COLUMNAS_NUTRICION, columna_id="id_plan"
        )
        comidas = [Comida.from_row(fila) for fila in filas]

        self.assertEqual(len(comidas), 7)
        self.assertEqual(comidas[2].comida, "Almuerzo")
        self.assertEqual(len(comidas[2].alimentos), 3)


class CoberturaTests(unittest.TestCase):
    def test_porcentaje(self) -> None:
        cobertura = Cobertura(
            usados=("a", "b", "c"),
            encontrados=("a", "b"),
            faltantes=("c",),
        )

        self.assertEqual(cobertura.total, 3)
        self.assertAlmostEqual(cobertura.porcentaje, 66.6667, places=4)

    def test_sin_uso(self) -> None:
        self.assertEqual(Cobertura().porcentaje, 100.0)


if __name__ == "__main__":
    unittest.main()
