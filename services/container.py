from dataclasses import dataclass

from services.ejercicio_service import EjercicioService
from services.estadistica_service import EstadisticaService
from services.nutricion_service import NutricionService
from services.rutina_service import RutinaService


@dataclass(frozen=True)
class AppServices:
    rutinas: RutinaService
    ejercicios: EjercicioService
    nutricion: NutricionService
    estadisticas: EstadisticaService
