from src.data_loader import cargar_datos
from src.recommendations import generar_recomendaciones


def detectar_ordenes_atipicas(analisis, consumo, umbral_puntos=20):
    """
    Detecta sucursales cuya participación en el pedido semanal de un
    ingrediente se aleja mucho de su participación histórica de consumo
    de ese mismo ingrediente, comparándola contra el resto de las sucursales.

    Ejemplo: si una sucursal históricamente representa el 25% del consumo
    total de mozzarella entre las 4 sucursales, pero esta semana su pedido
    de mozzarella es el 70% del pedido total, es una orden atípica —
    independientemente de qué tan grande sea esa sucursal en general.
    """

    # Participación histórica de consumo por sucursal, para cada ingrediente.
    consumo_total = (
        consumo.groupby(["sucursal", "ingrediente_id"])["consumo_unidad_base"]
        .sum()
        .reset_index(name="consumo_historico_total")
    )

    consumo_total["participacion_consumo"] = (
        consumo_total.groupby("ingrediente_id")["consumo_historico_total"]
        .transform(lambda x: x / x.sum() if x.sum() > 0 else 0)
    )

    # Participación del pedido de esta semana por sucursal, para cada ingrediente.
    pedidos = analisis[
        [
            "sucursal",
            "ingrediente_id",
            "nombre",
            "proveedor",
            "formatos_pedidos",
            "unidad_base_por_formato",
        ]
    ].copy()

    pedidos["pedido_unidad_base"] = (
        pedidos["formatos_pedidos"] * pedidos["unidad_base_por_formato"]
    )

    pedidos["participacion_pedido"] = (
        pedidos.groupby("ingrediente_id")["pedido_unidad_base"]
        .transform(lambda x: x / x.sum() if x.sum() > 0 else 0)
    )

    # Unimos ambas participaciones para compararlas.
    comparacion = pedidos.merge(
        consumo_total[["sucursal", "ingrediente_id", "participacion_consumo"]],
        on=["sucursal", "ingrediente_id"],
        how="left",
    )

    # Si no hay historial para esa combinación, asumimos participación 0
    # (cualquier pedido ahí ya sería, de por sí, una desviación total).
    comparacion["participacion_consumo"] = (
        comparacion["participacion_consumo"].fillna(0)
    )

    comparacion["diferencia_puntos"] = (
        comparacion["participacion_pedido"] - comparacion["participacion_consumo"]
    ) * 100

    # Solo nos interesan sucursales que sí pidieron algo, y cuya desviación
    # supere el umbral definido (en puntos porcentuales).
    atipicas = comparacion[
        (comparacion["pedido_unidad_base"] > 0)
        & (comparacion["diferencia_puntos"].abs() >= umbral_puntos)
    ].copy()

    atipicas["participacion_pedido"] = (
        atipicas["participacion_pedido"] * 100
    ).round(1)
    atipicas["participacion_consumo"] = (
        atipicas["participacion_consumo"] * 100
    ).round(1)
    atipicas["diferencia_puntos"] = atipicas["diferencia_puntos"].round(1)

    return atipicas.sort_values("diferencia_puntos", ascending=False)


if __name__ == "__main__":
    ingredientes, consumo, inventario, ordenes = cargar_datos()

    analisis = generar_recomendaciones(ingredientes, consumo, inventario, ordenes)

    resultado = detectar_ordenes_atipicas(analisis, consumo)

    print("=== ÓRDENES ATÍPICAS ENTRE SUCURSALES ===")

    if resultado.empty:
        print("No se detectaron órdenes atípicas con el umbral actual.")
    else:
        columnas = [
            "sucursal",
            "nombre",
            "proveedor",
            "participacion_pedido",
            "participacion_consumo",
            "diferencia_puntos",
        ]
        print(resultado[columnas].to_string(index=False))