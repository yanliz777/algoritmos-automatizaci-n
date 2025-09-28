import os, time
from datetime import datetime
from urllib.parse import urlparse, parse_qs
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException, ElementClickInterceptedException
)
from .browser import esperar_descarga_por_extension, renombrar_si_es_necesario

# ---------------- utilidades pequeñas ----------------

def _scroll_into_view(driver, elem):
    try:
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", elem)
    except Exception:
        pass

def _click(driver, how, what, timeout=12, use_js_fallback=False):
    el = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((how, what)))
    _scroll_into_view(driver, el)
    try:
        el.click()
    except ElementClickInterceptedException:
        if use_js_fallback:
            driver.execute_script("arguments[0].click();", el)
        else:
            raise
    return el

def _type(driver, how, what, text, timeout=12):
    el = WebDriverWait(driver, timeout).until(EC.presence_of_element_located((how, what)))
    _scroll_into_view(driver, el)
    el.clear()
    el.send_keys(text)
    return el

def _guardar(driver, carpeta, nombre):
    try:
        os.makedirs(carpeta, exist_ok=True)
        driver.save_screenshot(os.path.join(carpeta, nombre))
    except Exception:
        pass

# ---------------- helpers específicos SD ----------------

def _esperar_resultados_listos(driver, timeout=20):
    """
    SRP lista si:
      - existe select-all (#select-all-results) o el botón Export
      - y hay resultados visibles
    """
    def listo(d):
        try:
            hay_select_all = bool(d.find_elements(By.CSS_SELECTOR, '#select-all-results'))
            hay_export = bool(d.find_elements(By.CSS_SELECTOR, 'button[data-aa-button="srp-export-multi-expand"]'))
            hay_items = bool(d.find_elements(By.CSS_SELECTOR, 'a.result-list-title-link, ol.search-results li, div.result-item-content'))
            return (hay_select_all or hay_export) and hay_items
        except Exception:
            return False
    WebDriverWait(driver, timeout).until(listo)

def _marcar_select_all_robusto(driver):
    """
    Marca 'Select all articles':
      - input#select-all-results
      - label[for="select-all-results"]
      - fallback: JS click y set checked=true
    """
    try:
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(0.2)
    except Exception:
        pass

    inp = None
    for sel in ['#select-all-results', 'input.checkbox-input#select-all-results', 'input.checkbox-input[aria-label*="Select all"]']:
        try:
            inp = driver.find_element(By.CSS_SELECTOR, sel)
            break
        except NoSuchElementException:
            continue

    lbl = None
    for sel in ['label[for="select-all-results"]', 'label.checkbox-label[for="select-all-results"]']:
        try:
            lbl = driver.find_element(By.CSS_SELECTOR, sel)
            break
        except NoSuchElementException:
            continue

    if not inp and not lbl:
        raise TimeoutException("No encontré el checkbox ni su label para 'Select all articles'.")

    def _checked():
        try:
            if inp and getattr(inp, "is_selected", None):
                if inp.is_selected():
                    return True
            if inp:
                aria = (inp.get_attribute("aria-checked") or "").lower()
                return aria == "true"
            return False
        except Exception:
            return False

    if not _checked() and inp:
        try:
            _scroll_into_view(driver, inp)
            try:
                inp.click()
            except ElementClickInterceptedException:
                driver.execute_script("arguments[0].click();", inp)
            time.sleep(0.25)
        except Exception:
            pass

    if not _checked() and lbl:
        try:
            _scroll_into_view(driver, lbl)
            try:
                lbl.click()
            except ElementClickInterceptedException:
                driver.execute_script("arguments[0].click();", lbl)
            time.sleep(0.25)
        except Exception:
            pass

    if not _checked() and inp:
        try:
            driver.execute_script("""
                const el = arguments[0];
                try { el.click(); } catch(e){}
                el.checked = true;
                el.setAttribute('aria-checked','true');
                el.dispatchEvent(new Event('change', {bubbles:true}));
            """, inp)
            time.sleep(0.25)
        except Exception:
            pass

    if not _checked():
        raise TimeoutException("No pude marcar 'Select all articles' (no quedó seleccionado).")

def _esperar_export_habilitado(driver, timeout=10):
    def habilitado(d):
        try:
            b = d.find_element(By.CSS_SELECTOR, 'button[data-aa-button="srp-export-multi-expand"]')
            aria = (b.get_attribute("aria-disabled") or "").lower()
            disabled = b.get_attribute("disabled")
            return (aria == "false") or (aria == "") and (disabled is None)
        except Exception:
            return False
    WebDriverWait(driver, timeout).until(habilitado)

def _get_per_page_actual(driver):
    try:
        li_activo = driver.find_element(By.CSS_SELECTOR, 'ol.ResultsPerPage li[aria-current="true"]')
        txt = li_activo.text or li_activo.get_attribute("textContent") or ""
        txt = txt.strip()
        return int(''.join(ch for ch in txt if ch.isdigit()))
    except Exception:
        return None

def _set_results_per_page(driver, per_page=100, timeout=20):
    rp = WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "ol.ResultsPerPage"))
    )
    _scroll_into_view(driver, rp)
    time.sleep(0.2)

    actual = _get_per_page_actual(driver)
    if actual == per_page:
        return True

    xpath = f'//ol[contains(@class,"ResultsPerPage")]//a[.//span[normalize-space()="{per_page}"]]'
    try:
        a = driver.find_element(By.XPATH, xpath)
    except NoSuchElementException:
        actual = _get_per_page_actual(driver)
        if actual == per_page:
            return True
        raise TimeoutException(f"No encontré el enlace para per-page = {per_page}.")

    href_before = driver.current_url
    try:
        _scroll_into_view(driver, a)
        a.click()
    except ElementClickInterceptedException:
        driver.execute_script("arguments[0].click();", a)

    def _recargo_ok(d):
        if d.current_url != href_before:
            return True
        try:
            val = _get_per_page_actual(d)
            return val == per_page
        except Exception:
            return False

    WebDriverWait(driver, timeout).until(_recargo_ok)
    _esperar_resultados_listos(driver, timeout=timeout)
    time.sleep(0.3)
    return True

def _get_offset_show_from_url(url):
    try:
        q = parse_qs(urlparse(url).query)
        offset = int((q.get('offset', ['0'])[0]) or 0)
        show = int((q.get('show', ['10'])[0]) or 10)
        return offset, show
    except Exception:
        return 0, 10

# --------------- paso SD-1: abrir home autenticada ---------------

def abrir_home_sciencedirect(driver, url, carpeta_descargas):
    driver.get(url)
    candidatos = [
        (By.CSS_SELECTOR, 'input#qs[name="qs"]'),
        (By.CSS_SELECTOR, 'input.search-input-field[name="qs"]'),
        (By.CSS_SELECTOR, 'input[aria-label*="Find articles"]'),
    ]
    visible = False
    for how, what in candidatos:
        try:
            WebDriverWait(driver, 15).until(EC.presence_of_element_located((how, what)))
            visible = True
            break
        except Exception:
            continue
    _guardar(driver, carpeta_descargas, "sd_home.png")
    if not visible:
        raise RuntimeError("No se detectó el buscador en ScienceDirect. ¿Sesión CRAI/SSO activa?")
    print("✅ Home de ScienceDirect lista:", driver.current_url)
    return True

# --------------- paso SD-2: buscar cadena ----------------

def buscar_en_sciencedirect(driver, query, carpeta_descargas):
    text = f"\"{query}\"" if '"' not in query else query
    _type(driver, By.CSS_SELECTOR, 'input#qs[name="qs"]', text)
    _click(driver, By.CSS_SELECTOR, 'button[aria-label="Submit quick search"]', use_js_fallback=True)
    _esperar_resultados_listos(driver, timeout=25)
    time.sleep(0.4)
    _guardar(driver, carpeta_descargas, "sd_resultados.png")
    print("✅ Resultados de ScienceDirect cargados:", driver.current_url)
    return True

# --------------- SD-2b: forzar 100 por página ----------------

def fijar_resultados_por_pagina(driver, per_page=100, carpeta_descargas=None):
    ok = _set_results_per_page(driver, per_page=per_page, timeout=25)
    if carpeta_descargas:
        _guardar(driver, carpeta_descargas, f"sd_per_page_{per_page}.png")
    if ok:
        print(f"✅ Per-page fijado a {per_page}.")
    return ok

# --------------- paso SD-3: exportar RIS de la página actual ---------------

def exportar_ris_pagina_actual_sd(driver, carpeta_descargas, consulta_slug="generative-artificial-intelligence", etiqueta="p1"):
    _esperar_resultados_listos(driver, timeout=25)
    _marcar_select_all_robusto(driver)

    try:
        _esperar_export_habilitado(driver, timeout=10)
    except TimeoutException:
        pass

    _click(driver, By.CSS_SELECTOR, 'button[data-aa-button="srp-export-multi-expand"]', use_js_fallback=True)
    time.sleep(0.3)
    _click(driver, By.CSS_SELECTOR, 'button[data-aa-button="srp-export-multi-ris"]', use_js_fallback=True)

    ruta = esperar_descarga_por_extension(carpeta_descargas, extension=".ris", timeout=120)
    fecha = datetime.now().strftime("%Y%m%d_%H%M")
    nombre_final = f"sd_{consulta_slug}_{etiqueta}_{fecha}.ris"
    final_path = renombrar_si_es_necesario(ruta, nombre_final)

    print(f"✅ SD {etiqueta}: descargado -> {final_path}")
    return final_path

# --------------- NUEVO: paginación ----------------

def ir_a_siguiente_pagina_sd(driver, timeout=20):
    """
    Click en 'next' y espera a que la URL cambie o aumente el offset.
    Devuelve True si avanzó, False si no hay siguiente.
    """
    _esperar_resultados_listos(driver, timeout=timeout)
    old_url = driver.current_url
    old_offset, old_show = _get_offset_show_from_url(old_url)

    try:
        nxt = driver.find_element(By.CSS_SELECTOR, 'li.pagination-link.next-link a.anchor[data-aa-name="srp-next-page"]')
    except NoSuchElementException:
        return False  # no hay siguiente

    _scroll_into_view(driver, nxt)
    try:
        nxt.click()
    except ElementClickInterceptedException:
        driver.execute_script("arguments[0].click();", nxt)

    def avanzó(d):
        new_url = d.current_url
        if new_url != old_url:
            return True
        new_offset, _ = _get_offset_show_from_url(new_url)
        return new_offset > old_offset

    try:
        WebDriverWait(driver, timeout).until(avanzó)
    except TimeoutException:
        # Si la URL no cambió pero la página recargó dinámicamente, revalidamos resultados.
        pass

    _esperar_resultados_listos(driver, timeout=timeout)
    time.sleep(0.3)
    return True

def descargar_varias_paginas_sd(driver, carpeta_descargas, consulta_slug="generative-artificial-intelligence", paginas=5, etiqueta_prefijo="p"):
    """
    Descarga RIS de la página actual y avanza 'next' hasta 'paginas' veces.
    Asume que ya está fijado show=100 y en resultados.
    """
    archivos = []
    for i in range(1, paginas + 1):
        etiqueta = f"{etiqueta_prefijo}{i}"
        path = exportar_ris_pagina_actual_sd(
            driver,
            carpeta_descargas=carpeta_descargas,
            consulta_slug=consulta_slug,
            etiqueta=etiqueta
        )
        archivos.append(path)

        if i < paginas:
            moved = ir_a_siguiente_pagina_sd(driver, timeout=25)
            if not moved:
                print("ℹ️ No hay más páginas (se detiene la paginación).")
                break

    return archivos