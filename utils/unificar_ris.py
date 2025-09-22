#!/usr/bin/env python3
"""
unificar_ris.py

Lee todos los archivos .ris en una carpeta y genera un único CSV con
las columnas: title, year, authors.

Uso:
  python unificar_ris.py --indir /home/ycmejia/Descargas/Sage_Journals --output unificado.csv
"""

import os
import csv
import argparse

def parse_ris(file_path):
    records = []
    current = {}
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            # Normalizar espacios raros
            line = line.replace("\u00a0", " ").strip()
            if not line:
                continue

            if line.startswith("TY  -"):
                current = {"type": line[6:].strip()}
            elif line.startswith("T1  -"):  # Título
                current["title"] = line[6:].strip()
            elif line.startswith("AU  -"):  # Autor
                current.setdefault("authors", []).append(line[6:].strip())
            elif line.startswith("PY  -"):  # Año
                current["year"] = line[6:].strip()
            elif line.startswith("ER  -"):  # Fin de registro
                if current:
                    records.append(current)
                    current = {}
    return records


def unificar_ris(indir, output):
    all_records = []
    for fname in os.listdir(indir):
        if fname.endswith(".ris"):
            fpath = os.path.join(indir, fname)
            print(f"Procesando: {fpath}")
            recs = parse_ris(fpath)
            all_records.extend(recs)

    if not all_records:
        print("⚠️ No se encontraron registros en los archivos .ris")
        return

    with open(output, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["type", "title", "authors", "year"])
        for r in all_records:
            writer.writerow([
                r.get("type", ""),
                r.get("title", ""),
                "; ".join(r.get("authors", [])),
                r.get("year", "")
            ])
    print(f"✅ Unificación completada. Guardado en {output}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--indir", required=True, help="Directorio con archivos RIS")
    parser.add_argument("--output", required=True, help="Archivo CSV de salida")
    args = parser.parse_args()

    unificar_ris(args.indir, args.output)
