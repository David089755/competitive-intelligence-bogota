import pandas as pd

from app.config import ADDRESSES, STORES, CSV_PATH
from app.scrapers.rappi import scrape_restaurant_link


def main():
    """
    Función principal del pipeline.

    Recorre:
    - todas las direcciones
    - todos los restaurantes

    Y guarda cada resultado en una lista.
    """
    results = []

    # Loop principal del scraping
    for address in ADDRESSES:
        for store in STORES:
            result = scrape_restaurant_link(
                address_text=address,
                store_name=store
            )
            results.append(result)

    # Convertimos la lista de diccionarios en DataFrame
    df = pd.DataFrame(results)

    # Guardamos el DataFrame en CSV
    df.to_csv(CSV_PATH, index=False)

    # Imprimimos resultado en consola
    print("\nCSV guardado en:", CSV_PATH)
    print(df)


if __name__ == "__main__":
    main()