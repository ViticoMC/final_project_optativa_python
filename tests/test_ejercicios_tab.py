import unittest

from PyQt5.QtWidgets import QComboBox

from app.config import CATALOGO_PATH, RUTINAS_PATH
from app.utils import normalizar_texto
from services.csv_service import CsvService
from services.ejercicio_service import EjercicioService
from services.rutina_service import RutinaService
from tests.qt_test_case import QtTestCase
from ui.widgets.ejercicios_tab import EjerciciosTab


class EjerciciosTabTests(QtTestCase):
    def setUp(self) -> None:
        csv_service = CsvService()
        self.ejercicios = EjercicioService(csv_service, CATALOGO_PATH)
        self.ejercicios.cargar()
        self.rutinas = RutinaService(csv_service, RUTINAS_PATH)
        self.rutinas.cargar()

        self.tab = EjerciciosTab(self.ejercicios, self.rutinas)
        self.addCleanup(self.tab.close)
        self.addCleanup(self.tab.deleteLater)

    def seleccionar(self, combo: QComboBox, valor: str) -> None:
        indice = combo.findData(valor)
        self.assertGreaterEqual(indice, 0, f"No se encontró el valor {valor!r}")
        combo.setCurrentIndex(indice)

    def test_combos_poblados(self) -> None:
        self.assertEqual(
            self.tab.combo_grupo.count(),
            len(self.ejercicios.grupos()) + 1,
        )
        self.assertEqual(
            self.tab.combo_nivel.count(),
            len(self.ejercicios.niveles()) + 1,
        )
        self.assertEqual(
            self.tab.combo_patron.count(),
            len(self.ejercicios.patrones()) + 1,
        )
        self.assertEqual(
            self.tab.combo_equipo.count(),
            len(self.ejercicios.equipamientos()) + 1,
        )

        placeholders = (
            (self.tab.combo_grupo, "Todos los grupos"),
            (self.tab.combo_nivel, "Todos los niveles"),
            (self.tab.combo_patron, "Todos los patrones"),
            (self.tab.combo_equipo, "Todos los equipos"),
        )
        for combo, placeholder in placeholders:
            self.assertEqual(combo.currentData(), "")
            self.assertEqual(combo.itemText(0), placeholder)

    def test_niveles_reales_sin_duplicar_placeholder(self) -> None:
        textos = [
            self.tab.combo_nivel.itemText(indice)
            for indice in range(self.tab.combo_nivel.count())
        ]

        self.assertEqual(textos[0], "Todos los niveles")
        self.assertNotIn("Todos los niveles", textos[1:])
        self.assertEqual(len(textos), len(set(textos)))
        for nivel in self.ejercicios.niveles():
            self.assertEqual(textos.count(nivel), 1)

    def test_catalogo_inicial_y_detalle(self) -> None:
        self.assertEqual(self.tab.modelo.rowCount(), 100)
        self.assertEqual(self.tab.detalle_titulo.text(), "Press de banca")
        self.assertIn("Pecho", self.tab.detalle_info.text())
        self.assertIn("técnica correcta", self.tab.detalle_nota.text())

    def test_cobertura_mostrada(self) -> None:
        texto = self.tab.etiqueta_cobertura.text()

        self.assertIn("100/100", texto)
        self.assertIn("100.0", texto)
        self.assertIn(
            "Todos los ejercicios de las rutinas están en el catálogo",
            self.tab.etiqueta_cobertura.toolTip(),
        )

    def test_filtro_por_grupo(self) -> None:
        self.seleccionar(self.tab.combo_grupo, "Pecho")

        self.assertEqual(self.tab.modelo.rowCount(), 10)
        self.assertEqual(
            self.tab.etiqueta_estado.text(),
            "Mostrando 10 de 100 ejercicios.",
        )
        self.assertEqual(self.tab.detalle_titulo.text(), "Press de banca")

    def test_filtro_por_nivel_real(self) -> None:
        nivel = self.ejercicios.niveles()[0]
        self.seleccionar(self.tab.combo_nivel, nivel)

        ids = [
            self.tab.modelo.registro_en(fila).id_ejercicio
            for fila in range(self.tab.modelo.rowCount())
        ]
        esperados = [
            ejercicio.id_ejercicio
            for ejercicio in self.ejercicios.todos()
            if normalizar_texto(ejercicio.nivel_sugerido)
            == normalizar_texto(nivel)
        ]
        self.assertEqual(ids, esperados)

    def test_filtro_por_patron_y_equipo(self) -> None:
        self.seleccionar(self.tab.combo_patron, "Empuje horizontal")
        self.assertEqual(self.tab.modelo.rowCount(), 5)
        self.assertEqual(self.tab.detalle_titulo.text(), "Press de banca")

        self.seleccionar(self.tab.combo_patron, "")
        self.seleccionar(self.tab.combo_equipo, "Polea")
        ids = {
            self.tab.modelo.registro_en(fila).id_ejercicio
            for fila in range(self.tab.modelo.rowCount())
        }
        self.assertEqual(len(ids), 9)
        self.assertIn("E003", ids)
        self.assertIn("E009", ids)
        self.assertTrue(
            all(
                self.tab.modelo.registro_en(fila).equipamiento == "Polea"
                for fila in range(self.tab.modelo.rowCount())
            )
        )

    def test_busqueda_y_ficha(self) -> None:
        self.tab.busqueda.setText("lumbar")

        self.assertEqual(self.tab.modelo.rowCount(), 6)
        self.assertEqual(self.tab.detalle_titulo.text(), "Dead bug")
        self.assertIn("lumbar", self.tab.detalle_nota.text())

    def test_busqueda_sin_resultados(self) -> None:
        self.tab.busqueda.setText("no existe")

        self.assertEqual(self.tab.modelo.rowCount(), 0)
        self.assertEqual(
            self.tab.etiqueta_estado.text(),
            "Sin coincidencias. 0 de 100 ejercicios.",
        )
        self.assertEqual(
            self.tab.detalle_titulo.text(),
            "Sin ejercicio seleccionado",
        )

    def test_limpiar_filtros(self) -> None:
        self.seleccionar(self.tab.combo_grupo, "Pecho")
        self.tab.busqueda.setText("press")

        self.tab.boton_limpiar.click()

        self.assertEqual(self.tab.modelo.rowCount(), 100)
        self.assertEqual(self.tab.combo_grupo.currentIndex(), 0)
        self.assertEqual(self.tab.busqueda.text(), "")
        self.assertEqual(
            self.tab.etiqueta_estado.text(),
            "100 ejercicios cargados.",
        )

    def test_atajos_de_busqueda_y_filtros(self) -> None:
        self.assertEqual(self.tab.atajo_buscar.key().toString(), "Ctrl+F")
        self.assertEqual(self.tab.atajo_limpiar.key().toString(), "Ctrl+L")

    def test_exportar_emite_senal_y_respeta_filtros(self) -> None:
        self.seleccionar(self.tab.combo_grupo, "Pecho")
        recibido: list[bool] = []
        self.tab.exportar_solicitado.connect(lambda: recibido.append(True))

        self.tab.boton_exportar.click()

        self.assertEqual(recibido, [True])
        visibles = self.tab.registros_visibles()
        self.assertEqual(len(visibles), 10)
        self.assertEqual(
            {ejercicio.grupo_muscular for ejercicio in visibles},
            {"Pecho"},
        )

    def test_tab_sin_catalogo(self) -> None:
        servicio_vacio = EjercicioService(CsvService(), CATALOGO_PATH)
        tab = EjerciciosTab(servicio_vacio, self.rutinas)
        self.addCleanup(tab.close)
        self.addCleanup(tab.deleteLater)

        self.assertEqual(tab.modelo.rowCount(), 0)
        self.assertEqual(tab.combo_grupo.count(), 1)
        self.assertIn("catálogo no cargado", tab.etiqueta_cobertura.text())
        self.assertIn("No hay ejercicios cargados", tab.etiqueta_estado.text())


if __name__ == "__main__":
    unittest.main()
