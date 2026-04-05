"""
Debug específico para descubrir el endpoint del MENÚ de un restaurante en Rappi.

Qué hace:
1. Abre Rappi
2. Fija una dirección
3. Busca un restaurante
4. Encuentra la URL real del restaurante
5. Captura respuestas JSON ANTES de entrar
6. Entra al restaurante
7. Captura respuestas JSON DESPUÉS de entrar
8. Guarda solo las respuestas nuevas del menú en output/debug_menu_json/

Objetivo:
encontrar respuestas que contengan productos, items o precios.
"""

import json
import time
import random
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

from app.utils import safe_click, safe_fill, type_in_visible_search, find_restaurant_url


# Carpeta principal de salida
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

# Carpeta donde guardaremos los JSON del "antes"
BEFORE_JSON_DIR = OUTPUT_DIR / "debug_menu_json_before"
BEFORE_JSON_DIR.mkdir(exist_ok=True)

# Carpeta donde guardaremos los JSON del "después" de entrar al restaurante
AFTER_JSON_DIR = OUTPUT_DIR / "debug_menu_json_after"
AFTER_JSON_DIR.mkdir(exist_ok=True)


def random_sleep(base: int = 2) -> None:
    """
    Hace una pausa aleatoria para que la navegación sea más parecida a la de un usuario real.
    """
    time.sleep(base + random.uniform(0.5, 1.2))


def save_json(data, path: Path) -> None:
    """
    Guarda un objeto Python como JSON legible.
    """
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def sanitize_filename(text: str) -> str:
    """
    Convierte un texto en un nombre de archivo seguro.
    """
    safe = "".join(c if c.isalnum() else "_" for c in text)
    return safe[:140]


def is_interesting_menu_url(url: str) -> bool:
    """
    En esta versión de debug queremos capturar TODO JSON nuevo
    después de entrar al restaurante.

    Así dejamos de depender de keywords que pueden estar mal.
    """
    return True


def short_name_from_url(url: str) -> str:
    """
    Extrae una parte corta de la URL para usarla en el nombre del archivo.
    """
    path = urlparse(url).path
    last_part = path.split("/")[-1] if path else "response"
    return sanitize_filename(last_part)


def run_menu_debug(address_text: str = "Chapinero Alto, Bogotá", store_name: str = "McDonald's") -> None:
    """
    Flujo principal:
    - abre Rappi
    - setea dirección
    - busca restaurante
    - encuentra URL del restaurante
    - separa respuestas JSON antes/después de entrar
    """

    # Aquí guardamos metadata de respuestas antes de entrar al restaurante
    captured_before = []

    # Aquí guardamos metadata de respuestas después de entrar
    captured_after = []

    # Set con URLs observadas antes de entrar al restaurante
    before_urls = set()

    # Bandera para saber si ya entramos al restaurante
    state = {"inside_store": False}

    # Contadores para nombrar archivos
    counters = {
        "before": 0,
        "after": 0,
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            slow_mo=400,
        )

        context = browser.new_context(
            viewport={"width": 1440, "height": 1200},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        )

        page = context.new_page()
        page.set_default_timeout(15000)
        page.set_default_navigation_timeout(45000)

        def handle_response(response):
            """
            Listener que corre cada vez que la página recibe una respuesta HTTP.

            Solo guardamos respuestas:
            - con content-type JSON
            - cuya URL parezca relacionada con menú/productos/items
            """
            try:
                url = response.url
                url_lower = url.lower()

                # Debug visual: ver todo lo que llega
                print("[URL]", url)

                content_type = response.headers.get("content-type", "").lower()

                # Solo nos interesan respuestas JSON
                if "application/json" not in content_type:
                    return

                # Solo respuestas candidatas a menú/productos
                if not is_interesting_menu_url(url_lower):
                    return

                # Intentamos parsear JSON
                try:
                    body = response.json()
                except Exception:
                    return

                # Si todavía no entramos al restaurante, guardamos en BEFORE
                if not state["inside_store"]:
                    counters["before"] += 1
                    idx = counters["before"]

                    file_name = f"{idx}_{short_name_from_url(url)}.json"
                    json_path = BEFORE_JSON_DIR / file_name

                    save_json(body, json_path)

                    captured_before.append({
                        "idx": idx,
                        "url": url,
                        "status": response.status,
                        "content_type": content_type,
                        "saved_to": str(json_path),
                    })

                    before_urls.add(url)

                    print(f"[BEFORE JSON] {url}")
                    print(f"Guardado en: {json_path}")

                # Si ya entramos al restaurante, guardamos solo respuestas nuevas
                else:
                    # Evita re-guardar URLs que ya habíamos visto antes de entrar
                    if url in before_urls:
                        return

                    counters["after"] += 1
                    idx = counters["after"]

                    file_name = f"{idx}_{short_name_from_url(url)}.json"
                    json_path = AFTER_JSON_DIR / file_name

                    save_json(body, json_path)

                    captured_after.append({
                        "idx": idx,
                        "url": url,
                        "status": response.status,
                        "content_type": content_type,
                        "saved_to": str(json_path),
                    })

                    print(f"[AFTER JSON] {url}")
                    print(f"Guardado en: {json_path}")

            except Exception:
                # Nunca queremos que una respuesta rompa todo el flujo
                pass

        # Registramos el listener
        page.on("response", handle_response)

        try:
            print("1. Abriendo Rappi...")
            page.goto("https://www.rappi.com.co/", wait_until="domcontentloaded", timeout=45000)
            random_sleep(3)

            page.screenshot(path=str(OUTPUT_DIR / "menu_debug_01_home.png"), full_page=True)

            print("2. Cerrando cookies...")
            safe_click(page, [
                "button:has-text('Aceptar')",
                "button:has-text('Entendido')",
                "button:has-text('Continuar')",
                "button:has-text('Aceptar y continuar')",
                "[data-qa='accept-cookies']",
            ], timeout=2500)

            random_sleep(2)

            print("3. Escribiendo dirección...")
            ok_address, address_selector = safe_fill(page, [
                "input[placeholder='¿Dónde quieres recibir tu compra?']",
                "input[placeholder*='¿Dónde quieres recibir tu compra?']",
                "input[type='text']",
            ], address_text)

            print("Dirección escrita:", ok_address, "| selector:", address_selector)
            if not ok_address:
                raise Exception("No se pudo escribir la dirección")

            random_sleep(4)

            print("4. Confirmando dirección...")
            ok_confirm, confirm_selector = safe_click(page, [
                "[role='option']",
                "div[role='option']",
                "li",
                "button:has-text('Confirmar')",
                "button:has-text('Guardar')",
                "button:has-text('Usar esta dirección')",
                "text='Chapinero'",
                "text='Zona T'",
                "text='Usaquén'",
            ], timeout=7000)

            print("Dirección confirmada:", ok_confirm, "| selector:", confirm_selector)
            if not ok_confirm:
                raise Exception("No se pudo confirmar la dirección")

            random_sleep(8)
            page.screenshot(path=str(OUTPUT_DIR / "menu_debug_02_post_address.png"), full_page=True)

            print("5. Buscando restaurante...")
            ok_search, search_selector = type_in_visible_search(page, store_name)
            print("Restaurante escrito:", ok_search, "| selector:", search_selector)
            if not ok_search:
                raise Exception("No se pudo escribir en el buscador")

            # Esperamos a que lleguen responses del listing/search
            random_sleep(8)
            page.screenshot(path=str(OUTPUT_DIR / "menu_debug_03_search_results.png"), full_page=True)

            print("6. Extrayendo links de resultados...")
            links = page.locator("a").evaluate_all("""
                els => els.map((el, i) => ({
                    idx: i,
                    text: (el.innerText || '').trim(),
                    href: el.href || null
                })).filter(x => x.text || x.href)
            """)

            match = find_restaurant_url(links, store_name)
            if not match:
                raise Exception("No encontré ninguna URL válida del restaurante")

            restaurant_url = match.get("href")
            restaurant_text = match.get("text")

            print("\n=== RESTAURANTE ENCONTRADO ===")
            print("Texto:", restaurant_text)
            print("Href :", restaurant_url)

            print("7. Entrando al restaurante...")
            state["inside_store"] = True

            # Navegamos a la URL del restaurante
            page.goto(restaurant_url, wait_until="domcontentloaded", timeout=45000)

            # Esperamos suficiente tiempo para que el menú dispare requests
            random_sleep(12)
            page.screenshot(path=str(OUTPUT_DIR / "menu_debug_04_store_page.png"), full_page=True)

            print("URL final:", page.url)
            print("Título final:", page.title())

            # Guardamos metadata de before/after
            save_json(captured_before, OUTPUT_DIR / "menu_debug_before_metadata.json")
            save_json(captured_after, OUTPUT_DIR / "menu_debug_after_metadata.json")

            print("\n=== RESUMEN ===")
            print("JSON before:", len(captured_before))
            print("JSON after :", len(captured_after))
            print("Metadata before:", OUTPUT_DIR / "menu_debug_before_metadata.json")
            print("Metadata after :", OUTPUT_DIR / "menu_debug_after_metadata.json")
            print("JSON before dir:", BEFORE_JSON_DIR)
            print("JSON after dir :", AFTER_JSON_DIR)

        finally:
            context.close()
            browser.close()


if __name__ == "__main__":
    run_menu_debug()