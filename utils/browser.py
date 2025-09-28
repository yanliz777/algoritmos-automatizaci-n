# utils/browser.py
import os
import time
import glob
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def crear_navegador(ruta_driver: str = None, carpeta_descargas: str = ".") -> webdriver.Chrome:
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
    opciones.add_argument("--no-first-run")
    opciones.add_argument("--no-default-browser-check")
    opciones.add_argument("--disable-sync")
    opciones.binary_location = "/usr/bin/google-chrome"

    # 👇 Fuerza a usar Google Chrome en lugar de Chromium
    opciones.binary_location = "/usr/bin/google-chrome"

    if ruta_driver:
        servicio = Service(ruta_driver)
        return webdriver.Chrome(service=servicio, options=opciones)
    return webdriver.Chrome(options=opciones)


def cerrar_banners(driver: webdriver.Chrome) -> None:
    """
    Intenta cerrar banners comunes de cookies/consentimiento.

    Args:
        driver (webdriver.Chrome): Instancia activa del navegador.
    """
    posibles = [
        (By.CSS_SELECTOR, 'button#onetrust-accept-btn-handler'),
        (By.XPATH, '//button[contains(., "Aceptar") or contains(., "Accept")]'),
        (By.XPATH, '//button[contains(., "De acuerdo") or contains(., "Agree")]'),
    ]

    for como, que in posibles:
        try:
            WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((como, que))
            ).click()
            time.sleep(0.5)
        except Exception:
            pass


def esperar_descarga_por_extension(
    carpeta_descargas: str,
    extension: str = ".ris",
    timeout: int = 60
) -> str | None:
    """
    Espera hasta que aparezca un archivo con la extensión dada en la carpeta de descargas.

    Args:
        carpeta_descargas (str): Carpeta donde se espera la descarga.
        extension (str): Extensión del archivo esperado (por defecto ".ris").
        timeout (int): Tiempo máximo de espera en segundos.

    Returns:
        str | None: Ruta del archivo descargado más reciente, o None si no aparece.
    """
    inicio = time.time()
    fin = inicio + timeout
    ya_existentes = set(glob.glob(os.path.join(carpeta_descargas, f"*{extension}")))
    ultimo = None

    while time.time() < fin:
        candidatos = set(glob.glob(os.path.join(carpeta_descargas, f"*{extension}")))
        nuevos = [
            p for p in candidatos
            if p not in ya_existentes and os.path.getmtime(p) >= inicio - 1
        ]
        if nuevos:
            nuevos.sort(key=os.path.getmtime, reverse=True)
            ultimo = nuevos[0]
            break

        if candidatos:
            ordenados = sorted(candidatos, key=os.path.getmtime, reverse=True)
            if os.path.getmtime(ordenados[0]) >= inicio:
                ultimo = ordenados[0]
                break

        time.sleep(0.3)

    return ultimo


def renombrar_si_es_necesario(ruta_archivo: str, nombre_final_sugerido: str) -> str | None:
    """
    Renombra un archivo descargado si es necesario.

    Args:
        ruta_archivo (str): Ruta original del archivo.
        nombre_final_sugerido (str): Nombre final deseado.

    Returns:
        str | None: Ruta final del archivo renombrado, o la original si no se pudo.
    """
    if not ruta_archivo:
        return None

    carpeta = os.path.dirname(ruta_archivo)
    destino = os.path.join(carpeta, nombre_final_sugerido)

    try:
        if os.path.abspath(ruta_archivo) != os.path.abspath(destino):
            os.replace(ruta_archivo, destino)
        return destino
    except Exception:
        return ruta_archivo
