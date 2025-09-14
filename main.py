# main.py
from utils.browser import crear_navegador, cerrar_banners
from utils.sso_google import login_con_google
from utils.sage import buscar_en_sage  # exportar_ris_por_lotes lo conectamos luego
import config

if __name__ == "__main__":
    driver = crear_navegador(config.CHROMEDRIVER_PATH, config.DOWNLOAD_DIR)
    try:
        # 1) Entrar a SAGE vía CRAI con Google SSO
        URL_REVISTA = "https://journals-sagepub-com.crai.referencistas.com/"
        DOMINIO_OBJETIVO = "journals-sagepub-com"

        login_con_google(
            driver=driver,
            url_revista=URL_REVISTA,
            correo_institucional=config.USUARIO,
            contrasena=config.CONTRASENA,
            carpeta_descargas=config.DOWNLOAD_DIR,
            dominio_objetivo=DOMINIO_OBJETIVO
        )

        cerrar_banners(driver)

        # 2) Buscar la cadena entre comillas
        QUERY = "generative artificial intelligence"
        buscar_en_sage(driver, QUERY, config.DOWNLOAD_DIR)

        # 3) (Siguiente paso) Exportar RIS por lotes con paginación
        #    -> cuando me pases el DOM de resultados/exportación:
        # from utils.sage import exportar_ris_por_lotes
        # exportar_ris_por_lotes(driver, config.DOWNLOAD_DIR, max_paginas=10)

        print("URL actual:", driver.current_url)
        print("Título:", driver.title)

    finally:
        driver.quit()
