"""
Debug técnico de red para Uber Eats.

Objetivo:
- abrir Uber Eats Colombia
- navegar a una página útil
- capturar respuestas JSON
- guardar metadatos y bodies JSON para inspección

Este script NO intenta todavía extraer productos finales.
Primero descubre endpoints.
"""

import json
import time
import random
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright


# -----------------------------
# 1. Configuración
# -----------------------------

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

DEBUG_DIR = OUTPUT_DIR / "ubereats_debug_json"
DEBUG_DIR.mkdir(exist_ok=True)

# Puedes cambiar esta URL si luego consigues una URL mejor de restaurante
# Por ahora arrancamos por la home de Uber Eats Colombia.
START_URL = "https://www.ubereats.com/co"


# -----------------------------
# 2. Utilidades
# -----------------------------

def random_sleep(base: int = 2) -> None:
    """
    Pausa aleatoria para que la navegación no sea tan agresiva.
    """
    time.sleep(base + random.uniform(0.5, 1.2))


def save_json(data, path: Path) -> None:
    """
    Guarda un objeto Python en JSON bonito.
    """
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def sanitize_filename(text: str) -> str:
    """
    Convierte texto arbitrario en nombre de archivo seguro.
    """
    safe = "".join(c if c.isalnum() else "_" for c in text)
    return safe[:140]


def short_name_from_url(url: str) -> str:
    """
    Extrae una parte corta y útil desde la URL.
    """
    path = urlparse(url).path
    last_part = path.split("/")[-1] if path else "response"
    return sanitize_filename(last_part or "response")


# -----------------------------
# 3. Script principal
# -----------------------------

def run_ubereats_network_debug() -> None:
    """
    Flujo principal:
    - abre Uber Eats
    - escucha responses
    - guarda JSON interesantes
    """
    captured_metadata = []
    counter = {"value": 0}

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
            Listener que corre en cada respuesta HTTP.

            Qué guardamos:
            - solo content-type JSON
            - cualquier JSON, para no asumir de antemano nombres de endpoints
            """
            try:
                url = response.url
                content_type = response.headers.get("content-type", "").lower()

                # Debug visual en consola
                print("[URL]", url)

                if "application/json" not in content_type:
                    return

                try:
                    body = response.json()
                except Exception:
                    return

                counter["value"] += 1
                idx = counter["value"]

                file_name = f"{idx}_{short_name_from_url(url)}.json"
                json_path = DEBUG_DIR / file_name

                save_json(body, json_path)

                captured_metadata.append({
                    "idx": idx,
                    "url": url,
                    "status": response.status,
                    "content_type": content_type,
                    "saved_to": str(json_path),
                })

                print(f"[JSON] {response.status} | {url}")
                print(f"Guardado en: {json_path}")

            except Exception:
                # Nunca queremos romper el script por una sola respuesta
                pass

        # Registramos listener
        page.on("response", handle_response)

        try:
            print("1. Abriendo Uber Eats...")
            page.goto(START_URL, wait_until="domcontentloaded", timeout=45000)
            random_sleep(6)

            # Screenshot de referencia
            page.screenshot(path=str(OUTPUT_DIR / "ubereats_network_01_home.png"), full_page=True)

            # Intento suave de cerrar modales/cookies
            for selector in [
                "button:has-text('Aceptar')",
                "button:has-text('Aceptar todo')",
                "button:has-text('Continuar')",
                "button:has-text('Entendido')",
                "button:has-text('OK')",
                "button:has-text('Close')",
                "button:has-text('Cerrar')",
            ]:
                try:
                    page.locator(selector).first.click(timeout=2500)
                    print("Modal cerrado con:", selector)
                    break
                except Exception:
                    pass

            random_sleep(3)

            # Guardar HTML por si toca revisar estructura
            html_path = OUTPUT_DIR / "ubereats_home_source.html"
            html_path.write_text(page.content(), encoding="utf-8")
            print("HTML guardado en:", html_path)

            # También extraemos links visibles para ver si hay rutas útiles
            links = page.locator("a").evaluate_all("""
                els => els.map((el, i) => ({
                    idx: i,
                    text: (el.innerText || '').trim(),
                    href: el.href || null
                })).filter(x => x.text || x.href)
            """)

            links_path = OUTPUT_DIR / "ubereats_links_snapshot.json"
            save_json(links, links_path)
            print("Links visibles guardados en:", links_path)

            # Espera extra por si la app dispara requests tardíos
            random_sleep(8)

            # Guardar metadata de todas las respuestas JSON
            metadata_path = OUTPUT_DIR / "ubereats_network_metadata.json"
            save_json(captured_metadata, metadata_path)

            print("\n=== RESUMEN ===")
            print("Total JSON capturados:", len(captured_metadata))
            print("Metadata guardada en:", metadata_path)
            print("JSON guardados en:", DEBUG_DIR)

        finally:
            context.close()
            browser.close()


if __name__ == "__main__":
    run_ubereats_network_debug()