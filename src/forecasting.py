import numpy as np
import pandas as pd

from src.data_loader import cargar_datos


def calcular_consumo_proyectado(consumo):
    """
    Calcula el consumo esperado para la próxima semana utilizando
    un promedio ponderado.

    Las observaciones más recientes reciben mayor peso.
    """

    consumo = consumo.copy()

    # Aseguramos el orden cronológico dentro de cada combinación
    consumo = consumo.sort_values(
        by=["sucursal", "ingrediente_id", "semana"]
    )

    def promedio_ponderado(grupo):
        valores = grupo["consumo_unidad_base"].to_numpy()

        # 1, 2, 3... dependiendo de la cantidad de semanas disponibles
        pesos = np.arange(1, len(valores) + 1)

        return np.average(valores, weights=pesos)

    proyeccion = (
        consumo
        .groupby(["sucursal", "ingrediente_id"])
        .apply(promedio_ponderado, include_groups=False)
        .reset_index(name="consumo_proyectado")
    )

    return proyeccion


if __name__ == "__main__":
    ingredientes, consumo, inventario, ordenes = cargar_datos()

    proyeccion = calcular_consumo_proyectado(consumo)

    print("=== CONSUMO PROYECTADO ===")
    print(proyeccion.head(20).to_string(index=False))

    print("\nTotal de proyecciones:", len(proyeccion))