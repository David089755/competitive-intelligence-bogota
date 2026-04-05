from playwright.sync_api import sync_playwright

from app.utils import (
    now_str,
    random_sleep,
    safe_click,
    safe_fill,
    type_in_visible_search,
    find_restaurant_url,
)


def scrape_restaurant_link(address_text: str, store_name: str) -> dict:
    """
    Hace el scraping de una combinación:
    - una dirección
    - un restaurante

    Objetivo de esta función:
    encontrar la URL real del restaurante en Rappi
    y devolver un resultado estructurado.
    """

    # Inicia Playwright
    with sync_playwright() as p:

        # Abre Chromium visible (headless=False) para debug
        # slow_mo agrega una pequeña pausa entre acciones
        browser = p.chromium.launch(
            headless=False,
            slow_mo=500,
        )

        # Crea un contexto de navegador como si fuera una sesión nueva
        context = browser.new_context(
            viewport={"width": 1440, "height": 1200},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        )

        # Abre una nueva pestaña
        page = context.new_page()

        # Timeout por defecto para acciones y navegación
        page.set_default_timeout(15000)
        page.set_default_navigation_timeout(45000)

        try:
            print(f"\n--- Procesando: {address_text} | {store_name} ---")

            # 1. Abrir Rappi
            page.goto("https://www.rappi.com.co/", wait_until="domcontentloaded", timeout=45000)
            random_sleep(3)

            # 2. Cerrar banners/cookies si aparecen
            safe_click(page, [
                "button:has-text('Aceptar')",
                "button:has-text('Entendido')",
                "button:has-text('Continuar')",
                "button:has-text('Aceptar y continuar')",
                "[data-qa='accept-cookies']",
            ], timeout=2500)

            random_sleep(2)

            # 3. Escribir la dirección del usuario
            ok_address, _ = safe_fill(page, [
                "input[placeholder='¿Dónde quieres recibir tu compra?']",
                "input[placeholder*='¿Dónde quieres recibir tu compra?']",
                "input[type='text']",
            ], address_text)

            if not ok_address:
                raise Exception("No se pudo escribir la dirección")

            random_sleep(4)

            # 4. Confirmar la dirección seleccionando una sugerencia
            ok_confirm, _ = safe_click(page, [
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

            if not ok_confirm:
                raise Exception("No se pudo confirmar la dirección")

            random_sleep(8)

            # 5. Escribir el nombre del restaurante en el buscador
            ok_search, _ = type_in_visible_search(page, store_name)

            if not ok_search:
                raise Exception("No se pudo escribir en el buscador")

            random_sleep(5)

            # 6. Extraer todos los links visibles de la página
            # Esto nos sirve para luego encontrar la URL correcta del restaurante
            links = page.locator("a").evaluate_all("""
                els => els.map((el, i) => ({
                    idx: i,
                    text: (el.innerText || '').trim(),
                    href: el.href || null
                })).filter(x => x.text || x.href)
            """)

            # 7. Buscar entre esos links el restaurante correcto
            match = find_restaurant_url(links, store_name)

            if not match:
                raise Exception("No encontré ninguna URL válida del restaurante")

            # 8. Retornar el resultado en formato estructurado
            return {
                "scraped_at": now_str(),
                "platform": "Rappi",
                "address_text": address_text,
                "store_name": store_name,
                "restaurant_text": match.get("text"),
                "restaurant_url": match.get("href"),
                "status": "success",
            }

        except Exception as exc:
            # Si algo falla, devolvemos una fila con error
            return {
                "scraped_at": now_str(),
                "platform": "Rappi",
                "address_text": address_text,
                "store_name": store_name,
                "restaurant_text": None,
                "restaurant_url": None,
                "status": f"error: {exc}",
            }

        finally:
            # Cerrar recursos siempre, haya éxito o error
            context.close()
            browser.close()