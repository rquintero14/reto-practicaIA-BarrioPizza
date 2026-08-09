import pandas as pd
from google import genai

SYSTEM_PROMPT = """
Sos un asistente que ayuda a la gerente de compras de Barrio Pizza a
entender las alertas de las órdenes de compra de la semana. Respondé
siempre en español, de forma breve, clara y accionable — como si le
hablaras a alguien que no tiene tiempo de leer tablas.

Reglas:
- Basate ÚNICAMENTE en los datos que te paso abajo. No inventes
  sucursales, ingredientes ni cifras que no estén en la tabla.
- Si la pregunta no se puede responder con estos datos, decilo
  claramente en vez de inventar una respuesta.
- Cuando sea útil, mencioná el estado (Correcto / Faltante /
  Sobrepedido / Olvidado), la prioridad y la acción recomendada.
"""


def _construir_contexto(analisis: pd.DataFrame, atipicas: pd.DataFrame) -> str:
    columnas = [
        "sucursal",
        "nombre",
        "proveedor",
        "formatos_pedidos",
        "formatos_recomendados",
        "diferencia_formatos",
        "estado",
        "prioridad",
        "accion_recomendada",
        "es_perecedero",
    ]

    tabla_alertas = analisis[columnas].to_csv(index=False)

    if atipicas.empty:
        tabla_atipicas = (
            "No se detectaron órdenes atípicas entre sucursales esta semana."
        )
    else:
        tabla_atipicas = atipicas[
            [
                "sucursal",
                "nombre",
                "proveedor",
                "participacion_pedido",
                "participacion_consumo",
                "diferencia_puntos",
            ]
        ].to_csv(index=False)

    return (
        "TABLA DE ANÁLISIS (una fila por sucursal e ingrediente):\n"
        f"{tabla_alertas}\n\n"
        "ÓRDENES ATÍPICAS ENTRE SUCURSALES (comparación entre pares):\n"
        f"{tabla_atipicas}"
    )


def preguntar_datos(
    pregunta: str,
    analisis: pd.DataFrame,
    atipicas: pd.DataFrame,
    api_key: str,
) -> str:
    """
    Responde una pregunta en español sobre las órdenes de compra,
    usando Gemini con el análisis ya calculado como contexto.
    """

    contexto = _construir_contexto(analisis, atipicas)

    prompt = (
        f"{SYSTEM_PROMPT}\n\n{contexto}\n\nPREGUNTA DE LA GERENTE:\n{pregunta}"
    )

    client = genai.Client(api_key=api_key)

    respuesta = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt,
    )

    return respuesta.text