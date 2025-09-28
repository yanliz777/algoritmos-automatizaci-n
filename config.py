# config.py
# === CONFIGURACIÓN DEL PROYECTO ===

import platform
import os

# === RUTAS SEGÚN EL SISTEMA OPERATIVO ===
if platform.system() == "Windows":
    # Windows
    CHROMEDRIVER_PATH = r"C:\Users\USER\Desktop\YAN\Carpeta Universidad\decimo-semestre\Analisis-de-algoritmos\Proyecto-final-algoritmos\chromedriver.exe"
    DOWNLOAD_DIR_SAGE = r"C:\Users\USER\Desktop\proyecto-final-algoritmos\Sage_Journals"
    DOWNLOAD_DIR_SCIENCEDIRECT = r"C:\Users\USER\Desktop\proyecto-final-algoritmos\science_direct"
else:
    # Linux / macOS
    CHROMEDRIVER_PATH = "/usr/bin/chromedriver"
    DOWNLOAD_DIR_SAGE = os.path.expanduser("~/Descargas/Sage_Journals")
    DOWNLOAD_DIR_SCIENCEDIRECT = os.path.expanduser("~/Descargas/science_direct")

# === URLS IMPORTANTES ===
URL_LOGIN = "https://library.uniquindio.edu.co/databases"

# === CREDENCIALES ===
USUARIO = "yarleyc.mejiab@uqvirtual.edu.co"
CONTRASENA = "Familia967vfg15a"
#ss