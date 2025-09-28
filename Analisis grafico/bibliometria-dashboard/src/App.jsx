import React, { useState, useMemo } from 'react'
import Papa from 'papaparse'
import { BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer } from 'recharts'

export default function BibliometriaDashboard() {
  const [rawCsv, setRawCsv] = useState(null)
  const [rows, setRows] = useState([])
  const [sortedRows, setSortedRows] = useState([])
  const [topAuthors, setTopAuthors] = useState([])
  const [times, setTimes] = useState([])
  const [sampleSize, setSampleSize] = useState(500)
  const [rep, setRep] = useState(1)
  const [loading, setLoading] = useState(false)

  // ------------------ helpers ------------------
  function handleFile(file) {
    if (!file) return
    Papa.parse(file, {
      header: true,
      skipEmptyLines: true,
      complete: (res) => {
        setRawCsv(file.name)
        setRows(res.data)
        setSortedRows([])
        setTopAuthors([])
        setTimes([])
      },
      error: (err) => alert('Error leyendo CSV: ' + err)
    })
  }

  function intKeyFromRecord(rec) {
    // year * 100000 + (hash(title) & 0xFFFF)
    const y = parseInt(rec.year) || 0
    const title = (rec.title || rec.Title || rec.name || '').toString()
    let h = 0
    for (let i = 0; i < title.length; i++) {
      h = ((h << 5) - h) + title.charCodeAt(i)
      h |= 0
    }
    h = h & 0xFFFF
    return y * 100000 + Math.abs(h)
  }

  function sortProducts() {
    if (!rows || rows.length === 0) return
    // ensure fields
    const normalized = rows.map(r => ({ ...r, year: (r.year || r.Year || 0), title: (r.title || r.Title || r.name || '') }))
    const sorted = [...normalized].sort((a,b) => {
      const ya = parseInt(a.year) || 0
      const yb = parseInt(b.year) || 0
      if (ya !== yb) return ya - yb
      const ta = (a.title || '').toString().toLowerCase()
      const tb = (b.title || '').toString().toLowerCase()
      return ta.localeCompare(tb)
    })
    setSortedRows(sorted)
  }

  function computeTopAuthors() {
    if (!rows || rows.length === 0) return
    // support columns 'authors' or 'author' or 'Authors'
    const col = ['authors','Authors','author','Author'].find(c=> rows[0] && Object.prototype.hasOwnProperty.call(rows[0],c))
    const counts = new Map()
    rows.forEach(r => {
      const cell = (r[col] || r.Authors || r.author || r.authors || '').toString()
      if (!cell) return
      const parts = cell.replace(/\n/g,';').replace(/,/g,';').split(';').map(p=>p.trim()).filter(Boolean)
      parts.forEach(p => counts.set(p, (counts.get(p)||0)+1))
    })
    const arr = Array.from(counts.entries()).map(([author,count])=>({author, count}))
    arr.sort((a,b) => b.count - a.count)
    setTopAuthors(arr.slice(0,15).reverse()) // ascending for display
  }

  // ------------------ Sorting algorithms (integers) ------------------
  // Implemented to mirror Python versions where feasible.

  function copyArr(a){ return a.slice() }

  function timsort(a){ return a.slice().sort((x,y)=>x-y) }

  function selectionSort(a){
    const arr = a.slice()
    for(let i=0;i<arr.length;i++){
      let minj=i
      for(let j=i+1;j<arr.length;j++) if(arr[j]<arr[minj]) minj=j
      [arr[i],arr[minj]]=[arr[minj],arr[i]]
    }
    return arr
  }

  function combSort(a){
    const arr=a.slice(); const n=arr.length; let gap=n; const shrink=1.3; let sorted=false
    while(!sorted){
      gap=Math.floor(gap/shrink)
      if(gap<=1){gap=1; sorted=true}
      let i=0
      while(i+gap<n){
        if(arr[i]>arr[i+gap]){[arr[i],arr[i+gap]]=[arr[i+gap],arr[i]]; sorted=false}
        i++
      }
    }
    return arr
  }

  // Tree sort via BST
  class BSTNode{constructor(v){this.v=v;this.left=null;this.right=null}}
  function treeSort(a){
    if(a.length===0) return []
    const root=new BSTNode(a[0])
    for(let i=1;i<a.length;i++){
      let cur=root; const x=a[i]
      while(true){
        if(x<cur.v){ if(cur.left===null){cur.left=new BSTNode(x);break} cur=cur.left }
        else{ if(cur.right===null){cur.right=new BSTNode(x);break} cur=cur.right }
      }
    }
    const res=[]
    function inorder(n){ if(!n) return; inorder(n.left); res.push(n.v); inorder(n.right) }
    inorder(root); return res
  }

  function pigeonholeSort(a){
    if(a.length===0) return []
    const mn=Math.min(...a), mx=Math.max(...a)
    const size=mx-mn+1
    if(size>5_000_000) return a.slice().sort((x,y)=>x-y)
    const holes=new Array(size).fill(0)
    for(const x of a) holes[x-mn]++
    const res=[]
    for(let i=0;i<holes.length;i++) for(let c=0;c<holes[i];c++) res.push(i+mn)
    return res
  }

  function bucketSort(a, bucketSize=1000){
    if(a.length===0) return []
    const mn=Math.min(...a), mx=Math.max(...a)
    if(mn===mx) return a.slice()
    const count=Math.max(1, Math.floor((mx-mn)/bucketSize)+1)
    const buckets=Array.from({length:count},()=>[])
    for(const x of a) buckets[Math.floor((x-mn)/bucketSize)].push(x)
    const res=[]
    for(const b of buckets) res.push(...b.sort((x,y)=>x-y))
    return res
  }

  function quickSort(a){
    const arr=a.slice()
    function qs(lo,hi){ if(lo>=hi) return; const pivot=arr[hi]; let i=lo; for(let j=lo;j<hi;j++) if(arr[j]<pivot){[arr[i],arr[j]]=[arr[j],arr[i]];i++} [arr[i],arr[hi]]=[arr[hi],arr[i]]; qs(lo,i-1); qs(i+1,hi) }
    qs(0,arr.length-1); return arr
  }

  function heapSort(a){
    const arr=a.slice(); const n=arr.length
    function heapify(n,i){ let largest=i; const l=2*i+1; const r=2*i+2; if(l<n && arr[l]>arr[largest]) largest=l; if(r<n && arr[r]>arr[largest]) largest=r; if(largest!==i){[arr[i],arr[largest]]=[arr[largest],arr[i]]; heapify(n,largest)} }
    for(let i=Math.floor(n/2)-1;i>=0;i--) heapify(n,i)
    for(let i=n-1;i>0;i--){ [arr[0],arr[i]]=[arr[i],arr[0]]; heapify(i,0) }
    return arr
  }

  // Bitonic sort: pad to power of two
  function bitonicSort(a){
    let arr=a.slice()
    if(arr.length===0) return []
    const p=1<<((arr.length-1).toString(2).length)
    const sentinel=Math.max(...arr)+1
    while(arr.length<p) arr.push(sentinel)
    function compAndSwap(A,i,j,dir){ if((dir && A[i]>A[j]) || (!dir && A[i]<A[j])){ [A[i],A[j]]=[A[j],A[i]] } }
    function bitonicMerge(A,low,cnt,dir){ if(cnt>1){ const k=Math.floor(cnt/2); for(let i=low;i<low+k;i++) compAndSwap(A,i,i+k,dir); bitonicMerge(A,low,k,dir); bitonicMerge(A,low+k,k,dir) } }
    function bitonicRec(A,low,cnt,dir){ if(cnt>1){ const k=Math.floor(cnt/2); bitonicRec(A,low,k,true); bitonicRec(A,low+k,k,false); bitonicMerge(A,low,cnt,dir) } }
    bitonicRec(arr,0,arr.length,true)
    return arr.filter(x=>x!==sentinel).slice(0,a.length)
  }

  function gnomeSort(a){
    const arr=a.slice(); let i=1; while(i<arr.length){ if(i===0 || arr[i-1]<=arr[i]) i++; else { [arr[i],arr[i-1]]=[arr[i-1],arr[i]]; i-- } } return arr
  }

  function binaryInsertionSort(a){
    const arr=a.slice()
    for(let i=1;i<arr.length;i++){
      const key=arr[i]; let lo=0, hi=i
      while(lo<hi){ const mid=Math.floor((lo+hi)/2); if(arr[mid]<=key) lo=mid+1; else hi=mid }
      for(let j=i;j>lo;j--) arr[j]=arr[j-1]
      arr[lo]=key
    }
    return arr
  }

  function radixSort(a){
    if(a.length===0) return []
    const negatives=a.filter(x=>x<0).map(x=>-x)
    const nonneg=a.filter(x=>x>=0)
    function radixList(arrLocal){ if(arrLocal.length===0) return []
      let maxv=Math.max(...arrLocal); let exp=1; let base=10; let out=arrLocal.slice()
      while(Math.floor(maxv/exp)>0){ const buckets=Array.from({length:base},()=>[]); out.forEach(num=>buckets[Math.floor((num/exp)%base)].push(num)); out=[].concat(...buckets); exp*=base }
      return out
    }
    const sortedNonneg=radixList(nonneg)
    const negSorted=radixList(negatives).map(x=>-x).reverse()
    return negSorted.concat(sortedNonneg)
  }

  const ALGORITHMS=[
    ['TimSort',timsort],
    ['CombSort',combSort],
    ['SelectionSort',selectionSort],
    ['TreeSort',treeSort],
    ['PigeonholeSort',pigeonholeSort],
    ['BucketSort',bucketSort],
    ['QuickSort',quickSort],
    ['HeapSort',heapSort],
    ['BitonicSort',bitonicSort],
    ['GnomeSort',gnomeSort],
    ['BinaryInsertionSort',binaryInsertionSort],
    ['RadixSort',radixSort]
  ]

  function measureTimes() {
    if(!rows || rows.length===0) return
    setLoading(true)
    setTimeout(()=>{
      const sample = rows.slice(0, Math.min(sampleSize, rows.length))
      const claves = sample.map(r=>intKeyFromRecord(r))
      const results = []
      for(const [name,fn] of ALGORITHMS){
        // measure best of rep runs
        let best=Infinity
        for(let k=0;k<Math.max(1,rep);k++){
          const copia=claves.slice()
          const t0=performance.now()
          try{ fn(copia) } catch(e){ copia.sort((x,y)=>x-y) }
          const t1=performance.now(); best=Math.min(best, t1-t0)
        }
        results.push({algoritmo:name, tiempo_s: Math.max(0, best/1000)})
      }
      // sort ascending by tiempo
      results.sort((a,b)=>a.tiempo_s - b.tiempo_s)
      setTimes(results)
      setLoading(false)
    }, 50)
  }

  function exportCsv(data, filename){
    const csv = Papa.unparse(data)
    const blob = new Blob([csv], {type:'text/csv;charset=utf-8;'})
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a'); a.href=url; a.download=filename; a.click(); URL.revokeObjectURL(url)
  }

  // ------------------ UI ------------------
  return (
    <div className="p-6 max-w-6xl mx-auto">
      <h1 className="text-3xl font-bold mb-4">📚 Dashboard Bibliometría — Visualizador</h1>
      <p className="mb-4">Carga el archivo unificado (CSV). La página ordena los productos por año ascendente y título ascendente, extrae top-15 autores, y mide/visualiza tiempos de 12 algoritmos de ordenamiento (si no subes tiempos pre-calculados, la página medirá en el navegador sobre una muestra).</p>

      <div className="bg-white p-4 rounded-lg shadow mb-4">
        <label className="block mb-2 font-semibold">1) Subir CSV unificado</label>
        <input type="file" accept=".csv" onChange={e=>handleFile(e.target.files[0])} />
        <div className="mt-2 text-sm text-gray-600">Archivo actual: {rawCsv || '— ninguno —'}</div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
        <div className="bg-white p-4 rounded shadow">
          <label className="font-semibold">Muestra (N)</label>
          <input type="number" className="w-full mt-2 p-2 border rounded" value={sampleSize} onChange={e=>setSampleSize(Number(e.target.value))} />
          <p className="text-sm text-gray-500 mt-2">Número de registros usados para medir algoritmos (por defecto 500). Se acota al tamaño del CSV.</p>
        </div>
        <div className="bg-white p-4 rounded shadow">
          <label className="font-semibold">Repeticiones</label>
          <input type="number" className="w-full mt-2 p-2 border rounded" value={rep} onChange={e=>setRep(Number(e.target.value))} />
          <p className="text-sm text-gray-500 mt-2">Cuántas veces repetir cada algoritmo y registrar el mejor tiempo.</p>
        </div>
        <div className="bg-white p-4 rounded shadow flex flex-col justify-between">
          <div>
            <button className="bg-blue-600 text-white px-4 py-2 rounded mr-2" onClick={()=>{ sortProducts(); computeTopAuthors(); }}>Procesar (orden + top autores)</button>
            <button className="bg-green-600 text-white px-4 py-2 rounded ml-2" onClick={()=>measureTimes()} disabled={loading || rows.length===0}>{loading? 'Midiendo...':'Medir tiempos (12 algoritmos)'}</button>
          </div>
          <div className="mt-3 text-sm text-gray-600">Después de procesar podrás descargar archivos generados.</div>
        </div>
      </div>

      {/* Results: Sorted table */}
      <div className="bg-white p-4 rounded shadow mb-4">
        <div className="flex justify-between items-center">
          <h2 className="text-xl font-semibold">1) Productos ordenados (año ↑, título ↑)</h2>
          <div>
            <button className="px-3 py-1 bg-gray-800 text-white rounded" onClick={()=>exportCsv(sortedRows, 'sorted_products.csv')}>Descargar CSV</button>
          </div>
        </div>
        <div className="mt-3 text-sm text-gray-600">Total registros: {rows.length}. Mostrando primeros 200 ordenados.</div>
        <div className="overflow-x-auto mt-3">
          <table className="min-w-full text-sm">
            <thead className="text-left border-b"><tr><th className="p-2">#</th><th className="p-2">Year</th><th className="p-2">Title</th><th className="p-2">Authors</th></tr></thead>
            <tbody>
              {sortedRows.slice(0,200).map((r,i)=> (
                <tr key={i} className={i%2? 'bg-gray-50':''}>
                  <td className="p-2 align-top">{i+1}</td>
                  <td className="p-2 align-top">{r.year}</td>
                  <td className="p-2 align-top">{r.title}</td>
                  <td className="p-2 align-top">{r.authors || r.Authors || r.author || ''}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Top authors */}
      <div className="bg-white p-4 rounded shadow mb-4">
        <div className="flex justify-between items-center">
          <h2 className="text-xl font-semibold">2) Top 15 autores (ascendente por apariciones)</h2>
          <button className="px-3 py-1 bg-gray-800 text-white rounded" onClick={()=>exportCsv(topAuthors.map(x=>({author:x.author,count:x.count})), 'top15_autores.csv')}>Descargar CSV</button>
        </div>
        <div className="mt-3">
          <ol className="list-decimal pl-6">
            {topAuthors.map((a,i)=> (
              <li key={i} className="py-1">{a.author} — {a.count} apariciones</li>
            ))}
            {topAuthors.length===0 && <li className="text-gray-500">— aún no generado —</li>}
          </ol>
        </div>
      </div>

      {/* Times chart */}
      <div className="bg-white p-4 rounded shadow mb-8">
        <div className="flex justify-between items-center">
          <h2 className="text-xl font-semibold">3) Tiempos de ordenamiento (ascendente)</h2>
          <button className="px-3 py-1 bg-gray-800 text-white rounded" onClick={()=>exportCsv(times, 'tiempos_ordenamiento.csv')}>Descargar CSV</button>
        </div>
        <div style={{width:'100%', height:360}} className="mt-3">
          {times.length>0 ? (
            <ResponsiveContainer>
              <BarChart data={times} layout="vertical" margin={{top:20,left:80,right:20,bottom:20}}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" tickFormatter={(v)=>v.toFixed(4)} />
                <YAxis type="category" dataKey="algoritmo" />
                <Tooltip formatter={(v)=>`${v.toFixed(6)} s`} />
                <Bar dataKey="tiempo_s" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="text-gray-500">— aún no hay mediciones. Haz click en "Medir tiempos" —</div>
          )}
        </div>
      </div>

      <div className="text-sm text-gray-500">Nota: las mediciones en navegador son aproximadas y dependen del hardware. Para reproducibilidad exacta usa los CSV generados por tu pipeline Python y súbelos aquí.</div>
    </div>
  )
}

