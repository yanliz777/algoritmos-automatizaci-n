# utils/sage.py
# Automatiza la búsqueda en SAGE Journals.
# Paso 1: localizar el buscador de la home y enviar la cadena entre comillas.
# Paso 2 (pendiente): en la página de resultados, seleccionar/descargar RIS por lotes.
from datetime import datetime
from selenium.common.exceptions import TimeoutException
from .browser import esperar_descarga_por_extension, renombrar_si_es_necesario
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


#******
from datetime import datetime
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from .browser import esperar_descarga_por_extension, renombrar_si_es_necesario

def _export_habilitado(d):
    """Devuelve True cuando el enlace 'Export selected citations' está habilitado."""
    try:
        a = d.find_element(By.CSS_SELECTOR, 'a[data-id="srp-export-citations"]')
        cls = a.get_attribute("class") or ""
        aria = (a.get_attribute("aria-disabled") or "").lower()
        disabled = a.get_attribute("disabled")
        return ("disabled" not in cls) and (aria != "true") and (disabled is None)
    except Exception:
        return False

def _cerrar_modal_export(driver, timeout=10):
    """Cierra el modal #exportCitation con el botón 'Close'."""
    try:
        modal = WebDriverWait(driver, timeout).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, '#exportCitation'))
        )
    except TimeoutException:
        return False

    # botón close
    candidatos = [
        (By.CSS_SELECTOR, '#exportCitation button.close[data-dismiss="modal"]'),
        (By.CSS_SELECTOR, '#exportCitation button.close'),
        (By.XPATH, '//*[@id="exportCitation"]//button[@data-dismiss="modal" and contains(@class,"close")]')
    ]
    for how, what in candidatos:
        try:
            WebDriverWait(driver, 5).until(EC.element_to_be_clickable((how, what))).click()
            # esperar a que desaparezca el modal
            WebDriverWait(driver, timeout).until(
                EC.invisibility_of_element_located((By.CSS_SELECTOR, '#exportCitation'))
            )
            return True
        except Exception:
            continue
    return False

def _ir_a_siguiente_pagina(driver):
    """
    Hace click en 'Siguiente' y espera a que cargue la nueva página.
    Devuelve True si navegó, False si no encontró el botón (última página).
    """
    candidatos = [
        (By.CSS_SELECTOR, 'a.pagination__link.next'),
        (By.CSS_SELECTOR, 'a.next.hvr-forward.pagination__link'),
        (By.XPATH, '//a[contains(@class,"pagination__link") and contains(@class,"next")]')
    ]
    next_link = None
    for how, what in candidatos:
        try:
            next_link = driver.find_element(how, what)
            break
        except NoSuchElementException:
            continue

    if not next_link:
        return False

    href_before = driver.current_url
    driver.execute_script("arguments[0].scrollIntoView({block:'end'});", next_link)
    next_link.click()

    # Esperar que cambie la URL o que se refresque el listado
    try:
        WebDriverWait(driver, 15).until(
            lambda d: d.current_url != href_before or _lista_resultados_cargada(d)
        )
        time.sleep(0.8)
        return True
    except TimeoutException:
        return False

def _lista_resultados_cargada(d):
    """Heurística simple: hay resultados listados (sin depender de selectores frágiles)."""
    try:
        # cualquier card/enlace de resultado
        items = d.find_elements(By.CSS_SELECTOR, 'a[href*="/doi/"], a.issue-item__title, div.search__item')
        return len(items) > 0
    except Exception:
        return False

def exportar_ris_pagina_actual(driver, carpeta_descargas, consulta_slug="generative-artificial-intelligence", etiqueta="p1"):
    """
    Selecciona todos los resultados visibles, abre Export, descarga RIS y CIERRA el modal.
    Usa tus selectores:
      - Select all: #action-bar-select-all
      - Export: a[data-id="srp-export-citations"]
      - Modal: #exportCitation
      - Descargar: a.download__btn
    """
    _cerrar_banners_sage(driver)

    # Select all
    chk_all = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, '#action-bar-select-all'))
    )
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", chk_all)
    if not chk_all.is_selected():
        chk_all.click()
        time.sleep(0.4)

    # Esperar que Export se habilite
    WebDriverWait(driver, 10).until(_export_habilitado)
    export_link = driver.find_element(By.CSS_SELECTOR, 'a[data-id="srp-export-citations"]')
    export_link.click()

    # Modal visible
    modal = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, '#exportCitation'))
    )
    time.sleep(0.3)

    # (El formato RIS parece ser el default; si hubiera un <select>, forzamos 'RIS')
    try:
        sel = modal.find_element(By.CSS_SELECTOR, 'select')
        for opt in sel.find_elements(By.TAG_NAME, 'option'):
            if "RIS" in (opt.text or ""):
                opt.click()
                time.sleep(0.3)
                break
    except Exception:
        pass

    # Descargar
    btn_download = WebDriverWait(modal, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, 'a.download__btn'))
    )
    btn_download.click()

    # Esperar archivo .ris
    ruta = esperar_descarga_por_extension(carpeta_descargas, extension=".ris", timeout=90)
    fecha = datetime.now().strftime("%Y%m%d_%H%M")
    nombre_final = f"sage_{consulta_slug}_{etiqueta}_{fecha}.ris"
    final_path = renombrar_si_es_necesario(ruta, nombre_final)
    print(f"✅ Página {etiqueta}: descargado -> {final_path}")

    # Cerrar modal
    _cerrar_modal_export(driver)
    return final_path

def exportar_ris_paginando(driver, carpeta_descargas, consulta_slug="generative-artificial-intelligence", max_paginas=5):
    """
    Exporta RIS de varias páginas: página actual + 'Siguiente' hasta max_paginas o fin.
    Retorna lista de rutas de archivos descargados.
    """
    rutas = []
    for i in range(1, max_paginas + 1):
        etiqueta = f"p{i}"
        print(f"--- Procesando {etiqueta} ---")
        try:
            ruta = exportar_ris_pagina_actual(driver, carpeta_descargas, consulta_slug, etiqueta)
            rutas.append(ruta)
        except Exception as e:
            print(f"⚠️  Falló exportación en {etiqueta}: {e}")
            break

        # Intentar ir a siguiente
        pudo = _ir_a_siguiente_pagina(driver)
        if not pudo:
            print("ℹ️  No hay más páginas (o no se encontró 'Siguiente').")
            break
        # pequeña espera para que renderice
        time.sleep(0.8)

    print(f"✅ Descargas completadas: {len(rutas)} archivo(s).")
    return rutas
#******


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
