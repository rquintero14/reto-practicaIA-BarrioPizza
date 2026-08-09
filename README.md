# 🍕 Sistema Inteligente de Optimización de Compras — Barrio Pizza

Herramienta que analiza automáticamente las órdenes de compra semanales de las sucursales de Barrio Pizza, comparándolas contra el consumo histórico y el inventario actual, para detectar pedidos de más, de menos o ingredientes olvidados — antes de que lleguen al proveedor.

> Reto técnico para la práctica de IA en Barrio Pizza. Repo original con el enunciado y los datos: https://github.com/soydelbarrio/reto-practicante-ia

**🔗 App en vivo:** _[pegar acá el link de Streamlit Cloud una vez desplegado]_
**🎥 Video explicativo:** _[pegar acá el link del video]_

---

## Qué hace

### Lo mínimo pedido por el reto

1. **Proyecta** el consumo de la próxima semana por sucursal e ingrediente, usando un promedio ponderado de las últimas 6 semanas (le da más peso a las semanas recientes).
2. Calcula la **necesidad real** = consumo proyectado − inventario actual (nunca negativa).
3. Convierte esa necesidad a **formatos de compra completos** (redondeando siempre hacia arriba, porque no se compran medios sacos).
4. **Compara** contra lo que cada sucursal pidió esta semana y genera alertas clasificadas en:
   - 🔴 **Olvidado** — el ingrediente ni siquiera apareció en la orden, pero hacía falta.
   - **Faltante** — se pidió menos de lo recomendado.
   - **Sobrepedido** — se pidió más de lo recomendado.
   - **Correcto** — coincide con la recomendación.
5. Asigna una **prioridad** (🔴 Crítica / 🟠 Alta / 🟡 Media) según el tamaño de la diferencia y si el ingrediente es perecedero.
6. Muestra todo en un **dashboard** con alertas de un vistazo y gráfica de distribución por sucursal.

### Extras agregados (secciones "para destacar" del reto)

- **📦 Pedido corregido por proveedor** — la orden recomendada, agrupada por proveedor, con un CSV descargable por cada uno, lista para reenviar directamente.
- **🔍 Detección de órdenes atípicas entre sucursales** — compara qué % del pedido semanal de cada ingrediente le corresponde a cada sucursal, contra qué % representa históricamente en el consumo de ese mismo ingrediente entre las 4 sucursales. Detecta acaparamiento desproporcionado sin mezclar unidades distintas (ver `src/anomalies.py`).
- **✏️ Editar orden con alertas en vivo** — una tabla editable donde se pueden simular cambios en las cantidades pedidas y ver al instante cómo se actualizarían las alertas, sin tocar los archivos originales. Es la aproximación a "la visión final" que describe el reto.
- **💬 Chat con los datos** — un chat en lenguaje natural (Gemini API) donde se le puede preguntar directamente al análisis de la semana (ej. *"¿qué sucursal tiene la alerta más crítica?"*), sin tener que leer tablas.
- **Identidad visual propia** — el dashboard tiene una paleta y tipografía diseñadas específicamente para este proyecto (ver `assets/style.css`), en vez del tema por defecto de Streamlit.

---

## Cómo correrlo localmente

```bash
# 1. Clonar el repo
git clone https://github.com/rquintero14/reto-practicaIA-BarrioPizza.git
cd reto-practicaIA-BarrioPizza

# 2. Crear un entorno virtual (opcional pero recomendado)
python -m venv .venv
.venv\Scripts\activate      # Windows
source .venv/bin/activate   # Mac/Linux

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar la API key de Gemini (necesaria para el tab "Chat con los datos")
```

Para el chat con los datos, creá el archivo `.streamlit/secrets.toml` en la raíz del proyecto:
```toml
GEMINI_API_KEY = "tu-key-de-Google-AI-Studio"
```
La key se saca gratis, sin tarjeta, en [aistudio.google.com](https://aistudio.google.com) → "Get API key". Sin esta key, el resto del dashboard funciona igual — solo el tab de chat muestra un aviso en vez de responder.

```bash
# 5. Correr la app
streamlit run app.py
```

La app se abre automáticamente en `http://localhost:8501`. Los datos se leen directamente de la carpeta `/datos` incluida en el repo.

### Scripts sueltos para revisar la lógica sin levantar el dashboard

```bash
python -m src.data_loader     # Verifica que los 4 CSV cargan bien
python -m src.recommendations # Muestra el cálculo de proyección y recomendación
python -m src.alerts          # Muestra el resumen de alertas y prioridades
python -m src.validator       # Muestra ingredientes desconocidos y datos faltantes
python -m src.anomalies       # Muestra las órdenes atípicas entre sucursales
```

---

## Estructura del proyecto

```
├── app.py                    # Dashboard de Streamlit (4 tabs)
├── src/
│   ├── data_loader.py        # Carga los 4 CSV
│   ├── forecasting.py        # Proyección de consumo (promedio ponderado)
│   ├── recommendations.py    # Necesidad real, conversión a formatos, recomendación
│   ├── alerts.py             # Clasificación de estado, prioridad y acción recomendada
│   ├── validator.py          # Detección de ingredientes desconocidos y datos incompletos
│   ├── anomalies.py          # Detección de órdenes atípicas entre sucursales
│   └── chat.py                # Chat con los datos (Gemini API)
├── assets/style.css          # Identidad visual del dashboard
├── datos/                    # CSVs provistos por Barrio Pizza
├── .streamlit/secrets.toml   # API key de Gemini (NO se sube a git)
└── requirements.txt
```

---

## Supuestos que hice

**Sobre el cálculo de la recomendación:**
- **Proyección de consumo:** promedio ponderado de las últimas 6 semanas, dándole más peso a las semanas recientes, en vez de un promedio simple.
- **Redondeo:** la necesidad en unidad base se convierte a formatos de compra redondeando siempre hacia arriba (`np.ceil`), porque los proveedores solo venden formatos completos.
- **Necesidad negativa:** si el inventario ya cubre la proyección, la necesidad se fija en 0.
- **Ingredientes no pedidos:** si una sucursal no incluye un ingrediente en su orden, se asume que pidió 0 formatos. Si la recomendación es mayor a 0, se marca "Olvidado" con prioridad crítica.
- **Ingredientes desconocidos:** si una orden incluye un `ingrediente_id` que no existe en el catálogo, no se calcula recomendación — se lista aparte en "Revisión manual" en vez de descartarse silenciosamente.
- **Prioridad y perecederos:** un faltante es prioridad Alta si la desviación es ≥3 formatos **o** si el ingrediente es perecedero. Un sobrepedido solo sube a Alta si es perecedero **y** la desviación es ≥3 formatos.
- **Base del análisis:** el análisis parte de `inventario_actual.csv`, asumiendo que toda combinación sucursal-ingrediente relevante tiene registro de inventario. No se detectó ningún caso de orden sin registro de inventario en los datos provistos, pero se deja documentado como limitación conocida.

**Sobre los extras:**
- **Órdenes atípicas:** para comparar sucursales de distinto tamaño de forma justa, se normaliza por ingrediente (participación del pedido vs. participación histórica de consumo, ambas como % del total entre las 4 sucursales) en vez de comparar cantidades absolutas o mezclar unidades distintas entre ingredientes. El umbral por defecto es 20 puntos porcentuales de desviación.
- **Editar orden en vivo:** los cambios hechos en esa tabla son una simulación aislada — no modifican `analisis`, el Dashboard ni la "Orden recomendada" oficial. Es una decisión deliberada para que la gerente pueda explorar "qué pasaría si..." sin que eso se confunda con la orden real ya confirmada.
- **Chat con los datos:** el modelo solo recibe como contexto la tabla de análisis y la de órdenes atípicas ya calculadas (no los CSV crudos), y tiene instrucción explícita de no inventar cifras que no estén ahí. Si se le pregunta algo que los datos no permiten responder (ej. costos, ya que no hay precios en los CSV), lo dice en vez de inventar un número.

---

## Cómo usé IA para resolverlo

_[Completar acá con el detalle real: qué partes armaste con ayuda de IA (ej. estructura del proyecto, lógica de alertas/prioridad, el módulo de órdenes atípicas, la integración con Gemini, el CSS), qué le pediste explícitamente, y qué decisiones de negocio tomaste vos en vez de aceptar la primera sugerencia (ej. las reglas de prioridad para perecederos, o la normalización por participación en vez de valores absolutos para detectar órdenes atípicas).]_

---

## Cómo llevar esto a producción con Odoo

Si tuviera que integrarlo con un sistema como Odoo:

- **Origen de datos:** reemplazar la lectura de los CSV en `data_loader.py` por llamadas al API XML-RPC/JSON-RPC de Odoo (módulos de Inventario y Compras) para traer stock actual, histórico de movimientos de inventario y órdenes de compra en tiempo real.
- **Catálogo de ingredientes:** mapear `ingredientes.csv` a los productos y sus unidades de medida/UoM configuradas en Odoo.
- **Alertas automáticas:** correr `alerts.py` y `anomalies.py` como un cron job (Odoo Scheduled Actions) que dispare notificaciones o tareas en Odoo cuando detecte una alerta crítica, antes de que la orden se confirme.
- **Cierre del loop:** las órdenes recomendadas (hoy un CSV manual) podrían escribirse directamente como líneas de una orden de compra en el módulo de Compras de Odoo vía API.
- **Chat con los datos:** el mismo patrón de `chat.py` podría exponerse como un asistente dentro de Odoo, con el contexto armado a partir de las tablas reales del ERP en vez de los CSV de prueba.

---

## Cómo lo evalúan (referencia del reto)

Funcionalidad y correcta detección de problemas · manejo de unidades y datos incompletos · uso de IA · razonamiento · claridad de la explicación.