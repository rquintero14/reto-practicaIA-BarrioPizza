import pandas as pd

from src.data_loader import cargar_datos


def validar_datos(ingredientes, consumo, inventario, ordenes):
    """
    Revisa la consistencia básica de los datos antes de realizar
    cualquier cálculo de recomendación de compra.
    """

    ids_catalogo = set(ingredientes["ingrediente_id"])

    # Ingredientes presentes en las órdenes pero inexistentes en el catálogo
    ingredientes_desconocidos = ordenes[
        ~ordenes["ingrediente_id"].isin(ids_catalogo)
    ].copy()

    # Ingredientes del catálogo que no aparecen en alguna orden.
    sucursales = inventario["sucursal"].unique()

    combinaciones_esperadas = pd.MultiIndex.from_product(
        [sucursales, ids_catalogo],
        names=["sucursal", "ingrediente_id"]
    ).to_frame(index=False)

    ordenes_catalogo = ordenes[
        ordenes["ingrediente_id"].isin(ids_catalogo)
    ][["sucursal", "ingrediente_id"]]

    faltantes_orden = combinaciones_esperadas.merge(
        ordenes_catalogo,
        on=["sucursal", "ingrediente_id"],
        how="left",
        indicator=True
    )

    faltantes_orden = faltantes_orden[
        faltantes_orden["_merge"] == "left_only"
    ].drop(columns="_merge")

    # Valores nulos
    nulos = {
        "ingredientes": int(ingredientes.isnull().sum().sum()),
        "consumo": int(consumo.isnull().sum().sum()),
        "inventario": int(inventario.isnull().sum().sum()),
        "ordenes": int(ordenes.isnull().sum().sum()),
    }

    return {
        "ingredientes_desconocidos": ingredientes_desconocidos,
        "faltantes_orden": faltantes_orden,
        "nulos": nulos,
    }


if __name__ == "__main__":
    ingredientes, consumo, inventario, ordenes = cargar_datos()

    resultado = validar_datos(
        ingredientes,
        consumo,
        inventario,
        ordenes
    )

    print("=== VALIDACIÓN DE DATOS ===")

    print("\n1. Valores nulos:")
    for archivo, cantidad in resultado["nulos"].items():
        print(f"   {archivo}: {cantidad}")

    print("\n2. Ingredientes desconocidos en órdenes:")
    if resultado["ingredientes_desconocidos"].empty:
        print("   Ninguno")
    else:
        print(
            resultado["ingredientes_desconocidos"].to_string(index=False)
        )

    print("\n3. Ingredientes sin registro en la orden:")
    if resultado["faltantes_orden"].empty:
        print("   Ninguno")
    else:
        print(
            resultado["faltantes_orden"].to_string(index=False)
        )