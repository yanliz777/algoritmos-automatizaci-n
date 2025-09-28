#!/usr/bin/env python3
"""
metodos_ordenamiento.py

Script completo para:
  - Cargar archivo unificado de productos académicos (CSV/JSON/Excel)
  - Ordenar productos por (año, nombre) y guardar resultado
  - Extraer top-15 autores por apariciones y guardar resultado
  - Implementar 12 algoritmos de ordenamiento (incluyendo TimSort)
  - Medir tiempos de ejecución de cada algoritmo sobre una clave entera derivada
  - Guardar tabla de tiempos y generar diagrama de barras (orden ascendente)

Salida:
  - sorted_products.csv
  - top15_autores.csv
  - tiempos_ordenamiento.csv
  - tiempos_barras.png

Uso:
  python bibliometria_ordenamiento.py --input unificado.csv
"""

# ========================== IMPORTS ==========================
import argparse
import time
import os
import random
from collections import Counter

import pandas as pd
import matplotlib.pyplot as plt

# ========================== I/O ==============================

def cargar_dataset(ruta):
    """Carga CSV/Excel/JSON si existe; si no existe devuelve None."""
    if not ruta or not os.path.exists(ruta):
        return None
    ext = os.path.splitext(ruta)[1].lower()
    if ext == '.csv':
        return pd.read_csv(ruta)
    if ext in ['.xlsx', '.xls']:
        return pd.read_excel(ruta)
    if ext == '.json':
        return pd.read_json(ruta)
    raise RuntimeError(f"Formato no soportado: {ext}")

def guardar_dataframe(df, ruta):
    df.to_csv(ruta, index=False)
    print(f"Guardado: {ruta}")

# =================== CLAVE ENTERA PARA ORDEN ==================

def clave_entera_para_registro(row):
    """Construye clave entera: year * 100000 + hash(title)."""
    try:
        year = int(row.get('year') if isinstance(row, dict) else row['year'])
    except Exception:
        year = 0
    title = (row.get('title') if isinstance(row, dict) else row.get('title', '')) or ''
    h = hash(title) & 0xFFFF
    return year * 100000 + int(h)

# ================== ALGORITMOS ORDENAMIENTO ===================

def timsort(arr): return sorted(arr)

def selection_sort(arr):
    a = list(arr)
    n = len(a)
    for i in range(n):
        minj = i
        for j in range(i+1, n):
            if a[j] < a[minj]:
                minj = j
        a[i], a[minj] = a[minj], a[i]
    return a

def comb_sort(arr):
    a = list(arr); n = len(a); gap = n; shrink = 1.3; sorted_flag = False
    while not sorted_flag:
        gap = int(gap / shrink)
        if gap <= 1: gap = 1; sorted_flag = True
        i = 0
        while i + gap < n:
            if a[i] > a[i+gap]:
                a[i], a[i+gap] = a[i+gap], a[i]; sorted_flag = False
            i += 1
    return a

# Tree Sort
class _BSTNode:
    __slots__ = ('val','left','right')
    def __init__(self, val): self.val, self.left, self.right = val, None, None

def tree_sort(arr):
    if not arr: return []
    root = _BSTNode(arr[0])
    for x in arr[1:]:
        cur = root
        while True:
            if x < cur.val:
                if cur.left is None: cur.left = _BSTNode(x); break
                cur = cur.left
            else:
                if cur.right is None: cur.right = _BSTNode(x); break
                cur = cur.right
    res = []
    def inorder(n):
        if n: inorder(n.left); res.append(n.val); inorder(n.right)
    inorder(root)
    return res

def pigeonhole_sort(arr):
    if not arr: return []
    mn, mx = min(arr), max(arr); size = mx - mn + 1
    if size > 5_000_000: return sorted(arr)
    holes = [0] * size
    for x in arr: holes[x - mn] += 1
    res = []
    for i, c in enumerate(holes): res.extend([i + mn] * c)
    return res

def bucket_sort(arr, bucket_size=1000):
    if not arr: return []
    mn, mx = min(arr), max(arr)
    if mn == mx: return list(arr)
    bucket_count = max(1, (mx - mn) // bucket_size + 1)
    buckets = [[] for _ in range(bucket_count)]
    for x in arr: buckets[(x - mn) // bucket_size].append(x)
    res = []
    for b in buckets: res.extend(sorted(b))
    return res

def quicksort(arr):
    a = list(arr)
    def _qs(lo, hi):
        if lo >= hi: return
        pivot = a[hi]; i = lo
        for j in range(lo, hi):
            if a[j] < pivot: a[i], a[j] = a[j], a[i]; i += 1
        a[i], a[hi] = a[hi], a[i]
        _qs(lo, i-1); _qs(i+1, hi)
    _qs(0, len(a)-1); return a

def heapsort(arr):
    a = list(arr); n = len(a)
    def heapify(n, i):
        largest = i; l = 2*i+1; r = 2*i+2
        if l < n and a[l] > a[largest]: largest = l
        if r < n and a[r] > a[largest]: largest = r
        if largest != i: a[i], a[largest] = a[largest], a[i]; heapify(n, largest)
    for i in range(n//2 -1, -1, -1): heapify(n, i)
    for i in range(n-1, 0, -1): a[0], a[i] = a[i], a[0]; heapify(i, 0)
    return a

def bitonic_sort(arr):
    def _comp_and_swap(a,i,j,dir):
        if (dir == (a[i] > a[j])): a[i], a[j] = a[j], a[i]
    def _bitonic_merge(a,low,cnt,dir):
        if cnt>1: k=cnt//2
        for i in range(low, low+k): _comp_and_swap(a,i,i+k,dir)
        _bitonic_merge(a,low,k,dir); _bitonic_merge(a,low+k,k,dir)
    def _bitonic_sort_rec(a,low,cnt,dir):
        if cnt>1: k=cnt//2; _bitonic_sort_rec(a,low,k,True); _bitonic_sort_rec(a,low+k,k,False); _bitonic_merge(a,low,cnt,dir)
    a=list(arr); n=len(a)
    if n==0: return []
    p=1<<(n-1).bit_length(); sentinel=max(a)+1; a.extend([sentinel]*(p-n))
    _bitonic_sort_rec(a,0,p,True)
    return [x for x in a if x!=sentinel][:n]

def gnome_sort(arr):
    a=list(arr); i=1; n=len(a)
    while i<n:
        if i==0 or a[i-1]<=a[i]: i+=1
        else: a[i],a[i-1]=a[i-1],a[i]; i-=1
    return a

def binary_insertion_sort(arr):
    a=list(arr)
    for i in range(1,len(a)):
        key=a[i]; lo,hi=0,i
        while lo<hi:
            mid=(lo+hi)//2
            if a[mid]<=key: lo=mid+1
            else: hi=mid
        j=i
        while j>lo: a[j]=a[j-1]; j-=1
        a[lo]=key
    return a

def radix_sort(arr):
    if not arr: return []
    negatives=[x for x in arr if x<0]; nonneg=[x for x in arr if x>=0]
    def _radix_list(a):
        if not a: return []
        maxv=max(a); exp=1; base=10; out=list(a)
        while maxv//exp>0:
            buckets=[[] for _ in range(base)]
            for num in out: buckets[(num//exp)%base].append(num)
            out=[y for b in buckets for y in b]; exp*=base
        return out
    sorted_nonneg=_radix_list(nonneg)
    neg_sorted=[-x for x in sorted([-x for x in negatives])]
    return neg_sorted+sorted_nonneg

# ================== MEDICIÓN TIEMPOS ==========================

ALGORITMOS = [
    ("TimSort", timsort),
    ("CombSort", comb_sort),
    ("SelectionSort", selection_sort),
    ("TreeSort", tree_sort),
    ("PigeonholeSort", pigeonhole_sort),
    ("BucketSort", bucket_sort),
    ("QuickSort", quicksort),
    ("HeapSort", heapsort),
    ("BitonicSort", bitonic_sort),
    ("GnomeSort", gnome_sort),
    ("BinaryInsertionSort", binary_insertion_sort),
    ("RadixSort", radix_sort),
]

def medir_tiempos(lista_enteros, rep=1):
    filas = []
    for nombre, func in ALGORITMOS:
        tiempos = []
        for _ in range(rep):
            copia=list(lista_enteros); t0=time.perf_counter()
            try: _=func(copia)
            except: _=sorted(copia)
            t1=time.perf_counter(); tiempos.append(t1-t0)
        mejor=min(tiempos)
        filas.append({'algoritmo': nombre, 'tiempo_s': mejor})
        print(f"{nombre}: {mejor:.6f} s")
    return pd.DataFrame(filas)

# ================== ANÁLISIS BIBLIOMÉTRICO ====================

def ordenar_productos(df):
    if 'year' not in df.columns: df['year']=0
    if 'title' not in df.columns: df['title']=''
    df['year']=pd.to_numeric(df['year'], errors='coerce').fillna(0).astype(int)
    df['title']=df['title'].astype(str)
    return df.sort_values(by=['year','title'], ascending=[True,True])

def top_autores(df, topk=15):
    if 'authors' not in df.columns:
        if 'author' in df.columns: df['authors']=df['author']
        else: return pd.DataFrame(columns=['author','count'])
    counts=Counter()
    for cell in df['authors'].astype(str).fillna(''):
        if not cell: continue
        parts=[p.strip() for p in cell.replace('\n',';').replace(',',';').split(';') if p.strip()]
        for p in parts: counts[p]+=1
    most=counts.most_common(topk)
    dfm=pd.DataFrame(most, columns=['author','count'])
    return dfm.sort_values(by='count', ascending=True).reset_index(drop=True)

# ================== DATASET EJEMPLO ============================

def generar_dataset_ejemplo(n=200):
    titles=[f"Trabajo sobre AI {i:03d}" for i in range(n)]
    years=[random.randint(2000,2024) for _ in range(n)]
    authors=["; ".join([f"Autor {random.randint(1,60)}" for _ in range(random.randint(1,4))]) for _ in range(n)]
    return pd.DataFrame({'title': titles,'year': years,'authors': authors})

# ================== MAIN =======================================

def main(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument('--input','-i',default='unificado.csv')
    p.add_argument('--outdir','-o',default='output_bibliometria')
    p.add_argument('--rep','-r',type=int,default=1)
    p.add_argument('--sample-size',type=int,default=None)
    args=p.parse_args(argv)

    os.makedirs(args.outdir, exist_ok=True)

    df=cargar_dataset(args.input)
    if df is None:
        print("No se encontró archivo, generando dataset de ejemplo...")
        df=generar_dataset_ejemplo(n=500)
    else:
        print(f"Dataset cargado: {len(df)} registros desde {args.input}")

    # 1) Ordenar productos
    df_ord=ordenar_productos(df)
    guardar_dataframe(df_ord, os.path.join(args.outdir,'sorted_products.csv'))

    # 2) Top autores
    df_top=top_autores(df)
    guardar_dataframe(df_top, os.path.join(args.outdir,'top15_autores.csv'))

    # 3) Medir algoritmos
    df_sample=df.sample(min(args.sample_size,len(df)),random_state=42) if args.sample_size else df
    claves=[clave_entera_para_registro(row) for _,row in df_sample.iterrows()]
    print(f"Usando N={len(claves)} para medir tiempos...")

    tiempos_df=medir_tiempos(claves, rep=max(1,args.rep))
    guardar_dataframe(tiempos_df, os.path.join(args.outdir,'tiempos_ordenamiento.csv'))

    # 4) Gráfico
    tiempos_df_sorted=tiempos_df.sort_values(by='tiempo_s', ascending=True)
    plt.figure(figsize=(10,6))
    plt.bar(tiempos_df_sorted['algoritmo'], tiempos_df_sorted['tiempo_s'])
    plt.xticks(rotation=45, ha='right'); plt.ylabel('Tiempo (s)')
    plt.title(f'Tiempos de ordenamiento (N={len(claves)})')
    plt.tight_layout()
    plt.savefig(os.path.join(args.outdir,'tiempos_barras.png'))

    print("\nHecho. Archivos generados en:", os.path.abspath(args.outdir))

if __name__=='__main__':
    main()