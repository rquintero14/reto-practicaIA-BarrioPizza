from src.data_loader import cargar_datos
from src.recommendations import generar_recomendaciones
from src.validator import validar_datos

def clasificar_estado(fila):
    """
    Clasifica la orden de compra comparando los formatos solicitados
    contra los formatos recomendados.
    """

    recomendado = fila["formatos_recomendados"]
    pedido = fila["formatos_pedidos"]
    incluido = fila["incluido_en_orden"]

    # Necesitaba comprar, pero el ingrediente no apareció en la orden.
    if not incluido and recomendado > 0:
        return "Olvidado"

    # No necesitaba comprar y tampoco lo pidió.
    if not incluido and recomendado == 0:
        return "Sin compra necesaria"

    if pedido < recomendado:
        return "Faltante"

    if pedido > recomendado:
        return "Sobrepedido"

    return "Correcto"

def calcular_prioridad(fila):
    """
    Asigna una prioridad a cada alerta considerando el tipo de problema,
    la magnitud de la diferencia y si el ingrediente es perecedero.
    """

    estado = fila["estado"]
    desviacion = fila["desviacion_formatos"]
    perecedero = fila["es_perecedero"] == "Si"

    if estado == "Olvidado":
        return "🔴 Crítica"

    if estado == "Faltante":
        if desviacion >= 3 or perecedero:
            return "🟠 Alta"
        return "🟡 Media"

    if estado == "Sobrepedido":
        if perecedero and desviacion >= 3:
            return "🟠 Alta"
        return "🟡 Media"

    return "🟢 Sin alerta"


def generar_accion(fila):
    """
    Genera una recomendación concreta para la gerente de compras.
    """

    estado = fila["estado"]
    diferencia = fila["diferencia_formatos"]

    if estado == "Olvidado":
        return f"➕ Agregar {diferencia} formatos a la orden"

    if estado == "Faltante":
        return f"➕ Agregar {diferencia} formatos"

    if estado == "Sobrepedido":
        return f"➖ Reducir {abs(diferencia)} formatos"

    if estado == "Correcto":
        return "✅ Mantener pedido"

    return "No requiere compra"

def generar_alertas(
    ingredientes,
    consumo,
    inventario,
    ordenes
):
    analisis = generar_recomendaciones(
        ingredientes,
        consumo,
        inventario,
        ordenes
    )

    analisis["estado"] = analisis.apply(
        clasificar_estado,
        axis=1
    )

    # Magnitud de la diferencia para facilitar la priorización.
    analisis["desviacion_formatos"] = (
        analisis["formatos_pedidos"]
        - analisis["formatos_recomendados"]
    ).abs()

    analisis["prioridad"] = analisis.apply(
    calcular_prioridad,
    axis=1
    )

    analisis["accion_recomendada"] = analisis.apply(
        generar_accion,
        axis=1
    )

    return analisis


if __name__ == "__main__":
    ingredientes, consumo, inventario, ordenes = cargar_datos()

    resultado = generar_alertas(
        ingredientes,
        consumo,
        inventario,
        ordenes
    )

    print("=== RESUMEN DE ÓRDENES ===")

    resumen = resultado["estado"].value_counts()

    print(resumen.to_string())

    print("\n=== ALERTAS DETECTADAS ===")

    alertas = resultado[
        resultado["estado"].isin(
            ["Olvidado", "Faltante", "Sobrepedido"]
        )
    ]

    columnas = [
        "sucursal",
        "nombre",
        "formatos_pedidos",
        "formatos_recomendados",
        "diferencia_formatos",
        "estado",
        "prioridad",
        "accion_recomendada",
        "es_perecedero",
    ]

    print(
        alertas[columnas]
        .sort_values(
            ["sucursal", "estado", "nombre"]
        )
        .to_string(index=False)
    )

    # También mostramos problemas estructurales del dataset.
    validacion = validar_datos(
        ingredientes,
        consumo,
        inventario,
        ordenes
    )

    desconocidos = validacion["ingredientes_desconocidos"]

    print("\n=== REVISIÓN MANUAL ===")

    if desconocidos.empty:
        print("No hay ingredientes desconocidos.")
    else:
        print(
            desconocidos.to_string(index=False)
        )   