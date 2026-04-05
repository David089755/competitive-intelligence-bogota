import time
import random
from datetime import datetime


def now_str() -> str:
    """
    Devuelve la fecha/hora actual en formato ISO.
    Sirve para guardar cuándo se hizo cada scrape.
    """
    return datetime.utcnow().isoformat()


def random_sleep(base: int = 2) -> None:
    """
    Espera un tiempo aleatorio.
    Esto ayuda a que la navegación sea más natural
    y reduce un poco el riesgo de bloqueos por anti-bot.
    """
    time.sleep(base + random.uniform(0.5, 1.2))


def safe_click(page, selectors, timeout=5000):
    """
    Intenta hacer click usando una lista de selectores.

    ¿Por qué hacemos esto?
    Porque en scraping real un botón puede cambiar de nombre
    o aparecer con distintas variantes.

    Retorna:
    - True y el selector usado, si funcionó
    - False y None, si ninguno funcionó
    """
    for selector in selectors:
        try:
            locator = page.locator(selector).first
            locator.wait_for(timeout=timeout)
            locator.click(timeout=timeout)
            return True, selector
        except Exception:
            continue
    return False, None


def safe_fill(page, selectors, value, timeout=6000):
    """
    Intenta escribir texto en un input usando varios selectores posibles.

    Flujo:
    - espera el input
    - hace click
    - limpia el contenido
    - escribe el valor

    Retorna:
    - True y el selector usado, si funcionó
    - False y None, si no encontró un input válido
    """
    for selector in selectors:
        try:
            locator = page.locator(selector).first
            locator.wait_for(timeout=timeout)
            locator.click(timeout=timeout)
            locator.fill("")
            locator.type(value, delay=80)
            return True, selector
        except Exception:
            continue
    return False, None


def type_in_visible_search(page, value):
    """
    Busca un input de búsqueda visible y escribe allí.

    Esto es útil porque Rappi a veces tiene varios inputs en el DOM:
    algunos visibles y otros ocultos.

    Estrategia:
    - recorrer posibles selectores del buscador
    - revisar cuántos inputs existen
    - usar solo el que esté visible
    """
    candidates = [
        "input[role='searchbox']",
        "input[data-qa='input']",
        "input[type='search']",
        "input[placeholder*='Comida, restaurantes']",
        "input[aria-label*='Comida, restaurantes']",
    ]

    for selector in candidates:
        try:
            count = page.locator(selector).count()

            for i in range(count):
                locator = page.locator(selector).nth(i)
                try:
                    if locator.is_visible():
                        locator.click(timeout=4000)
                        locator.press("Control+A")
                        locator.press("Backspace")
                        locator.type(value, delay=100)
                        return True, f"{selector} [visible index={i}]"
                except Exception:
                    continue
        except Exception:
            continue

    return False, None


def find_restaurant_url(links, store_name: str):
    """
    Dada una lista de links encontrados en la página,
    intenta encontrar la mejor URL real del restaurante.

    Reglas:
    1. Solo nos interesan links que tengan '/restaurantes/'.
    2. Si alguno contiene el nombre del restaurante, lo priorizamos.
    3. Si no hay match exacto, usamos el primer candidato disponible.

    Ejemplo:
    - buscamos 'McDonald's'
    - puede aparecer como 'Mcdonalds turbo'
    - igual nos sirve porque es el restaurante real
    """
    store_name_lower = store_name.lower().replace("'", "").strip()

    candidatos = []

    for link in links:
        text = (link.get("text") or "").lower()
        href = (link.get("href") or "").lower()

        if "/restaurantes/" in href:
            candidatos.append(link)

    # Primero intentamos encontrar un match de nombre
    for c in candidatos:
        text = (c.get("text") or "").lower().replace("'", "")
        if store_name_lower in text:
            return c

    # Si no hubo match exacto, devolvemos el primero
    if candidatos:
        return candidatos[0]

    return None