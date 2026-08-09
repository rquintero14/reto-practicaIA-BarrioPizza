# 🍕 Sistema Inteligente de Optimización de Compras — Barrio Pizza

Herramienta que analiza automáticamente las órdenes de compra semanales de las sucursales de Barrio Pizza, comparándolas contra el consumo histórico y el inventario actual, para detectar pedidos de más, de menos o ingredientes olvidados — antes de que lleguen al proveedor.

> Reto técnico para la práctica de IA en Barrio Pizza. Repo original con el enunciado y los datos: https://github.com/soydelbarrio/reto-practicante-ia

**🔗 App en vivo:** _[pegar acá el link de Streamlit Cloud una vez desplegado]_
**🎥 Video explicativo:** _[pegar acá el link del video]_

---

## Qué hace

1. **Proyecta** el consumo de la próxima semana por sucursal e ingrediente, usando un promedio ponderado de las últimas 6 semanas (le da más peso a las semanas recientes).
2. Calcula la **necesidad real** = consumo proyectado − inventario actual (nunca negativa).
3. Convierte esa necesidad a **formatos de compra completos** (redondeando siempre hacia arriba, porque no se compran medios sacos).
4. **Compara** contra lo que cada sucursal pidió esta semana y genera alertas clasificadas en:
   - 🔴 **Olvidado** — el ingrediente ni siquiera apareció en la orden, pero hacía falta.
   - **Faltante** — se pidió menos de lo recomendado.
   - **Sobrepedido** — se pidió más de lo recomendado.
   - **Correcto** — coincide con la recomendación.
5. Asigna una **prioridad** (🔴 Crítica / 🟠 Alta / 🟡 Media) según el tamaño de la diferencia y si el ingrediente es perecedero — un faltante pequeño de algo perecedero se trata como urgente aunque la desviación numérica sea chica.
6. Muestra todo en un **dashboard** con 3 vistas: resumen de alertas, análisis por ingrediente con gráfica de histórico + proyección, y orden de compra recomendada descargable en CSV.

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

# 4. Correr la app
streamlit run app.py
```

La app se abre automáticamente en `http://localhost:8501`. Los datos se leen directamente de la carpeta `/datos` incluida en el repo.

### Scripts sueltos para revisar la lógica sin levantar el dashboard

```bash
python -m src.data_loader     # Verifica que los 4 CSV cargan bien
python -m src.recommendations # Muestra el cálculo de proyección y recomendación
python -m src.alerts          # Muestra el resumen de alertas y prioridades
python -m src.validator       # Muestra ingredientes desconocidos y datos faltantes
```

---

## Estructura del proyecto

```
├── app.py                    # Dashboard de Streamlit (3 tabs)
├── src/
│   ├── data_loader.py        # Carga los 4 CSV
│   ├── forecasting.py        # Proyección de consumo (promedio ponderado)
│   ├── recommendations.py    # Necesidad real, conversión a formatos, recomendación
│   ├── alerts.py             # Clasificación de estado, prioridad y acción recomendada
│   └── validator.py          # Detección de ingredientes desconocidos y datos incompletos
├── assets/style.css          # Estilos del dashboard
├── datos/                    # CSVs provistos por Barrio Pizza
└── requirements.txt
```

---

## Supuestos que hice

- **Proyección de consumo:** promedio ponderado de las últimas 6 semanas, dándole más peso a las semanas recientes, en vez de un promedio simple — así la herramienta reacciona más rápido a tendencias de crecimiento o caída en el consumo.
- **Redondeo:** la necesidad en unidad base se convierte a formatos de compra redondeando siempre hacia arriba (`np.ceil`), porque los proveedores solo venden formatos completos. Un excedente menor a un formato completo no se trata como sobrepedido.
- **Necesidad negativa:** si el inventario ya cubre la proyección, la necesidad se fija en 0 en vez de un valor negativo (no tiene sentido "necesidad negativa" de compra).
- **Ingredientes no pedidos:** si una sucursal no incluye un ingrediente en su orden, se asume que pidió 0 formatos. Si la recomendación para ese ingrediente es mayor a 0, se marca como "Olvidado" con prioridad crítica.
- **Ingredientes desconocidos:** si una orden incluye un `ingrediente_id` que no existe en el catálogo, no se calcula una recomendación (no hay forma de saber su formato de compra ni si es perecedero) — se lista aparte en la sección "Revisión manual" del dashboard en vez de descartarse silenciosamente.
- **Prioridad y perecederos:** un faltante se marca como prioridad Alta si la desviación es de 3 o más formatos, **o** si el ingrediente es perecedero (aunque la desviación sea de 1 formato) — porque quedarse corto de un perecedero es más urgente. Un sobrepedido solo sube a Alta si es perecedero **y** la desviación es de 3 o más formatos, ya que sobrepedir algo no perecedero es un problema menor (solo capital inmovilizado, no desperdicio).
- **Combinación sucursal + inventario como base del análisis:** el análisis parte de `inventario_actual.csv`, asumiendo que toda combinación sucursal-ingrediente relevante tiene un registro de inventario. Si una sucursal pidiera un ingrediente del catálogo sin registro de inventario para esa sucursal, quedaría fuera del análisis — no se detectó este caso en los datos provistos, pero se deja documentado como una limitación conocida.

---

## Cómo usé IA para resolverlo

_[Completar acá con el detalle real: qué partes armaste con ayuda de IA (ej. estructura del proyecto, lógica de alertas/prioridad, CSS del dashboard, debugging), qué le pediste explícitamente, y qué decisiones de negocio tomaste vos (ej. las reglas de prioridad para perecederos) en vez de aceptar la primera sugerencia.]_

---

## Cómo llevar esto a producción con Odoo

Si tuviera que integrarlo con un sistema como Odoo:

- **Origen de datos:** reemplazar la lectura de los CSV en `data_loader.py` por llamadas al API XML-RPC/JSON-RPC de Odoo (módulos de Inventario y Compras) para traer stock actual, histórico de movimientos de inventario y órdenes de compra en tiempo real.
- **Catálogo de ingredientes:** mapear `ingredientes.csv` a los productos y sus unidades de medida/UoM configuradas en Odoo (Odoo ya maneja conversiones de unidad de compra vs. unidad de consumo de forma nativa).
- **Alertas automáticas:** en vez de que la gerente entre al dashboard, se podría correr `alerts.py` como un cron job (Odoo Scheduled Actions) que dispare notificaciones o cree actividades/tareas en Odoo cuando detecte una orden con alerta crítica, antes de que la orden de compra se confirme.
- **Cierre del loop:** las órdenes recomendadas (el CSV que hoy se descarga manualmente) podrían escribirse directamente como líneas de una orden de compra en el módulo de Compras de Odoo vía API, para que la gerente solo tenga que aprobar en vez de re-tipear.

---

## Cómo lo evalúan (referencia del reto)

Funcionalidad y correcta detección de problemas · manejo de unidades y datos incompletos · uso de IA · razonamiento · claridad de la explicación.