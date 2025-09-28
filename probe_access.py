from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time, os

# === CONFIGURA ESTO (Ubuntu) ===
CHROMEDRIVER_PATH = "/usr/bin/chromedriver"
DOWNLOAD_DIR = "/home/ycmejia/Escritorio/PROYECTO ALGORITMOS/bibliometria_ai/downloads"

URLS_A_PROBAR = [
    # SAGE vía CRAI
    "https://journals-sagepub-com.crai.referencistas.com/",
    # ScienceDirect vía CRAI
    "https://www-sciencedirect-com.crai.referencistas.com/",
]

# Heurística de detección de login (elementos típicos)
LOGIN_SELECTORS = [
    (By.CSS_SELECTOR, 'input[type="email"]'),
    (By.CSS_SELECTOR, 'input[type="text"][name*="user" i]'),
    (By.CSS_SELECTOR, 'input[type="password"]'),
    (By.XPATH, '//button[contains(translate(.,"SIGNININICIAR","signiniciar"), "sign in") or contains(., "Iniciar sesión")]'),
]

def build_driver():
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    opts = Options()
    # Descargas sin prompts
    prefs = {
        "download.default_directory": DOWNLOAD_DIR,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
    }
    opts.add_experimental_option("prefs", prefs)
    opts.add_argument("--start-maximized")
    # Descomenta si necesitas español forzado:
    # opts.add_argument("--lang=es-419")

    service = Service(CHROMEDRIVER_PATH)
    return webdriver.Chrome(service=service, options=opts)

def hay_login_en_pantalla(driver):
    """Detecta rápidamente un formulario de login."""
    try:
        for how, what in LOGIN_SELECTORS:
            if driver.find_elements(how, what):
                return True
        if len(driver.find_elements(By.TAG_NAME, "iframe")) >= 2 and "login" in driver.current_url.lower():
            return True
    except Exception:
        pass
    return False

def cerrar_banners_comunes(driver):
    """Intenta cerrar banners de cookies comunes."""
    posibles = [
        (By.XPATH, '//button[contains(., "Aceptar") or contains(., "Accept")]'),
        (By.XPATH, '//button[contains(., "De acuerdo") or contains(., "Agree")]'),
        (By.CSS_SELECTOR, 'button#onetrust-accept-btn-handler'),
    ]
    for how, what in posibles:
        try:
            WebDriverWait(driver, 3).until(EC.element_to_be_clickable((how, what))).click()
            time.sleep(0.5)
        except Exception:
            pass

def probar_url(driver, url):
    print(f"\n==> Abriendo: {url}")
    driver.get(url)

    time.sleep(3)
    cerrar_banners_comunes(driver)

    try:
        WebDriverWait(driver, 12).until(
            lambda d: hay_login_en_pantalla(d) or len(d.find_elements(By.TAG_NAME, "a")) > 10
        )
    except Exception:
        pass

    ts = str(int(time.time()))
    screenshot_path = os.path.join(DOWNLOAD_DIR, f"screenshot_{ts}.png")
    try:
        driver.save_screenshot(screenshot_path)
        print(f"Screenshot guardado: {screenshot_path}")
    except Exception:
        pass

    print(f"Título: {driver.title!r}")
    print(f"URL actual: {driver.current_url}")

    if hay_login_en_pantalla(driver):
        print("➡️  Detección: Parece que requiere LOGIN (formulario visible).")
        return "LOGIN"
    else:
        print("✅ Detección: No se ve login. Probablemente ya tienes acceso.")
        return "OK"

def main():
    driver = build_driver()
    try:
        resultados = {}
        for url in URLS_A_PROBAR:
            resultados[url] = probar_url(driver, url)

        print("\nResumen:")
        for u, r in resultados.items():
            print(f" - {u} -> {r}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
