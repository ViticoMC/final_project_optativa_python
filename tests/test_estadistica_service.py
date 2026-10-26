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

        self.assertEqual(estadisticas.total_rutinas, 10)
        self.assertEqual(estadisticas.total_series, 26)
        self.assertAlmostEqual(estadisticas.promedio_series, 2.6)
        self.assertEqual(estadisticas.dias_entrenamiento, 6)
        self.assertEqual(estadisticas.dias_descanso, 1)
        self.assertEqual(estadisticas.total_ejercicios, 13)
        self.assertEqual(estadisticas.total_comidas, 7)
        self.assertEqual(estadisticas.alimentos_unicos, 16)
        self.assertEqual(estadisticas.sugerencias, 17)
        self.assertEqual(estadisticas.total_ejercicios_rutinas, 28)

    def test_cobertura_de_ejercicios(self) -> None:
        estadisticas = self.calcular()

        self.assertEqual(estadisticas.cobertura.total, 28)
        self.assertEqual(len(estadisticas.cobertura.encontrados), 12)
        self.assertEqual(len(estadisticas.cobertura.faltantes), 16)
        self.assertAlmostEqual(
            estadisticas.cobertura.porcentaje,
            42.857,
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
        self.assertEqual([fila.valor for fila in filas], [2, 2, 2, 1, 1, 1, 1])
        self.assertAlmostEqual(filas[0].porcentaje, 20.0)
        self.assertAlmostEqual(sum(fila.porcentaje for fila in filas), 100.0)

    def test_rutinas_por_grupo_y_nivel(self) -> None:
        estadisticas = self.calcular()

        self.assertEqual(len(estadisticas.rutinas_por_grupo), 10)
        self.assertEqual(
            sum(fila.valor for fila in estadisticas.rutinas_por_grupo),
            10,
        )
        self.assertEqual(
            {
                fila.categoria: fila.valor
                for fila in estadisticas.rutinas_por_nivel
            },
            {"Principiante": 7, "Intermedio": 3},
        )
        self.assertEqual(
            estadisticas.rutinas_por_nivel[0].categoria,
            "Principiante",
        )

    def test_series_por_grupo(self) -> None:
        filas = self.calcular().series_por_grupo

        valores = {fila.categoria: fila.valor for fila in filas}
        self.assertEqual(sum(valores.values()), 26)
        self.assertEqual(valores["Movilidad"], 2)
        self.assertNotIn("Recuperación", valores)
        self.assertTrue(all(fila.valor > 0 for fila in filas))

    def test_catalogo_y_nutricion_por_categoria(self) -> None:
        estadisticas = self.calcular()

        self.assertEqual(
            sum(fila.valor for fila in estadisticas.catalogo_por_grupo),
            13,
        )
        self.assertIn(
            "Core",
            {fila.categoria for fila in estadisticas.catalogo_por_grupo},
        )
        self.assertEqual(len(estadisticas.comidas_por_objetivo), 7)
        self.assertEqual(
            sum(fila.valor for fila in estadisticas.comidas_por_objetivo),
            7,
        )

    def test_ejercicios_mas_mencionados(self) -> None:
        filas = self.calcular().ejercicios_rutinas

        self.assertEqual(len(filas), 28)
        self.assertEqual(filas[0].nombre, "Plancha")
        self.assertEqual(filas[0].menciones, 2)
        self.assertTrue(filas[0].en_catalogo)
        self.assertEqual(
            sum(fila.menciones for fila in filas),
            29,
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
