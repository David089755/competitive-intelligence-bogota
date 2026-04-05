"""
Este script inspecciona los archivos JSON guardados en output/debug_json/.

Objetivo:
- abrir los JSON capturados desde Rappi
- mostrar su estructura general
- buscar claves importantes como:
  - name
  - price
  - products
  - items
  - suggestions
  - stores
- imprimir ejemplos de valores

Esto NO navega la web.
Solo analiza los JSON ya guardados localmente.
"""

import json
from pathlib import Path
from typing import Any


# Carpeta donde quedaron guardados los JSON capturados
DEBUG_JSON_DIR = Path("output/debug_json")


def load_json(path: Path) -> Any:
    """
    Carga un archivo JSON y devuelve su contenido como objeto Python.
    """
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def print_basic_info(data: Any, path: Path) -> None:
    """
    Imprime información básica del JSON:
    - tipo principal (dict o list)
    - claves top-level si es dict
    - longitud si es list
    """
    print("=" * 100)
    print(f"Archivo: {path.name}")

    if isinstance(data, dict):
        print("Tipo raíz: dict")
        print("Claves top-level:")
        for key in list(data.keys())[:30]:
            print(" -", key)

    elif isinstance(data, list):
        print("Tipo raíz: list")
        print("Longitud:", len(data))

        # Si la lista tiene elementos y el primero es dict, mostramos sus claves
        if data and isinstance(data[0], dict):
            print("Claves del primer elemento:")
            for key in list(data[0].keys())[:30]:
                print(" -", key)
    else:
        print("Tipo raíz:", type(data).__name__)


def recursive_find_keys(data: Any, target_keys: set[str], found: list[dict], path: str = "root") -> None:
    """
    Recorre recursivamente un objeto JSON y busca claves de interés.

    Parámetros:
    - data: objeto Python (dict/list/valor)
    - target_keys: claves que queremos encontrar
    - found: lista acumuladora de hallazgos
    - path: ruta lógica dentro del JSON
    """
    if isinstance(data, dict):
        for key, value in data.items():
            current_path = f"{path}.{key}"

            if key.lower() in target_keys:
                found.append({
                    "path": current_path,
                    "key": key,
                    "value_type": type(value).__name__,
                    "preview": preview_value(value),
                })

            recursive_find_keys(value, target_keys, found, current_path)

    elif isinstance(data, list):
        for idx, item in enumerate(data[:50]):  # limitamos para no imprimir demasiado
            current_path = f"{path}[{idx}]"
            recursive_find_keys(item, target_keys, found, current_path)


def preview_value(value: Any, max_len: int = 200) -> str:
    """
    Devuelve una versión corta y legible de un valor.
    """
    if isinstance(value, (dict, list)):
        text = json.dumps(value, ensure_ascii=False)
    else:
        text = str(value)

    if len(text) > max_len:
        return text[:max_len] + "..."
    return text


def inspect_file(path: Path) -> None:
    """
    Analiza un archivo JSON individual.
    """
    data = load_json(path)

    # Imprimir estructura básica
    print_basic_info(data, path)

    # Claves que nos interesan para este caso técnico
    target_keys = {
        "name",
        "price",
        "prices",
        "products",
        "product",
        "items",
        "item",
        "suggestions",
        "stores",
        "store",
        "catalog",
        "title",
        "description",
        "amount",
        "value",
    }

    found = []
    recursive_find_keys(data, target_keys, found)

    print("\nClaves de interés encontradas:")
    if not found:
        print(" - No se encontraron claves objetivo")
    else:
        for row in found[:40]:
            print(f"- {row['path']}")
            print(f"  key       : {row['key']}")
            print(f"  value_type: {row['value_type']}")
            print(f"  preview   : {row['preview']}")


def main():
    """
    Recorre todos los JSON en output/debug_json/
    y los inspecciona uno por uno.
    """
    if not DEBUG_JSON_DIR.exists():
        print("No existe la carpeta:", DEBUG_JSON_DIR)
        print("Primero ejecuta: python -m app.debug_rappi_json")
        return

    json_files = sorted(DEBUG_JSON_DIR.glob("*.json"))

    if not json_files:
        print("No se encontraron archivos JSON en:", DEBUG_JSON_DIR)
        return

    print(f"Se encontraron {len(json_files)} archivos JSON.\n")

    for path in json_files:
        inspect_file(path)
        print("\n")


if __name__ == "__main__":
    main()