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
# CARGAR ESTILOS CSS
# ---------------------------------------------------------

with open("assets/style.css") as css:
    st.markdown(
        f"<style>{css.read()}</style>",
        unsafe_allow_html=True
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

st.title("Sistema Inteligente de Optimización de Compras")

st.caption(
    "Barrio Pizza • Predicción de consumo • Inventario • Recomendaciones automáticas"
)

st.write(
    """
Analiza automáticamente las órdenes de compra utilizando
el historial de consumo, el inventario disponible y una
proyección de demanda para recomendar la cantidad óptima
de compra por sucursal.
"""
)

st.divider()

# ==========================================================
# PESTAÑAS PRINCIPALES
# ==========================================================

tab_dashboard, tab_analisis, tab_ordenes = st.tabs(
    [
        "📊 Dashboard",
        "📈 Análisis",
        "📦 Orden recomendada"
    ]
)

with tab_dashboard:

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

    if "🔴 Crítica" in analisis["prioridad"].values:
        st.error(
            "🔴 Existen pedidos críticos que requieren corrección antes de realizar la compra."
        )

    elif "🟠 Alta" in analisis["prioridad"].values:
        st.warning(
            "🟠 Se detectaron pedidos con diferencias importantes."
        )

    elif "🟡 Media" in analisis["prioridad"].values:
        st.info(
            "🟡 Existen diferencias menores en algunas órdenes."
        )

    else:
        st.success(
            "🟢 TODAS LAS ÓRDENES SON CORRECTAS."
        )

    st.info(
        f"Se analizaron {len(analisis)} combinaciones de sucursal e ingrediente. "
        f"Se detectaron {total_alertas} alertas que requieren atención "
        f"y {desconocidos} registro(s) que requieren revisión manual."
    )

    # ---------------------------------------------------------
    # ALERTAS
    # ---------------------------------------------------------

    st.subheader("Alertas de compra")

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

    st.subheader("Distribución de alertas por sucursal")

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

with tab_analisis:

    # ---------------------------------------------------------
    # ANÁLISIS DETALLADO
    # ---------------------------------------------------------

    st.subheader("Análisis por ingrediente")

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

    # ---------------------------------------------------------
    # AGREGAMOS LA SEMANA PROYECTADA
    # ---------------------------------------------------------

    proyeccion = pd.DataFrame({
        "semana": ["S7 (Predicción)"],
        "consumo_unidad_base": [detalle["consumo_proyectado"]]
    })

    historico_grafica = pd.concat(
        [historico_detalle, proyeccion],
        ignore_index=True
    )

    fig_historico = px.line(
        historico_grafica,
        x="semana",
        y="consumo_unidad_base",
        markers=True,
        title=f"Consumo histórico y proyección — {ingrediente_detalle}"
    )

    fig_historico.update_layout(
        xaxis_title="Semana",
        yaxis_title=detalle["unidad_base"]
    )

    fig_historico.add_vline(
        x=5.5,
        line_dash="dash",
        line_color="orange"
    )

    fig_historico.add_annotation(
        x="S7 (Predicción)",
        y=detalle["consumo_proyectado"],
        text="Predicción",
        showarrow=True,
        arrowhead=2
    )

    st.plotly_chart(
        fig_historico,
        use_container_width=True
    )

    st.caption(
        "La semana S7 corresponde a la proyección calculada utilizando "
        "el promedio ponderado de las últimas seis semanas."
    )

with tab_ordenes:

    # ---------------------------------------------------------
    # ORDEN RECOMENDADA
    # ---------------------------------------------------------

    st.subheader("Orden de compra recomendada")

    sucursal_orden = st.selectbox(
        "Sucursal para generar la orden",
        sucursales,
        key="orden_sucursal"
    )

    orden_recomendada = (
        analisis[
            analisis["sucursal"] == sucursal_orden
        ]
        .copy()
    )

    correctos = (
        orden_recomendada["estado"] == "Correcto"
    ).sum()

    cambios = (
        orden_recomendada["estado"] != "Correcto"
    ).sum()

    total = len(orden_recomendada)

    st.markdown(f"### 📍 {sucursal_orden}")

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "✅ Correctos",
        int(correctos)
    )

    c2.metric(
        "⚠️ Requieren cambios",
        int(cambios)
    )

    c3.metric(
        "📦 Ingredientes analizados",
        total
    )

    mostrar_solo_cambios = st.checkbox(
        "Mostrar únicamente ingredientes que requieren cambios",
        value=True
    )

    if mostrar_solo_cambios:
        orden_recomendada = orden_recomendada[
            orden_recomendada["formatos_pedidos"]
            != orden_recomendada["formatos_recomendados"]
        ]

    orden_recomendada = orden_recomendada[
        [
            "nombre",
            "formatos_pedidos",
            "formatos_recomendados",
            "accion_recomendada"
        ]
    ]

    orden_recomendada.columns = [
        "Ingrediente",
        "Pedido actual",
        "Pedido recomendado",
        "Acción"
    ]

    st.dataframe(
        orden_recomendada,
        use_container_width=True,
        hide_index=True
    )

    csv = orden_recomendada.to_csv(index=False).encode("utf-8")

    st.download_button(
        "⬇ Descargar orden recomendada (CSV)",
        data=csv,
        file_name=f"orden_recomendada_{sucursal_orden}.csv",
        mime="text/csv"
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