from collections.abc import Iterable
from pathlib import Path

from app.config import COLUMNAS_PLANTILLA, PLANTILLAS_PATH
from app.exceptions import DataValidationError
from app.models import PlantillaRutina, Rutina
from app.utils import a_entero, normalizar_texto
from services.csv_service import CsvService
from services.ejercicio_service import EjercicioService
from services.rutina_service import RutinaService


class PlantillaService:
    def __init__(
        self,
        csv_service: CsvService,
        catalogo: EjercicioService,
        rutinas: RutinaService,
        ruta: str | Path = PLANTILLAS_PATH,
    ) -> None:
        self.csv_service = csv_service
        self.catalogo = catalogo
        self.rutinas = rutinas
        self.ruta = Path(ruta)
        self._plantillas: tuple[PlantillaRutina, ...] = ()

    def cargar(self, ruta: str | Path | None = None) -> int:
        archivo = Path(ruta) if ruta is not None else self.ruta
        if not archivo.is_file():
            self.ruta = archivo
            self._plantillas = ()
            return 0

        filas = self.csv_service.leer(
            archivo,
            COLUMNAS_PLANTILLA,
            columna_id="id_plantilla",
        )
        plantillas: list[PlantillaRutina] = []
        for fila in filas:
            try:
                plantillas.append(PlantillaRutina.from_row(fila))
            except DataValidationError as exc:
                raise DataValidationError(
                    f"Error en '{archivo.name}': {exc}"
                ) from exc

        self.ruta = archivo
        self._plantillas = tuple(plantillas)
        return len(self._plantillas)

    def todas(self) -> tuple[PlantillaRutina, ...]:
        return self._plantillas

    def total(self) -> int:
        return len(self._plantillas)

    def por_id(self, id_plantilla: str) -> PlantillaRutina | None:
        for plantilla in self._plantillas:
            if plantilla.id_plantilla == id_plantilla:
                return plantilla
        return None

    def crear(
        self,
        ejercicios: Iterable[str],
        series: object,
        repeticiones: str,
        nivel: str,
        descanso: str,
    ) -> PlantillaRutina:
        seleccion = self._validar_ejercicios(ejercicios)
        plantilla = self._construir(
            self._siguiente_id(),
            seleccion,
            series,
            repeticiones,
            nivel,
            descanso,
        )
        self._guardar(self._plantillas + (plantilla,))
        return plantilla

    def actualizar(
        self,
        id_plantilla: str,
        ejercicios: Iterable[str],
        series: object,
        repeticiones: str,
        nivel: str,
        descanso: str,
    ) -> PlantillaRutina:
        indice = next(
            (
                posicion
                for posicion, plantilla in enumerate(self._plantillas)
                if plantilla.id_plantilla == id_plantilla
            ),
            None,
        )
        if indice is None:
            raise DataValidationError(
                f"No existe la plantilla {id_plantilla!r}."
            )

        seleccion = self._validar_ejercicios(ejercicios)
        plantilla = self._construir(
            id_plantilla,
            seleccion,
            series,
            repeticiones,
            nivel,
            descanso,
        )
        actualizadas = list(self._plantillas)
        actualizadas[indice] = plantilla
        self._guardar(tuple(actualizadas))
        return plantilla

    def eliminar(self, id_plantilla: str) -> bool:
        restantes = tuple(
            plantilla
            for plantilla in self._plantillas
            if plantilla.id_plantilla != id_plantilla
        )
        if len(restantes) == len(self._plantillas):
            return False
        self._guardar(restantes)
        return True

    def grupo_para(self, ejercicios: Iterable[str]) -> str:
        grupos: list[str] = []
        vistos: set[str] = set()
        for nombre in ejercicios:
            ejercicio = self.catalogo.por_nombre(nombre)
            if ejercicio is None:
                raise DataValidationError(
                    f"El ejercicio {nombre!r} no pertenece al catálogo estándar."
                )
            clave = normalizar_texto(ejercicio.grupo_muscular)
            if clave not in vistos:
                vistos.add(clave)
                grupos.append(ejercicio.grupo_muscular)
        if not grupos:
            raise DataValidationError(
                "La plantilla debe incluir al menos un ejercicio."
            )
        if len(grupos) == 1:
            return grupos[0]
        return "Cuerpo completo"

    def rutinas_estandar(self) -> tuple[Rutina, ...]:
        return self.rutinas.todas()

    def ejercicios_disponibles(
        self,
        grupo: str = "",
        patron: str = "",
        equipo: str = "",
        nivel: str = "",
        texto: str = "",
    ):
        return self.catalogo.filtrar(
            grupo=grupo,
            patron=patron,
            equipo=equipo,
            nivel=nivel,
            texto=texto,
        )

    def grupos_ejercicio(self) -> list[str]:
        return self.catalogo.grupos()

    def patrones_ejercicio(self) -> list[str]:
        return self.catalogo.patrones()

    def equipamientos_ejercicio(self) -> list[str]:
        return self.catalogo.equipamientos()

    def niveles_ejercicio(self) -> list[str]:
        return self.catalogo.niveles()

    def opciones_series(self) -> list[int]:
        return sorted(
            {
                rutina.series
                for rutina in self.rutinas.todas()
                if rutina.series > 0
            }
        )

    def opciones_repeticiones(self) -> list[str]:
        return self._opciones_rutina("repeticiones")

    def opciones_descanso(self) -> list[str]:
        return self._opciones_rutina("descanso")

    def opciones_nivel(self) -> list[str]:
        return self.rutinas.niveles()

    def _opciones_rutina(self, campo: str) -> list[str]:
        valores: dict[str, str] = {}
        for rutina in self.rutinas.todas():
            texto = getattr(rutina, campo).strip()
            clave = normalizar_texto(texto)
            if clave and clave != "no aplica" and clave not in valores:
                valores[clave] = texto
        return sorted(valores.values(), key=normalizar_texto)

    def _construir(
        self,
        id_plantilla: str,
        ejercicios: tuple[str, ...],
        series: object,
        repeticiones: str,
        nivel: str,
        descanso: str,
    ) -> PlantillaRutina:
        series_numero = a_entero(series, defecto=-1)
        opciones_series = self.opciones_series()
        if series_numero not in opciones_series:
            raise DataValidationError(
                "El valor de series debe elegirse entre las opciones estándar."
            )

        return PlantillaRutina(
            id_plantilla=id_plantilla,
            grupo_muscular=self.grupo_para(ejercicios),
            ejercicios=ejercicios,
            series=series_numero,
            repeticiones=self._resolver_opcion(
                repeticiones,
                self.opciones_repeticiones(),
                "repeticiones",
            ),
            nivel=self._resolver_opcion(
                nivel,
                self.opciones_nivel(),
                "nivel",
            ),
            descanso=self._resolver_opcion(
                descanso,
                self.opciones_descanso(),
                "descanso",
            ),
        )

    def _validar_ejercicios(
        self,
        ejercicios: Iterable[str],
    ) -> tuple[str, ...]:
        seleccionados: list[str] = []
        vistos: set[str] = set()
        for nombre in ejercicios:
            texto = str(nombre).strip()
            if not texto:
                continue
            ejercicio = self.catalogo.por_nombre(texto)
            if ejercicio is None:
                raise DataValidationError(
                    f"El ejercicio {texto!r} no pertenece al catálogo estándar."
                )
            clave = normalizar_texto(ejercicio.nombre)
            if clave in vistos:
                continue
            vistos.add(clave)
            seleccionados.append(ejercicio.nombre)

        if not seleccionados:
            raise DataValidationError(
                "La plantilla debe incluir al menos un ejercicio."
            )
        return tuple(seleccionados)

    @staticmethod
    def _resolver_opcion(
        valor: str,
        opciones: Iterable[str],
        campo: str,
    ) -> str:
        buscado = normalizar_texto(valor)
        for opcion in opciones:
            if normalizar_texto(opcion) == buscado:
                return opcion
        raise DataValidationError(
            f"El valor de {campo} debe elegirse entre las opciones estándar."
        )

    def _siguiente_id(self) -> str:
        maximo = 0
        for plantilla in self._plantillas:
            identificador = plantilla.id_plantilla
            if not identificador.startswith("MR"):
                continue
            sufijo = identificador[2:]
            if sufijo.isdigit():
                maximo = max(maximo, int(sufijo))
        return f"MR{maximo + 1:03d}"

    def _guardar(self, plantillas: tuple[PlantillaRutina, ...]) -> None:
        self.csv_service.escribir(
            self.ruta,
            COLUMNAS_PLANTILLA,
            [plantilla.to_row() for plantilla in plantillas],
        )
        self._plantillas = plantillas
