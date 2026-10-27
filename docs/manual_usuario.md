# Manual de usuario — FitPlan

## 1. Qué es FitPlan

FitPlan es una aplicación de escritorio para consultar y analizar rutinas de entrenamiento, un catálogo de ejercicios y un plan de alimentación. También permite crear una biblioteca personal de rutinas y comidas reutilizando exclusivamente las opciones disponibles en los datos estándar.

La aplicación está pensada para trabajar con archivos CSV locales. No requiere conexión a internet ni una base de datos.

## 2. Requisitos e instalación

Requisitos:

- Python 3.10 o superior.
- PyQt5 5.15.

Instalación desde la carpeta del proyecto:

```bash
python3 -m pip install -r requirements.txt
```

Ejecución:

```bash
python3 main.py
```

## 3. Primer inicio

Al abrir FitPlan se cargan automáticamente:

- `data/rutinas_fitness.csv`
- `data/catalogo_ejercicios.csv`
- `data/plan_alimentacion_fitness.csv`
- Tus datos personales, si ya existen en `data/personal/`.

La ventana principal contiene cinco pestañas:

1. **Rutinas**
2. **Ejercicios**
3. **Nutrición**
4. **Estadísticas**
5. **Mi plan**

Cada pestaña de datos tiene una tabla ordenable, filtros, búsqueda y un contador de resultados. La barra de estado muestra los totales cargados. Con los datos actuales se cargan **60 rutinas**, **100 ejercicios** y **42 comidas**.

## 4. Menús y atajos

### Archivo

| Acción | Atajo |
|---|---|
| Importar rutinas CSV | `Ctrl+O` |
| Importar catálogo CSV | `Ctrl+Shift+O` |
| Importar plan nutricional CSV | `Ctrl+Shift+N` |
| Exportar rutinas visibles | — |
| Exportar catálogo visible | — |
| Exportar plan visible | — |
| Exportar estadísticas | — |
| Exportar mis rutinas | — |
| Exportar mis comidas | — |
| Salir | `Ctrl+Q` |

### Ver

| Acción | Atajo |
|---|---|
| Ir a Rutinas | `Ctrl+1` |
| Ir a Ejercicios | `Ctrl+2` |
| Ir a Nutrición | `Ctrl+3` |
| Ir a Estadísticas | `Ctrl+4` |
| Ir a Mi plan | `Ctrl+5` |
| Recargar datos estándar y personales | `F5` |

### Búsqueda y filtros

| Acción | Atajo |
|---|---|
| Enfocar la búsqueda de la pestaña activa | `Ctrl+F` |
| Limpiar los filtros de la pestaña activa | `Ctrl+L` |

## 5. Pestañas de datos estándar

### 5.1 Rutinas

Permite consultar el plan de entrenamiento semanal.

- Filtra por **Día**, **Grupo muscular**, **Nivel** y **Horario**.
- Busca por ID, día, grupo, ejercicio, nivel, horario, series, repeticiones o descanso.
- La búsqueda ignora mayúsculas y tildes y admite varias palabras.
- Haz clic en una cabecera para ordenar.
- El contador indica cuántas rutinas se muestran sobre el total.
- **Limpiar filtros** restablece la vista.
- **Exportar vista CSV** guarda únicamente las filas visibles.
- **Importar CSV** reemplaza las rutinas cargadas; no modifica los datos personales.

La fila R009 representa un día de descanso y tiene `series = 0`.

### 5.2 Ejercicios

Muestra el catálogo técnico y su relación con las rutinas.

- Filtra por **Grupo muscular**, **Nivel sugerido**, **Patrón de movimiento** y **Equipamiento**.
- Busca por nombre, grupo, patrón, equipamiento, nivel o nota técnica.
- Al seleccionar un ejercicio se muestra su ficha con la nota técnica completa.
- La cobertura compara los ejercicios mencionados en las rutinas con el catálogo.
- El indicador muestra encontrados, total y porcentaje; el tooltip lista los nombres faltantes.
- **Importar catálogo CSV** reemplaza solo el catálogo y recalcula la cobertura.

Con los datos actuales, la cobertura es **100 de 100 ejercicios únicos (100.0 %)**. Si se importan rutinas con ejercicios que no estén en el catálogo, el indicador muestra la brecha y el tooltip lista los faltantes; no se inventan equivalencias.

### 5.3 Nutrición

Permite consultar el plan de alimentación diario.

- Filtra por **Comida**, **Horario** y **Objetivo general**.
- Busca por comida, horario, alimento, objetivo u observaciones.
- La tabla ordena los horarios de forma cronológica cuando son reconocibles.
- Al seleccionar una comida se muestran los alimentos sugeridos y las observaciones.
- El resumen indica comidas, sugerencias de alimentos y alimentos únicos.
- **Importar plan CSV** reemplaza solo el plan nutricional.

### 5.4 Estadísticas

Presenta indicadores y distribuciones calculados a partir de los datos estándar:

- Rutinas, series programadas, catálogo y nutrición.
- Rutinas por día, grupo muscular y nivel.
- Series por grupo muscular.
- Catálogo por grupo.
- Comidas por objetivo.
- Ejercicios mencionados en las rutinas y si están en el catálogo.

Las estadísticas se recalculan al importar datos o al pulsar **Actualizar**. No incluyen las plantillas ni comidas personales. La exportación genera un CSV en formato largo con las columnas `seccion`, `categoria`, `valor`, `porcentaje` y `detalle`.

## 6. Mi plan

La pestaña **Mi plan** (`Ctrl+5`) contiene dos vistas:

- **Mis rutinas**
- **Mis comidas**

Los datos personales se guardan de inmediato en:

- `data/personal/mis_rutinas.csv`
- `data/personal/mis_comidas.csv`

Estos archivos se crean en el primer guardado. No se modifican al importar los CSV estándar.

### 6.1 Crear una rutina personal

1. Abre **Mi plan → Mis rutinas**.
2. Pulsa **Nueva plantilla**.
3. Opcionalmente, elige una rutina en **Copiar ejercicios de una rutina estándar**.
4. Filtra el catálogo por grupo, patrón, equipamiento, nivel o texto.
5. Selecciona un ejercicio y pulsa **Añadir →**, o haz doble clic.
6. Repite hasta completar la plantilla.
7. Usa **Subir** y **Bajar** para ordenar los ejercicios.
8. Elige **Series**, **Repeticiones / duración**, **Descanso** y **Nivel**.
9. Comprueba el grupo resultante y pulsa **Guardar**.

Reglas:

- Una plantilla debe tener al menos un ejercicio.
- No se permiten ejercicios repetidos.
- Todos los ejercicios deben pertenecer al catálogo estándar.
- El grupo muscular se calcula automáticamente: si todos los ejercicios comparten grupo se usa ese grupo; si hay varios, se usa **Cuerpo completo**.
- Las opciones de series, repeticiones, descanso y nivel proceden de los datos estándar.
- Si una rutina estándar contiene ejercicios que no están en el catálogo, se omiten y aparece un aviso. Con los datos actuales, R001 incluye todos sus ejercicios y no genera aviso.
- El identificador se asigna automáticamente como `MR001`, `MR002`, etc.

### 6.2 Crear una comida personal

1. Abre **Mi plan → Mis comidas**.
2. Pulsa **Nueva comida**.
3. Opcionalmente, elige una comida estándar en **Copiar alimentos de una comida estándar**.
4. Elige **Comida**, **Horario** y **Objetivo general**.
5. Filtra los alimentos por comida de origen o por texto.
6. Añade los alimentos con **Añadir →** o doble clic.
7. Ordena la selección si lo necesitas.
8. Pulsa **Guardar**.

Reglas:

- Una comida debe tener al menos un alimento.
- No se permiten alimentos repetidos.
- El tipo de comida, horario, objetivo y alimentos deben existir en el plan estándar.
- Las observaciones se generan automáticamente.
- El identificador se asigna como `MC001`, `MC002`, etc.

### 6.3 Editar y eliminar

- Selecciona una fila y pulsa **Editar**, o haz doble clic.
- Selecciona una fila y pulsa **Eliminar**.
- La eliminación pide confirmación.
- Editar o eliminar datos personales no modifica los CSV estándar.

### 6.4 Exportar y recargar

- **Exportar mis rutinas CSV** guarda la biblioteca personal.
- **Exportar mis comidas CSV** guarda las comidas personales.
- Las mismas acciones están en **Archivo → Exportar**.
- `F5` recarga los datos estándar y personales.

## 7. Importar datos

Los archivos deben cumplir estas condiciones:

- Codificación UTF-8 con BOM (`utf-8-sig`) o UTF-8.
- Separador coma.
- Encabezado con las columnas obligatorias.
- Identificadores únicos y no vacíos.
- Una fila por registro, con el mismo número de columnas que el encabezado.
- Campos con comas internas entre comillas dobles.

Si un archivo falla:

- La importación se cancela para ese conjunto.
- Se conserva la versión válida anterior.
- Se muestra un resumen del error y un detalle técnico.

Los archivos estándar esperados son:

| Archivo | Columnas |
|---|---|
| `rutinas_fitness.csv` | `id_rutina`, `dia`, `horario`, `grupo_muscular`, `ejercicios`, `series`, `repeticiones_o_duracion`, `nivel`, `descanso` |
| `catalogo_ejercicios.csv` | `id_ejercicio`, `nombre`, `grupo_muscular`, `patron_movimiento`, `equipamiento`, `nivel_sugerido`, `nota_tecnica` |
| `plan_alimentacion_fitness.csv` | `id_plan`, `comida`, `horario`, `alimentos_sugeridos`, `objetivo_general`, `observaciones` |

Los campos de lista se separan con punto y coma (`;`).

## 8. Exportar datos

La exportación:

- Usa UTF-8 con BOM y separador coma.
- Añade la extensión `.csv` si se omite.
- Crea la carpeta de destino si no existe.
- Escribe de forma atómica para evitar archivos incompletos.

Las pestañas estándar exportan la vista filtrada actual. En **Mi plan**, la exportación guarda todos los registros personales de la vista seleccionada.

## 9. Datos personales y copias de seguridad

Para respaldar tu información, copia la carpeta `data/personal/`:

```text
data/personal/
├── mis_rutinas.csv
└── mis_comidas.csv
```

También puedes exportar cada vista desde la aplicación. Para restaurar, cierra FitPlan y copia los archivos de nuevo en `data/personal/`.

No edites los archivos personales mientras la aplicación está abierta: los cambios podrían sobrescribirse en el siguiente guardado. Usa **Mi plan** para modificarlos.

## 10. Problemas frecuentes

### La aplicación no inicia

Comprueba que PyQt5 está instalado:

```bash
python3 -m pip install -r requirements.txt
```

### Un CSV no se importa

Revisa:

- Que la ruta sea correcta.
- Que el archivo no esté vacío.
- Que el encabezado tenga las columnas obligatorias.
- Que no haya IDs duplicados.
- Que todas las filas tengan el mismo número de columnas.
- Que la codificación sea UTF-8.

El detalle técnico del diálogo de error indica el archivo y la línea cuando están disponibles.

### No aparecen mis datos personales

Comprueba que existan `data/personal/mis_rutinas.csv` y `data/personal/mis_comidas.csv` y pulsa `F5`. Si los archivos tienen un formato inválido, FitPlan muestra el error y conserva los datos que ya estaban cargados en memoria.

### Una opción no aparece en un selector

Los selectores solo muestran valores presentes en los CSV estándar. Si necesitas otra serie, repetición, descanso, nivel, ejercicio, alimento, horario u objetivo, debe existir primero en los datos estándar.

### Cambié un CSV estándar y no veo el cambio

Pulsa `F5` o reinicia la aplicación. Si el archivo tiene errores, se conserva la versión válida anterior.

## 11. Alcance y limitaciones

- FitPlan no prescribe entrenamientos ni dietas; organiza y consulta datos.
- No calcula calorías, macronutrientes ni cargas de entrenamiento.
- No programa plantillas personales en días u horarios; son una biblioteca reutilizable.
- Las estadísticas no incluyen datos personales.
- No se inventan equivalencias para ejercicios ausentes del catálogo.
- Las repeticiones y descansos heredan los textos del CSV, incluidas expresiones como `12-Aug` o `8-12 (plancha: 30 s)`.
- La aplicación no envía datos a internet.

## 12. Privacidad

Todos los datos permanecen en el equipo local. FitPlan no recopila información, no usa telemetría y no realiza solicitudes de red.
