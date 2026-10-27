from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
PERSONAL_DIR = DATA_DIR / "personal"

RUTINAS_PATH = DATA_DIR / "rutinas_fitness.csv"
CATALOGO_PATH = DATA_DIR / "catalogo_ejercicios.csv"
NUTRICION_PATH = DATA_DIR / "plan_alimentacion_fitness.csv"
PLANTILLAS_PATH = PERSONAL_DIR / "mis_rutinas.csv"
COMIDAS_PERSONALES_PATH = PERSONAL_DIR / "mis_comidas.csv"

ENCODING = "utf-8-sig"
DELIMITER = ","

COLUMNAS_RUTINA = (
    "id_rutina",
    "dia",
    "horario",
    "grupo_muscular",
    "ejercicios",
    "series",
    "repeticiones_o_duracion",
    "nivel",
    "descanso",
)

COLUMNAS_EJERCICIO = (
    "id_ejercicio",
    "nombre",
    "grupo_muscular",
    "patron_movimiento",
    "equipamiento",
    "nivel_sugerido",
    "nota_tecnica",
)

COLUMNAS_NUTRICION = (
    "id_plan",
    "comida",
    "horario",
    "alimentos_sugeridos",
    "objetivo_general",
    "observaciones",
)

COLUMNAS_PLANTILLA = (
    "id_plantilla",
    "grupo_muscular",
    "ejercicios",
    "series",
    "repeticiones_o_duracion",
    "nivel",
    "descanso",
)

OBSERVACION_COMIDA_PERSONAL = (
    "Combinación personal creada con alimentos del plan estándar."
)

DIAS = (
    "Lunes",
    "Martes",
    "Miércoles",
    "Jueves",
    "Viernes",
    "Sábado",
    "Domingo",
)

NIVELES = ("Principiante", "Intermedio", "Avanzado", "Todos")

APP_NAME = "FitPlan"
APP_TITLE = "FitPlan — Gestor de Rutinas y Nutrición"
APP_VERSION = "0.1.0"
ORGANIZATION = "FitPlan"
