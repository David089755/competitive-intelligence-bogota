"""
Comparación interna de restaurantes dentro de Rappi.

Este script:
1. Lee el CSV consolidado de Rappi (todos los restaurantes).
2. Limpia y normaliza los datos.
3. Clasifica productos en grupos comparables.
4. Elimina ruido (combos familiares, promos, outliers).
5. Calcula precios comparables.
6. Genera tablas comparativas (pivot).
7. Exporta CSVs y gráficos.

Este es el corazón del análisis competitivo.
"""

from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt


# -----------------------------
# 1. Rutas de entrada / salida
# -----------------------------

INPUT_CSV = Path("output/rappi_all_stores.csv")

OUTPUT_COMPARABLE_CSV = Path("output/rappi_comparable_products.csv")
OUTPUT_PIVOT_PRICE_CSV = Path("output/rappi_comparison_pivot_price.csv")
OUTPUT_PIVOT_TOTAL_CSV = Path("output/rappi_comparison_pivot_total.csv")

PLOTS_DIR = Path("output/plots")
PLOTS_DIR.mkdir(exist_ok=True)


# -----------------------------
# 2. Funciones auxiliares
# -----------------------------

def normalize_text(value: str) -> str:
    """
    Normaliza texto para facilitar matching:
    - minúsculas
    - sin espacios extra
    """
    if pd.isna(value):
        return ""
    return str(value).strip().lower()


def assign_product_group(product_name: str) -> str:
    """
    Clasifica productos en grupos comparables.

    IMPORTANTE:
    Aquí también detectamos productos que NO queremos usar (ruido)
    como combos familiares o promociones grandes.
    """
    name = normalize_text(product_name)

    # -------------------------
    # ❌ FILTRO DE RUIDO
    # -------------------------
    if any(term in name for term in ["family", "promo", "doble", "dobles"]):
        return "exclude"

    # -------------------------
    # 🍔 Hamburguesa firma
    # -------------------------
    if any(term in name for term in ["big mac", "whopper", "coronel burger"]):
        return "hamburguesa_firma"

    # -------------------------
    # 🍟 Combo hamburguesa
    # -------------------------
    if "combo" in name:
        return "combo_hamburguesa"

    # -------------------------
    # 🍗 Nuggets / pollo
    # -------------------------
    if any(term in name for term in ["nuggets", "mcnuggets", "popcorn", "tenders"]):
        return "pollo_bocados"

    return "otros"


def build_final_total_est(row: pd.Series) -> float:
    """
    Calcula total estimado:
    producto + delivery

    (simple pero suficiente para análisis)
    """
    product_price = row.get("product_price", 0) or 0
    delivery_price = row.get("delivery_price", 0) or 0
    return float(product_price) + float(delivery_price)


# -----------------------------
# 3. Cargar datos
# -----------------------------

def load_data() -> pd.DataFrame:
    """
    Carga el CSV consolidado.
    """
    if not INPUT_CSV.exists():
        raise FileNotFoundError(f"No existe el archivo: {INPUT_CSV}")

    return pd.read_csv(INPUT_CSV)


# -----------------------------
# 4. Limpieza y transformación
# -----------------------------

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Limpia y transforma el dataset.
    """
    df = df.copy()

    # -------------------------
    # Convertir a numérico
    # -------------------------
    numeric_cols = [
        "product_price",
        "delivery_price",
        "eta_value_min",
    ]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # -------------------------
    # Normalizar nombres
    # -------------------------
    df["product_name_normalized"] = df["product_name"].apply(normalize_text)

    # -------------------------
    # Clasificar productos
    # -------------------------
    df["product_group"] = df["product_name"].apply(assign_product_group)

    # -------------------------
    # ❌ FILTRO 1: excluir ruido
    # -------------------------
    df = df[df["product_group"] != "exclude"]

    # -------------------------
    # ❌ FILTRO 2: eliminar outliers
    # (combos familiares, precios absurdos)
    # -------------------------
    df = df[df["product_price"] < 60000]

    # -------------------------
    # Total estimado
    # -------------------------
    df["final_total_est"] = df.apply(build_final_total_est, axis=1)

    return df


# -----------------------------
# 5. Filtrar productos comparables
# -----------------------------

def build_comparable_products(df: pd.DataFrame) -> pd.DataFrame:
    """
    Nos quedamos solo con productos clave para comparar.
    """
    groups = [
        "hamburguesa_firma",
        "combo_hamburguesa",
        "pollo_bocados",
    ]

    df = df[df["product_group"].isin(groups)].copy()

    return df


# -----------------------------
# 6. Pivots comparativos
# -----------------------------

def build_price_pivot(df: pd.DataFrame) -> pd.DataFrame:
    """
    Precio promedio por grupo y restaurante.
    """
    return pd.pivot_table(
        df,
        index="product_group",
        columns="store_query",
        values="product_price",
        aggfunc="mean"
    ).reset_index()


def build_total_pivot(df: pd.DataFrame) -> pd.DataFrame:
    """
    Total estimado promedio.
    """
    return pd.pivot_table(
        df,
        index="product_group",
        columns="store_query",
        values="final_total_est",
        aggfunc="mean"
    ).reset_index()


# -----------------------------
# 7. Gráficas
# -----------------------------

def plot_price_by_group(pivot: pd.DataFrame):
    """
    Gráfico de precios promedio.
    """
    pivot.set_index("product_group").plot(kind="bar", figsize=(10, 6))
    plt.title("Precio promedio por grupo y restaurante")
    plt.tight_layout()
    plt.savefig(PLOTS_DIR / "price_comparison.png")
    plt.close()


def plot_total_by_group(pivot: pd.DataFrame):
    """
    Gráfico de total estimado.
    """
    pivot.set_index("product_group").plot(kind="bar", figsize=(10, 6))
    plt.title("Total estimado por grupo y restaurante")
    plt.tight_layout()
    plt.savefig(PLOTS_DIR / "total_comparison.png")
    plt.close()


# -----------------------------
# 8. MAIN
# -----------------------------

def main():
    print("Leyendo datos...")
    df = load_data()

    print("Limpiando...")
    df = clean_data(df)

    print("Filtrando productos comparables...")
    comparable_df = build_comparable_products(df)

    print("Generando pivots...")
    price_pivot = build_price_pivot(comparable_df)
    total_pivot = build_total_pivot(comparable_df)

    print("Guardando resultados...")
    comparable_df.to_csv(OUTPUT_COMPARABLE_CSV, index=False)
    price_pivot.to_csv(OUTPUT_PIVOT_PRICE_CSV, index=False)
    total_pivot.to_csv(OUTPUT_PIVOT_TOTAL_CSV, index=False)

    print("Generando gráficos...")
    plot_price_by_group(price_pivot)
    plot_total_by_group(total_pivot)

    print("\n=== RESULTADO FINAL ===")
    print(price_pivot)
    print("\n")
    print(total_pivot)


if __name__ == "__main__":
    main()