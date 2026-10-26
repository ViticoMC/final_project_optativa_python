import unittest

from app.utils import a_entero, clave_horario, contiene, dividir_lista, normalizar_texto


class UtilsTests(unittest.TestCase):
    def test_normalizar_texto(self) -> None:
        self.assertEqual(normalizar_texto("  Tríceps  "), "triceps")
        self.assertEqual(normalizar_texto("Miércoles"), "miercoles")
        self.assertEqual(normalizar_texto(None), "")

    def test_contiene_ignora_tildes_y_mayusculas(self) -> None:
        self.assertTrue(contiene("Press de banca", "BANCA"))
        self.assertTrue(contiene("Tríceps", "triceps"))
        self.assertTrue(contiene("Cuerpo completo", ""))
        self.assertFalse(contiene("Espalda", "piernas"))

    def test_dividir_lista(self) -> None:
        self.assertEqual(
            dividir_lista("Press de banca; Plancha ; ; Sentadilla"),
            ("Press de banca", "Plancha", "Sentadilla"),
        )
        self.assertEqual(dividir_lista(None), ())
        self.assertEqual(dividir_lista(""), ())

    def test_a_entero(self) -> None:
        self.assertEqual(a_entero(" 3 "), 3)
        self.assertEqual(a_entero(4), 4)
        self.assertEqual(a_entero(5.0), 5)
        self.assertEqual(a_entero("tres", defecto=7), 7)
        self.assertEqual(a_entero(None, defecto=-1), -1)
        self.assertEqual(a_entero(""), 0)

    def test_clave_horario(self) -> None:
        horarios = [
            "Después de entrenar",
            "10:30",
            "07:30",
            "Durante el día",
        ]

        ordenados = sorted(horarios, key=clave_horario)

        self.assertEqual(ordenados[:2], ["07:30", "10:30"])
        self.assertEqual(set(ordenados[2:]), {"Después de entrenar", "Durante el día"})

    def test_clave_horario_con_rango(self) -> None:
        self.assertEqual(clave_horario("07:00-08:00"), (0, "07:00"))
        self.assertEqual(clave_horario("7:05"), (0, "07:05"))
        self.assertEqual(clave_horario("Descanso"), (1, "descanso"))


if __name__ == "__main__":
    unittest.main()
