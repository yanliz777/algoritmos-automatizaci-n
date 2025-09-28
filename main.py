# main.py
from utils.browser import crear_navegador, cerrar_banners
from utils.sso_google import login_con_google
from utils.sage import buscar_en_sage, exportar_ris_paginando
import config

if __name__ == "__main__":
    # 👇 Usa CHROMEDRIVER_PATH si lo tienes en config, si no lo dejas en None
    driver = crear_navegador(
        ruta_driver=getattr(config, "CHROMEDRIVER_PATH", None),
        carpeta_descargas=config.DOWNLOAD_DIR_SAGE
    )

    try:
        URL_REVISTA = "https://journals-sagepub-com.crai.referencistas.com/"
        DOMINIO_OBJETIVO = "journals-sagepub-com"

        # === Login con Google institucional ===
        login_con_google(
            driver=driver,
            url_revista=URL_REVISTA,
            correo_institucional=config.USUARIO,
            contrasena=config.CONTRASENA,
            carpeta_descargas=config.DOWNLOAD_DIR_SAGE,
            dominio_objetivo=DOMINIO_OBJETIVO
        )

        # === Cerrar posibles banners de cookies u otros ===
        cerrar_banners(driver)

        # === Búsqueda en SAGE ===
        QUERY = "generative artificial intelligence"
        buscar_en_sage(driver, QUERY, config.DOWNLOAD_DIR_SAGE)

        # === Exportar resultados en formato RIS, varias páginas ===
        exportar_ris_paginando(
            driver,
            carpeta_descargas=config.DOWNLOAD_DIR_SAGE,
            consulta_slug="generative-artificial-intelligence",
            max_paginas=5  # Cambia a 10 para ≈ 100 artículos si pageSize=10
        )

        print("URL actual:", driver.current_url)
        print("Título:", driver.title)

    finally:
        driver.quit()
