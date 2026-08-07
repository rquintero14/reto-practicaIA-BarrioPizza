from pathlib import Path
import pandas as pd


# Ruta raíz del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "datos"


def cargar_datos():
    """
    Carga los cuatro archivos CSV utilizados por la aplicación.
    """

    ingredientes = pd.read_csv(DATA_DIR / "ingredientes.csv")
    consumo = pd.read_csv(DATA_DIR / "consumo_historico.csv")
    inventario = pd.read_csv(DATA_DIR / "inventario_actual.csv")
    ordenes = pd.read_csv(DATA_DIR / "orden_compra_semana.csv")

    return ingredientes, consumo, inventario, ordenes


if __name__ == "__main__":
    ingredientes, consumo, inventario, ordenes = cargar_datos()

    print("=== DATOS CARGADOS ===")
    print(f"Ingredientes: {len(ingredientes)} registros")
    print(f"Consumo histórico: {len(consumo)} registros")
    print(f"Inventario actual: {len(inventario)} registros")
    print(f"Órdenes de compra: {len(ordenes)} registros")

    print("\nColumnas encontradas:")
    print("Ingredientes:", ingredientes.columns.tolist())
    print("Consumo:", consumo.columns.tolist())
    print("Inventario:", inventario.columns.tolist())
    print("Órdenes:", ordenes.columns.tolist())