# utils/sage.py
# Automatiza la búsqueda en SAGE Journals.
# Paso 1: localizar el buscador de la home y enviar la cadena entre comillas.
# Paso 2 (pendiente): en la página de resultados, seleccionar/descargar RIS por lotes.

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time, os

def _guardar(driver, carpeta, nombre_png):
    try:
        os.makedirs(carpeta, exist_ok=True)
        driver.save_screenshot(os.path.join(carpeta, nombre_png))
    except Exception:
        pass

def _cerrar_banners_sage(driver):
    """Intenta cerrar el banner de cookies de SAGE (OneTrust u otros)."""
    candidatos = [
        (By.CSS_SELECTOR, "#onetrust-accept-btn-handler"),
        (By.XPATH, '//button[contains(., "Accept") or contains(., "Aceptar")]'),
        (By.XPATH, '//button[contains(., "Agree") or contains(., "De acuerdo")]'),
    ]
    for how, what in candidatos:
        try:
            WebDriverWait(driver, 3).until(EC.element_to_be_clickable((how, what))).click()
            time.sleep(0.5)
            break
        except Exception:
            pass

def buscar_en_sage(driver, query, carpeta_descargas):
    """
    Desde la home de SAGE:
      - cierra banners
      - escribe la cadena (entre comillas) en el input
      - envía el formulario
      - espera a que cargue la página de resultados
    """
    _cerrar_banners_sage(driver)

    # 1) Localizar el contenedor "role=search" para asegurarnos que la UI cargó
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'div[role="search"][aria-label*="Search Sage Journals"]'))
    )

    # 2) El id del input es dinámico, así que usamos selectores estables:
    #    - por name="AllField"
    #    - o por clase .quick-search__input
    input_selectores = [
        (By.NAME, "AllField"),
        (By.CSS_SELECTOR, 'input.quick-search__input'),
        (By.CSS_SELECTOR, 'form.quick-search__form input[type="search"]'),
    ]

    textbox = None
    for how, what in input_selectores:
        try:
            textbox = WebDriverWait(driver, 8).until(EC.element_to_be_clickable((how, what)))
            break
        except Exception:
            continue

    if textbox is None:
        raise RuntimeError("No se encontró el input de búsqueda en SAGE.")

    # 3) Escribir la cadena (forzamos comillas)
    cadena = f"\"{query}\"" if not (query.startswith('"') and query.endswith('"')) else query
    textbox.clear()
    textbox.send_keys(cadena)

    # 4) Enviar búsqueda: por el botón o submit del formulario
    try:
        boton_buscar = driver.find_element(By.CSS_SELECTOR, 'button.quick-search__button')
        boton_buscar.click()
    except Exception:
        # Alternativa: enviar ENTER al formulario si el botón no está accesible
        textbox.submit()

    # 5) Esperar a que cambie de la home a resultados
    #    Normalmente la URL incluye /action/doSearch o /search
    WebDriverWait(driver, 20).until(
        lambda d: ("/action/doSearch" in d.current_url) or ("/search" in d.current_url)
    )

    time.sleep(1)  # pequeña pausa para que terminen de renderizar contadores/listas
    _guardar(driver, carpeta_descargas, "06_sage_resultados.png")

    print("✅ Búsqueda enviada en SAGE. URL resultados:", driver.current_url)

    # (Placeholder) Devolvemos True si aparentemente estamos en resultados
    return True

# ------------------ ESQUELETO para la exportación RIS (pendiente DOM) ------------------

def exportar_ris_por_lotes(driver, carpeta_descargas, max_paginas=None):
    """
    PENDIENTE: Necesitamos el DOM de la página de resultados para:
      - marcar todos los resultados de la página (checkbox general)
      - abrir 'Export' / 'Cite' / 'Download' y elegir formato 'RIS'
      - confirmar descarga
      - paginar (siguiente página) y repetir
    Cuando me compartas los selectores, implemento este bloque.
    """
    raise NotImplementedError(
        "Necesito los selectores de la página de resultados de SAGE para implementar la exportación RIS y la paginación."
    )
