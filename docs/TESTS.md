# 🧪 Test Suite - Ultra Godot MCP

## Resumen

| Métrica | Valor |
|---------|-------|
| **Tests totales** | 496 |
| **Fallos** | 0 |
| **Archivos de test** | 25 |
| **Cobertura estimada** | ~87% |
| **Tests de estrés (LAIKA)** | 25/25 ✅ |
| **Última actualización** | 2026-04-30 |
| **Tests E2E** | 6/6 ✅ |
| **Tests Server** | 16/16 ✅ |
| **Tests Templates** | 35/35 ✅ |
| **Tests Fuzzy** | 11/11 ✅ |

---

## 📁 Archivos de Test

### Core (Parser y Validación)

| Archivo | Tests | Qué cubre |
|---------|-------|-----------|
| `test_parser.py` | 31 | Parseo TSCN, to_dict, to_tscn, búsqueda de nodos, casos borde |
| `test_tres_parser.py` | 24 | Parseo .tres, ResourceHeader, Resource, roundtrip, UIDs |
| `test_tscn_validator.py` | 23 | Validación TSCN: errores, warnings, escenas válidas/inválidas |
| `test_header_validation.py` | 4 | Validación de header gd_scene: load_steps, recursos |
| `test_parent_validation.py` | 7 | Validación de paths de padres: directos, jerárquicos |
| `test_sibling_name_validation.py` | 7 | Validación nombres hermanos: add, rename, duplicate, instantiate |

### Herramientas (Tools)

| Archivo | Tests | Qué cubre |
|---------|-------|-----------|
| `test_node_tools.py` | 52 | CRUD nodos: add, remove, update, rename, move, duplicate, find, ext_resource |
| `test_scene_tools.py` | 24 | Escenas: create, get_tree, save, list, instantiate, modify |
| `test_session_tools.py` | 20 | Sesiones: start, end, commit, discard, SessionContext, require_session |
| `test_project_tools.py` | 22 | Proyecto: parse metadata, find files, estructura, MCP tools |
| `test_resource_tools.py` | 26 | Recursos .tres: create, read, update, uid, list |
| `test_property_tools.py` | 32 | Propiedades: schemas, shapes, validación, procesamiento |
| `test_signal_and_script_tools.py` | 24 | Señales y scripts: connect_signal, set_script, add_sub_resource |
| `test_tilemap_tools.py` | 12 | TileMap: inspect, set cells, terrain, patterns, layer properties |

### Infraestructura

| Archivo | Tests | Qué cubre |
|---------|-------|-----------|
| `test_cache.py` | 8 | Cache LRU: set/get, evicción, invalidación, stats |
| `test_dirty_tracking.py` | 7 | Dirty tracking, commit, retry logic |
| `test_debug_tools.py` | 15 | Debug: búsqueda Godot, parseo logs, run_debug_scene |
| `test_deduplicate_ext_resources.py` | 11 | Deduplicación ExtResources: paths, remapeo, nested |
| `test_instantiate_scene_paths.py` | 5 | Paths de instanciación: mismos/diferentes directorios |
| `test_new_features.py` | 18 | Features nuevas: ext_resource, orphan subresources, validate |

### Estrés (Proyecto Real)

| Archivo | Tests | Qué cubre |
|---------|-------|-----------|
| `test_stress_laike.py` | 25 | Parseo masivo, roundtrip, validacion, escritura bulk, sesiones, busquedas, tilemap tools |

### Deuda Técnica (v2.5 - 2026-04-14)

| Archivo | Tests | Qué cubre |
|---------|-------|-----------|
| `tests/e2e/test_full_workflow.py` | 6 | Flujos E2E: crear escena, señales, operaciones nodos, búsqueda, recursos, listado |
| `test_server.py` | 16 | Registro MCP: todas las herramientas, schemas, parámetros requeridos, nombre servidor |
| `test_templates.py` | 35 | Templates: node templates (listar, obtener, renderizar, validar), script templates, snippets |
| `test_fuzzy_search.py` | 11 | Búsqueda fuzzy: match exacto, parcial, typo, sin resultados, edge cases |

---

## 🏗️ Estructura de Tests

### Fixtures Compartidos (`conftest.py`)

| Fixture | Propósito |
|---------|-----------|
| `test_data_dir` | Directorio de datos de test |
| `test_scene_path` | Ruta a escena de prueba |
| `simple_tscn_content` | TSCN simple (2 nodos) |
| `complex_tscn_content` | TSCN complejo (ext/sub resources, conexiones) |
| `sample_scene` | Objeto Scene completo con todos los componentes |
| `minimal_scene` | Scene mínima (solo header + root) |
| `nested_scene` | Scene con jerarquía de 3 niveles |

### Fixtures por Módulo

| Fixture | Archivo | Propósito |
|---------|---------|-----------|
| `reset_session_manager` | Múltiples | Limpia session manager antes de cada test |
| `temp_project` | Múltiples | Proyecto Godot temporal con project.godot |
| `session_id` | Múltiples | Sesión activa para tests que requieren sesión |
| `simple_scene_file` | test_node_tools | Escena simple (1 nodo Root) |
| `complex_scene_file` | test_node_tools | Escena compleja (5 nodos jerárquicos) |
| `complex_project` | test_project_tools | Proyecto completo con escenas, scripts, recursos |
| `existing_resource` | test_resource_tools | Archivo .tres existente para pruebas |
| `sample_tres_content` | test_tres_parser | Contenido .tres de ejemplo |
| `tres_file` | test_tres_parser | Archivo .tres temporal |

---

## 🐛 Bugs Corregidos (v2.3)

### v2.3 - Stress Test (2026-04-14)

| # | Bug | Impacto | Fix | Archivo |
|---|-----|---------|-----|---------|
| 6 | Parser trunca paths con espacios (`256x256 textures (122).png` → `256x256`) | **Alto** | Regex `(\w+)="([^"]*)"|(\w+)=(\S+)` reemplaza `split()` | `tscn_parser.py` |
| 7 | Parser trunca paths con `&` (`Game Menus` → `Game`, `Themes & Styles` → `Themes`) | **Alto** | Mismo fix regex en `_parse_ext_resource_line` y `_parse_node_header` | `tscn_parser.py` |
| 8 | `load_steps` no se auto-calcula en `Scene.to_tscn()` | **Media** | Auto-cálculo: `1 + len(ext) + len(sub)` antes de serializar | `tscn_parser.py` |
| 9 | `duplicate_node` no duplica hijos del nodo | **Alto** | BFS recursivo para toda la jerarquía de descendientes | `node_tools.py` |
| 10 | `move_node` acepta mover a padre inexistente | **Alto** | Validación explícita: rechaza si `new_parent` no existe en la escena | `node_tools.py` |

### v2.2 - Anteriores

| # | Bug | Impacto | Fix |
|---|-----|---------|-----|
| 1 | `ConfigParser(allow_no_values=True)` → TypeError en Python 3.12 | **Crítico** | Quitar parámetro inválido |
| 2 | `Path.read_text(lines=N)` → parámetro inexistente | **Alto** | `read_text()` + slicing manual |
| 3 | `manager.commit_session()` → método no existe | **Crítico** | Cambiar a `manager.commit_scene()` |
| 4 | `"Root"` hardcodeado en `_resolve_parent_path` → `"."` | **Medio** | Quitar condición espuria |
| 5 | `KeyError: 'parent'` en validador de templates | **Medio** | Agregar `parent=node.parent` al format + fallback |

---

## [STATS] Resultados de Estres (Proyecto LAIKA)

Tests ejecutados en el proyecto real **LAIKA-Solarpunk-GJ** (46 escenas, 36 scripts, 6 recursos):

### Rendimiento

| Operacion | Cantidad | Tiempo Total | Tiempo Unitario |
|-----------|----------|-------------|-----------------|
| Parseo de escenas | 46 | 11ms | 0.2ms |
| Roundtrip (parse->serialize->parse) | 46 | 17ms | 0.4ms |
| Agregar nodos | 50 | 100ms | 2.0ms |
| Eliminar nodos | 20 | 40ms | 2.0ms |
| Instanciar escenas | 15 | 36ms | 2.4ms |
| Crear/destruir sesiones | 5 | 1ms | 0.2ms |

### Hallazgos del Proyecto LAIKA

| Tipo | Cantidad | Descripcion | Estado |
|------|----------|-------------|--------|
| Paths truncados (espacios, `&`) | 3 escenas | Parser `split()` cortaba paths como `Game Menus` → `Game` | ✅ **CORREGIDO** (v2.3) |
| `load_steps` incorrecto | Múltiples | No se auto-calculaba al serializar | ✅ **CORREGIDO** (v2.3) |
| Nodos duplicados | 8 escenas | Nombres de hermanos duplicados (ej: 'Turn', 'Citizen', 'CanvasModulate') | Problema real del proyecto |
| ExtResources faltantes | 7 escenas | Archivos referenciados que no existen | Problema real del proyecto |
| Parent paths invalidos | 5 escenas | Rutas de padre que no coinciden con la jerarquia de nodos | Problema real del proyecto |
| Tipos de nodos encontrados | 37 | Incluye Node2D, Control, Label, Sprite2D, CharacterBody2D, etc. | Informativo |

---

## ⚠️ Deuda Técnica Pendiente

| 11 | **`duplicate_node` nietos con padre ambiguo** | `node_tools.py` | ✅ **CORREGIDO en v2.4** — Renombrado preventivo con sufijo `_2` para evitar colisiones | — | ✅ Resuelto |
| 12 | **`_find_node_by_path` solo devuelve primer match** | `node_tools.py` | ✅ **CORREGIDO en v2.4** — Soporte de rutas completas (`Parent/Child`) | — | ✅ Resuelto |
| 13 | **`rename_node` actualiza hijos de nodo equivocado** | `node_tools.py` | ✅ **CORREGIDO en v2.4** — Solo actualiza hijos definidos después del nodo (orden TSCN) | — | ✅ Resuelto |
| 14 | **`remove_node` elimina hijos de nodo equivocado** | `node_tools.py` | ✅ **CORREGIDO en v2.4** — Solo elimina hijos definidos después del nodo (orden TSCN) | — | ✅ Resuelto |

### Fuera de Alcance (Requiere fix en servidor JS de Godot)

| # | Problema | Descripción | Razón |
|---|----------|-------------|-------|
| O1 | `SubResource type="Vector2"` en escenas generadas | El servidor MCP de Godot (JS) serializa Vector2 como SubResource en vez de inline `Vector2(x, y)`. Godot **no puede abrir** estas escenas. | El fix debe aplicarse en el código JS del servidor MCP (`D:\Mis Juegos\GodotMCP\godot-mcp\server.js`), no en el Python |
| O2 | `load_steps` incorrecto en escenas generadas por MCP | El servidor JS no recalcula `load_steps` al agregar/eliminar recursos. El fix Python en `Scene.to_tscn()` solo aplica al uso directo del parser. | Mismo motivo: el servidor JS escribe escenas directamente |
| O3 | `duplicate_node` no duplica hijos vía MCP | El fix Python en `node_tools.py` no se usa cuando el servidor JS maneja la duplicación internamente. | Mismo motivo: el servidor JS tiene su propia lógica |

### Prioridad Media

| # | Problema | Archivo | Descripción | Impacto | Estado |
|---|----------|---------|-------------|---------|--------|
| 1 | **Tests E2E de flujo completo** | `tests/e2e/test_full_workflow.py` | No hay tests que simulen un flujo real | **Media** | ✅ **Resuelto v2.5** |
| 2 | **Tests de `server.py`** | `tests/test_server.py` | No se verifica que las herramientas se registren correctamente | **Media** | ✅ **Resuelto v2.5** |
| 3 | **Tests de templates** | `tests/test_templates.py` | Los generadores de templates no tienen cobertura | **Media** | ✅ **Resuelto v2.5** |

### Prioridad Baja

| # | Problema | Archivo | Descripción | Impacto | Estado |
|---|----------|---------|-------------|---------|--------|
| 4 | **`parse_project_godot` no maneja valores con `=`** | `project_tools.py` | Si un valor contiene `=`, el parsing puede fallar | **Baja** | Pendiente |
| 5 | **`_find_node_by_path` con fuzzywuzzy** | `tests/test_fuzzy_search.py` | La búsqueda fuzzy no tiene tests dedicados | **Baja** | ✅ **Resuelto v2.5** |
| 6 | **`SessionContext` commit automático** | `session_tools.py` | El context manager no hace auto-commit al salir | **Baja** | Pendiente |
| 7 | **`load_steps` auto-cálculo** | `tscn_parser.py` | ✅ **CORREGIDO en v2.3** | — | ✅ Resuelto |
| 8 | **UIDs en ExtResources** | `node_tools.py` | No se generan UIDs automáticamente (Godot 4.4+) | **Baja** | Pendiente |
| 9 | **Concurrencia en escritura** | `node_tools.py` | No hay tests de estrés concurrente | **Baja** | Pendiente |
| 10 | **Validación de ciclos en `move_node`** | `node_tools.py` | ✅ **CORREGIDO en v2.3** | — | ✅ Parcial |

### Mejoras de Arquitectura

| # | Mejora | Descripción | Esfuerzo |
|---|--------|-------------|----------|
| A1 | **Mock de FastMCP para tests MCP** | Crear fixture que permita testear herramientas MCP sin depender de la API interna de FastMCP | 2h |
| A2 | **Cobertura con pytest-cov** | Configurar reporte de cobertura automática y umbral mínimo (80%) | 1h |
| A3 | **Tests parametrizados** | Convertir tests repetitivos a `@pytest.mark.parametrize` | 3h |
| A4 | **CI/CD pipeline** | GitHub Actions para ejecutar tests en cada PR | 2h |

---

## 🚀 Cómo Ejecutar Tests

```bash
# Todos los tests
python -m pytest tests/ -v

# Solo tests nuevos (últimos creados)
python -m pytest tests/test_node_tools.py tests/test_scene_tools.py tests/test_session_tools.py tests/test_project_tools.py tests/test_tres_parser.py tests/test_resource_tools.py -v

# Con cobertura
python -m pytest tests/ --cov=src/godot_mcp --cov-report=html

# Solo tests que fallaron anteriormente
python -m pytest tests/ --lf

# Tests rápidos (sin I/O de disco)
python -m pytest tests/ -k "not session and not project" --tb=short
```

---

*Documento actualizado automáticamente el 2026-04-14 - v2.3*
