# config.py
# === CONFIGURACIÓN DEL PROYECTO ===

import platform
from pathlib import Path

# === DETECTAR SISTEMA OPERATIVO ===
SO = platform.system()

# === BASE DEL PROYECTO SEGÚN EL USUARIO ===
if SO == "Windows":
    # ⚠️ Tu compañero en Windows cambia solo esta ruta
    BASE_DIR = Path(r"C:\Users\USER\Desktop\YAN\Carpeta Universidad\decimo-semestre\Analisis-de-algoritmos\Proyecto-final-algoritmos")
else:
    # ⚠️ Tú en Ubuntu
    BASE_DIR = Path("/home/ycmejia/Escritorio/PROYECTO ALGORITMOS")

# === CHROMEDRIVER ===
if SO == "Windows":
    CHROMEDRIVER_PATH = BASE_DIR / "chromedriver.exe"
else:
    CHROMEDRIVER_PATH = Path("/usr/bin/chromedriver")  # instalado en Linux vía apt

# === RUTAS DE DESCARGA ===
DOWNLOAD_DIR_SAGE = BASE_DIR / "bases_de_datos" / "Sage_Journals"
DOWNLOAD_DIR_SCIENCEDIRECT = BASE_DIR / "bases_de_datos" / "science_direct"

# === DIRECTORIO DE SALIDA ===
OUTPUT_DIR_BIBLIO = BASE_DIR / "salidas"

# === URLS IMPORTANTES ===
URL_LOGIN = "https://library.uniquindio.edu.co/databases"
SCIENCEDIRECT_URL = "https://www-sciencedirect-com.crai.referencistas.com/"

# === CREDENCIALES ===
USUARIO = "yarleyc.mejiab@uqvirtual.edu.co"
CONTRASENA = "Familia967vfg15a"
