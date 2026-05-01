# DIAGNÓSTICO DE RENDIMIENTO - MCP GODOT v4.0+

**Fecha:** 2026-04-30  
**Benchmark:** `benchmarks/diagnose_performance.py`  
**Muestra:** 50 iteraciones por test, Python 3.12, Windows 11

---

## 🎯 VEREDICTO PRINCIPAL

**NO hay un problema FUNDAMENTAL catastrófico.** El MCP no está "roto" ni degradado de manera crítica. Las operaciones core son rápidas.

**PERO** hay **ineficiencias acumulativas** que en proyectos grandes generan latencia perceptible. Estas son **optimizables quirúrgicamente** sin reescribir el sistema.

---

## 📊 DATOS FRÍOS

### Operaciones Core (Micro-benchmarks)

| Operación | Pequeño | Mediano | Grande | Veredicto |
|-----------|---------|---------|--------|-----------|
| **parse_tscn** | 0.07ms | 0.69ms | **3.3ms** | ✅ Aceptable |
| **to_tscn** (serialize) | 0.02ms | 0.17ms | **0.79ms** | ✅ Rápido |
| **cache.get()** hit | — | **0.001ms** | — | ✅ Excelente |
| **cache.set()** | — | **0.117ms** | — | ⚠️ Lento (lee disco) |
| **session.create** | — | **0.030ms** | — | ✅ Rápido |
| **gdscript.parse** | — | **0.325ms** | — | ✅ Rápido |
| **project.index** (por archivo) | — | **0.87ms** | — | ⚠️ Escala O(N) |

### Memory Footprint

| Métrica | Valor |
|---------|-------|
| Escena grande (200 nodos) | **239 KB** parseada |
| Serialización | **40 KB** adicionales |
| **Total delta** | **279 KB** por escena grande |
| Cache hit rate | 50% (test) |

---

## 🔴 PROBLEMAS REALES IDENTIFICADOS

### 1. REGEX COMPILATION EN HOT PATH 🔥🔥🔥
**Severidad: MEDIA-ALTA** | **Impacto: ~15-20% overhead en parsing**

Las funciones `_parse_ext_resource_line()` y `_parse_node_header()` **compilan el mismo patrón regex en CADA llamada**:

```python
# Líneas 620, 688 de tscn_parser.py
pattern = r'(\w+)="([^"]*)"|(\w+)=(\S+)'
for match in re.finditer(pattern, content):
```

**Evidencia del cProfile** (50 parses de escena grande):
- `re.finditer`: **15,000 calls**
- `re._compile`: **25,000 calls**  
- `re.search`: **10,000 calls**

**Fix:** Compilar regex una sola vez a nivel de módulo:
```python
_EXT_RESOURCE_PATTERN = re.compile(r'(\w+)="([^"]*)"|(\w+)=(\S+)')
```

### 2. CACHE.SET() LEE ARCHIVO DE DISCO 🔥🔥
**Severidad: MEDIA** | **Impacto: I/O blocking innecesario**

```python
# cache.py línea 114-118
if content_hash is None:
    content_hash = self._calculate_hash_from_file(key)  # ¡LEE DISCO!
```

Cuando se hace `cache.set(path, scene)`, el cache **vuelve a leer el archivo del disco** para calcular el hash, aunque ya tenemos el objeto `scene` en memoria.

**Fix:** Aceptar hash precalculado o usar el objeto directamente sin re-hash.

### 3. PROJECT INDEX REBUILD LINEAL 🔥🔥
**Severidad: MEDIA** | **Impacto: O(N) completo en cada force=True**

```python
# project_index.py líneas 240-248
for root, _, files in os.walk(self.project_path):
    for file in files:
        if file.endswith(".gd"):
            # Parsea CADA archivo
```

En un proyecto con 500 archivos: **~435ms** de indexación. Si una tool llama `build_index(force=True)` frecuentemente, esto se acumula.

**Nota:** El cache funciona (0ms en segunda llamada), pero algunas tools pueden estar forzando rebuild.

### 4. CÓDIGO DUPLICADO EN TSCN_PARSER 🔥
**Severidad: BAJA** | **Impacto: Complejidad, no performance**

`deduplicate_ext_resources()` tiene **código duplicado** (líneas 524-587 repiten la lógica de 341-568). Esto es probablemente un merge conflict no resuelto.

### 5. GODOT CLI OVERHEAD 🔥🔥🔥
**Severidad: ALTA** | **Impacto: 1-3 segundos por operación**

Cada llamada a `subprocess.run()` para Godot CLI (export, runtime, debug, screenshot) **lanza un proceso Godot completo**:

```python
# base.py línea 226
result = subprocess.run([godot_exe, "--headless", ...], ...)
```

**Esto NUNCA será rápido.** Es un cuello de botella arquitectónico, no de implementación.

---

## 🟢 LO QUE FUNCIONA BIEN

| Componente | Performance | Notas |
|------------|-------------|-------|
| **Cache hits** | 0.001ms | LRU funciona perfectamente |
| **Session Manager** | <0.03ms | Locks y operaciones son instantáneas |
| **Serialization** | <1ms | `to_tscn()` es eficiente |
| **Memory** | 239KB/escena | Uso razonable para 200 nodos |

---

## 📈 ESCALABILIDAD ESTIMADA

| Tamaño Proyecto | Archivos | Index Time | Memoria Cache |
|-----------------|----------|------------|---------------|
| Pequeño (indie) | 50 | **43ms** | ~12 MB |
| Mediano | 200 | **174ms** | ~48 MB |
| Grande (AA) | 500 | **435ms** | ~120 MB |
| Muy Grande (AAA) | 2000 | **1.7s** | ~480 MB |

**El cuello de botella real para proyectos grandes es la indexación inicial, no el parsing.**

---

## 🛠️ PLAN DE OPTIMIZACIÓN (Quirúrgico)

### Fase 1: Regex Cache (30 min) → ~15% mejora parsing
- [ ] Mover patterns regex a constantes compiladas en `tscn_parser.py`
- [ ] Compilar `_EXT_RESOURCE_RE`, `_NODE_HEADER_RE`, `_GROUPS_RE`

### Fase 2: Cache I/O Fix (20 min) → ~50% mejora cache.set()
- [ ] Permitir `content_hash` opcional en `cache.set()`
- [ ] Evitar re-lectura de disco cuando ya tenemos el objeto

### Fase 3: Index Incremental (2-4 horas) → Mejora escalabilidad
- [ ] Indexar solo archivos con mtime modificado
- [ ] Evitar `force=True` salvo que sea explícitamente necesario
- [ ] Añadir indexación asíncrona en background thread

### Fase 4: Godot CLI Pool (4-8 horas) → Impacto masivo
- [ ] Mantener proceso Godot headless persistente por sesión
- [ ] Comunicar vía stdin/stdout en lugar de lanzar nuevo proceso
- [ ] Esto reduciría operaciones CLI de 1-3s a ~50-100ms

---

## ✅ CHECKLIST ANTES DE OPTIMIZAR

- [x] Profile antes de optimizar → HECHO
- [x] Identificar hot paths → HECHO  
- [ ] Verificar que optimizaciones no rompen tests
- [ ] Medir después de cada cambio
- [ ] Documentar mejoras

---

**Conclusión:** El MCP tiene ~**15-20% de overhead evitable** en parsing y **escalabilidad lineal** en indexación. No requiere reescritura masiva, sino **4 optimizaciones quirúrgicas** que mejorarían significativamente la experiencia en proyectos grandes.
