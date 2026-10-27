# Guion de exposición — FitPlan

## 1. Objetivo de la demostración

Presentar FitPlan en 10–12 minutos mostrando:

1. La carga y exploración de los datos estándar.
2. Los filtros, la búsqueda, el ordenamiento y la cobertura.
3. Las estadísticas y la exportación.
4. La creación de una rutina y una comida personales sin escribir datos nuevos.
5. La persistencia y la separación entre datos estándar y personales.

## 2. Preparación previa

### Comprobar que todo funciona

```bash
python3 -m compileall -q app services ui tests main.py
QT_QPA_PLATFORM=offscreen python3 -m unittest discover -s tests -q
python3 main.py
```

Resultado esperado: compilación sin errores y **214 pruebas OK**.

### Preparar un estado limpio (opcional)

Si ya existen datos personales y se quiere empezar desde cero, haz una copia antes de la exposición:

```bash
mkdir -p /tmp/opencode/demo_fitplan
cp -r data/personal /tmp/opencode/demo_fitplan/personal_backup 2>/dev/null || true
rm -f data/personal/mis_rutinas.csv data/personal/mis_comidas.csv
```

No borres esos archivos si contienen información que quieres conservar.

### Comprobar el entorno

- Abrir FitPlan una vez antes de la exposición.
- Verificar que la ventana se ve completa en el proyector.
- Cerrar diálogos de error o de importación pendientes.
- Tener a mano una carpeta de destino para exportar, por ejemplo `/tmp/opencode/demo_fitplan/`.
- No es necesario tener conexión a internet.

## 3. Guion cronometrado

### 0:00–0:40 — Presentación

**Narrar:**

> FitPlan es una aplicación de escritorio en Python y PyQt5 para consultar rutinas, ejercicios y alimentación desde archivos CSV. Separa los datos estándar de los datos personales y funciona completamente en local.

**Mostrar:** ventana principal y las cinco pestañas.

### 0:40–1:30 — Vista general

**Acciones:**

1. Señalar las pestañas **Rutinas**, **Ejercicios**, **Nutrición**, **Estadísticas** y **Mi plan**.
2. Señalar la barra de estado: 60 rutinas, 100 ejercicios, 42 comidas, 0 plantillas y 0 comidas personales si se partió de un estado limpio.
3. Abrir **Ver** para mostrar los atajos `Ctrl+1` a `Ctrl+5`.

**Narrar:**

> La barra de estado resume los datos cargados. Los atajos permiten navegar sin usar el mouse.

### 1:30–3:00 — Rutinas: filtros, búsqueda y orden

**Acciones:**

1. Ir a **Rutinas** (`Ctrl+1`).
2. En **Día**, elegir **Lunes**.
3. En **Grupo muscular**, elegir **Pecho**.
4. Mostrar el resultado: **R001**, **R011**, **R021** y **R029**, con distintos horarios y niveles.
5. Escribir `pecho` en la búsqueda y mostrar cómo se mantiene el filtro combinado.
6. Pulsar **Limpiar filtros** (`Ctrl+L`).
7. Hacer clic en **Día** para ordenar y explicar que el orden se conserva al filtrar.

**Narrar:**

> Los filtros son combinables. La búsqueda ignora tildes y mayúsculas. La vista filtrada es la que luego se exporta.

### 3:00–4:30 — Ejercicios y cobertura

**Acciones:**

1. Ir a **Ejercicios** (`Ctrl+2`).
2. En **Grupo muscular**, elegir **Pecho**.
3. Seleccionar **Press de banca**.
4. Mostrar la ficha: grupo, patrón, equipamiento, nivel y nota técnica.
5. Limpiar filtros y señalar la cobertura: **100/100, 100.0 %**.
6. Pasar el mouse sobre el indicador y mostrar que todos los ejercicios de las rutinas están en el catálogo.
7. Explicar que, si se importaran rutinas con ejercicios ausentes, FitPlan reportaría la brecha sin inventar equivalencias.

**Narrar:**

> El catálogo tiene 100 ejercicios y las rutinas usan esos mismos 100. La cobertura es completa; si se importa un conjunto nuevo, la aplicación reporta cualquier brecha en lugar de ocultarla.

### 4:30–5:45 — Nutrición

**Acciones:**

1. Ir a **Nutrición** (`Ctrl+3`).
2. En **Comida**, elegir **Desayuno**.
3. Seleccionar la fila y mostrar alimentos y observaciones.
4. Limpiar filtros.
5. Señalar el resumen: **42 comidas, 132 sugerencias, 93 alimentos únicos**.

**Narrar:**

> El plan se puede filtrar por comida, horario u objetivo. El panel de detalle muestra los alimentos y las observaciones del CSV.

### 5:45–7:00 — Estadísticas

**Acciones:**

1. Ir a **Estadísticas** (`Ctrl+4`).
2. Mostrar las tarjetas: **60 rutinas**, **196 series**, **100 ejercicios**, **42 comidas**.
3. Señalar las distribuciones por día, grupo, nivel, series y catálogo.
4. Explicar que las estadísticas usan solo datos estándar.
5. Pulsar **Exportar estadísticas CSV** y guardar en `/tmp/opencode/demo_fitplan/estadisticas.csv`.
6. Mostrar el mensaje de confirmación en la barra de estado.

**Narrar:**

> Las estadísticas se recalculan al importar o al pulsar Actualizar. La exportación genera un CSV en formato largo, listo para analizar.

### 7:00–9:30 — Crear una rutina personal

**Acciones:**

1. Ir a **Mi plan** (`Ctrl+5`).
2. Abrir **Mis rutinas**.
3. Pulsar **Nueva plantilla**.
4. En **Copiar ejercicios de una rutina estándar**, elegir:
   `R001 · Lunes · Pecho · 07:00-08:00`.
5. Mostrar que se seleccionan **Press de banca**, **Press inclinado con mancuernas** y **Aperturas**.
6. Señalar que no aparece aviso: todos los ejercicios de R001 están en el catálogo.
7. Mostrar que la prescripción se precargó: 3 series, `12-Aug`, 60-90 s, Intermedio.
8. Pulsar **Guardar**.
9. Mostrar la fila **MR001** en la tabla.
10. Seleccionar la fila y pulsar **Editar** para mostrar que los datos se recuperan; cancelar.

**Narrar:**

> La plantilla reutiliza el catálogo y las opciones estándar; no se escribe texto libre. Si falta un ejercicio, se avisa y no se copia. El grupo se calcula automáticamente.

### 9:30–11:15 — Crear una comida personal

**Acciones:**

1. Abrir **Mis comidas**.
2. Pulsar **Nueva comida**.
3. En **Copiar alimentos de una comida estándar**, elegir:
   `D001 · Desayuno · 07:30`.
4. Mostrar que se precargan comida, horario, objetivo y alimentos.
5. En el filtro de alimentos, buscar `fruta`.
6. Añadir **fruta** a la selección.
7. Pulsar **Guardar**.
8. Mostrar la fila **MC001**.

**Narrar:**

> La comida personal también se construye solo con alimentos del plan estándar. El identificador y las observaciones se generan de forma automática.

### 11:15–12:00 — Persistencia, exportación y cierre

**Acciones:**

1. Pulsar `F5`.
2. Mostrar que **MR001** y **MC001** siguen presentes y que la barra de estado actualizó los conteos.
3. Exportar **Mis rutinas CSV** a `/tmp/opencode/demo_fitplan/mis_rutinas.csv`.
4. Abrir brevemente **Archivo → Exportar** para mostrar las seis opciones.
5. Cerrar la aplicación y abrirla de nuevo si el tiempo lo permite, para demostrar la persistencia.
6. Cerrar con `Ctrl+Q`.

**Narrar:**

> Los datos personales se guardan en `data/personal/` y no se mezclan con los estándar. Al importar un CSV estándar, las plantillas y comidas propias se conservan.

## 4. Frases clave

- “Los CSV estándar son catálogos de solo lectura para la aplicación.”
- “Los filtros y la búsqueda determinan exactamente lo que se exporta.”
- “La cobertura actual es completa: 100 de 100 ejercicios, 100.0 %.”
- “Una plantilla es una biblioteca reutilizable, no una programación semanal.”
- “No se escribe texto libre: todo se elige de las opciones existentes.”
- “Los datos personales viven en archivos separados y sobreviven a las importaciones.”

## 5. Preguntas previsibles

### ¿Por qué no se pueden escribir alimentos o ejercicios nuevos?

Porque el objetivo es mantener trazabilidad con los CSV estándar y evitar datos inconsistentes. Al ampliar los CSV, los selectores crecen automáticamente. No se requieren cambios de interfaz.

### ¿Qué pasa si una rutina usa un ejercicio que no está en el catálogo?

FitPlan lo marca como faltante, muestra la cobertura real y no inventa equivalencias. Con los datos actuales no hay faltantes: los 100 ejercicios de las rutinas existen en el catálogo.

### ¿Por qué las repeticiones dicen `12-Aug`?

Es el texto original del CSV. La aplicación no lo interpreta ni lo corrige para no alterar el dato fuente. Se puede normalizar el CSV en una fase posterior.

### ¿Las estadísticas incluyen Mi plan?

No. Las estadísticas son de los datos estándar. Mi plan muestra sus propios contadores.

### ¿Dónde se guardan los datos personales?

En `data/personal/mis_rutinas.csv` y `data/personal/mis_comidas.csv`. Se crean al primer guardado.

### ¿Qué pasa si un CSV está mal?

La carga de ese conjunto se cancela, se conserva la versión válida anterior y se muestra el error con detalle técnico.

## 6. Plan de contingencia

### La aplicación no abre

```bash
python3 -m pip install -r requirements.txt
python3 main.py
```

Si el problema persiste, ejecutar las pruebas y mostrar el código o una captura de respaldo.

### Los conteos iniciales no son cero

Hay datos personales de una ejecución anterior. No es un error: explicar que la persistencia funciona. Si se necesita una demo limpia, restaurar el respaldo o eliminar los dos CSV personales con la aplicación cerrada.

### Aparece un aviso al copiar una rutina

El aviso solo aparece cuando la rutina de origen contiene ejercicios ausentes del catálogo cargado. Con R001 y el catálogo estándar no debería aparecer. Comprobar que se cargó el catálogo estándar y pulsar `F5`.

### Falla una exportación

Comprobar permisos de escritura y elegir `/tmp/opencode/demo_fitplan/`. La aplicación añade `.csv` si se omite la extensión.

### La ventana no cabe en el proyector

Reducir la escala del sistema o usar una resolución de al menos 1280×800. La ventana admite redimensionado y la tabla tiene scroll.

## 7. Cierre sugerido

> FitPlan demuestra separación de capas, validación de CSV, filtros combinables, estadísticas, exportación y una extensión personal basada en catálogos. Todo funciona en local, con 214 pruebas automatizadas y documentación de usuario y exposición.
