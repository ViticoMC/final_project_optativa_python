from collections.abc import Iterable
from pathlib import Path

from app.config import (
    COLUMNAS_NUTRICION,
    COMIDAS_PERSONALES_PATH,
    OBSERVACION_COMIDA_PERSONAL,
)
from app.exceptions import DataValidationError
from app.models import Comida
from app.utils import normalizar_texto
from services.csv_service import CsvService
from services.nutricion_service import NutricionService


class ComidaPersonalService:
    def __init__(
        self,
        csv_service: CsvService,
        nutricion: NutricionService,
        ruta: str | Path = COMIDAS_PERSONALES_PATH,
    ) -> None:
        self.csv_service = csv_service
        self.nutricion = nutricion
        self.ruta = Path(ruta)
        self._comidas: tuple[Comida, ...] = ()

    def cargar(self, ruta: str | Path | None = None) -> int:
        archivo = Path(ruta) if ruta is not None else self.ruta
        if not archivo.is_file():
            self.ruta = archivo
            self._comidas = ()
            return 0

        filas = self.csv_service.leer(
            archivo,
            COLUMNAS_NUTRICION,
            columna_id="id_plan",
        )
        comidas: list[Comida] = []
        for fila in filas:
            try:
                comidas.append(Comida.from_row(fila))
            except DataValidationError as exc:
                raise DataValidationError(
                    f"Error en '{archivo.name}': {exc}"
                ) from exc

        self.ruta = archivo
        self._comidas = tuple(comidas)
        return len(self._comidas)

    def todas(self) -> tuple[Comida, ...]:
        return self._comidas

    def total(self) -> int:
        return len(self._comidas)

    def por_id(self, id_comida: str) -> Comida | None:
        for comida in self._comidas:
            if comida.id_plan == id_comida:
                return comida
        return None

    def crear(
        self,
        comida: str,
        horario: str,
        alimentos: Iterable[str],
        objetivo: str,
    ) -> Comida:
        seleccion = self._validar_alimentos(alimentos)
        registro = self._construir(
            self._siguiente_id(),
            comida,
            horario,
            seleccion,
            objetivo,
        )
        self._guardar(self._comidas + (registro,))
        return registro

    def actualizar(
        self,
        id_comida: str,
        comida: str,
        horario: str,
        alimentos: Iterable[str],
        objetivo: str,
    ) -> Comida:
        indice = next(
            (
                posicion
                for posicion, registro in enumerate(self._comidas)
                if registro.id_plan == id_comida
            ),
            None,
        )
        if indice is None:
            raise DataValidationError(
                f"No existe la comida personal {id_comida!r}."
            )

        seleccion = self._validar_alimentos(alimentos)
        actualizado = self._construir(
            id_comida,
            comida,
            horario,
            seleccion,
            objetivo,
        )
        actualizadas = list(self._comidas)
        actualizadas[indice] = actualizado
        self._guardar(tuple(actualizadas))
        return actualizado

    def eliminar(self, id_comida: str) -> bool:
        restantes = tuple(
            registro
            for registro in self._comidas
            if registro.id_plan != id_comida
        )
        if len(restantes) == len(self._comidas):
            return False
        self._guardar(restantes)
        return True

    def comidas_estandar(self) -> tuple[Comida, ...]:
        return self.nutricion.todos()

    def tipos_comida(self) -> list[str]:
        return self.nutricion.comidas()

    def horarios(self) -> list[str]:
        return self.nutricion.horarios()

    def objetivos(self) -> list[str]:
        return self.nutricion.objetivos()

    def alimentos_por_comida(self, comida: str = "") -> list[str]:
        if not comida:
            return self.nutricion.alimentos_unicos()

        alimentos: dict[str, str] = {}
        for registro in self.nutricion.todos():
            if normalizar_texto(registro.comida) != normalizar_texto(comida):
                continue
            for alimento in registro.alimentos:
                clave = normalizar_texto(alimento)
                if clave and clave not in alimentos:
                    alimentos[clave] = alimento.strip()
        return sorted(alimentos.values(), key=normalizar_texto)

    def _construir(
        self,
        id_comida: str,
        comida: str,
        horario: str,
        alimentos: tuple[str, ...],
        objetivo: str,
    ) -> Comida:
        return Comida(
            id_plan=id_comida,
            comida=self._resolver_opcion(
                comida,
                self.tipos_comida(),
                "comida",
            ),
            horario=self._resolver_opcion(
                horario,
                self.horarios(),
                "horario",
            ),
            alimentos=alimentos,
            objetivo_general=self._resolver_opcion(
                objetivo,
                self.objetivos(),
                "objetivo",
            ),
            observaciones=OBSERVACION_COMIDA_PERSONAL,
        )

    def _validar_alimentos(
        self,
        alimentos: Iterable[str],
    ) -> tuple[str, ...]:
        disponibles = self.nutricion.alimentos_unicos()
        seleccionados: list[str] = []
        vistos: set[str] = set()
        for alimento in alimentos:
            texto = str(alimento).strip()
            if not texto:
                continue
            canonico = self._resolver_opcion(texto, disponibles, "alimento")
            clave = normalizar_texto(canonico)
            if clave in vistos:
                continue
            vistos.add(clave)
            seleccionados.append(canonico)

        if not seleccionados:
            raise DataValidationError(
                "La comida debe incluir al menos un alimento estándar."
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
        for comida in self._comidas:
            identificador = comida.id_plan
            if not identificador.startswith("MC"):
                continue
            sufijo = identificador[2:]
            if sufijo.isdigit():
                maximo = max(maximo, int(sufijo))
        return f"MC{maximo + 1:03d}"

    def _guardar(self, comidas: tuple[Comida, ...]) -> None:
        self.csv_service.escribir(
            self.ruta,
            COLUMNAS_NUTRICION,
            [comida.to_row() for comida in comidas],
        )
        self._comidas = comidas
