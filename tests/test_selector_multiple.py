import unittest

from PyQt5.QtCore import Qt

from tests.qt_test_case import QtTestCase
from ui.widgets.selector_multiple import SelectorMultiple


class SelectorMultipleTests(QtTestCase):
    def setUp(self) -> None:
        self.selector = SelectorMultiple()
        self.addCleanup(self.selector.deleteLater)
        self.selector.set_disponibles(
            (
                ("Press de banca", "Press de banca · Pecho"),
                ("Plancha", "Plancha · Core"),
                ("Sentadilla goblet", "Sentadilla goblet · Piernas"),
            )
        )

    def test_agregar_quitar_y_orden(self) -> None:
        self.selector.agregar_valor("Plancha")
        self.selector.agregar_valor("Press de banca")

        self.assertEqual(
            self.selector.seleccionados(),
            ("Plancha", "Press de banca"),
        )
        self.assertEqual(
            self.selector.disponibles(),
            ("Sentadilla goblet",),
        )

        self.selector.lista_seleccionados.setCurrentRow(1)
        self.selector.boton_subir.click()
        self.assertEqual(
            self.selector.seleccionados(),
            ("Press de banca", "Plancha"),
        )

        self.selector.lista_seleccionados.setCurrentRow(0)
        self.selector.boton_quitar.click()
        self.assertEqual(self.selector.seleccionados(), ("Plancha",))
        self.assertIn("Press de banca", self.selector.disponibles())

    def test_no_duplica_y_muestra_etiquetas(self) -> None:
        self.selector.set_seleccionados(("Plancha", "Plancha"))

        self.assertEqual(self.selector.seleccionados(), ("Plancha",))
        item = self.selector.lista_seleccionados.item(0)
        self.assertEqual(item.text(), "Plancha · Core")
        self.assertEqual(item.data(Qt.UserRole), "Plancha")

    def test_filtrar_disponibles_conserva_seleccion(self) -> None:
        self.selector.agregar_valor("Plancha")
        self.selector.set_disponibles((("Press de banca", "Press de banca"),))

        self.assertEqual(self.selector.seleccionados(), ("Plancha",))
        self.assertEqual(
            self.selector.disponibles(),
            ("Press de banca",),
        )
        item = self.selector.lista_seleccionados.item(0)
        self.assertEqual(item.text(), "Plancha")

    def test_mover_fuera_de_rango_no_cambia(self) -> None:
        self.selector.set_seleccionados(("Plancha",))
        self.selector.lista_seleccionados.setCurrentRow(0)
        self.selector.boton_subir.click()
        self.selector.boton_bajar.click()

        self.assertEqual(self.selector.seleccionados(), ("Plancha",))

    def test_limpiar_seleccion(self) -> None:
        self.selector.set_seleccionados(("Plancha", "Press de banca"))
        self.selector.limpiar_seleccion()

        self.assertEqual(self.selector.seleccionados(), ())
        self.assertEqual(len(self.selector.disponibles()), 3)


if __name__ == "__main__":
    unittest.main()
