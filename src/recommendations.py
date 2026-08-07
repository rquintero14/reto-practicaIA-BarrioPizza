import numpy as np
import pandas as pd

from src.data_loader import cargar_datos
from src.forecasting import calcular_consumo_proyectado


def generar_recomendaciones(
    ingredientes,
    consumo,
    inventario,
    ordenes
):
    """
    Genera la cantidad recomendada de formatos de compra
    para cada sucursal e ingrediente.
    """

    proyeccion = calcular_consumo_proyectado(consumo)

    # Partimos del inventario porque contiene las combinaciones válidas
    # sucursal + ingrediente.
    analisis = inventario.merge(
        proyeccion,
        on=["sucursal", "ingrediente_id"],
        how="left"
    )

    # Agregamos información del catálogo.
    analisis = analisis.merge(
        ingredientes,
        on="ingrediente_id",
        how="left"
    )

    # Necesidad real después de considerar inventario.
    analisis["necesidad_unidad_base"] = (
        analisis["consumo_proyectado"]
        - analisis["stock_actual_unidad_base"]
    ).clip(lower=0)

    # Convertimos la necesidad desde unidades base
    # hacia formatos completos de compra.
    analisis["formatos_recomendados"] = np.ceil(
        analisis["necesidad_unidad_base"]
        / analisis["unidad_base_por_formato"]
    ).astype(int)

    # Solo utilizamos órdenes de ingredientes válidos del catálogo.
    ordenes_validas = ordenes[
        ordenes["ingrediente_id"].isin(
            ingredientes["ingrediente_id"]
        )
    ].copy()

    analisis = analisis.merge(
        ordenes_validas[
            ["sucursal", "ingrediente_id", "cantidad_formatos"]
        ],
        on=["sucursal", "ingrediente_id"],
        how="left"
    )

    # Guardamos si el ingrediente realmente apareció en la orden.
    analisis["incluido_en_orden"] = (
        analisis["cantidad_formatos"].notna()
    )

    # Para poder comparar, una ausencia equivale a cero formatos solicitados.
    analisis["formatos_pedidos"] = (
        analisis["cantidad_formatos"]
        .fillna(0)
        .astype(int)
    )

    # Diferencia positiva = hacen falta formatos.
    # Diferencia negativa = se pidieron formatos adicionales.
    analisis["diferencia_formatos"] = (
        analisis["formatos_recomendados"]
        - analisis["formatos_pedidos"]
    )

    return analisis


if __name__ == "__main__":
    ingredientes, consumo, inventario, ordenes = cargar_datos()

    resultado = generar_recomendaciones(
        ingredientes,
        consumo,
        inventario,
        ordenes
    )

    columnas = [
        "sucursal",
        "nombre",
        "consumo_proyectado",
        "stock_actual_unidad_base",
        "necesidad_unidad_base",
        "unidad_base_por_formato",
        "formatos_recomendados",
        "formatos_pedidos",
        "diferencia_formatos",
    ]

    print("=== RECOMENDACIONES DE COMPRA ===")

    print(
        resultado[columnas]
        .head(30)
        .to_string(index=False)
    )

    print("\nTotal analizado:", len(resultado))
