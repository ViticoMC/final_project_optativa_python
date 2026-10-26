from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from app.config import DIAS
from app.models import Cobertura, Comida, Ejercicio, Rutina
from app.utils import normalizar_texto
from services.ejercicio_service import calcular_cobertura


@dataclass(frozen=True, slots=True)
class Distribucion:
    categoria: str
    valor: int
    porcentaje: float = 0.0


@dataclass(frozen=True, slots=True)
class EjercicioRutina:
    nombre: str
    menciones: int
    en_catalogo: bool


@dataclass(frozen=True, slots=True)
class Estadisticas:
    total_rutinas: int
    total_series: int
    promedio_series: float
    dias_entrenamiento: int
    dias_descanso: int
    total_ejercicios: int
    total_comidas: int
    alimentos_unicos: int
    sugerencias: int
    cobertura: Cobertura
    rutinas_por_dia: tuple[Distribucion, ...]
    rutinas_por_grupo: tuple[Distribucion, ...]
    rutinas_por_nivel: tuple[Distribucion, ...]
    series_por_grupo: tuple[Distribucion, ...]
    catalogo_por_grupo: tuple[Distribucion, ...]
    comidas_por_objetivo: tuple[Distribucion, ...]
    ejercicios_rutinas: tuple[EjercicioRutina, ...]

    @property
    def total_ejercicios_rutinas(self) -> int:
        return len(self.ejercicios_rutinas)


class EstadisticaService:
    def calcular(
        self,
        rutinas: Iterable[Rutina],
        ejercicios: Iterable[Ejercicio],
        comidas: Iterable[Comida],
    ) -> Estadisticas:
        rutinas = tuple(rutinas)
        ejercicios = tuple(ejercicios)
        comidas = tuple(comidas)

        total_rutinas = len(rutinas)
        total_series = sum(rutina.series for rutina in rutinas)
        promedio = total_series / total_rutinas if total_rutinas else 0.0
        activas = [rutina for rutina in rutinas if not rutina.es_descanso]
        descansos = [rutina for rutina in rutinas if rutina.es_descanso]
        series_grupo: Counter[str] = Counter()
        for rutina in rutinas:
            series_grupo[rutina.grupo_muscular] += rutina.series

        return Estadisticas(
            total_rutinas=total_rutinas,
            total_series=total_series,
            promedio_series=promedio,
            dias_entrenamiento=len({rutina.dia for rutina in activas}),
            dias_descanso=len({rutina.dia for rutina in descansos}),
            total_ejercicios=len(ejercicios),
            total_comidas=len(comidas),
            alimentos_unicos=self._contar_alimentos(comidas),
            sugerencias=sum(len(comida.alimentos) for comida in comidas),
            cobertura=calcular_cobertura(rutinas, ejercicios),
            rutinas_por_dia=self._por_dia(rutinas),
            rutinas_por_grupo=self._por_cantidad(
                Counter(rutina.grupo_muscular for rutina in rutinas),
                total_rutinas,
            ),
            rutinas_por_nivel=self._por_cantidad(
                Counter(rutina.nivel for rutina in rutinas),
                total_rutinas,
            ),
            series_por_grupo=self._por_cantidad(
                series_grupo,
                total_series,
                omitir_ceros=True,
            ),
            catalogo_por_grupo=self._por_cantidad(
                Counter(
                    ejercicio.grupo_muscular for ejercicio in ejercicios
                ),
                len(ejercicios),
            ),
            comidas_por_objetivo=self._por_cantidad(
                Counter(comida.objetivo_general for comida in comidas),
                len(comidas),
            ),
            ejercicios_rutinas=self._ejercicios_rutinas(
                rutinas,
                ejercicios,
            ),
        )

    @staticmethod
    def _por_dia(rutinas: tuple[Rutina, ...]) -> tuple[Distribucion, ...]:
        conteo = Counter(rutina.dia for rutina in rutinas)
        conocidos = [dia for dia in DIAS if dia in conteo]
        otros = sorted(set(conteo) - set(DIAS), key=normalizar_texto)
        total = len(rutinas)
        return tuple(
            Distribucion(dia, conteo[dia], EstadisticaService._pct(conteo[dia], total))
            for dia in conocidos + otros
        )

    @staticmethod
    def _por_cantidad(
        conteo: Mapping[str, int],
        total: int,
        omitir_ceros: bool = False,
    ) -> tuple[Distribucion, ...]:
        elementos = [
            (categoria, valor)
            for categoria, valor in conteo.items()
            if not omitir_ceros or valor > 0
        ]
        elementos.sort(key=lambda item: (-item[1], normalizar_texto(item[0])))
        return tuple(
            Distribucion(categoria, valor, EstadisticaService._pct(valor, total))
            for categoria, valor in elementos
        )

    @staticmethod
    def _pct(valor: int, total: int) -> float:
        return valor / total * 100.0 if total else 0.0

    @staticmethod
    def _contar_alimentos(comidas: tuple[Comida, ...]) -> int:
        alimentos = {
            normalizar_texto(alimento)
            for comida in comidas
            for alimento in comida.alimentos
            if normalizar_texto(alimento)
        }
        return len(alimentos)

    @staticmethod
    def _ejercicios_rutinas(
        rutinas: tuple[Rutina, ...],
        ejercicios: tuple[Ejercicio, ...],
    ) -> tuple[EjercicioRutina, ...]:
        menciones: Counter[str] = Counter()
        nombres: dict[str, str] = {}
        for rutina in rutinas:
            for nombre in rutina.ejercicios:
                clave = normalizar_texto(nombre)
                if not clave:
                    continue
                menciones[clave] += 1
                nombres.setdefault(clave, nombre.strip())

        catalogo = {
            normalizar_texto(ejercicio.nombre) for ejercicio in ejercicios
        }
        filas = [
            EjercicioRutina(
                nombre=nombres[clave],
                menciones=cantidad,
                en_catalogo=clave in catalogo,
            )
            for clave, cantidad in menciones.items()
        ]
        filas.sort(key=lambda fila: (-fila.menciones, normalizar_texto(fila.nombre)))
        return tuple(filas)
