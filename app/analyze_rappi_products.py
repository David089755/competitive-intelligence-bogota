"""
Análisis básico de productos extraídos desde Rappi.

Qué hace este script:
1. Lee el CSV generado por el extractor de productos.
2. Limpia columnas numéricas importantes.
3. Calcula métricas derivadas.
4. Genera un resumen agregado.
5. Exporta un CSV de análisis.
6. Genera 3 gráficas:
   - Top productos por precio
   - Precio promedio por corredor/categoría
   - ETA y delivery fee de la tienda

Este script es la base para la parte analítica del caso técnico.
"""

from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt


# -----------------------------
# 1. Rutas de entrada y salida
# -----------------------------

# CSV generado previamente desde el JSON del restaurante
INPUT_CSV = Path("output/rappi_products_extracted.csv")

# CSV resumen con métricas agregadas
OUTPUT_SUMMARY_CSV = Path("output/rappi_products_analysis_summary.csv")

# Carpeta donde guardaremos gráficos
PLOTS_DIR = Path("output/plots")
PLOTS_DIR.mkdir(exist_ok=True)


# -----------------------------
# 2. Funciones auxiliares
# -----------------------------

def normalize_product_name(name: str) -> str:
    """
    Normaliza el nombre del producto para facilitar análisis.

    Ejemplos:
    - pasa a minúsculas
    - elimina espacios al inicio/final
    """
    if pd.isna(name):
        return ""
    return str(name).strip().lower()


def build_final_total_est(row: pd.Series) -> float:
    """
    Calcula un total estimado básico:
    precio producto + delivery fee

    Nota:
    Aquí todavía no sumamos tarifa de servicio real si no está clara
    o si viene en otro campo con otra lógica.
    """
    product_price = row.get("product_price", 0) or 0
    delivery_price = row.get("delivery_price", 0) or 0
    return float(product_price) + float(delivery_price)


# -----------------------------
# 3. Cargar CSV
# -----------------------------

def load_data() -> pd.DataFrame:
    """
    Lee el CSV principal y valida que exista.
    """
    if not INPUT_CSV.exists():
        raise FileNotFoundError(f"No existe el archivo de entrada: {INPUT_CSV}")

    df = pd.read_csv(INPUT_CSV)
    return df


# -----------------------------
# 4. Limpieza y transformación
# -----------------------------

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Limpia y prepara el DataFrame para análisis.
    """
    # Copia para evitar modificar el original directamente
    df = df.copy()

    # Convertimos columnas numéricas importantes
    numeric_cols = [
        "product_price",
        "product_real_price",
        "delivery_price",
        "eta_value_min",
        "percentage_service_fee",
        "discount_percentage",
    ]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Normalizar nombre del producto
    if "product_name" in df.columns:
        df["product_name_normalized"] = df["product_name"].apply(normalize_product_name)
    else:
        df["product_name_normalized"] = ""

    # Calcular total estimado
    df["final_total_est"] = df.apply(build_final_total_est, axis=1)

    # Availability a boolean simple si existe
    if "is_available" in df.columns:
        df["is_available"] = df["is_available"].fillna(False)

    return df


# -----------------------------
# 5. Resumen agregado
# -----------------------------

def build_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Construye una tabla resumen por corredor/categoría.
    """
    group_cols = []

    if "corridor_name" in df.columns:
        group_cols.append("corridor_name")

    if not group_cols:
        # Si no existe corridor_name, resumimos todo junto
        summary = pd.DataFrame([{
            "avg_product_price": df["product_price"].mean(),
            "avg_delivery_price": df["delivery_price"].mean(),
            "avg_final_total_est": df["final_total_est"].mean(),
            "avg_eta_value_min": df["eta_value_min"].mean(),
            "product_count": len(df),
        }])
        return summary

    summary = (
        df.groupby(group_cols, dropna=False)
        .agg(
            avg_product_price=("product_price", "mean"),
            avg_delivery_price=("delivery_price", "mean"),
            avg_final_total_est=("final_total_est", "mean"),
            avg_eta_value_min=("eta_value_min", "mean"),
            product_count=("product_id", "count"),
        )
        .reset_index()
        .sort_values(by="avg_product_price", ascending=False)
    )

    return summary


# -----------------------------
# 6. Gráficas
# -----------------------------

def plot_top_products_by_price(df: pd.DataFrame) -> None:
    """
    Gráfica 1:
    Top 10 productos más caros.
    """
    if "product_name" not in df.columns or "product_price" not in df.columns:
        return

    top_df = (
        df[["product_name", "product_price"]]
        .dropna()
        .sort_values(by="product_price", ascending=False)
        .head(10)
    )

    if top_df.empty:
        return

    plt.figure(figsize=(12, 6))
    plt.bar(top_df["product_name"], top_df["product_price"])
    plt.xticks(rotation=75, ha="right")
    plt.ylabel("Precio producto")
    plt.title("Top 10 productos por precio")
    plt.tight_layout()
    plt.savefig(PLOTS_DIR / "top_10_products_by_price.png")
    plt.close()


def plot_avg_price_by_corridor(summary_df: pd.DataFrame) -> None:
    """
    Gráfica 2:
    Precio promedio por corredor/categoría.
    """
    if "corridor_name" not in summary_df.columns or "avg_product_price" not in summary_df.columns:
        return

    plot_df = summary_df.dropna(subset=["corridor_name", "avg_product_price"]).head(12)

    if plot_df.empty:
        return

    plt.figure(figsize=(12, 6))
    plt.bar(plot_df["corridor_name"], plot_df["avg_product_price"])
    plt.xticks(rotation=75, ha="right")
    plt.ylabel("Precio promedio")
    plt.title("Precio promedio por categoría/corredor")
    plt.tight_layout()
    plt.savefig(PLOTS_DIR / "avg_price_by_corridor.png")
    plt.close()


def plot_store_operational_metrics(df: pd.DataFrame) -> None:
    """
    Gráfica 3:
    Métricas operativas de tienda:
    - delivery fee promedio
    - ETA promedio

    Como puede haber una sola tienda en este CSV, esta gráfica sirve
    para documentar las métricas operativas del scrape.
    """
    if "delivery_price" not in df.columns or "eta_value_min" not in df.columns:
        return

    metrics = {
        "delivery_price_avg": df["delivery_price"].mean(),
        "eta_value_min_avg": df["eta_value_min"].mean(),
    }

    labels = list(metrics.keys())
    values = list(metrics.values())

    plt.figure(figsize=(8, 5))
    plt.bar(labels, values)
    plt.ylabel("Valor promedio")
    plt.title("Métricas operativas promedio de la tienda")
    plt.tight_layout()
    plt.savefig(PLOTS_DIR / "store_operational_metrics.png")
    plt.close()


# -----------------------------
# 7. Main
# -----------------------------

def main():
    """
    Orquestador del análisis.
    """
    print("Leyendo CSV...")
    df = load_data()

    print("Limpiando datos...")
    df_clean = clean_data(df)

    print("Construyendo resumen...")
    summary_df = build_summary(df_clean)

    print("Guardando CSV resumen...")
    summary_df.to_csv(OUTPUT_SUMMARY_CSV, index=False)

    print("Generando gráficas...")
    plot_top_products_by_price(df_clean)
    plot_avg_price_by_corridor(summary_df)
    plot_store_operational_metrics(df_clean)

    print("\n=== ANÁLISIS COMPLETADO ===")
    print("Resumen guardado en:", OUTPUT_SUMMARY_CSV)
    print("Gráficas guardadas en:", PLOTS_DIR)

    print("\nVista previa del resumen:")
    print(summary_df.head(10))


if __name__ == "__main__":
    main()