# utils/ris_merge.py
# ============================================================
# Unificador y deduplicador de archivos RIS (SAGE + ScienceDirect)
# Lee .ris/.txt con contenido RIS desde varias carpetas, unifica,
# deduplica por DOI y, si no hay DOI, por título canónico.
# Exporta:
#   - CSV unificado (sin duplicados)
#   - CSV de duplicados eliminados (trazabilidad)
#   - JSONL (útil para apps posteriores)
# ============================================================

import os, re, unicodedata, json
from typing import List, Dict, Tuple, Iterable
import pandas as pd

# -------------------- Utilidades de normalización --------------------

def _norm_spaces(s: str) -> str:
    """Colapsa espacios repetidos y hace strip."""
    return re.sub(r"\s+", " ", s).strip()

def _norm_doi(raw: str) -> str:
    """Normaliza un DOI: quita prefijos, espacios, http(s)://doi.org/ etc."""
    if not raw:
        return ""
    s = raw.strip().replace("\\", "/").replace(" ", "")
    s = re.sub(r"(?i)^doi:\s*", "", s)
    s = re.sub(r"(?i)^https?://(dx\.)?doi\.org/", "", s)
    return s.strip().lower()

def _canon_title(t: str) -> str:
    """Crea una versión 'canónica' del título para dedupe por título."""
    if not t:
        return ""
    s = t.strip().lower()
    s = unicodedata.normalize("NFKD", s)              # quita tildes
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^a-z0-9]+", " ", s)                 # solo alfanumérico + espacio
    return _norm_spaces(s)

def _year_from_py(py: str) -> str:
    """Extrae año (4 dígitos) de campos PY/Y1/DA."""
    if not py:
        return ""
    m = re.search(r"\d{4}", py)
    return m.group(0) if m else ""

def _read_text(path: str) -> str:
    """Lee archivo como UTF-8 y si falla, latin-1."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError:
        with open(path, "r", encoding="latin-1") as f:
            return f.read()

def _looks_like_ris(txt: str) -> bool:
    """Heurística rápida: ¿parece un RIS? (busca TAGs 'XX  - ')."""
    hits = 0
    for ln in txt.splitlines()[:200]:
        if re.match(r"^[A-Z0-9]{2}\s*-\s+", ln):
            hits += 1
        if hits >= 3:
            return True
    return False

# -------------------- Parser RIS --------------------

def parse_ris_text(txt: str, source_db: str, source_file: str) -> List[Dict]:
    """Parsea texto RIS en una lista de diccionarios normalizados."""
    lines = txt.splitlines()
    recs: List[Dict] = []
    cur: Dict = {}
    authors: List[str] = []
    keywords: List[str] = []

    def _flush():
        """Cierra el registro en construcción y lo añade a la lista."""
        if not cur:
            return
        if authors:
            cur["authors"] = authors.copy()
        if keywords:
            cur["keywords"] = list(dict.fromkeys([_norm_spaces(k) for k in keywords if k.strip()]))

        # Claves de deduplicación
        cur["doi_norm"] = _norm_doi(cur.get("doi", ""))
        title_main = cur.get("title", "") or cur.get("ti", "")
        cur["title_canon"] = _canon_title(title_main)

        # Trazabilidad de origen
        cur.setdefault("sources", []).append(source_db)
        cur.setdefault("source_files", []).append(source_file)

        recs.append(cur.copy())

    for raw in lines:
        m = re.match(r"^([A-Z0-9]{2})\s*-\s*(.*)$", raw)
        if not m:
            continue
        tag, val = m.group(1), (m.group(2) or "").rstrip()

        if tag == "TY":
            if cur:
                _flush()
            cur = {"ty": val}
            authors = []
            keywords = []
        elif tag == "ER":
            _flush()
            cur = {}
            authors = []
            keywords = []
        elif tag in ("T1", "TI"):
            cur["title"] = _norm_spaces(val); cur["ti"] = cur["title"]
        elif tag in ("T2", "JF", "JO"):
            cur["journal"] = _norm_spaces(val)
        elif tag == "AU":
            if val.strip():
                authors.append(_norm_spaces(val))
        elif tag in ("PY", "Y1"):
            cur["year"] = _year_from_py(val)
            cur["date"] = val.strip()
        elif tag == "DA":
            cur["date"] = _norm_spaces(val)
        elif tag in ("AB", "N2"):
            # Conserva el abstract más largo si vienen varios
            cur["abstract"] = max([cur.get("abstract", ""), _norm_spaces(val)], key=len)
        elif tag == "KW":
            if val.strip():
                keywords.append(val)
        elif tag == "DO":
            cur["doi"] = _norm_doi(val)
        elif tag == "UR":
            cur["url"] = val.strip()
        elif tag == "SN":
            cur["issn"] = _norm_spaces(val)
        elif tag == "VL":
            cur["volume"] = _norm_spaces(val)
        elif tag == "IS":
            cur["issue"] = _norm_spaces(val)
        elif tag == "SP":
            cur["page_start"] = _norm_spaces(val)
        elif tag == "EP":
            cur["page_end"] = _norm_spaces(val)

    return recs

def parse_ris_file(path: str, source_db: str = "") -> List[Dict]:
    """Abre un archivo, valida que parezca RIS y lo parsea."""
    txt = _read_text(path)
    if not _looks_like_ris(txt):
        return []
    return parse_ris_text(txt, source_db=source_db or "unknown", source_file=path)

# -------------------- Descubrimiento de archivos --------------------

def _iter_candidate_files(folder: str, exts: Iterable[str]) -> Iterable[str]:
    """Itera archivos bajo 'folder' que terminen con alguna extensión en exts."""
    exts_l = tuple(e.lower() for e in exts)
    for root, _, files in os.walk(folder):
        for fn in files:
            if fn.lower().endswith(exts_l):
                yield os.path.join(root, fn)

def load_ris_from_dirs(
    dirs: List[Tuple[str, str]],
    exts: Iterable[str] = (".ris", ".RIS", ".txt", ".TXT"),
    verbose: bool = True
) -> List[Dict]:
    """
    Carga/parsea desde múltiples carpetas.
    Parámetros:
      - dirs: lista de (ruta_carpeta, etiqueta_source_db)
      - exts: extensiones a buscar (por defecto .ris y .txt)
      - verbose: si True, imprime diagnóstico
    """
    out: List[Dict] = []
    for folder, source in dirs:
        if not folder or not os.path.isdir(folder):
            if verbose:
                print(f"⚠️ Carpeta no existe o no es válida: {folder}")
            continue

        cand = list(_iter_candidate_files(folder, exts))
        if verbose:
            print(f"📂 {source:<13} -> {folder}")
            print(f"   Archivos candidatos ({', '.join(exts)}): {len(cand)}")
            for p in cand[:5]:
                print(f"   - {p}")

        count_before = len(out)
        for path in cand:
            try:
                recs = parse_ris_file(path, source_db=source)
                out.extend(recs)
            except Exception as e:
                print(f"⚠️ Error parseando {path}: {e}")

        if verbose:
            print(f"   Registros RIS válidos añadidos: {len(out) - count_before}")

    return out

# -------------------- Dedupe y fusión de registros --------------------

def _prefer(a: str, b: str) -> str:
    """Elige campo no vacío; si ambos, conserva el más largo."""
    a = (a or "").strip(); b = (b or "").strip()
    if a and not b: return a
    if b and not a: return b
    return a if len(a) >= len(b) else b

def _merge_lists(a: List[str], b: List[str]) -> List[str]:
    """Une listas sin duplicados (case-insensitive)."""
    merged, seen = [], set()
    for item in (a or []) + (b or []):
        key = item.strip()
        if key and key.lower() not in seen:
            seen.add(key.lower())
            merged.append(key)
    return merged

def merge_records(records: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
    """
    Dedupe por DOI normalizado; si no hay DOI, por título canónico.
    Devuelve:
      - lista de registros unificados (sin duplicados)
      - lista de duplicados eliminados con trazabilidad
    """
    by_key: Dict[Tuple[str, str], Dict] = {}
    dups: List[Dict] = []

    def key_for(r: Dict):
        if r.get("doi_norm"):
            return ("doi", r["doi_norm"])
        return ("title", r.get("title_canon", ""))

    def merge_two(dst: Dict, src: Dict):
        # Campos de texto
        for k in ["title","journal","year","date","abstract","doi","url","issn","volume","issue","page_start","page_end"]:
            dst[k] = _prefer(dst.get(k, ""), src.get(k, ""))
        # Listas
        dst["authors"]      = _merge_lists(dst.get("authors", []), src.get("authors", []))
        dst["keywords"]     = _merge_lists(dst.get("keywords", []), src.get("keywords", []))
        dst["sources"]      = _merge_lists(dst.get("sources", []), src.get("sources", []))
        dst["source_files"] = _merge_lists(dst.get("source_files", []), src.get("source_files", []))
        # Recalcula llaves normalizadas
        dst["doi_norm"]    = _norm_doi(dst.get("doi", "") or dst.get("doi_norm",""))
        dst["title_canon"] = _canon_title(dst.get("title","")) or dst.get("title_canon","")

    for r in records:
        k = key_for(r)
        if not k[1]:
            # sin DOI ni título canónico -> no deduplicable, se guarda con clave única
            by_key[("row", str(id(r)))] = r
            continue

        if k not in by_key:
            by_key[k] = r
        else:
            kept = by_key[k]
            dups.append({
                "dedupe_key_type": k[0],
                "dedupe_key_value": k[1],
                "kept_title": kept.get("title",""),
                "kept_doi": kept.get("doi",""),
                "kept_sources": "; ".join(kept.get("sources", [])),
                "dropped_title": r.get("title",""),
                "dropped_doi": r.get("doi",""),
                "dropped_sources": "; ".join(r.get("sources", [])),
                "dropped_file": "; ".join(r.get("source_files", [])),
            })
            merge_two(kept, r)

    result = list(by_key.values())

    # Ordena por año desc y luego título
    def _year_num(x: Dict) -> int:
        try:
            return int((x.get("year") or "0")[:4])
        except:
            return 0

    result.sort(key=lambda x: (-_year_num(x), x.get("title","").lower()))
    return result, dups

# -------------------- Exportadores --------------------

def records_to_dataframe(records: List[Dict]) -> pd.DataFrame:
    """Convierte lista de registros normalizados a DataFrame."""
    rows = []
    for r in records:
        rows.append({
            "title": r.get("title",""),
            "authors": "; ".join(r.get("authors", [])),
            "year": r.get("year",""),
            "date": r.get("date",""),
            "journal": r.get("journal",""),
            "doi": r.get("doi",""),
            "url": r.get("url",""),
            "abstract": r.get("abstract",""),
            "keywords": "; ".join(r.get("keywords", [])),
            "issn": r.get("issn",""),
            "volume": r.get("volume",""),
            "issue": r.get("issue",""),
            "page_start": r.get("page_start",""),
            "page_end": r.get("page_end",""),
            "sources": "; ".join(r.get("sources", [])),
            "source_files": "; ".join(r.get("source_files", [])),
        })
    return pd.DataFrame(rows)

def duplicates_to_dataframe(dups: List[Dict]) -> pd.DataFrame:
    """Convierte duplicados eliminados a DataFrame (para auditoría)."""
    return pd.DataFrame(dups)

def export_outputs(unified: List[Dict], duplicates: List[Dict], out_dir: str, base_name: str="unificado"):
    """Exporta CSV unificado, CSV de duplicados y JSONL."""
    os.makedirs(out_dir, exist_ok=True)
    df_u = records_to_dataframe(unified)
    df_d = duplicates_to_dataframe(duplicates)

    csv_u   = os.path.join(out_dir, f"{base_name}.csv")
    csv_d   = os.path.join(out_dir, f"{base_name}_duplicados_eliminados.csv")
    jsonl_u = os.path.join(out_dir, f"{base_name}.jsonl")

    df_u.to_csv(csv_u, index=False, encoding="utf-8-sig")
    df_d.to_csv(csv_d, index=False, encoding="utf-8-sig")

    with open(jsonl_u, "w", encoding="utf-8") as f:
        for r in unified:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"✅ Unificado deduplicado -> {csv_u}")
    print(f"✅ Duplicados eliminados -> {csv_d}")
    print(f"✅ JSONL (para app)     -> {jsonl_u}")
