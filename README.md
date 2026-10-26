# AndinaFoods: inteligencia de ventas y cadena de suministro

Proyecto de ingeniería y análisis de datos que integra ventas y producción mediante un pipeline en Python, una base PostgreSQL y un dashboard en Power BI. Utiliza datos simulados para demostrar la preparación de información, el análisis mensual y la generación de alertas mediante reglas explícitas.

## Problema y objetivo

Analizar ventas y producción por separado dificulta relacionar los ingresos de un producto con los defectos registrados en una planta. Este proyecto reúne ambos conjuntos de datos para consultar el desempeño comercial y productivo y señalar combinaciones de mes, producto y planta que superan determinados umbrales.

El alcance implementado comprende generación de datos de prueba, limpieza, carga en PostgreSQL, vistas analíticas y exportación de alertas a CSV. Las alertas identifican condiciones que requieren revisión; no demuestran pérdidas económicas ni predicen fallas futuras.

## Arquitectura de tres capas

| Capa | Componentes | Función |
| --- | --- | --- |
| Procesamiento de datos | Python, pandas, NumPy, SQLAlchemy y scripts de `src/` | Generar archivos de prueba, limpiar datos, cargar tablas y evaluar reglas de alertas. |
| Almacenamiento y análisis | PostgreSQL, `database/schema.sql` y `database/analytical_views.sql` | Mantener tablas con restricciones de integridad y calcular agregaciones mensuales. |
| Visualización | Power BI, archivo PBIX, vista previa y PDF | Presentar indicadores, tendencias, comparaciones por planta y un monitor de alertas. |

### Modelo de datos

El esquema contiene tres dimensiones y dos tablas de hechos:

| Tabla | Contenido y relaciones |
| --- | --- |
| `products` | Identificador, nombre y categoría del producto. |
| `plants` | Identificador, ubicación y región de la planta. |
| `clients` | Identificador, nombre y tipo de cliente. |
| `sales` | Pedido, fecha, producto, planta, cliente, cantidad y precio unitario. Referencia las tres dimensiones. |
| `production` | Fecha, planta, producto, cantidad fabricada y cantidad defectuosa. Referencia `plants` y `products`. |

Ventas y producción comparten las dimensiones de producto y planta. El SQL define claves primarias y foráneas, campos obligatorios, restricciones de cantidades y precios no negativos, y la condición de que los defectos no superen la cantidad fabricada. También crea índices sobre fechas y claves de las tablas de hechos.

Estas relaciones permiten organizar el análisis, pero no evitan por sí solas la duplicación de totales al unir hechos con distinta granularidad. El motor de alertas agrega las ventas antes de cruzarlas con producción.

## Flujo de datos de principio a fin

`run_pipeline.py` ejecuta cuatro scripts en este orden:

1. **Generación — `src/ingestion/generate_mock_data.py`.** Crea datos simulados entre el 1 de enero y el 30 de junio de 2023: cuatro productos, tres plantas —Lima, Arequipa y Trujillo— y cuatro clientes. Guarda dimensiones y ventas como CSV y producción como Excel en `data/raw/`. Introduce anomalías para ejercitar la limpieza.
2. **Limpieza — `src/cleaning/clean_data.py`.** Lee los archivos originales y escribe cinco CSV con prefijo `clean_` en `data/processed/`. Registra las operaciones de limpieza mediante `logging`.
3. **Carga — `src/loading/load_data.py`.** Ejecuta el esquema SQL, carga primero plantas, clientes y productos, después ventas y producción, y finalmente crea las vistas analíticas.
4. **Alertas — `src/alerts/generate_alerts.py`.** Consulta las vistas, agrega los ingresos por mes, producto y planta, cruza ventas con producción y exporta `data/processed/business_alerts.csv`.

La actualización de Power BI es un paso posterior: el orquestador no abre, actualiza ni publica el PBIX.

**Comportamiento de las ejecuciones:** el generador sobrescribe los archivos de entrada y `schema.sql` elimina y recrea las tablas y vistas del proyecto. Por tanto, cada ejecución reconstruye los datos; no implementa una carga incremental ni conserva el historial anterior.

## Preparación y limpieza

### Ventas

El generador introduce cantidades ausentes en una muestra del 5 %, precios negativos en una muestra del 3 % y añade una muestra duplicada del 2 %. La limpieza:

- Elimina filas completamente duplicadas con `drop_duplicates()`; no deduplica únicamente por `order_id`.
- Convierte `order_date` a fecha mediante `pd.to_datetime(..., format='mixed', errors='coerce')`.
- Descarta registros sin `quantity`.
- Convierte los precios unitarios negativos a su valor absoluto.

La conversión de fechas inválidas produce valores ausentes. El script no los elimina ni los corrige después, y tampoco especifica una preferencia explícita de día/mes para fechas ambiguas. Conviene revisar este tratamiento antes de incorporar otras fuentes.

### Producción

El generador introduce el texto `ERROR` en una muestra del 2 % de `manufactured_qty`. La limpieza:

- Convierte `manufactured_qty` a número y transforma los valores no interpretables en ausentes.
- Imputa los ausentes con la mediana de la cantidad fabricada de su misma planta.
- Ajusta `defect_qty` a `manufactured_qty` cuando los defectos superan lo fabricado.

No existe un tratamiento adicional si una planta carece de valores válidos para calcular la mediana. La columna de destino en PostgreSQL es entera, por lo que también debe revisarse la compatibilidad de cualquier mediana no entera al ampliar los datos.

### Dimensiones y registro

Los archivos de productos, plantas y clientes se copian a sus versiones `clean_` sin transformaciones adicionales. El script de limpieza configura salida a consola y al archivo `data_quality.log`, con mensajes y conteos de las operaciones realizadas. No genera un informe independiente de calidad con validaciones exhaustivas.

## Vistas analíticas

### `vw_monthly_sales_ranking`

Agrupa las ventas por **mes, producto, planta y cliente**. Calcula:

- `total_revenue`: suma de `quantity * unit_price`.
- `total_units_sold`: suma de unidades vendidas.
- `revenue_rank`: posición mediante `RANK()`, particionada por mes y ordenada por ingresos descendentes.

El ranking compara las combinaciones agregadas de producto, planta y cliente dentro de cada mes; no representa directamente un ranking global de productos.

### `vw_plant_performance`

Agrupa producción por **mes, producto y planta**. Calcula el total fabricado, los defectos y la tasa:

```text
defect_rate_percentage = 100 × SUM(defect_qty) / SUM(manufactured_qty)
```

La tasa se redondea a dos decimales. `NULLIF` evita dividir entre cero; si la suma fabricada es cero, la tasa resultante es nula.

## Reglas de alertas

El motor suma los ingresos de los distintos clientes para obtener una fila por mes, producto y planta. Luego realiza un `inner join` con la vista de producción usando esas tres claves.

| Tipo | Condición implementada | Prioridad |
| --- | --- | --- |
| `HIGH_DEFECT_RATE` | Tasa de defectos mayor que 5 %. | `HIGH` |
| `REVENUE_AT_RISK` | Si no se cumple la regla anterior: tasa de defectos mayor que 3 % e ingresos mayores que 5000. | `CRITICAL` |

Las condiciones usan comparaciones estrictas. La segunda regla se evalúa mediante `elif`: una combinación con defectos mayores al 5 % genera únicamente `HIGH_DEFECT_RATE`, aunque también supere el umbral de ingresos.

El valor 5000 corresponde al ingreso mensual agregado de la combinación evaluada. El código no declara una moneda; el reporte visual presenta los ingresos con el símbolo `S/`.

El CSV contiene `alert_date`, `alert_type`, `description` y `priority`. `alert_date` es el primer día del mes analizado, no la fecha de ejecución. La descripción incluye planta, producto y periodo. Si no se detectan alertas y el procesamiento termina correctamente, se escribe un CSV con encabezados y sin filas.

**Límites del motor:** el cruce interno excluye combinaciones sin ventas o sin producción. Las alertas se guardan en un archivo que se sobrescribe; no hay envío de notificaciones, persistencia histórica ni gestión de estados de atención. El archivo tampoco incluye identificadores separados de producto y planta.

## Archivos principales

| Ruta | Uso |
| --- | --- |
| `run_pipeline.py` | Ejecución secuencial de las cuatro etapas. |
| `src/ingestion/generate_mock_data.py` | Generación de dimensiones, ventas y producción simuladas. |
| `src/cleaning/clean_data.py` | Preparación de los archivos limpios. |
| `src/loading/load_data.py` | Conexión a PostgreSQL, reconstrucción del esquema y carga. |
| `src/alerts/generate_alerts.py` | Evaluación de reglas y exportación de alertas. |
| `database/schema.sql` | Tablas, restricciones e índices. |
| `database/analytical_views.sql` | Vistas de ventas y desempeño productivo. |
| `.env.example` | Plantilla de la variable `DB_PASSWORD`. |
| `powerbi/SupplyChain_Dashboard.pbix` | Modelo y reporte de Power BI. |
| `docs/reporte_ejecutivo.pdf` | Exportación estática del dashboard. |
| `images/dashboard_preview.png` | Vista previa del dashboard. |

`data/raw/` y `data/processed/` se crean durante la ejecución. Sus contenidos y los archivos `.log` están excluidos del control de versiones mediante `.gitignore`. `data/interim/` contiene un `.gitkeep`, pero los scripts actuales no utilizan esa carpeta.

## Ejecución local

### 1. Preparar el entorno

Se necesita Git, Python 3 y PostgreSQL en ejecución. Power BI Desktop se utiliza para abrir y actualizar el PBIX.

No se incluye `requirements.txt` ni un archivo que fije las versiones de las dependencias. La siguiente instalación se deriva de las importaciones y de los formatos utilizados; no constituye un entorno de versiones validado:

```bash
git clone https://github.com/GustavoGarciaPUCP/SupplyChain-Intelligence-Data-Pipeline.git
cd SupplyChain-Intelligence-Data-Pipeline
python -m venv .venv
```

Activar el entorno en Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

O en Linux/macOS:

```bash
source .venv/bin/activate
```

Instalar dependencias:

```bash
python -m pip install "pandas>=2.0" numpy sqlalchemy psycopg2-binary openpyxl python-dotenv
```

La limpieza utiliza `format='mixed'`, por lo que requiere una versión de pandas que admita esa opción. La versión mínima de Python y la combinación completa de versiones no están validadas en el repositorio.

### 2. Crear la base y configurar la contraseña

Los scripts de carga y alertas utilizan esta configuración fija:

| Parámetro | Valor |
| --- | --- |
| Servidor | `localhost` |
| Puerto | `5432` |
| Usuario | `postgres` |
| Base | `andina_foods_db` |
| Contraseña | Variable de entorno `DB_PASSWORD` |

Crear la base desde una sesión de PostgreSQL con permisos suficientes:

```sql
CREATE DATABASE andina_foods_db;
```

Copiar `.env.example` como `.env` en la raíz del proyecto y reemplazar el valor de ejemplo:

```dotenv
DB_PASSWORD=your_database_password_here
```

También puede definirse `DB_PASSWORD` en el entorno. Los demás parámetros no se leen desde `.env`; para cambiarlos hay que modificar `load_data.py` y `generate_alerts.py`.

La contraseña se interpola directamente en una URL de SQLAlchemy. Si contiene caracteres reservados de URL, la conexión puede requerir ajustar esa construcción o codificar correctamente el valor.

**Usar una base dedicada a esta demostración:** la carga ejecuta sentencias `DROP TABLE ... CASCADE` y elimina las vistas y tablas del proyecto antes de recrearlas.

### 3. Ejecutar el pipeline

Desde la raíz del repositorio:

```bash
python run_pipeline.py
```

Para ejecutar las etapas por separado, conservar este orden:

```bash
python src/ingestion/generate_mock_data.py
python src/cleaning/clean_data.py
python src/loading/load_data.py
python src/alerts/generate_alerts.py
```

El orquestador usa el mismo intérprete de Python con el que se inició y se detiene si un subproceso devuelve un código distinto de cero. Sin embargo, algunas rutas de error de carga y alertas solo registran el problema y retornan sin propagarlo como fallo del proceso. El mensaje final de éxito no basta para confirmar una carga completa.

### 4. Comprobar las salidas

Revisar los mensajes de consola, `data_quality.log` y los archivos generados:

| Carpeta | Archivos esperados al completar las etapas correspondientes |
| --- | --- |
| `data/raw/` | `products.csv`, `plants.csv`, `clients.csv`, `sales_data.csv`, `production_data.xlsx`. |
| `data/processed/` | `clean_products.csv`, `clean_plants.csv`, `clean_clients.csv`, `clean_sales.csv`, `clean_production.csv`, `business_alerts.csv`. |

Consultar la base para comprobar la carga y las vistas:

```sql
SELECT 'products' AS tabla, COUNT(*) AS filas FROM products
UNION ALL
SELECT 'plants', COUNT(*) FROM plants
UNION ALL
SELECT 'clients', COUNT(*) FROM clients
UNION ALL
SELECT 'sales', COUNT(*) FROM sales
UNION ALL
SELECT 'production', COUNT(*) FROM production;

SELECT *
FROM vw_monthly_sales_ranking
ORDER BY sales_month, revenue_rank
LIMIT 10;

SELECT *
FROM vw_plant_performance
ORDER BY production_month, plant_id, product_id
LIMIT 10;
```

Con los catálogos definidos en el generador, una carga completa debe contener cuatro productos, tres plantas y cuatro clientes. Las cantidades de ventas, producción y alertas varían entre ejecuciones porque no se fija una semilla aleatoria.

### 5. Abrir y actualizar Power BI

1. Abrir [`powerbi/SupplyChain_Dashboard.pbix`](./powerbi/SupplyChain_Dashboard.pbix) en Power BI Desktop.
2. Revisar la configuración de orígenes y credenciales de PostgreSQL para el entorno local.
3. Revisar el origen de `business_alerts` y, si corresponde, ajustar su ruta al CSV generado en `data/processed/business_alerts.csv`.
4. Actualizar los datos y comprobar los indicadores, filtros y tabla de alertas.

El README original describe una conexión con PostgreSQL y el PBIX contiene referencias a tablas `public` y a `business_alerts`. La inspección de su estructura visual no confirma el modo de conexión, las consultas de origen, todas las relaciones ni las fórmulas de sus medidas. La actualización completa debe verificarse en Power BI Desktop.

## Dashboard y resultados observables

![Dashboard de ventas, producción y alertas](./images/dashboard_preview.png)

El PBIX incluye la página **Rendimiento y Alertas**, con:

- Tarjetas de ingresos totales, unidades vendidas, tasa de defectos y alertas activas.
- Tendencia temporal de ingresos y comparación de defectos por planta.
- Filtros de producto, planta y periodo.
- Tabla de alertas con fecha, tipo, prioridad y descripción.
- Matriz de ingresos por periodo y producto.

Los entregables disponibles son el [archivo interactivo PBIX](./powerbi/SupplyChain_Dashboard.pbix) y el [reporte exportado en PDF](./docs/reporte_ejecutivo.pdf).

La imagen y el PDF muestran una captura guardada con selecciones de filtros. Sus cifras no son resultados fijos que deban repetirse al regenerar los datos. Además, el PDF muestra alertas de otros productos mientras el filtro visible selecciona Aceite Premium: esa captura no demuestra que el filtro de producto afecte también al monitor de alertas.

Los resultados comprobables en los archivos son la implementación del flujo, las transformaciones, las consultas SQL, las reglas de alertas y los componentes del reporte. No se documentan tiempos de ejecución medidos, pruebas de carga, ahorro económico ni mejoras porcentuales del negocio.

## Alcance de la verificación

Esta documentación se basa en la inspección de los scripts Python, SQL, configuración de ejemplo, estructura visual del PBIX y reporte PDF. No representa una ejecución validada del pipeline ni una actualización comprobada del dashboard.

No se incluyen datos operativos reales, un entorno de dependencias fijado ni pruebas automatizadas. Tampoco se puede confirmar únicamente con la captura que todos los filtros se propaguen correctamente a cada visual o que las cifras guardadas correspondan a una nueva ejecución.

## Mejoras futuras

Las siguientes propuestas amplían el proyecto; no forman parte de la implementación actual:

- Incorporar un archivo de dependencias con versiones verificadas e instrucciones de entorno reproducibles.
- Fijar semillas aleatorias para reproducir los conjuntos de prueba.
- Definir formatos de fecha explícitos y validar fechas ausentes, identificadores y cantidades antes de cargar.
- Validar la imputación de producción y registrar las filas descartadas o corregidas con su motivo.
- Externalizar servidor, puerto, usuario y base; construir la URL de conexión sin interpolar directamente la contraseña.
- Propagar errores de todas las etapas y validar las salidas antes de declarar éxito.
- Sustituir la reconstrucción destructiva por una estrategia de carga incremental si se necesita conservar historial.
- Evaluar combinaciones sin ventas o sin producción y documentar cómo deben tratarse.
- Añadir identificadores de producto y planta a las alertas, guardar su historial y revisar su relación con los filtros de Power BI.
- Incorporar pruebas de limpieza, integridad, límites de las reglas y agregaciones; verificar las medidas y relaciones del PBIX.
- Documentar y, si se necesita, automatizar la actualización del reporte y la programación del pipeline.
