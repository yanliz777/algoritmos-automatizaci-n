#!/usr/bin/env python3
import os, time
import pandas as pd
import matplotlib.pyplot as plt
from collections import Counter

# ---------- Rutas ----------
INPUT = "/home/ycmejia/Escritorio/PROYECTO ALGORITMOS/salidas/unificado_ai_generativa.csv"
OUTDIR = "salida_bibliometria"
os.makedirs(OUTDIR, exist_ok=True)

# ---------- Carga de datos ----------
df = pd.read_csv(INPUT)
df["year"] = pd.to_numeric(df.get("year", 0), errors="coerce").fillna(0).astype(int)
df["title"] = df.get("title", df.columns[0]).astype(str)

# ---------- Ordenar productos ----------
sorted_df = df.sort_values(["year", "title"], ascending=[True, True])
sorted_df.to_csv(f"{OUTDIR}/sorted_products.csv", index=False)

# ---------- Top-15 autores ----------
if "authors" not in df.columns:
    df["authors"] = df["author"] if "author" in df.columns else ""
counts = Counter()
for cell in df["authors"].astype(str):
    parts = [p.strip() for p in cell.replace("\n",";").replace(",",";").split(";") if p.strip()]
    for p in parts: counts[p] += 1
top_authors = pd.DataFrame(counts.most_common(15), columns=["author","count"])\
                 .sort_values("count", ascending=True)
top_authors.to_csv(f"{OUTDIR}/top15_autores.csv", index=False)

# ---------- Clave entera ----------
def clave(row):
    return int(row["year"]) * 100000 + (hash(row["title"]) & 0xFFFF)
claves = [clave(r) for _, r in df.iterrows()]

# ==============================================================
# =============== ALGORITMOS DE ORDENAMIENTO ===================
# ==============================================================

def timsort(a):
    """
    TimSort (versión simplificada).
    Combina insertion sort en 'runs' pequeños con merge sort.
    """
    arr = list(a)
    RUN = 32

    def insertion_sort(l, r):
        for i in range(l+1, r+1):
            key = arr[i]
            j = i - 1
            while j >= l and arr[j] > key:
                arr[j+1] = arr[j]
                j -= 1
            arr[j+1] = key

    def merge(l, m, r):
        left, right = arr[l:m+1], arr[m+1:r+1]
        i = j = 0
        k = l
        while i < len(left) and j < len(right):
            if left[i] <= right[j]:
                arr[k] = left[i]; i += 1
            else:
                arr[k] = right[j]; j += 1
            k += 1
        while i < len(left):  arr[k] = left[i];  i += 1; k += 1
        while j < len(right): arr[k] = right[j]; j += 1; k += 1

    # 1. ordenar bloques pequeños
    n = len(arr)
    for start in range(0, n, RUN):
        end = min(start + RUN - 1, n - 1)
        insertion_sort(start, end)

    # 2. ir combinando
    size = RUN
    while size < n:
        for left in range(0, n, 2*size):
            mid = min(n-1, left + size - 1)
            right = min((left + 2*size - 1), n-1)
            if mid < right:
                merge(left, mid, right)
        size *= 2
    return arr

def selection(a):
    """Selection Sort: busca el mínimo y lo coloca al frente."""
    arr = list(a)
    for i in range(len(arr)):
        m = i
        for j in range(i+1, len(arr)):
            if arr[j] < arr[m]:
                m = j
        arr[i], arr[m] = arr[m], arr[i]
    return arr

def comb(a):
    """Comb Sort: mejora de bubble con 'gap' decreciente."""
    arr = list(a)
    gap = len(arr)
    shrink = 1.3
    swapped = True
    while gap > 1 or swapped:
        gap = max(1, int(gap / shrink))
        swapped = False
        for i in range(len(arr) - gap):
            if arr[i] > arr[i + gap]:
                arr[i], arr[i + gap] = arr[i + gap], arr[i]
                swapped = True
    return arr

def quick(a):
    """QuickSort recursivo (divide y conquista)."""
    arr = list(a)
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr)//2]
    left  = [x for x in arr if x < pivot]
    mid   = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quick(left) + mid + quick(right)

def heap(a):
    """HeapSort usando heapq (montículo mínimo)."""
    import heapq
    arr = list(a)
    heapq.heapify(arr)
    return [heapq.heappop(arr) for _ in range(len(arr))]

def gnome(a):
    """Gnome Sort: similar a insertion pero con movimientos locales."""
    arr = list(a)
    i = 0
    while i < len(arr):
        if i == 0 or arr[i] >= arr[i-1]:
            i += 1
        else:
            arr[i], arr[i-1] = arr[i-1], arr[i]
            i -= 1
    return arr

def binary_insertion(a):
    """Insertion Sort usando búsqueda binaria para ubicar el elemento."""
    from bisect import insort
    res = []
    for x in a:
        insort(res, x)
    return res

def radix(a):
    """Radix Sort para enteros no negativos (base 10)."""
    arr = list(a)
    if not arr: return arr
    max_val = max(arr)
    exp = 1
    while max_val // exp > 0:
        buckets = [[] for _ in range(10)]
        for num in arr:
            buckets[(num // exp) % 10].append(num)
        arr = [num for bucket in buckets for num in bucket]
        exp *= 10
    return arr

def bucket(a):
    """Bucket Sort: reparte elementos en cubetas y ordena cada una."""
    arr = list(a)
    if len(arr) == 0: return arr
    min_val, max_val = min(arr), max(arr)
    bucket_count = max(1, int(len(arr) ** 0.5))
    size = (max_val - min_val) / bucket_count + 1e-9
    buckets = [[] for _ in range(bucket_count)]
    for num in arr:
        idx = int((num - min_val) // size)
        buckets[idx].append(num)
    res = []
    for b in buckets:
        res.extend(sorted(b))
    return res

def pigeonhole(a):
    """Pigeonhole Sort: cuenta ocurrencias (solo enteros)."""
    arr = list(a)
    if not arr: return arr
    mi, ma = min(arr), max(arr)
    holes = [0]*(ma - mi + 1)
    for x in arr:
        holes[x - mi] += 1
    res = []
    for i, c in enumerate(holes):
        res.extend([i + mi] * c)
    return res

def tree(a):
    """Tree Sort: inserta en un árbol binario y hace recorrido en orden."""
    class Node:
        __slots__ = ("v","l","r")
        def __init__(self, v): self.v=v; self.l=None; self.r=None
        def insert(self, x):
            if x < self.v:
                self.l.insert(x) if self.l else setattr(self, "l", Node(x))
            else:
                self.r.insert(x) if self.r else setattr(self, "r", Node(x))
        def inorder(self, res):
            if self.l: self.l.inorder(res)
            res.append(self.v)
            if self.r: self.r.inorder(res)
    arr = list(a)
    if not arr: return arr
    it = iter(arr)
    root = Node(next(it))
    for x in it:
        root.insert(x)
    res = []
    root.inorder(res)
    return res

def bitonic(a):
    """
    Bitonic Sort: algoritmo de comparación para potencias de 2.
    Aquí se rellena a potencia de 2 si hace falta.
    """
    arr = list(a)
    n = 1
    while n < len(arr): n *= 2
    arr += [max(arr)] * (n - len(arr))

    def compare_and_swap(i, j, asc):
        if (arr[i] > arr[j]) == asc:
            arr[i], arr[j] = arr[j], arr[i]

    def bitonic_merge(l, cnt, asc):
        if cnt > 1:
            k = cnt // 2
            for i in range(l, l + k):
                compare_and_swap(i, i + k, asc)
            bitonic_merge(l, k, asc)
            bitonic_merge(l + k, k, asc)

    def bitonic_sort(l, cnt, asc):
        if cnt > 1:
            k = cnt // 2
            bitonic_sort(l, k, True)
            bitonic_sort(l + k, k, False)
            bitonic_merge(l, cnt, asc)

    bitonic_sort(0, n, True)
    return arr[:len(a)]

# ---------- Lista de algoritmos ----------
ALGORITHMS = [
    ("TimSort", timsort),
    ("SelectionSort", selection),
    ("CombSort", comb),
    ("QuickSort", quick),
    ("HeapSort", heap),
    ("GnomeSort", gnome),
    ("BinaryInsertionSort", binary_insertion),
    ("RadixSort", radix),
    ("BucketSort", bucket),
    ("PigeonholeSort", pigeonhole),
    ("TreeSort", tree),
    ("BitonicSort", bitonic),
]

# ---------- Medir tiempos ----------
results = []
for name, fn in ALGORITHMS:
    data = claves[:]          # copia para no alterar la original
    t0 = time.perf_counter()
    fn(data)
    t1 = time.perf_counter()
    results.append({"algoritmo": name, "tamaño": len(claves), "tiempo_s": t1 - t0})

times_df = pd.DataFrame(results).sort_values("tiempo_s")
times_df.to_csv(f"{OUTDIR}/tiempos_ordenamiento.csv", index=False)

# ---------- Gráfico ----------
plt.figure(figsize=(10,6))
plt.barh(times_df["algoritmo"], times_df["tiempo_s"])
plt.xlabel("Tiempo (s)")
plt.ylabel("Algoritmo")
plt.title(f"Tiempos de ordenamiento (Cantidad de Archivos={len(claves)})")
plt.tight_layout()
plt.savefig(f"{OUTDIR}/tiempos_barras.png")
print("Archivos generados en:", os.path.abspath(OUTDIR))
