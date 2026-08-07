import streamlit as st
import pandas as pd
import plotly.express as px

from src.data_loader import cargar_datos
from src.alerts import generar_alertas
from src.validator import validar_datos


# ---------------------------------------------------------
# CONFIGURACIÓN
# ---------------------------------------------------------

st.set_page_config(
    page_title="Barrio Pizza | Control de Compras",
    page_icon="🍕",
    layout="wide"
)


# ---------------------------------------------------------
# CARGA Y PROCESAMIENTO
# ---------------------------------------------------------

@st.cache_data
def obtener_datos():
    ingredientes, consumo, inventario, ordenes = cargar_datos()

    analisis = generar_alertas(
        ingredientes,
        consumo,
        inventario,
        ordenes
    )

    validacion = validar_datos(
        ingredientes,
        consumo,
        inventario,
        ordenes
    )

    return (
        ingredientes,
        consumo,
        inventario,
        ordenes,
        analisis,
        validacion
    )


(
    ingredientes,
    consumo,
    inventario,
    ordenes,
    analisis,
    validacion
) = obtener_datos()


# ---------------------------------------------------------
# ENCABEZADO
# ---------------------------------------------------------

st.title("🍕 Control Inteligente de Compras")
st.caption(
    "Análisis semanal de órdenes de compra — Barrio Pizza"
)

st.divider()


# ---------------------------------------------------------
# MÉTRICAS
# ---------------------------------------------------------

alertas = analisis[
    analisis["estado"].isin(
        ["Faltante", "Sobrepedido", "Olvidado"]
    )
]

total_alertas = len(alertas)

faltantes = (analisis["estado"] == "Faltante").sum()
sobrepedidos = (analisis["estado"] == "Sobrepedido").sum()
olvidados = (analisis["estado"] == "Olvidado").sum()

desconocidos = len(
    validacion["ingredientes_desconocidos"]
)

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric(
    "Alertas",
    total_alertas
)

col2.metric(
    "Faltantes",
    int(faltantes)
)

col3.metric(
    "Sobrepedidos",
    int(sobrepedidos)
)

col4.metric(
    "Olvidados",
    int(olvidados)
)

col5.metric(
    "Revisión manual",
    desconocidos
)

st.info(
    f"Se analizaron {len(analisis)} combinaciones de sucursal e ingrediente. "
    f"Se detectaron {total_alertas} alertas que requieren atención "
    f"y {desconocidos} registro(s) que requieren revisión manual."
)

# ---------------------------------------------------------
# ALERTAS
# ---------------------------------------------------------

st.subheader("🚨 Alertas de compra")

col_filtro1, col_filtro2 = st.columns(2)

sucursales = sorted(
    analisis["sucursal"].unique()
)

with col_filtro1:
    sucursal_seleccionada = st.selectbox(
        "Sucursal",
        ["Todas"] + sucursales
    )

with col_filtro2:
    estado_seleccionado = st.selectbox(
        "Tipo de alerta",
        [
            "Todas",
            "Faltante",
            "Sobrepedido",
            "Olvidado"
        ]
    )


alertas_filtradas = alertas.copy()

if sucursal_seleccionada != "Todas":
    alertas_filtradas = alertas_filtradas[
        alertas_filtradas["sucursal"]
        == sucursal_seleccionada
    ]

if estado_seleccionado != "Todas":
    alertas_filtradas = alertas_filtradas[
        alertas_filtradas["estado"]
        == estado_seleccionado
    ]

# Ordenamos las alertas para mostrar primero las más importantes.
orden_prioridad = {
    "🔴 Crítica": 1,
    "🟠 Alta": 2,
    "🟡 Media": 3
}

alertas_filtradas["orden_prioridad"] = (
    alertas_filtradas["prioridad"]
    .map(orden_prioridad)
    .fillna(4)
)

alertas_filtradas = alertas_filtradas.sort_values(
    by=["orden_prioridad", "sucursal", "nombre"]
)


columnas_alertas = [
    "sucursal",
    "nombre",
    "formatos_pedidos",
    "formatos_recomendados",
    "estado",
    "prioridad",
    "accion_recomendada",
    "es_perecedero",
]

st.dataframe(
    alertas_filtradas[columnas_alertas],
    use_container_width=True,
    hide_index=True,
    column_config={
        "sucursal": "Sucursal",
        "nombre": "Ingrediente",
        "formatos_pedidos": st.column_config.NumberColumn(
            "Pedido",
            format="%d"
        ),
        "formatos_recomendados": st.column_config.NumberColumn(
            "Recomendado",
            format="%d"
        ),
        "estado": "Estado",
        "prioridad": st.column_config.TextColumn(
            "Prioridad",
            help="Nivel de atención recomendado para esta alerta"
        ),
        "accion_recomendada": st.column_config.TextColumn(
            "Acción recomendada",
            width="large"
        ),
        "es_perecedero": "Perecedero"
    }
)


# ---------------------------------------------------------
# ALERTAS POR SUCURSAL
# ---------------------------------------------------------

st.subheader("📊 Alertas por sucursal")

alertas_por_sucursal = (
    alertas
    .groupby(["sucursal", "estado"])
    .size()
    .reset_index(name="cantidad")
)

fig = px.bar(
    alertas_por_sucursal,
    x="sucursal",
    y="cantidad",
    color="estado",
    text="cantidad",
    barmode="stack",
    labels={
        "sucursal": "Sucursal",
        "cantidad": "Cantidad de alertas",
        "estado": "Tipo de alerta"
    }
)

fig.update_layout(
    xaxis_title="",
    yaxis_title="Cantidad de alertas",
    legend_title="Tipo de alerta"
)

st.plotly_chart(
    fig,
    use_container_width=True
)


# ---------------------------------------------------------
# ANÁLISIS DETALLADO
# ---------------------------------------------------------

st.subheader("🔎 Análisis por ingrediente")

col_a, col_b = st.columns(2)

with col_a:
    sucursal_detalle = st.selectbox(
        "Selecciona una sucursal",
        sucursales,
        key="detalle_sucursal"
    )

ingredientes_sucursal = (
    analisis[
        analisis["sucursal"] == sucursal_detalle
    ]
    .sort_values("nombre")
)

with col_b:
    ingrediente_detalle = st.selectbox(
        "Selecciona un ingrediente",
        ingredientes_sucursal["nombre"].tolist()
    )


detalle = ingredientes_sucursal[
    ingredientes_sucursal["nombre"]
    == ingrediente_detalle
].iloc[0]


col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Consumo proyectado",
    f'{detalle["consumo_proyectado"]:.2f} '
    f'{detalle["unidad_base"]}'
)

col2.metric(
    "Inventario actual",
    f'{detalle["stock_actual_unidad_base"]:.2f} '
    f'{detalle["unidad_base"]}'
)

col3.metric(
    "Pedido",
    f'{detalle["formatos_pedidos"]} formatos'
)

col4.metric(
    "Recomendado",
    f'{detalle["formatos_recomendados"]} formatos'
)


# ---------------------------------------------------------
# HISTÓRICO DEL INGREDIENTE
# ---------------------------------------------------------

historico_detalle = consumo[
    (consumo["sucursal"] == sucursal_detalle)
    &
    (
        consumo["ingrediente_id"]
        == detalle["ingrediente_id"]
    )
].sort_values("semana")


fig_historico = px.line(
    historico_detalle,
    x="semana",
    y="consumo_unidad_base",
    markers=True,
    title=(
        f"Consumo histórico — "
        f"{ingrediente_detalle}"
    )
)

fig_historico.update_layout(
    xaxis_title="Semana",
    yaxis_title=detalle["unidad_base"]
)

st.plotly_chart(
    fig_historico,
    use_container_width=True
)


# ---------------------------------------------------------
# DATOS QUE REQUIEREN REVISIÓN
# ---------------------------------------------------------

st.subheader("⚠️ Datos que requieren revisión manual")

ingredientes_desconocidos = (
    validacion["ingredientes_desconocidos"]
)

if ingredientes_desconocidos.empty:

    st.success(
        "No se encontraron registros desconocidos."
    )

else:

    st.warning(
        "Estos ingredientes aparecen en una orden de compra "
        "pero no existen en el catálogo, por lo que el sistema "
        "no puede calcular una recomendación confiable."
    )

    st.dataframe(
        ingredientes_desconocidos,
        use_container_width=True,
        hide_index=True
    )


# ---------------------------------------------------------
# EXPLICACIÓN
# ---------------------------------------------------------

with st.expander("ℹ️ ¿Cómo se calcula la recomendación?"):

    st.markdown(
        """
        **1. Proyección de consumo**

        Se utiliza un promedio ponderado de las últimas seis
        semanas, dando mayor importancia al consumo reciente.

        **2. Necesidad de compra**

        `consumo proyectado - inventario actual`

        Si el resultado es negativo, la necesidad se considera 0.

        **3. Conversión a formatos**

        La necesidad se divide entre las unidades que contiene
        cada formato de compra.

        El resultado se redondea hacia arriba porque los
        proveedores venden formatos completos.

        **4. Comparación**

        Finalmente se compara la cantidad recomendada contra
        la orden enviada por la sucursal.
        """
    )