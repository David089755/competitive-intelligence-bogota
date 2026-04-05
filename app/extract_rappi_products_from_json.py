"""
Este script lee el JSON capturado de un restaurante de Rappi
y extrae productos + precios en formato tabular.

Entrada:
- output/debug_menu_json_after/1_.json

Salida:
- output/rappi_products_extracted.csv

Qué extrae:
- datos de tienda
- delivery fee
- ETA
- corridor/categoría
- nombre del producto
- precio
- precio real
"""

import json
from pathlib import Path
import pandas as pd


# Archivo fuente: el JSON de detalle de tienda que ya capturaste
INPUT_JSON_PATH = Path("output/debug_menu_json_after/1_.json")

# Archivo de salida: CSV limpio
OUTPUT_CSV_PATH = Path("output/rappi_products_extracted.csv")


def load_json(path: Path) -> dict:
    """
    Carga el archivo JSON del restaurante.
    """
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_products(data: dict) -> list[dict]:
    """
    Recorre el JSON y devuelve una lista de filas,
    una por cada producto encontrado.

    Estructura esperada:
    - store info en el nivel raíz
    - productos dentro de corridors[].products[]
    """
    rows = []

    # -----------------------------
    # 1. Extraer datos generales de la tienda
    # -----------------------------
    store_id = data.get("store_id")
    super_store_id = data.get("super_store_id")
    brand_name = data.get("brand_name")
    store_name = data.get("name")
    address = data.get("address")
    delivery_price = data.get("delivery_price")
    eta_value = data.get("eta_value")
    percentage_service_fee = data.get("percentage_service_fee")
    is_open_today = data.get("is_open_today")

    # La lista de corredores/categorías del menú
    corridors = data.get("corridors", [])

    # -----------------------------
    # 2. Recorrer corredores
    # -----------------------------
    for corridor in corridors:
        corridor_id = corridor.get("id")
        corridor_name = corridor.get("name")
        corridor_index = corridor.get("index")

        products = corridor.get("products", [])

        # -----------------------------
        # 3. Recorrer productos dentro de cada corredor
        # -----------------------------
        for product in products:
            row = {
                # Fuente / plataforma
                "platform": "Rappi",

                # Datos de tienda
                "store_id": store_id,
                "super_store_id": super_store_id,
                "brand_name": brand_name,
                "store_name": store_name,
                "store_address": address,
                "is_open_today": is_open_today,

                # Métricas de tienda
                "delivery_price": delivery_price,
                "eta_value_min": eta_value,
                "percentage_service_fee": percentage_service_fee,

                # Categoría / corredor
                "corridor_id": corridor_id,
                "corridor_name": corridor_name,
                "corridor_index": corridor_index,

                # Producto
                "product_id": product.get("product_id"),
                "product_name": product.get("name"),
                "product_description": product.get("description"),
                "product_price": product.get("price"),
                "product_real_price": product.get("real_price"),
                "discount_percentage": product.get("discount_percentage"),
                "is_available": product.get("is_available"),
                "is_popular": product.get("is_popular"),
                "has_toppings": product.get("has_toppings"),
                "product_image": product.get("image"),
            }

            rows.append(row)

    return rows


def main():
    """
    Flujo principal:
    1. leer JSON
    2. extraer productos
    3. convertir a DataFrame
    4. guardar CSV
    """
    if not INPUT_JSON_PATH.exists():
        print("No existe el archivo:", INPUT_JSON_PATH)
        return

    data = load_json(INPUT_JSON_PATH)

    rows = extract_products(data)

    if not rows:
        print("No se encontraron productos en el JSON.")
        return

    df = pd.DataFrame(rows)
    df.to_csv(OUTPUT_CSV_PATH, index=False)

    print("Productos extraídos:", len(df))
    print("CSV guardado en:", OUTPUT_CSV_PATH)
    print(df.head(10))


if __name__ == "__main__":
    main()