# FitPlan — Gestor de Rutinas y Nutrición

Aplicación de escritorio en Python + PyQt5 para importar, consultar, filtrar y analizar rutinas de entrenamiento, un catálogo de ejercicios y un plan de alimentación a partir de archivos CSV.

## Estado del proyecto

- [x] Fase 0 — Configuración del proyecto y datos normalizados
- [x] Fase 1 — Núcleo de datos y lectura/validación de CSV
- [x] Fase 2 — Módulo de rutinas y ventana principal
- [x] Fase 3 — Búsqueda, filtros y ordenamiento
- [x] Fase 4 — Catálogo de ejercicios y cobertura
- [x] Fase 5 — Plan de alimentación
- [x] Fase 6 — Estadísticas
- [x] Fase 7 — Exportación CSV
- [x] Fase 8 — Robustez y experiencia de usuario
- [x] Fase 8.5 — Mi plan personal
- [x] Fase 9 — Pruebas, documentación y demostración

## Documentación

- [Manual de usuario](docs/manual_usuario.md)
- [Guion de exposición](docs/guion_exposicion.md)

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

Al iniciar, la aplicación carga automáticamente los tres CSV de `data/` y muestra las pestañas **Rutinas**, **Ejercicios**, **Nutrición**, **Estadísticas** y **Mi plan**. Cada pestaña de datos permite reemplazar su archivo desde el botón de importación o desde el menú **Archivo**: rutinas (`Ctrl+O`), catálogo (`Ctrl+Shift+O`) y plan nutricional (`Ctrl+Shift+N`). Las estadísticas se recalculan automáticamente después de cada importación. La vista filtrada de cada pestaña, las estadísticas y los datos personales se pueden guardar en CSV desde **Archivo → Exportar** o con los botones de exportación.

## Estructura

```text
final_project/
├── main.py
├── requirements.txt
├── README.md
├── data/
│   ├── rutinas_fitness.csv
│   ├── catalogo_ejercicios.csv
│   ├── plan_alimentacion_fitness.csv
│   └── personal/                  # se crea al guardar datos propios
│       ├── mis_rutinas.csv
│       └── mis_comidas.csv
├── app/
│   ├── config.py
│   ├── exceptions.py
│   ├── models.py
│   └── utils.py
├── services/
│   ├── csv_service.py
│   ├── rutina_service.py
│   ├── ejercicio_service.py
│   ├── container.py
│   ├── nutricion_service.py
│   ├── plantilla_service.py
│   ├── comida_personal_service.py
│   ├── estadistica_service.py
│   └── export_service.py
├── ui/
│   ├── main_window.py
│   ├── dialogs.py
│   ├── dialogs_personal.py
│   ├── styles.py
│   ├── models/
│   │   └── table_models.py
│   └── widgets/
│       ├── rutinas_tab.py
│       ├── ejercicios_tab.py
│       ├── nutricion_tab.py
│       ├── estadisticas_tab.py
│       ├── mi_plan_tab.py
│       └── selector_multiple.py
├── tests/
│   ├── fixtures/
│   └── test_*.py
└── docs/
    ├── manual_usuario.md
    └── guion_exposicion.md
```

La documentación está disponible en:

- [`docs/manual_usuario.md`](docs/manual_usuario.md): uso completo de la aplicación.
- [`docs/guion_exposicion.md`](docs/guion_exposicion.md): preparación y guion de la demostración.

## Datos

Los tres CSV se encuentran en `data/` y usan:

- Codificación UTF-8 con BOM (`utf-8-sig`), compatible con Excel.
- Separador coma.
- Campos con comas internas entre comillas dobles.
- Identificadores únicos por registro.

| Archivo | Registros | Columnas |
|---|---:|---:|
| `rutinas_fitness.csv` | 60 | 9 |
| `catalogo_ejercicios.csv` | 100 | 7 |
| `plan_alimentacion_fitness.csv` | 42 | 6 |

Los archivos de `data/personal/` no existen hasta que se guarda la primera plantilla o comida propia. Son independientes de los CSV estándar y no se sobrescriben al importar datos estándar.

`rutina.csv` fue renombrado a `rutinas_fitness.csv` para mantener una nomenclatura consistente con el resto del proyecto.

### Observaciones de calidad de datos

- El campo `series` contiene un `0` en el día de descanso; el lector lo acepta como valor válido.
- Los horarios incluyen valores no numéricos como `Descanso`, `Durante el día` o `Después de entrenar`.
- Las rutinas usan 100 ejercicios únicos y todos existen en el catálogo (**100/100, 100.0 %** de cobertura).
- El conjunto actual suma 196 series programadas (3.27 por rutina), 42 comidas, 93 alimentos únicos y 132 sugerencias.
- Los grupos musculares de las rutinas incluyen categorías que no aparecen en el catálogo, como `Abdomen y cardio` y `Recuperación`.

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

print(len(rutinas))  # 60
```

## Interfaz de rutinas

La Fase 2 incorpora:

- `services/rutina_service.py`: carga atómica, consulta por ID, días, grupos, niveles y valores únicos.
- `ui/models/table_models.py`: modelo Qt reutilizable, 9 columnas, orden numérico/texto y tooltips.
- `ui/widgets/rutinas_tab.py`: tabla ordenable, botón de importación y contador de registros.
- `ui/main_window.py`: ventana con menú Archivo/Ayuda, barra de estado y carga inicial automática de rutinas, catálogo y plan nutricional.
- `services/container.py`: `AppServices`, contenedor que inyecta los servicios en la interfaz.
- `main.py`: composición de servicios y arranque de la aplicación.

## Búsqueda, filtros y ordenamiento

La Fase 3 incorpora:

- Filtros combinables por día, grupo muscular, nivel y horario.
- Búsqueda libre por ID, día, grupo, ejercicio, nivel, horario, series, repeticiones y descanso.
- Búsqueda insensible a mayúsculas y tildes, con soporte para varias palabras (`lunes pecho`).
- Contador «Mostrando X de Y rutinas» y estado específico cuando no hay coincidencias.
- Botón y atajo `Ctrl+L` para limpiar todos los filtros.
- Ordenamiento por cualquier columna, conservado al aplicar o cambiar filtros.

## Catálogo de ejercicios y cobertura

La Fase 4 incorpora:

- `services/ejercicio_service.py`: carga atómica del catálogo, consulta por ID o nombre, filtros y cálculo de cobertura.
- `EjercicioTableModel`: 6 columnas ordenables por ID, nombre, grupo, patrón, equipamiento y nivel.
- Pestaña **Ejercicios** con filtros combinables por grupo muscular, nivel, patrón de movimiento y equipamiento.
- Búsqueda libre por nombre, grupo, patrón, equipamiento, nivel y nota técnica.
- Ficha técnica del ejercicio seleccionado, con tooltip y nota completa.
- Indicador de cobertura (100/100, 100.0 %) y tooltip con los faltantes; con los datos actuales no hay ejercicios sin coincidencia.
- Importación independiente del catálogo sin perder las rutinas cargadas.

## Plan de alimentación

La Fase 5 incorpora:

- `services/nutricion_service.py`: carga atómica, consulta por ID, filtros y resumen de alimentos.
- `ComidaTableModel`: 6 columnas con orden cronológico de horarios.
- Pestaña **Nutrición** con filtros por comida, horario y objetivo general.
- Búsqueda libre por comida, horario, alimento, objetivo y observaciones.
- Panel de detalle con los alimentos sugeridos y las observaciones de cada comida.
- Resumen del plan (42 comidas, 132 sugerencias y 93 alimentos únicos) con listado completo en el tooltip.
- Importación independiente del plan sin perder rutinas ni catálogo.

## Estadísticas

La Fase 6 incorpora:

- `services/estadistica_service.py`: cálculo de indicadores y distribuciones sin depender de la interfaz.
- Tarjetas de resumen: rutinas, series programadas, catálogo y nutrición.
- Distribuciones de rutinas por día, grupo muscular y nivel.
- Volumen de series por grupo muscular y catálogo por grupo.
- Comidas por objetivo y ejercicios mencionados en las rutinas, indicando si están en el catálogo.
- Botón **Actualizar** y recálculo automático al importar cualquier CSV.

## Exportación CSV

La Fase 7 incorpora:

- `services/export_service.py`: exportación de rutinas, catálogo, plan y estadísticas mediante `CsvService`.
- Botones **Exportar vista CSV** en las pestañas de datos y **Exportar estadísticas CSV** en el panel.
- Menú **Archivo → Exportar** con las cuatro opciones.
- Exportación de la vista filtrada actual, respetando búsqueda y filtros, o de todo el conjunto cuando no hay filtros.
- Extensión `.csv` automática y escritura atómica, con creación de directorios si es necesario.
- Estadísticas en formato largo (`seccion`, `categoria`, `valor`, `porcentaje`, `detalle`) con resumen, cobertura, distribuciones y ejercicios mencionados.

## Robustez y experiencia de usuario

La Fase 8 incorpora:

- Tema visual centralizado en `ui/styles.py`, aplicado con el estilo Fusion.
- Diálogos reutilizables en `ui/dialogs.py`: los errores muestran un resumen y permiten consultar el detalle técnico.
- Persistencia con `QSettings` del tamaño y posición de la ventana, la pestaña activa y las últimas carpetas de importación/exportación.
- Acción **Recargar datos** (`F5`) para releer los CSV actuales sin reiniciar la aplicación.
- Navegación entre pestañas con `Ctrl+1` a `Ctrl+5`.
- `Ctrl+F` enfoca la búsqueda de la pestaña activa y `Ctrl+L` limpia sus filtros.
- Botones de importación destacados como acción principal.
- Recarga parcial segura: si falla un archivo, se conservan los datos válidos y se informa del problema.

## Mi plan personal

La Fase 8.5 incorpora:

- Pestaña **Mi plan** (`Ctrl+5`) con las vistas **Mis rutinas** y **Mis comidas**, separadas de los datos estándar.
- Plantillas de rutina reutilizables, sin día ni horario, formadas exclusivamente por ejercicios del catálogo.
- Comidas personales formadas por alimentos, tipos, horarios y objetivos existentes en el plan estándar.
- Formularios basados en selección: filtros de catálogo, listas de disponibles/seleccionados y opciones cerradas de series, repeticiones, descanso y nivel.
- Botón opcional para partir de una rutina o comida estándar y ajustar la selección.
- Advertencia cuando una rutina estándar contiene ejercicios que no están en el catálogo; esos ejercicios no se copian.
- Creación, edición y eliminación con confirmación; los datos estándar permanecen de solo lectura.
- Persistencia automática en `data/personal/mis_rutinas.csv` y `data/personal/mis_comidas.csv` con IDs `MR###` y `MC###`.
- Exportación específica desde cada vista y desde **Archivo → Exportar**.
- Resumen de plantillas, ejercicios, comidas y alimentos propios; `F5` recarga también los datos personales.

Limitación inicial: al usar únicamente opciones de los CSV, las alternativas disponibles son las que ya existen en los datos estándar. Al añadir más ejercicios, alimentos o valores de prescripción a esos CSV, los selectores se amplían sin cambiar la interfaz.

## Pruebas

```bash
python3 -m unittest discover -s tests -v
```

El proyecto incluye 214 pruebas de utilidades, modelos, servicio CSV, servicios de rutinas, ejercicios, nutrición, plantillas personales, comidas personales, estadísticas y exportación, modelos de tabla, selector múltiple, pestañas de rutinas, ejercicios, nutrición, estadísticas y Mi plan, diálogos personales, y ventana principal con preferencias persistentes.

Estado actual: **214 pruebas correctas** y compilación sin errores. Para ejecutar las pruebas en un entorno sin pantalla:

```bash
QT_QPA_PLATFORM=offscreen python3 -m unittest discover -s tests -q
```
