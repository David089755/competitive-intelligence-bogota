"""
Debug inicial para DiDi Food.

Objetivo:
- abrir la web
- cerrar modales/cookies si aparecen
- listar inputs, botones y links
- guardar screenshot

Este paso sirve para encontrar el input real de dirección.
"""

import time
import random
from pathlib import Path
from playwright.sync_api import sync_playwright


OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)


def random_sleep(base: int = 2) -> None:
    time.sleep(base + random.uniform(0.5, 1.2))


def run_didifood_inputs_debug() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            slow_mo=500,
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

        try:
            print("1. Abriendo DiDi Food...")
            page.goto("https://www.didiglobal.com/co/food", wait_until="domcontentloaded", timeout=45000)
            random_sleep(5)

            for selector in [
                "button:has-text('Aceptar')",
                "button:has-text('Aceptar todo')",
                "button:has-text('Continuar')",
                "button:has-text('Entendido')",
                "button:has-text('OK')",
                "button:has-text('Cerrar')",
            ]:
                try:
                    page.locator(selector).first.click(timeout=2500)
                    print("Cookie/modal cerrado con:", selector)
                    break
                except Exception:
                    pass

            random_sleep(3)

            screenshot_path = OUTPUT_DIR / "didifood_debug_home.png"
            page.screenshot(path=str(screenshot_path), full_page=True)
            print("Screenshot guardado en:", screenshot_path)

            inputs = page.locator("input").evaluate_all("""
                els => els.map((el, i) => ({
                    idx: i,
                    type: el.type || null,
                    name: el.name || null,
                    placeholder: el.placeholder || null,
                    ariaLabel: el.getAttribute('aria-label'),
                    role: el.getAttribute('role'),
                    value: el.value || null,
                    outerHTML: el.outerHTML.slice(0, 400)
                }))
            """)

            print("\\n=== INPUTS ===")
            for x in inputs:
                print(x)

            buttons = page.locator("button").evaluate_all("""
                els => els.map((el, i) => ({
                    idx: i,
                    text: (el.innerText || '').trim(),
                    ariaLabel: el.getAttribute('aria-label'),
                    outerHTML: el.outerHTML.slice(0, 300)
                }))
            """)

            print("\\n=== BUTTONS ===")
            for x in buttons[:50]:
                print(x)

            links = page.locator("a").evaluate_all("""
                els => els.slice(0, 60).map((el, i) => ({
                    idx: i,
                    text: (el.innerText || '').trim(),
                    href: el.href || null,
                    outerHTML: el.outerHTML.slice(0, 300)
                }))
            """)

            print("\\n=== LINKS ===")
            for x in links:
                print(x)

        finally:
            context.close()
            browser.close()


if __name__ == "__main__":
    run_didifood_inputs_debug()