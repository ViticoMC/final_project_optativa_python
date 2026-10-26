from collections.abc import Iterable
from pathlib import Path

from app.config import (
    COLUMNAS_EJERCICIO,
    COLUMNAS_NUTRICION,
    COLUMNAS_RUTINA,
)
from app.exceptions import ExportError
from app.models import Comida, Ejercicio, Rutina
from services.csv_service import CsvService
from services.estadistica_service import Estadisticas

COLUMNAS_ESTADISTICA = (
    "seccion",
    "categoria",
    "valor",
    "porcentaje",
    "detalle",
)


class ExportService:
    def __init__(self, csv_service: CsvService) -> None:
        self.csv_service = csv_service

    def exportar_rutinas(
        self,
        ruta: str | Path,
        rutinas: Iterable[Rutina],
    ) -> Path:
        return self._exportar(
            ruta,
            COLUMNAS_RUTINA,
            [rutina.to_row() for rutina in rutinas],
        )

    def exportar_ejercicios(
        self,
        ruta: str | Path,
        ejercicios: Iterable[Ejercicio],
    ) -> Path:
        return self._exportar(
            ruta,
            COLUMNAS_EJERCICIO,
            [ejercicio.to_row() for ejercicio in ejercicios],
        )

    def exportar_comidas(
        self,
        ruta: str | Path,
        comidas: Iterable[Comida],
    ) -> Path:
        return self._exportar(
            ruta,
            COLUMNAS_NUTRICION,
            [comida.to_row() for comida in comidas],
        )

    def exportar_estadisticas(
        self,
        ruta: str | Path,
        estadisticas: Estadisticas,
    ) -> Path:
        return self._exportar(
            ruta,
            COLUMNAS_ESTADISTICA,
            self._filas_estadisticas(estadisticas),
        )

    def _exportar(
        self,
        ruta: str | Path,
        columnas: tuple[str, ...],
        filas: list[dict[str, str]],
    ) -> Path:
        archivo = self._ruta_csv(ruta)
        return self.csv_service.escribir(archivo, columnas, filas)

    @staticmethod
    def _ruta_csv(ruta: str | Path) -> Path:
        texto = str(ruta).strip()
        if not texto:
            raise ExportError("Debe indicar una ruta para exportar.")
        archivo = Path(texto)
        if archivo.suffix.lower() != ".csv":
            archivo = archivo.with_suffix(".csv")
        return archivo

    @staticmethod
    def _filas_estadisticas(
        estadisticas: Estadisticas,
    ) -> list[dict[str, str]]:
        filas: list[dict[str, str]] = []

        def agregar(
            seccion: str,
            categoria: str,
            valor: object,
            porcentaje: str = "",
            detalle: str = "",
        ) -> None:
            filas.append(
                {
                    "seccion": seccion,
                    "categoria": categoria,
                    "valor": str(valor),
                    "porcentaje": porcentaje,
                    "detalle": detalle,
                }
            )

        agregar("Resumen", "Rutinas", estadisticas.total_rutinas)
        agregar("Resumen", "Series programadas", estadisticas.total_series)
        agregar(
            "Resumen",
            "Promedio de series por rutina",
            f"{estadisticas.promedio_series:.1f}",
        )
        agregar(
            "Resumen",
            "Días de entrenamiento",
            estadisticas.dias_entrenamiento,
        )
        agregar("Resumen", "Días de descanso", estadisticas.dias_descanso)
        agregar("Resumen", "Ejercicios en catálogo", estadisticas.total_ejercicios)
        agregar("Resumen", "Comidas", estadisticas.total_comidas)
        agregar("Resumen", "Alimentos únicos", estadisticas.alimentos_unicos)
        agregar(
            "Resumen",
            "Sugerencias nutricionales",
            estadisticas.sugerencias,
        )

        cobertura = estadisticas.cobertura
        if cobertura.total:
            agregar(
                "Cobertura",
                "Encontrados",
                len(cobertura.encontrados),
                f"{cobertura.porcentaje:.1f}",
                f"de {cobertura.total}",
            )
            agregar(
                "Cobertura",
                "Faltantes",
                len(cobertura.faltantes),
                f"{100.0 - cobertura.porcentaje:.1f}",
                f"de {cobertura.total}",
            )

        distribuciones = (
            ("Rutinas por día", estadisticas.rutinas_por_dia),
            ("Rutinas por grupo", estadisticas.rutinas_por_grupo),
            ("Rutinas por nivel", estadisticas.rutinas_por_nivel),
            ("Series por grupo", estadisticas.series_por_grupo),
            ("Catálogo por grupo", estadisticas.catalogo_por_grupo),
            ("Comidas por objetivo", estadisticas.comidas_por_objetivo),
        )
        for seccion, distribucion in distribuciones:
            for fila in distribucion:
                agregar(
                    seccion,
                    fila.categoria,
                    fila.valor,
                    f"{fila.porcentaje:.1f}",
                )

        for ejercicio in estadisticas.ejercicios_rutinas:
            agregar(
                "Ejercicios en rutinas",
                ejercicio.nombre,
                ejercicio.menciones,
                detalle="En catálogo" if ejercicio.en_catalogo else "Faltante",
            )

        return filas
