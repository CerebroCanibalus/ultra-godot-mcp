# 🏴 Ultra Godot MCP

[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Godot 4.6+](https://img.shields.io/badge/Godot-4.6+-478cbf?logo=godotengine&logoColor=white)](https://godotengine.org/)
[![Tests](https://img.shields.io/badge/Tests-496%20passing-2ea44f)](docs/TESTS.md)
[![Version](https://img.shields.io/badge/Version-4.3.0-6f42c1)](CHANGELOG.md)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> *"La técnica es una actividad compositora o destructora, violenta, y esto es lo que Aristóteles llamaba la poiesis, la poesía, precisamente."* — Gustavo Bueno

**Ultra Godot MCP** — *Plus Ultra*: ir más allá.

Servidor MCP para Godot Engine que permite a IAs y asistentes controlar proyectos directamente: crear escenas, manipular nodos, gestionar recursos, validar código, exportar builds, debuggear con breakpoints, y analizar la arquitectura del proyecto — **todo sin instalar addons en tu proyecto Godot**.

---

## ✨ Características

| Característica | Descripción |
|---|---|
| 🔍 **Parsing nativo TSCN** | Lee y escribe archivos `.tscn` directamente, sin Godot headless |
| 🛠️ **98 herramientas** | 7 capas: Core (42) + CLI Bridge (16) + LSP/DAP (10) + Intelligence (7) + Skeleton (6) + Array Ops (2) + Resource Builder (9) |
| 🎯 **Inspector unificado** | `set_node_properties` maneja TODOS los tipos de propiedad automáticamente |
| 🔄 **Sesiones en memoria** | Workspace con dirty tracking, lazy loading y cache LRU |
| ⚡ **Godot headless persistente** | Proceso Godot corriendo en background por sesión (10x más rápido) |
| 🛡️ **Validación Poka-Yoke** | Previene errores antes de escribir archivos |
| 🔎 **Búsqueda fuzzy** | Encuentra nodos tolerando typos con `fuzzywuzzy` |
| 📦 **Templates** | Genera estructuras de nodos y scripts GDScript desde plantillas |
| 🔧 **LSP/DAP nativos** | Autocompletado, hover, breakpoints, stepping — sin addons, solo Godot Editor abierto |
| 📊 **Project Intelligence** | Dependency graph, signal graph, code analysis, métricas |
| 🎬 **Export & Screenshot** | Exportar builds, capturar frames, grabar movies |
| 🐛 **Debug** | 2 herramientas que requieren Godot instalado (las demás funcionan sin él) |

---

## 🏆 Frente a otros MCPs de Godot

### Velocidad: composición directa vs. intermediación

La diferencia principal: otros MCPs lanzan `godot --headless --script` por cada operación (2-5s de overhead). Ultra Godot MCP lee y escribe `.tscn` directamente con su parser nativo — milisegundos. Y cuando necesita Godot, mantiene el proceso vivo en background — 10x más rápido.

| Operación | [godot-mcp](https://github.com/Coding-Solo/godot-mcp) (3.1k⭐) | [GoPeak](https://github.com/GoD0Yun/Gopeak-godot-mcp) (139⭐) | [GodotIQ](https://godotiq.com) | Ultra Godot MCP |
|---|---|---|---|---|
| Leer escena | ~2-5s (Godot headless) | ~2-5s (Godot headless) | ~2-5s (WebSocket) | **<10ms** (parser nativo) |
| Añadir nodo | ~2-5s | ~2-5s | ~2-5s | **<5ms** |
| Validar proyecto | ~10-30s | ~10-30s | ~10-30s | **<500ms** |
| Ejecutar GDScript | ~5s | ~5s | ~5s | **<1s** (headless persistente) |
| Autocompletado | ❌ | ✅ (LSP) | ❌ | **✅ (LSP nativo)** |
| Breakpoints | ❌ | ✅ (DAP) | ❌ | **✅ (DAP nativo)** |

### Comparativa completa

| Dimensión | [godot-mcp](https://github.com/Coding-Solo/godot-mcp) | [GoPeak](https://github.com/GoD0Yun/Gopeak-godot-mcp) | [GodotIQ](https://godotiq.com) | **Ultra Godot MCP** |
|---|---|---|---|---|
| **Herramientas** | ~15 | 110+ | 36 (22 free + 14 Pro) | **98** |
| **Precio** | Gratis | Gratis (MIT) | $19 Pro | **Gratis (MIT)** |
| **Addon requerido** | ❌ | ✅ (GDScript) | ✅ (18/22 tools) | **❌ Zero addon** |
| **WebSocket** | ❌ | ✅ (4 puertos) | ✅ (puerto 6007) | **❌ Zero WebSocket** |
| **Parsing** | Godot headless | Godot headless | Godot headless | **Nativo Python** |
| **Velocidad** | Lento (2-5s/op) | Lento (2-5s/op) | Lento (2-5s/op) | **<10ms / <1s** |
| **Sin Godot instalado** | ❌ | ❌ | ❌ | **✅ (70+/98 tools)** |
| **Sesiones en memoria** | ❌ | ❌ | ❌ | **✅** |
| **Cache LRU** | ❌ | ❌ | ❌ | **✅** |
| **Validación Poka-Yoke** | ❌ | ❌ | ❌ | **✅** |
| **Búsqueda fuzzy** | ❌ | ❌ | ❌ | **✅** |
| **Templates** | ❌ | ❌ | ❌ | **✅** |
| **LSP (autocompletado)** | ❌ | ✅ | ❌ | **✅** |
| **DAP (debugger)** | ❌ | ✅ | ❌ | **✅** |
| **Runtime inspection** | ❌ | ✅ | ✅ | **✅ (headless)** |
| **Export builds** | ❌ | ✅ | ❌ | **✅** |
| **Screenshots** | ❌ | ✅ | ✅ | **✅ (frame capture)** |
| **Dependency graph** | ❌ | ❌ | ✅ (Pro) | **✅ (gratis)** |
| **Signal graph** | ❌ | ❌ | ✅ (Pro) | **✅ (gratis)** |
| **Code analysis** | ❌ | Básico | ✅ (Pro) | **✅ (gratis)** |
| **Project metrics** | ❌ | ❌ | ✅ (Pro) | **✅ (gratis)** |
| **Docs en español** | ❌ | ❌ | ❌ | **✅** |
| **Instalación** | `npx` (npm) | `npx` (npm) | `pip` (Python) | **`pip` (Python)** |

> **Nota:** GoPeak tiene más herramientas en número (110+), pero requiere addon GDScript + WebSocket + 4 puertos. Ultra Godot MCP prioriza **zero-config**: 98 herramientas que funcionan sin tocar tu proyecto Godot.

### Comparativa de funcionalidades

| Funcionalidad | [godot-mcp](https://github.com/Coding-Solo/godot-mcp) | [GoPeak](https://github.com/HaD0Yun/Gopeak-godot-mcp) | [GodotIQ](https://godotiq.com) | **Ultra Godot MCP** |
|---|---|---|---|---|
| **Parser nativo TSCN** | ❌ | ❌ | ❌ | **✅** |
| **Zero addon** | ❌ | ❌ | ❌ | **✅** |
| **Zero WebSocket** | ❌ | ❌ | ❌ | **✅** |
| **Sesiones en memoria** | ❌ | ❌ | ❌ | **✅** |
| **Cache LRU** | ❌ | ❌ | ❌ | **✅** |
| **Validación Poka-Yoke** | ❌ | ❌ | ❌ | **✅** |
| **Búsqueda fuzzy** | ❌ | ❌ | ❌ | **✅** |
| **Templates** | ❌ | ❌ | ❌ | **✅** |
| **Inspector unificado** | ❌ | ✅ | ❌ | **✅** |
| **Asignación de recursos a nodos** | ❌ (Solo sprites) | ✅ (Requiere addon) | ✅ | **✅ (Automático)** |
| **Conexión de señales** | ❌ | ✅ | ✅ | **✅** |
| **Gestión de recursos** | ❌ | ✅ | ✅ | **✅** |
| **UIDs (Godot 4.4+)** | ✅ | ✅ | ✅ | **✅** |
| **LSP (autocompletado)** | ❌ | ✅ | ❌ | **✅** |
| **DAP (debugger)** | ❌ | ✅ | ❌ | **✅** |
| **Runtime inspection** | ❌ | ✅ (en vivo) | ✅ (en vivo) | **✅ (headless)** |
| **Export builds** | ❌ | ✅ | ❌ | **✅** |
| **Screenshots/input** | ❌ | ✅ (instantáneo) | ✅ (instantáneo) | **✅ (frame capture)** |
| **Dependency graph** | ❌ | ❌ | ✅ (Pro $19) | **✅ (gratis)** |
| **Signal graph** | ❌ | ❌ | ✅ (Pro $19) | **✅ (gratis)** |
| **Code analysis** | ❌ | Básico | ✅ (Pro $19) | **✅ (gratis)** |
| **Project metrics** | ❌ | ❌ | ✅ (Pro $19) | **✅ (gratis)** |
| **Asset library** | ❌ | ✅ (CC0) | ❌ | ❌ |
| **Project visualizer** | ❌ | ✅ | ❌ | ❌ |
| **Docs en español** | ❌ | ❌ | ❌ | **✅** |

> **Lo que tenemos y ellos no:** Parser nativo, zero addon, zero WebSocket, sesiones en memoria, cache LRU, validación Poka-Yoke, búsqueda fuzzy, templates, LSP/DAP sin addons, dependency graph gratis, signal graph gratis, code analysis gratis, docs en español.
>
> **Lo que ellos tienen y nosotros no:** Screenshots instantáneos del editor (requiere addon), input injection (requiere addon), asset library (CC0), project visualizer.

### 🌎 Hecho para la comunidad hispanohablante y lusófona

La comunidad de Godot en español y portugués es enorme, pero las herramientas de IA para desarrollo de juegos están diseñadas exclusivamente en inglés. Ultra Godot MCP nace de esa realidad:

- **Documentación en español**: guías, errores y referencia técnica en tu idioma
- **Creado por y para** desarrolladores de España, México, Argentina, Colombia, Brasil, Portugal y toda Iberoamérica
- **Sin barrera idiomática**: porque hacer juegos no debería requerir hablar inglés

---

## 📥 Instalación

### Desde PyPI (próximamente)

```bash
pip install godot-mcp
```

### Desde fuente

```bash
git clone https://github.com/CerebroCanibalus/ultra-godot-mcp.git
cd ultra-godot-mcp

pip install -e .
# O con dependencias de desarrollo:
pip install -e ".[dev]"
```

### Requisitos

- **Python 3.10+**
- **Godot 4.6+** (opcional, solo para tools de CLI Bridge, LSP/DAP y debug)

---

## 🚀 Inicio rápido

### 1. Iniciar el servidor

```bash
godot-mcp
# O como módulo:
python -m godot_mcp.server
```

### 2. Configurar en tu cliente MCP

```json
{
  "mcpServers": {
    "godot": {
      "command": "python",
      "args": ["-m", "godot_mcp.server"],
      "cwd": "/ruta/a/tu/proyecto-godot"
    }
  }
}
```

### 3. Configurar LSP/DAP (opcional, para autocompletado y debugging)

El LSP (Language Server Protocol) y DAP (Debug Adapter Protocol) son **features nativas de Godot** — no requieren instalación adicional. Solo necesitas:

**Habilitar LSP (autocompletado, hover, símbolos):**
1. Abre tu proyecto en Godot Editor
2. Ve a `Editor > Editor Settings > Network > Language Server`
3. Activa **"Enable Language Server"**
4. Verifica que el puerto sea **6005**
5. Reinicia Godot Editor

**Habilitar DAP (breakpoints, stepping):**
1. Ve a `Editor > Editor Settings > Network > Debug Adapter`
2. Activa **"Enable Debug Adapter"**
3. Verifica que el puerto sea **6006**
4. Reinicia Godot Editor

> **Nota:** El LSP/DAP solo funciona cuando Godot Editor está **abierto** con tu proyecto cargado. Si no lo necesitas, las otras 77 herramientas funcionan sin él.

### 4. Usar con tu asistente IA

```
→ "Crea una escena Player con CharacterBody2D, CollisionShape2D y Sprite2D"
→ "Añade un script de movimiento al jugador"
→ "Conecta la señal body_entered del Area2D al jugador"
→ "Valida que todas las escenas del proyecto estén correctas"
→ "Exporta el proyecto para Windows en modo release"
→ "Pon un breakpoint en la línea 15 de player.gd y dime las variables"
→ "Analiza la complejidad del código del proyecto"
```

---

## 🛠️ Herramientas

### Capa 1: Core (42 tools) — Sin Godot

#### Sesión
| Herramienta | Descripción |
|---|---|
| `start_session` | Crear sesión para un proyecto Godot |
| `end_session` | Cerrar sesión y guardar cambios |
| `get_active_session` | Obtener la sesión activa actual |
| `get_session_info` | Información de una sesión |
| `list_sessions` | Listar sesiones activas |
| `commit_session` | Guardar cambios a disco |
| `discard_changes` | Descartar cambios sin guardar |

#### Escenas
| Herramienta | Descripción |
|---|---|
| `create_scene` | Crear nueva escena `.tscn` |
| `get_scene_tree` | Obtener jerarquía completa de nodos |
| `save_scene` | Guardar escena a disco |
| `list_scenes` | Listar todas las escenas del proyecto |
| `instantiate_scene` | Instanciar una escena como nodo hijo |
| `modify_scene` | Modificar tipo/nombre del root de una escena |

#### Nodos
| Herramienta | Descripción |
|---|---|
| `add_node` | Añadir nodo a una escena |
| `remove_node` | Eliminar nodo |
| `update_node` | Actualizar propiedades de un nodo |
| `rename_node` | Renombrar nodo |
| `move_node` | Reparentar nodo |
| `duplicate_node` | Duplicar nodo y sus hijos |
| `find_nodes` | Buscar nodos por nombre o tipo (con fuzzy matching) |
| `get_node_properties` | Obtener todas las propiedades de un nodo |

#### 🔥 Inspector Unificado

```python
set_node_properties(session_id, scene_path, node_path, properties={...})
```

Maneja **automáticamente** todos los tipos:

| Tipo | Ejemplo |
|---|---|
| **Texturas** | `"texture": "res://sprites/player.png"` → crea ExtResource |
| **Shapes** | `"shape": {"shape_type": "CapsuleShape2D", "radius": 16.0}` → crea SubResource |
| **Scripts** | `"script": "res://scripts/player.gd"` → crea ExtResource |
| **Colores** | `"modulate": {"type": "Color", "r": 1, "g": 0.5, "b": 0.5, "a": 1}` |
| **Vectores** | `"position": {"type": "Vector2", "x": 100, "y": 200}` |
| **Enums** | `"motion_mode": "MOTION_MODE_GROUNDED"` |
| **Simples** | `"text": "Hello", "visible": true` |

#### Recursos
| Herramienta | Descripción |
|---|---|
| `create_resource` | Crear recurso `.tres` |
| `read_resource` | Leer propiedades de un `.tres` |
| `update_resource` | Actualizar propiedades de recurso |
| `add_ext_resource` | Añadir referencia externa a escena |
| `add_sub_resource` | Crear recurso embebido en escena |
| `list_resources` | Listar recursos del proyecto |
| `get_uid` | Obtener UID de recurso (Godot 4.4+) |
| `update_project_uids` | Actualizar todos los UIDs del proyecto |

#### Scripts y Señales
| Herramienta | Descripción |
|---|---|
| `set_script` | Adjuntar script `.gd` a un nodo |
| `connect_signal` | Conectar señal entre nodos |

#### Proyecto
| Herramienta | Descripción |
|---|---|
| `get_project_info` | Metadata del proyecto |
| `get_project_structure` | Estructura completa (escenas, scripts, assets) |
| `find_scripts` | Buscar scripts `.gd` |
| `find_resources` | Buscar recursos `.tres` |
| `list_projects` | Encontrar proyectos Godot en un directorio |

#### Validación
| Herramienta | Descripción |
|---|---|
| `validate_tscn` | Validar archivo `.tscn` (parser nativo, sin Godot) |
| `validate_gdscript` | Validar script `.gd` (API Godot 4.6 + sintaxis real con Godot) |
| `validate_project` | Validar proyecto completo (parser nativo, sin Godot) |

### Capa 2: Godot CLI Bridge (16 tools) — Requiere Godot

#### Export
| Herramienta | Descripción |
|---|---|
| `export_project` | Exportar proyecto con preset configurado |
| `list_export_presets` | Listar presets de exportación disponibles |
| `validate_export_preset` | Validar que un preset existe y es válido |
| `get_export_log` | Obtener log de la última exportación |

#### Runtime
| Herramienta | Descripción |
|---|---|
| `run_gdscript` | Ejecutar código GDScript arbitrario en headless |
| `get_scene_info_runtime` | Obtener información de escena cargada en runtime |
| `get_performance_metrics` | FPS, draw calls, memoria, nodos (ejecuta escena N segundos) |
| `test_scene_load` | Verificar que una escena carga sin errores |
| `get_classdb_info` | Obtener información de ClassDB de Godot |
| `call_group_runtime` | Llamar método en grupo de nodos en escena cargada |

#### Import
| Herramienta | Descripción |
|---|---|
| `reimport_assets` | Reimportar assets del proyecto |
| `get_import_settings` | Obtener configuración de importación de un asset |

#### Screenshot
| Herramienta | Descripción |
|---|---|
| `capture_scene_frame` | Capturar frame específico de escena ejecutándose |
| `capture_scene_sequence` | Capturar secuencia de frames |

#### Movie
| Herramienta | Descripción |
|---|---|
| `write_movie` | Grabar video de escena ejecutándose |
| `write_movie_with_script` | Grabar video con script de setup |

### Capa 3: LSP/DAP Native (10 tools) — Requiere Godot Editor abierto

#### LSP (Language Server Protocol)
| Herramienta | Descripción |
|---|---|
| `lsp_get_completions` | Autocompletado GDScript en posición específica |
| `lsp_get_hover` | Documentación hover para símbolo |
| `lsp_get_symbols` | Todos los símbolos de un archivo (clases, métodos, variables) |
| `lsp_get_diagnostics` | Errores y warnings de un archivo |

#### DAP (Debug Adapter Protocol)
| Herramienta | Descripción |
|---|---|
| `dap_start_debugging` | Iniciar sesión de debugging |
| `dap_set_breakpoint` | Establecer breakpoint en archivo y línea |
| `dap_continue` | Continuar ejecución |
| `dap_step_over` | Step over (ejecuta línea sin entrar a funciones) |
| `dap_step_into` | Step into (entra a funciones) |
| `dap_get_stack_trace` | Obtener stack trace con variables |

### Capa 4: Project Intelligence (7 tools) — Sin Godot

#### Dependency Graph
| Herramienta | Descripción |
|---|---|
| `get_dependency_graph` | Grafo de dependencias entre archivos del proyecto |
| `find_unused_assets` | Encontrar assets no referenciados |

#### Signal Graph
| Herramienta | Descripción |
|---|---|
| `get_signal_graph` | Grafo de conexiones de señales (emisor → receptor) |
| `find_orphan_signals` | Detectar señales conectadas a métodos inexistentes |

#### Code Analysis
| Herramienta | Descripción |
|---|---|
| `analyze_script` | Métricas de complejidad, funciones, clases, issues |
| `find_code_smells` | Code smells: funciones largas, complejidad alta, magic numbers |
| `get_project_metrics` | Métricas agregadas del proyecto completo |

### 🔧 Debug
> ⚠️ Estas 2 herramientas **sí requieren Godot instalado**. Son las únicas que lanzan el motor.

| Herramienta | Descripción |
|---|---|
| `run_debug_scene` | Ejecutar escena en modo headless y capturar errores, warnings y prints |
| `check_script_syntax` | Verificar sintaxis GDScript con `--check-only` de Godot |

### Capa 5: Skeleton (6 tools) — Sin Godot

#### Skeleton2D
| Herramienta | Descripción |
|---|---|
| `create_skeleton2d` | Crear nodo Skeleton2D en escena |
| `add_bone2d` | Añadir hueso Bone2D al skeleton |
| `setup_polygon2d_skinning` | Vincular Polygon2D al skeleton para deformación |

#### Skeleton3D
| Herramienta | Descripción |
|---|---|
| `create_skeleton3d` | Crear nodo Skeleton3D en escena |
| `add_bone_attachment3d` | Vincular nodos a huesos del skeleton |
| `setup_mesh_skinning` | Vincular MeshInstance3D al skeleton |

### Capa 6: Array Operations (2 tools) — Sin Godot

| Herramienta | Descripción |
|---|---|
| `scene_array_operation` | Modificar arrays en escenas (append/remove/replace/insert/clear) |
| `preview_array_operation` | Previsualizar cambios en arrays sin aplicarlos |

### Capa 7: Resource Builder (9 tools) — Sin Godot

#### Genéricos
| Herramienta | Descripción |
|---|---|
| `build_resource` | Crear cualquier SubResource genérico |
| `build_nested_resource` | Crear jerarquías de recursos con referencias cruzadas |

#### Animation
| Herramienta | Descripción |
|---|---|
| `create_animation` | Crear Animation con tracks de keyframes |
| `create_state_machine` | Crear AnimationNodeStateMachine con estados y transiciones |

#### AnimationTree
| Herramienta | Descripción |
|---|---|
| `create_blend_space_1d` | Crear BlendSpace1D (idle→walk→run) |
| `create_blend_space_2d` | Crear BlendSpace2D (direcciones 4-way) |
| `create_blend_tree` | Crear BlendTree (grafo de mezcla) |

#### Assets
| Herramienta | Descripción |
|---|---|
| `create_sprite_frames` | Crear SpriteFrames (animaciones frame-by-frame) |
| `create_tile_set` | Crear TileSet (atlas + colisiones) |

---

## 📚 Documentación

| Documento | Contenido |
|---|---|
| [TOOLS.md](docs/TOOLS.md) | Referencia completa de las 98 herramientas |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | Diseño interno, sesiones y cache |
| [ARCHITECTURE_v4.md](docs/ARCHITECTURE_v4.md) | Arquitectura v4.0.0 (4 capas) |
| [CLEANUP_v4.md](docs/CLEANUP_v4.md) | Análisis de limpieza e integración con sesiones |
| [COMMON_ERRORS.md](docs/COMMON_ERRORS.md) | Errores frecuentes y soluciones |
| [TESTS.md](docs/TESTS.md) | Métricas de testing y cobertura |
| [CHANGELOG.md](CHANGELOG.md) | Historial de versiones (v4.3.0) |

---

## 🧪 Testing

```bash
pytest tests/              # Todos los tests
pytest --cov=godot_mcp     # Con coverage
pytest tests/e2e/          # Solo E2E
pytest tests/test_server.py -v  # Tests específicos
```

**Estado:** 496 tests pasando · 22 módulos registrados en v4.3.0

---

## 🏗️ Arquitectura

```
src/godot_mcp/
├── server.py                    # Entry point FastMCP (22 módulos registrados)
├── session_manager.py           # Gestión de sesiones + Godot headless
├── core/                        # Núcleo
│   ├── api/                     # APIs de Godot (datos externos)
│   │   ├── __init__.py          # GodotAPI + NodeAPI classes
│   │   ├── godot_api_4.6.json   # API de Godot 4.6.1 (GDScript)
│   │   └── godot_nodes_4.6.json # Tipos de nodos 4.6.1 (TSCN)
│   ├── tscn_parser.py           # Parser de escenas Godot (v4.3: StringName, Vector2i/3i, Rect2i)
│   ├── tres_parser.py           # Parser de recursos
│   ├── tscn_validator.py        # Validador de escenas (v2.0)
│   ├── gdscript_validator.py    # Validador de scripts (v2.0)
│   ├── cache.py                 # Cache LRU
│   ├── models.py                # Modelos Pydantic
│   └── project_index.py         # Índice de proyectos
├── tools/                       # Capas 1, 5, 6, 7
│   ├── scene_tools.py           # Operaciones de escenas
│   ├── node_tools.py            # Operaciones de nodos
│   ├── resource_tools.py        # Gestión de recursos
│   ├── session_tools.py         # Gestión de sesiones
│   ├── project_tools.py         # Operaciones de proyecto
│   ├── validation_tools.py      # Validación
│   ├── signal_and_script_tools.py  # Señales y scripts
│   ├── property_tools.py        # Inspector unificado
│   ├── debug_tools.py           # Debug
│   ├── skeleton_tools.py        # Capa 5: Skeleton2D/3D
│   ├── array_tools.py           # Capa 6: Array Operations
│   └── resource_builder_tools.py # Capa 7: Resource Builder (9 tools)
├── godot_cli/                   # Capa 2: CLI Bridge (v4.0.0)
│   ├── base.py                  # GodotCLIWrapper
│   ├── export_tools.py          # Export builds
│   ├── runtime_tools.py         # Runtime headless
│   ├── import_tools.py          # Reimport assets
│   ├── screenshot_tools.py      # Frame capture
│   └── movie_tools.py           # Movie recording
├── lsp_dap/                     # Capa 3: LSP/DAP Native (v4.0.0)
│   ├── client.py                # Cliente JSON-RPC
│   ├── lsp_tools.py             # Language Server Protocol
│   └── dap_tools.py             # Debug Adapter Protocol
├── intelligence/                # Capa 4: Project Intelligence (v4.0.0)
│   ├── dependency_tools.py      # Dependency graph
│   ├── signal_graph_tools.py    # Signal graph
│   └── code_analysis_tools.py   # Code analysis
└── templates/                   # Templates
    ├── node_templates.py        # Templates de nodos
    └── script_templates.py      # Templates de scripts
```

---

## 📄 Licencia

**MIT** — ver [LICENSE](LICENSE) para detalles.

---

<div align="center">

**Por los trabajadores y los iberófonos del mundo** 🌍

🇪🇸🇲🇽🇦🇷🇨🇴🇵🇪🇨🇱🇻🇪🇧🇴🇪🇨🇬🇹🇭🇳🇳🇮🇵🇾🇸🇻🇺🇾🇩🇴🇵🇷🇬🇶🇵🇭🇦🇩🇧🇿🇵🇹🇧🇷🇦🇴🇲🇿🇨🇻🇬🇼🇸🇹🇹🇱🇲🇴

</div>
