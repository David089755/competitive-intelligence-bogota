"""
Inspección local de los archivos guardados desde Uber Eats.

Lee:
- output/ubereats_home_source.html
- output/ubereats_links_snapshot.json

Objetivo:
- buscar patrones útiles en el HTML
- listar links prometedores
- detectar si hay data embebida tipo JSON/Next.js/script tags
"""

import json
import re
from pathlib import Path


HTML_PATH = Path("output/ubereats_home_source.html")
LINKS_PATH = Path("output/ubereats_links_snapshot.json")


def load_text(path: Path) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def load_json(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def inspect_html(html: str) -> None:
    """
    Busca patrones comunes de apps web modernas.
    """
    print("=== INSPECCIÓN HTML ===")

    patterns = [
        "__NEXT_DATA__",
        "__NUXT__",
        "application/ld+json",
        "ubereats",
        "restaurant",
        "store",
        "menu",
        "feed",
        "apollo",
        "graphql",
    ]

    for pattern in patterns:
        found = pattern.lower() in html.lower()
        print(f"{pattern}: {found}")

    print("\n=== SCRIPTS JSON/LD ENCONTRADOS ===")
    matches = re.findall(
        r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>',
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )

    if not matches:
        print("No se encontraron scripts application/ld+json")
    else:
        for i, match in enumerate(matches[:5], start=1):
            snippet = match.strip().replace("\n", " ")
            print(f"[{i}] {snippet[:500]}")
            print("-" * 80)

    print("\n=== POSIBLE __NEXT_DATA__ ===")
    next_data_match = re.search(
        r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>',
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )

    if next_data_match:
        snippet = next_data_match.group(1).strip()
        print(snippet[:1000])
    else:
        print("No se encontró __NEXT_DATA__")


def inspect_links(links: list[dict]) -> None:
    """
    Filtra links que parezcan útiles para discovery.
    """
    print("\n=== LINKS PROMETEDORES ===")

    useful = []
    for link in links:
        text = (link.get("text") or "").lower()
        href = (link.get("href") or "").lower()

        if any(term in href for term in [
            "restaurant",
            "store",
            "menu",
            "search",
            "/co/",
            "/bogota",
            "/feed",
        ]):
            useful.append(link)
            continue

        if any(term in text for term in [
            "mcdonald",
            "burger",
            "kfc",
            "restaurant",
            "buscar",
            "search",
            "bogotá",
            "bogota",
        ]):
            useful.append(link)

    if not useful:
        print("No se encontraron links prometedores con estos filtros.")
    else:
        for x in useful[:50]:
            print(x)


def main():
    if not HTML_PATH.exists():
        print("No existe:", HTML_PATH)
        return

    if not LINKS_PATH.exists():
        print("No existe:", LINKS_PATH)
        return

    html = load_text(HTML_PATH)
    links = load_json(LINKS_PATH)

    inspect_html(html)
    inspect_links(links)


if __name__ == "__main__":
    main()