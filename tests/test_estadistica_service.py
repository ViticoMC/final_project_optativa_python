import unittest

from app.config import CATALOGO_PATH, NUTRICION_PATH, RUTINAS_PATH
from services.csv_service import CsvService
from services.ejercicio_service import EjercicioService
from services.estadistica_service import EstadisticaService
from services.nutricion_service import NutricionService
from services.rutina_service import RutinaService


class EstadisticaServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        csv_service = CsvService()
        self.rutinas = RutinaService(csv_service, RUTINAS_PATH)
        self.rutinas.cargar()
        self.ejercicios = EjercicioService(csv_service, CATALOGO_PATH)
        self.ejercicios.cargar()
        self.comidas = NutricionService(csv_service, NUTRICION_PATH)
        self.comidas.cargar()
        self.servicio = EstadisticaService()

    def calcular(self):
        return self.servicio.calcular(
            self.rutinas.todas(),
            self.ejercicios.todos(),
            self.comidas.todos(),
        )

    def test_resumen_general(self) -> None:
        estadisticas = self.calcular()

        self.assertEqual(estadisticas.total_rutinas, 60)
        self.assertEqual(estadisticas.total_series, 196)
        self.assertAlmostEqual(estadisticas.promedio_series, 3.2667, places=4)
        self.assertEqual(estadisticas.dias_entrenamiento, 7)
        self.assertEqual(estadisticas.dias_descanso, 1)
        self.assertEqual(estadisticas.total_ejercicios, 100)
        self.assertEqual(estadisticas.total_comidas, 42)
        self.assertEqual(estadisticas.alimentos_unicos, 93)
        self.assertEqual(estadisticas.sugerencias, 132)
        self.assertEqual(estadisticas.total_ejercicios_rutinas, 100)

    def test_cobertura_de_ejercicios(self) -> None:
        estadisticas = self.calcular()

        self.assertEqual(estadisticas.cobertura.total, 100)
        self.assertEqual(len(estadisticas.cobertura.encontrados), 100)
        self.assertEqual(len(estadisticas.cobertura.faltantes), 0)
        self.assertAlmostEqual(
            estadisticas.cobertura.porcentaje,
            100.0,
            places=3,
        )
        self.assertEqual(
            sum(
                1
                for ejercicio in estadisticas.ejercicios_rutinas
                if ejercicio.en_catalogo
            ),
            len(estadisticas.cobertura.encontrados),
        )

    def test_distribucion_por_dia(self) -> None:
        filas = self.calcular().rutinas_por_dia

        self.assertEqual(
            [fila.categoria for fila in filas],
            [
                "Lunes",
                "Martes",
                "Miércoles",
                "Jueves",
                "Viernes",
                "Sábado",
                "Domingo",
            ],
        )
        self.assertEqual(
            [fila.valor for fila in filas],
            [10, 9, 9, 8, 9, 9, 6],
        )
        self.assertAlmostEqual(filas[0].porcentaje, 16.6667, places=4)
        self.assertAlmostEqual(sum(fila.porcentaje for fila in filas), 100.0)

    def test_rutinas_por_grupo_y_nivel(self) -> None:
        estadisticas = self.calcular()

        self.assertEqual(len(estadisticas.rutinas_por_grupo), 14)
        self.assertEqual(
            sum(fila.valor for fila in estadisticas.rutinas_por_grupo),
            60,
        )
        self.assertEqual(
            {
                fila.categoria: fila.valor
                for fila in estadisticas.rutinas_por_nivel
            },
            {"Principiante": 22, "Intermedio": 27, "Avanzado": 11},
        )
        self.assertEqual(
            estadisticas.rutinas_por_nivel[0].categoria,
            "Intermedio",
        )

    def test_series_por_grupo(self) -> None:
        filas = self.calcular().series_por_grupo

        valores = {fila.categoria: fila.valor for fila in filas}
        self.assertEqual(sum(valores.values()), 196)
        self.assertEqual(valores["Movilidad"], 13)
        self.assertNotIn("Recuperación", valores)
        self.assertTrue(all(fila.valor > 0 for fila in filas))

    def test_catalogo_y_nutricion_por_categoria(self) -> None:
        estadisticas = self.calcular()

        self.assertEqual(
            sum(fila.valor for fila in estadisticas.catalogo_por_grupo),
            100,
        )
        self.assertIn(
            "Core",
            {fila.categoria for fila in estadisticas.catalogo_por_grupo},
        )
        self.assertEqual(len(estadisticas.comidas_por_objetivo), 25)
        self.assertEqual(
            sum(fila.valor for fila in estadisticas.comidas_por_objetivo),
            42,
        )

    def test_ejercicios_mas_mencionados(self) -> None:
        filas = self.calcular().ejercicios_rutinas

        self.assertEqual(len(filas), 100)
        self.assertEqual(filas[0].nombre, "Curl femoral")
        self.assertEqual(filas[0].menciones, 9)
        self.assertTrue(filas[0].en_catalogo)
        self.assertEqual(
            sum(fila.menciones for fila in filas),
            323,
        )

    def test_sin_datos(self) -> None:
        estadisticas = self.servicio.calcular([], [], [])

        self.assertEqual(estadisticas.total_rutinas, 0)
        self.assertEqual(estadisticas.total_series, 0)
        self.assertEqual(estadisticas.promedio_series, 0.0)
        self.assertEqual(estadisticas.dias_entrenamiento, 0)
        self.assertEqual(estadisticas.dias_descanso, 0)
        self.assertEqual(estadisticas.total_ejercicios, 0)
        self.assertEqual(estadisticas.total_comidas, 0)
        self.assertEqual(estadisticas.alimentos_unicos, 0)
        self.assertEqual(estadisticas.sugerencias, 0)
        self.assertEqual(estadisticas.cobertura.total, 0)
        self.assertEqual(estadisticas.rutinas_por_dia, ())
        self.assertEqual(estadisticas.rutinas_por_grupo, ())
        self.assertEqual(estadisticas.ejercicios_rutinas, ())


if __name__ == "__main__":
    unittest.main()
