# utils/navegador.py
import os, time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def crear_navegador(ruta_driver, carpeta_descargas):
    os.makedirs(carpeta_descargas, exist_ok=True)
    opciones = Options()
    preferencias = {
        "download.default_directory": carpeta_descargas,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
    }
    opciones.add_experimental_option("prefs", preferencias)
    opciones.add_argument("--start-maximized")

    # ✨ Flags para reducir prompts de bienvenida/sincronización
    opciones.add_argument("--no-first-run")
    opciones.add_argument("--no-default-browser-check")
    opciones.add_argument("--disable-sync")

    servicio = Service(ruta_driver)
    return webdriver.Chrome(service=servicio, options=opciones)

def cerrar_banners(driver):
    posibles = [
        (By.CSS_SELECTOR, 'button#onetrust-accept-btn-handler'),
        (By.XPATH, '//button[contains(., "Aceptar") or contains(., "Accept")]'),
        (By.XPATH, '//button[contains(., "De acuerdo") or contains(., "Agree")]'),
    ]
    for como, que in posibles:
        try:
            WebDriverWait(driver, 3).until(EC.element_to_be_clickable((como, que))).click()
            time.sleep(0.5)
        except Exception:
            pass
