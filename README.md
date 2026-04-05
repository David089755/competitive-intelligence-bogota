# 🍔 Competitive Intelligence - Rappi Bogotá

## 📌 Objetivo
Construir un pipeline automatizado para analizar precios y posicionamiento competitivo entre restaurantes en plataformas de delivery en Bogotá.

El enfoque se centra en comparar marcas clave como McDonald's, Burger King y KFC dentro de Rappi.

---

## 🧠 Metodología

El proyecto sigue tres etapas principales:

### 1. Extracción de datos
- Automatización con Playwright
- Navegación en Rappi simulando usuario real
- Intercepción de endpoints internos (no scraping del DOM)
- Extracción de menú, precios, delivery y ETA

### 2. Transformación
- Limpieza de datos
- Normalización de productos comparables
- Eliminación de outliers (combos familiares, promos)

### 3. Análisis
- Comparación entre marcas
- Cálculo de precios promedio
- Generación de tablas pivot y gráficos

---

## 🏪 Restaurantes analizados

- McDonald's
- Burger King
- KFC

---

## ⚙️ Instalación

```bash
pip install -r requirements.txt
python -m playwright install