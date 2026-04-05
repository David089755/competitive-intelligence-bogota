# Competitive Intelligence Scraper - Bogotá

Proyecto técnico para comparar plataformas de delivery en Bogotá.

## Scope actual
- Plataforma: Rappi
- Ciudad: Bogotá
- Restaurantes:
  - McDonald's
  - Burger King
  - KFC
- Direcciones:
  - Chapinero Alto
  - Zona T
  - Usaquén

## Stack
- Python
- Playwright
- Pandas

## Cómo correr

python -m venv .venv

## Windows
.venv\Scripts\activate

## Instalar dependencias
pip install -r requirements.txt
python -m playwright install

## EJECUTAR

python -m app.main

## Output

Genera un CSV en output/restaurant_links.csv.

## Limitaciones
Algunas rutas finales de restaurante pueden estar protegidas por anti-bot.
Los selectores del sitio pueden cambiar.
Este MVP resuelve descubrimiento de links de restaurantes; la extracción profunda de ítems/fees se deja como siguiente paso.