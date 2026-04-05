from pathlib import Path

# Carpeta donde se guardan los outputs del scraper
OUTPUT_DIR = Path("output")

# Si la carpeta no existe, la crea automáticamente
OUTPUT_DIR.mkdir(exist_ok=True)

# Ruta del CSV final donde vamos a guardar los resultados
CSV_PATH = OUTPUT_DIR / "restaurant_links.csv"

# Direcciones de prueba.
# Luego esto lo podemos reemplazar por lectura desde data/addresses.csv
ADDRESSES = [
    "Chapinero Alto, Bogotá",
    "Zona T, Bogotá",
    "Usaquén, Bogotá",
]

# Restaurantes objetivo para el scraping
STORES = [
    "McDonald's",
    "Burger King",
    "KFC",
]