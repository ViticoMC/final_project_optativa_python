from dataclasses import dataclass

from services.ejercicio_service import EjercicioService
from services.estadistica_service import EstadisticaService
from services.comida_personal_service import ComidaPersonalService
from services.export_service import ExportService
from services.nutricion_service import NutricionService
from services.plantilla_service import PlantillaService
from services.rutina_service import RutinaService


@dataclass(frozen=True)
class AppServices:
    rutinas: RutinaService
    ejercicios: EjercicioService
    nutricion: NutricionService
    estadisticas: EstadisticaService
    exportacion: ExportService
    plantillas: PlantillaService
    comidas_personales: ComidaPersonalService
