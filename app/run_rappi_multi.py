"""
Pipeline automático para múltiples restaurantes en Rappi.

Qué corrige esta versión:
1. Limpia los JSON anteriores antes de procesar cada tienda
2. Busca dinámicamente el JSON válido del restaurante
3. Evita reutilizar siempre el mismo archivo
4. Evita tomar JSON que no son menú/store detail
"""

from pathlib import Path
import json
import pandas as pd

from app.debug_rappi_menu import run_menu_debug
from app.extract_rappi_products_from_json import load_json, extract_products


# -----------------------------
# Configuración
# -----------------------------

ADDRESS = "Chapinero Alto, Bogotá"

STORES = [
    "McDonald's",
    "Burger King",
    "KFC",
]

OUTPUT_DIR = Path("output")
AFTER_JSON_DIR = OUTPUT_DIR / "debug_menu_json_after"
FINAL_CSV = OUTPUT_DIR / "rappi_all_stores.csv"


# -----------------------------
# Utilidades
# -----------------------------

def clean_after_json_dir() -> None:
    """
    Borra todos los JSON previos de la carpeta debug_menu_json_after.
    Esto evita mezclar respuestas de una tienda con otra.
    """
    AFTER_JSON_DIR.mkdir(exist_ok=True)

    for file in AFTER_JSON_DIR.glob("*.json"):
        file.unlink()


def get_valid_store_json() -> Path | None:
    """
    Busca el JSON que realmente corresponde al detalle de tienda.

    Debe ser un dict con:
    - store_id
    - name
    - brand_name
    - corridors
    """
    json_files = list(AFTER_JSON_DIR.glob("*.json"))

    if not json_files:
        return None

    json_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)

    for path in json_files:
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, dict):
                continue

            required_keys = {"store_id", "name", "brand_name", "corridors"}

            if required_keys.issubset(set(data.keys())):
                return path

        except Exception:
            continue

    return None


def safe_store_filename(store_name: str) -> str:
    """
    Convierte el nombre del restaurante en un nombre de archivo seguro.
    """
    return store_name.lower().replace(" ", "_").replace("'", "").replace("&", "and")


# -----------------------------
# Pipeline por tienda
# -----------------------------

def process_store(store_name: str) -> pd.DataFrame:
    """
    Ejecuta todo el flujo para una tienda:
    1. limpia JSON previos
    2. corre el scraping
    3. ubica el JSON válido del restaurante
    4. extrae productos
    5. guarda CSV individual
    """
    print("\n==============================")
    print(f"Procesando: {store_name}")
    print("==============================")

    # 1. Limpiar JSON previos
    clean_after_json_dir()

    # 2. Ejecutar debug de menú
    run_menu_debug(address_text=ADDRESS, store_name=store_name)

    # 3. Buscar JSON válido del restaurante
    json_path = get_valid_store_json()

    if json_path is None:
        print(f"⚠️ No se encontró JSON válido para {store_name}")
        return pd.DataFrame()

    print(f"Usando JSON válido: {json_path}")

    # 4. Cargar JSON
    data = load_json(json_path)

    # 5. Extraer productos
    rows = extract_products(data)

    if not rows:
        print(f"⚠️ No se encontraron productos en {store_name}")
        return pd.DataFrame()

    df = pd.DataFrame(rows)

    # 6. Agregar metadata útil
    df["store_query"] = store_name
    df["address_text"] = ADDRESS

    # 7. Guardar CSV individual
    file_name = safe_store_filename(store_name)
    store_csv = OUTPUT_DIR / f"rappi_{file_name}.csv"
    df.to_csv(store_csv, index=False)

    print(f"✅ CSV individual guardado en: {store_csv}")
    print(f"Registros extraídos: {len(df)}")

    return df


# -----------------------------
# Pipeline completo
# -----------------------------

def main():
    """
    Ejecuta el pipeline completo para todas las tiendas
    y une todo en un CSV final.
    """
    all_dfs = []

    for store in STORES:
        df = process_store(store)

        if not df.empty:
            all_dfs.append(df)

    if not all_dfs:
        print("❌ No se generaron datos")
        return

    final_df = pd.concat(all_dfs, ignore_index=True)
    final_df.to_csv(FINAL_CSV, index=False)

    print("\n==============================")
    print("✅ PIPELINE COMPLETADO")
    print("==============================")
    print("Total registros:", len(final_df))
    print("Archivo final:", FINAL_CSV)

    print("\nTiendas en CSV final:")
    print(final_df["store_query"].value_counts())


if __name__ == "__main__":
    main()