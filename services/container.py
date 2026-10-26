from dataclasses import dataclass

from services.ejercicio_service import EjercicioService
from services.rutina_service import RutinaService


@dataclass(frozen=True)
class AppServices:
    rutinas: RutinaService
    ejercicios: EjercicioService
