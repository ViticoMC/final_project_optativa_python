# FitPlan — Gestor de Rutinas y Nutrición

Aplicación de escritorio en Python + PyQt5 para importar, consultar, filtrar y analizar rutinas de entrenamiento, un catálogo de ejercicios y un plan de alimentación a partir de archivos CSV.

## Estado del proyecto

- [x] Fase 0 — Configuración del proyecto y datos normalizados
- [x] Fase 1 — Núcleo de datos y lectura/validación de CSV
- [ ] Fase 2 — Módulo de rutinas y ventana principal
- [ ] Fase 3 — Búsqueda, filtros y ordenamiento
- [ ] Fase 4 — Catálogo de ejercicios y cobertura
- [ ] Fase 5 — Plan de alimentación
- [ ] Fase 6 — Estadísticas
- [ ] Fase 7 — Exportación CSV
- [ ] Fase 8 — Robustez y experiencia de usuario
- [ ] Fase 9 — Pruebas, documentación y demostración

## Requisitos

- Python 3.10 o superior
- PyQt5 5.15

Instalación de dependencias:

```bash
python3 -m pip install -r requirements.txt
```

## Ejecución

```bash
python3 main.py
```

En esta fase se abre una ventana vacía como esqueleto de la aplicación.

## Estructura

```text
final_project/
├── main.py
├── requirements.txt
├── README.md
├── data/
│   ├── rutinas_fitness.csv
│   ├── catalogo_ejercicios.csv
│   └── plan_alimentacion_fitness.csv
├── app/
│   ├── config.py
│   ├── exceptions.py
│   ├── models.py
│   └── utils.py
├── services/
│   ├── csv_service.py
│   ├── rutina_service.py
│   ├── ejercicio_service.py
│   ├── nutricion_service.py
│   ├── estadistica_service.py
│   └── export_service.py
├── ui/
│   ├── main_window.py
│   ├── dialogs.py
│   ├── styles.py
│   ├── models/
│   │   └── table_models.py
│   └── widgets/
│       ├── rutinas_tab.py
│       ├── ejercicios_tab.py
│       ├── nutricion_tab.py
│       └── estadisticas_tab.py
├── tests/
│   ├── fixtures/
│   └── test_*.py
└── docs/
    ├── manual_usuario.md
    └── guion_exposicion.md
```

Las carpetas y los archivos marcados como pendientes se crearán en las siguientes fases.

## Datos

Los tres CSV se encuentran en `data/` y usan:

- Codificación UTF-8 con BOM (`utf-8-sig`), compatible con Excel.
- Separador coma.
- Campos con comas internas entre comillas dobles.
- Identificadores únicos por registro.

| Archivo | Registros | Columnas |
|---|---:|---:|
| `rutinas_fitness.csv` | 10 | 9 |
| `catalogo_ejercicios.csv` | 13 | 7 |
| `plan_alimentacion_fitness.csv` | 7 | 6 |

`rutina.csv` fue renombrado a `rutinas_fitness.csv` para mantener una nomenclatura consistente con el resto del proyecto.

### Observaciones de calidad de datos

- El campo `series` contiene un `0` en el día de descanso; el lector lo acepta como valor válido.
- Los horarios incluyen valores no numéricos como `Descanso`, `Durante el día` o `Después de entrenar`.
- Las rutinas mencionan 29 ejercicios (28 únicos), de los cuales solo 12 coinciden con el catálogo. La aplicación reportará la cobertura y los faltantes en lugar de inventar equivalencias.
- Los grupos musculares de las rutinas incluyen categorías que no aparecen en el catálogo, como `Cuerpo completo`, `Abdomen y cardio`, `Recuperación` y `Movilidad`.

## Núcleo de datos

La Fase 1 incorpora:

- `app/exceptions.py`: errores propios (`CsvFormatError`, `DataValidationError`, `ExportError`).
- `app/utils.py`: normalización de texto, búsqueda sin tildes, listas y orden de horarios.
- `app/models.py`: `Rutina`, `Ejercicio`, `Comida` y `Cobertura` con conversión desde/hacia filas CSV.
- `services/csv_service.py`: lectura con validación de encabezados, filas e IDs únicos; escritura atómica con BOM.

Ejemplo de uso:

```python
from app.config import COLUMNAS_RUTINA, RUTINAS_PATH
from app.models import Rutina
from services.csv_service import CsvService

servicio = CsvService()
filas = servicio.leer(RUTINAS_PATH, COLUMNAS_RUTINA, columna_id="id_rutina")
rutinas = [Rutina.from_row(fila) for fila in filas]

print(len(rutinas))  # 10
```

## Pruebas

```bash
python3 -m unittest discover -s tests -v
```

La Fase 1 incluye 41 pruebas de utilidades, modelos y servicio CSV. Las pruebas de los servicios restantes se incorporarán en la Fase 9.
