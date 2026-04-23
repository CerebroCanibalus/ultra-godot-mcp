# 🏗️ Arquitectura v4.0.0 - Ultra Godot MCP Python

## Resumen Ejecutivo

Ultra Godot MCP v4.0.0 introduce una **capa de integración nativa con Godot Engine** que complementa las herramientas filesystem existentes, cerrando los gaps críticos frente a la competencia **sin requerir addons GDScript, WebSockets ni IA local**.

**Filosofía de diseño:**
- **Filesystem First**: 70% de operaciones vía parser nativo (ya implementado en v3.x)
- **Godot CLI Bridge**: 25% vía Godot CLI nativo (--headless, --script, --check-only)
- **LSP/DAP Native**: 5% vía protocolos nativos del editor (puertos 6005/6006)
- **Zero Addon**: Ninguna operación requiere instalar addon en el proyecto Godot

---

## Arquitectura de Alto Nivel

```
┌─────────────────────────────────────────────────────────────────┐
│                    CLIENT (AI/LLM)                               │
└──────────────────────────┬──────────────────────────────────────┘
                           │ JSON-RPC (MCP)
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                  ULTRA GODOT MCP SERVER v4.0.0                   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              CAPA 1: CORE (v3.x existente)                │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐  │   │
│  │  │  Session     │  │  TSCN        │  │  Validator    │  │   │
│  │  │  Manager     │  │  Parser      │  │  (Poka-Yoke)  │  │   │
│  │  └──────────────┘  └──────────────┘  └───────────────┘  │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐  │   │
│  │  │  Node Tools  │  │  Property    │  │  Resource     │  │   │
│  │  │  (10 tools)  │  │  Tools       │  │  Tools        │  │   │
│  │  └──────────────┘  └──────────────┘  └───────────────┘  │   │
│  │  ┌──────────────┐  ┌──────────────┐                      │   │
│  │  │  Signal &    │  │  Project     │                      │   │
│  │  │  Script      │  │  Tools       │                      │   │
│  │  └──────────────┘  └──────────────┘                      │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │         CAPA 2: GODOT CLI BRIDGE (NUEVO v4.0.0)          │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐  │   │
│  │  │  Export      │  │  Runtime     │  │  Import       │  │   │
│  │  │  Tools       │  │  Tools       │  │  Tools        │  │   │
│  │  │  (4 tools)   │  │  (6 tools)   │  │  (2 tools)    │  │   │
│  │  └──────────────┘  └──────────────┘  └───────────────┘  │   │
│  │  ┌──────────────┐  ┌──────────────┐                      │   │
│  │  │  Screenshot  │  │  Movie       │                      │   │
│  │  │  Tools       │  │  Capture     │                      │   │
│  │  │  (2 tools)   │  │  Tools       │                      │   │
│  │  └──────────────┘  └──────────────┘                      │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │         CAPA 3: LSP/DAP NATIVE (NUEVO v4.0.0)            │   │
│  │  ┌──────────────┐  ┌──────────────┐                      │   │
│  │  │  LSP Tools   │  │  DAP Tools   │                      │   │
│  │  │  (3 tools)   │  │  (6 tools)   │                      │   │
│  │  └──────────────┘  └──────────────┘                      │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │         CAPA 4: PROJECT INTELLIGENCE (NUEVO v4.0.0)      │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐  │   │
│  │  │  Dependency  │  │  Signal      │  │  Code         │  │   │
│  │  │  Graph       │  │  Graph       │  │  Analysis     │  │   │
│  │  │  (2 tools)   │  │  (2 tools)   │  │  (3 tools)    │  │   │
│  │  └──────────────┘  └──────────────┘  └───────────────┘  │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                           │
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
    ┌────────────┐  ┌────────────┐  ┌────────────┐
    │ Filesystem │  │ Godot CLI  │  │ LSP/DAP    │
    │ (.tscn)    │  │ (subprocess)│  │ (TCP)      │
    └────────────┘  └────────────┘  └────────────┘
```

---

## Matriz de Herramientas v4.0.0

| Capa | Módulo | Tools | Requiere Godot | Requiere Editor Abierto |
|------|--------|-------|----------------|------------------------|
| **Core** | session_tools | 8 | ❌ | ❌ |
| **Core** | scene_tools | 12 | ❌ | ❌ |
| **Core** | node_tools | 10 | ❌ | ❌ |
| **Core** | property_tools | 1 | ❌ | ❌ |
| **Core** | resource_tools | 7 | ❌ | ❌ |
| **Core** | signal_and_script_tools | 2 | ❌ | ❌ |
| **Core** | project_tools | 5 | ❌ | ❌ |
| **Core** | validation_tools | 3 | ✅ (opcional) | ❌ |
| **Core** | debug_tools | 2 | ✅ | ❌ |
| **CLI Bridge** | export_tools | 4 | ✅ | ❌ |
| **CLI Bridge** | runtime_tools | 6 | ✅ | ❌ |
| **CLI Bridge** | import_tools | 2 | ✅ | ❌ |
| **CLI Bridge** | screenshot_tools | 2 | ✅ | ❌ |
| **CLI Bridge** | movie_tools | 2 | ✅ | ❌ |
| **LSP/DAP** | lsp_tools | 4 | ✅ | ✅ |
| **LSP/DAP** | dap_tools | 6 | ✅ | ✅ |
| **Intelligence** | dependency_tools | 2 | ❌ | ❌ |
| **Intelligence** | signal_graph_tools | 2 | ❌ | ❌ |
| **Intelligence** | code_analysis_tools | 3 | ❌ | ❌ |
| | **TOTAL** | **81** | | |

---

## Capa 2: Godot CLI Bridge

### 2.1 Export Tools (`export_tools.py`)

Wrapper alrededor de `godot --export-release`, `--export-debug`, `--export-pack`.

#### `export_project`
```python
export_project(
    project_path: str,
    export_preset: str,
    output_path: str,
    export_mode: str = "release",  # "release" | "debug" | "pack"
    patches: List[str] = None,     # PCK patches to include
    options: dict = None           # Extra export options
) -> dict
```
**Retorna:**
```json
{
  "success": true,
  "output_path": "D:/builds/game.exe",
  "export_time_ms": 12500,
  "warnings": [],
  "file_size_mb": 45.2
}
```

#### `list_export_presets`
```python
list_export_presets(project_path: str) -> dict
```
**Retorna:** Lista de presets configurados en `export_presets.cfg`.

#### `validate_export_preset`
```python
validate_export_preset(
    project_path: str,
    preset_name: str
) -> dict
```
**Retorna:** Validación de que el preset existe y sus rutas son correctas.

#### `get_export_log`
```python
get_export_log(project_path: str, lines: int = 50) -> dict
```
**Retorna:** Últimas líneas del log de exportación.

---

### 2.2 Runtime Tools (`runtime_tools.py`)

Wrapper alrededor de `godot --headless --script` para ejecutar scripts GDScript que heredan de SceneTree/MainLoop.

#### `run_gdscript`
```python
run_gdscript(
    project_path: str,
    script_content: str,
    timeout: int = 30,
    args: List[str] = None
) -> dict
```
Ejecuta código GDScript arbitrario en una instancia headless de Godot.

**Ejemplo de uso - Inspeccionar escena en runtime:**
```python
script = """
extends SceneTree
func _init():
    var scene = load("res://scenes/Player.tscn").instantiate()
    print("NODES:", scene.get_child_count(true))
    print("GROUPS:", scene.get_groups())
    for child in scene.get_children(true):
        print("NODE:", child.name, "TYPE:", child.get_class())
    quit()
"""
result = run_gdscript(project_path, script)
# Parsea stdout para obtener información de la escena
```

#### `get_scene_info_runtime`
```python
get_scene_info_runtime(
    project_path: str,
    scene_path: str
) -> dict
```
Obtiene información detallada de una escena cargándola en runtime headless.

**Retorna:**
```json
{
  "node_count": 42,
  "nodes": [
    {"name": "Player", "type": "CharacterBody2D", "groups": ["player"]},
    {"name": "Sprite2D", "type": "Sprite2D", "parent": "Player"}
  ],
  "scripts": ["res://scripts/player.gd"],
  "resources": ["res://sprites/player.png"]
}
```

#### `call_group_runtime`
```python
call_group_runtime(
    project_path: str,
    scene_path: str,
    group: str,
    method: str,
    args: List[Any] = None
) -> dict
```
Llama a un método en todos los nodos de un grupo en una escena cargada.

#### `get_classdb_info`
```python
get_classdb_info(
    project_path: str,
    class_name: str = None
) -> dict
```
Usa `godot --dump-extension-api` para obtener información de ClassDB.

**Retorna:** Información de clases, métodos, propiedades, señales.

#### `get_performance_metrics`
```python
get_performance_metrics(
    project_path: str,
    scene_path: str,
    run_seconds: int = 5
) -> dict
```
Ejecuta escena por N segundos y captura métricas de performance.

**Retorna:**
```json
{
  "fps_avg": 59.8,
  "fps_min": 45.2,
  "fps_max": 60.0,
  "draw_calls_avg": 124,
  "memory_mb": 45.2,
  "node_count": 156
}
```

#### `test_scene_load`
```python
test_scene_load(
    project_path: str,
    scene_path: str
) -> dict
```
Verifica que una escena se puede cargar sin errores.

**Retorna:**
```json
{
  "success": true,
  "load_time_ms": 45,
  "errors": [],
  "warnings": ["Missing texture: res://missing.png"]
}
```

---

### 2.3 Import Tools (`import_tools.py`)

#### `reimport_assets`
```python
reimport_assets(
    project_path: str,
    asset_paths: List[str] = None  # None = reimportar todo
) -> dict
```
Wrapper de `godot --import` o `--headless --script` con `EditorInterface.reimport_files()`.

#### `get_import_settings`
```python
get_import_settings(
    project_path: str,
    asset_path: str
) -> dict
```
Lee `.import` file y retorna configuración de importación.

---

### 2.4 Screenshot Tools (`screenshot_tools.py`)

**Limitación conocida:** Godot CLI no permite screenshots instantáneos del editor. Estas tools usan `--write-movie` para capturar frames de una escena ejecutándose.

#### `capture_scene_frame`
```python
capture_scene_frame(
    project_path: str,
    scene_path: str,
    frame_number: int = 1,
    output_path: str = None,
    resolution: Tuple[int, int] = None
) -> dict
```
Ejecuta escena por N frames y captura el frame especificado.

**Retorna:**
```json
{
  "success": true,
  "image_path": "D:/tmp/frame_0001.png",
  "resolution": [1920, 1080],
  "frame_captured": 1
}
```

#### `capture_scene_sequence`
```python
capture_scene_sequence(
    project_path: str,
    scene_path: str,
    frame_count: int = 30,
    output_dir: str = None,
    fps: int = 60
) -> dict
```
Captura una secuencia de frames de una escena ejecutándose.

---

### 2.5 Movie Tools (`movie_tools.py`)

#### `write_movie`
```python
write_movie(
    project_path: str,
    scene_path: str,
    output_path: str,
    duration_seconds: int = 5,
    fps: int = 60,
    resolution: Tuple[int, int] = None
) -> dict
```
Wrapper de `godot --write-movie` para capturar video de escena.

#### `write_movie_with_script`
```python
write_movie_with_script(
    project_path: str,
    scene_path: str,
    output_path: str,
    setup_script: str = None,  # GDScript para configurar escena antes de grabar
    duration_seconds: int = 5,
    fps: int = 60
) -> dict
```
Captura video con script de setup (mover cámara, spawnear objetos, etc.).

---

## Capa 3: LSP/DAP Native

### Estado del LSP en Godot 4.6.1

**⚠️ IMPORTANTE:** Godot 4.6 tuvo bugs de LSP que fueron corregidos en 4.6.1/4.7:
- **Bug #115631**: LSP broken en KDE Kate (fixed en 4.7)
- **Bug #114729**: Segfault con NeoVim + Goto References (fixed)
- **Bug #114685**: Segfault al iniciar LSP con GDUnit4 (fixed)
- **Bug #114305**: Crash al abrir archivo en VS Code (fixed)

**Recomendación:** Godot 4.6.1-stable o 4.7+ para LSP estable.

**Configuración del LSP:**
- Puerto por defecto: **6005**
- Protocolo: JSON-RPC sobre TCP
- Requiere: Editor Godot abierto con proyecto cargado
- Configuración: `Editor > Editor Settings > Network > Language Server`

### 3.1 LSP Tools (`lsp_tools.py`)

#### `lsp_get_completions`
```python
lsp_get_completions(
    project_path: str,
    file_path: str,
    line: int,
    column: int
) -> dict
```
Obtiene autocompletado de GDScript en posición específica.

**Retorna:**
```json
{
  "completions": [
    {"label": "move_and_slide", "kind": "method", "detail": "Vector2 move_and_slide()"},
    {"label": "velocity", "kind": "property", "detail": "Vector2"}
  ]
}
```

#### `lsp_get_hover`
```python
lsp_get_hover(
    project_path: str,
    file_path: str,
    line: int,
    column: int
) -> dict
```
Obtiene documentación hover para símbolo en posición.

#### `lsp_get_symbols`
```python
lsp_get_symbols(
    project_path: str,
    file_path: str
) -> dict
```
Obtiene todos los símbolos (clases, métodos, variables) de un archivo.

**Retorna:**
```json
{
  "symbols": [
    {"name": "Player", "kind": "class", "range": [1, 0, 50, 0]},
    {"name": "_ready", "kind": "method", "range": [5, 0, 10, 0]},
    {"name": "speed", "kind": "property", "range": [3, 0, 3, 20]}
  ]
}
```

#### `lsp_get_diagnostics`
```python
lsp_get_diagnostics(
    project_path: str,
    file_path: str
) -> dict
```
Obtiene errores y warnings del LSP para un archivo.

**Retorna:**
```json
{
  "diagnostics": [
    {"range": [10, 5, 10, 15], "severity": "error", "message": "Undefined variable"},
    {"range": [15, 0, 15, 10], "severity": "warning", "message": "Unused variable"}
  ]
}
```

---

### 3.2 DAP Tools (`dap_tools.py`)

Godot expone DAP en puerto 6006 cuando el editor está abierto. Permite debugging completo.

#### `dap_start_debugging`
```python
dap_start_debugging(
    project_path: str,
    scene_path: str = None  # None = main scene
) -> dict
```
Inicia sesión de debugging.

**Retorna:**
```json
{
  "session_id": "dap_001",
  "status": "started",
  "breakpoints_supported": true
}
```

#### `dap_set_breakpoint`
```python
dap_set_breakpoint(
    session_id: str,
    file_path: str,
    line: int,
    condition: str = None
) -> dict
```
Establece breakpoint en archivo y línea.

#### `dap_continue`
```python
dap_continue(session_id: str) -> dict
```
Continúa ejecución hasta siguiente breakpoint.

#### `dap_step_over`
```python
dap_step_over(session_id: str) -> dict
```
Step over (ejecuta línea actual sin entrar a funciones).

#### `dap_step_into`
```python
dap_step_into(session_id: str) -> dict
```
Step into (entra a funciones).

#### `dap_get_stack_trace`
```python
dap_get_stack_trace(session_id: str) -> dict
```
Obtiene stack trace actual.

**Retorna:**
```json
{
  "frames": [
    {
      "function": "_process",
      "file": "res://scripts/player.gd",
      "line": 15,
      "variables": {
        "velocity": "Vector2(100, 0)",
        "speed": 200.0
      }
    }
  ]
}
```

---

## Capa 4: Project Intelligence

### 4.1 Dependency Graph Tools (`dependency_tools.py`)

Análisis estático de dependencias entre archivos del proyecto.

#### `get_dependency_graph`
```python
get_dependency_graph(
    project_path: str,
    file_path: str = None,  # None = todo el proyecto
    depth: int = 3
) -> dict
```
Construye grafo de dependencias (qué archivos dependen de cuáles).

**Retorna:**
```json
{
  "nodes": [
    {"id": "res://scripts/player.gd", "type": "script"},
    {"id": "res://scenes/Player.tscn", "type": "scene"},
    {"id": "res://sprites/player.png", "type": "texture"}
  ],
  "edges": [
    {"from": "res://scenes/Player.tscn", "to": "res://scripts/player.gd", "type": "script"},
    {"from": "res://scenes/Player.tscn", "to": "res://sprites/player.png", "type": "texture"}
  ]
}
```

#### `find_unused_assets`
```python
find_unused_assets(
    project_path: str,
    asset_types: List[str] = None  # ["texture", "audio", "model"]
) -> dict
```
Encuentra assets que no son referenciados por ninguna escena o script.

---

### 4.2 Signal Graph Tools (`signal_graph_tools.py`)

Análisis estático de conexiones de señales en el proyecto.

#### `get_signal_graph`
```python
get_signal_graph(
    project_path: str,
    scene_path: str = None  # None = todo el proyecto
) -> dict
```
Construye grafo de señales (emisor → receptor).

**Retorna:**
```json
{
  "signals": [
    {
      "emitter": "res://scenes/Player.tscn:Area2D",
      "signal": "body_entered",
      "receiver": "res://scenes/Player.tscn:Player",
      "method": "_on_body_entered"
    }
  ],
  "orphan_signals": [],  # Señales conectadas a métodos que no existen
  "unconnected_signals": ["button_pressed"]  # Señales emitidas pero no conectadas
}
```

#### `find_orphan_signals`
```python
find_orphan_signals(project_path: str) -> dict
```
Encuentra señales conectadas a métodos que no existen en los scripts.

---

### 4.3 Code Analysis Tools (`code_analysis_tools.py`)

Análisis estático de código GDScript.

#### `analyze_script`
```python
analyze_script(
    project_path: str,
    script_path: str
) -> dict
```
Análisis completo de un script GDScript.

**Retorna:**
```json
{
  "classes": [
    {
      "name": "Player",
      "extends": "CharacterBody2D",
      "methods": ["_ready", "_process", "take_damage"],
      "signals": ["health_changed", "died"],
      "exports": ["speed", "max_health"]
    }
  ],
  "complexity": {
    "cyclomatic": 12,
    "cognitive": 8,
    "lines": 150
  },
  "issues": [
    {"line": 45, "severity": "warning", "message": "Function too long (>50 lines)"}
  ]
}
```

#### `find_code_smells`
```python
find_code_smells(
    project_path: str,
    severity: str = "warning"  # "info" | "warning" | "error"
) -> dict
```
Encuentra "code smells" en todo el proyecto:
- Funciones demasiado largas
- Clases demasiado grandes
- Duplicación de código
- Variables no usadas
- Señales huérfanas

#### `get_project_metrics`
```python
get_project_metrics(project_path: str) -> dict
```
Métricas del proyecto completo.

**Retorna:**
```json
{
  "total_files": 45,
  "scripts": 12,
  "scenes": 8,
  "resources": 25,
  "total_lines": 3500,
  "avg_complexity": 8.5,
  "issues": {
    "errors": 2,
    "warnings": 15,
    "infos": 30
  }
}
```

---

## Comparativa con Competencia

### GoPeak (110+ tools, TypeScript/Node, Gratis)

| Feature | GoPeak | Ultra Godot MCP v4.0.0 |
|---------|--------|------------------------|
| **Precio** | Gratis (MIT) | **Gratis (MIT)** |
| **Lenguaje** | TypeScript/Node | **Python** |
| **Addon requerido** | Sí (GDScript) | **No** |
| **WebSocket** | Sí (4 puertos) | **No** |
| **LSP** | Sí | **Sí** (nativo) |
| **DAP** | Sí | **Sí** (nativo) |
| **Screenshots** | Sí (instantáneo) | **Parcial** (frame capture) |
| **Input injection** | Sí | **No** (limitación Godot CLI) |
| **Runtime inspection** | Sí (en vivo) | **Parcial** (headless) |
| **Dependency graph** | No | **Sí** |
| **Signal graph** | No | **Sí** |
| **Code analysis** | Básico | **Avanzado** |
| **Project metrics** | No | **Sí** |
| **Parser nativo TSCN** | No | **Sí** |
| **Validación Poka-Yoke** | No | **Sí** |
| **Sesiones en memoria** | No | **Sí** |
| **Cache LRU** | No | **Sí** |

### GodotIQ (36 tools, Python, $19 Pro)

| Feature | GodotIQ | Ultra Godot MCP v4.0.0 |
|---------|---------|------------------------|
| **Precio** | $19 Pro / 22 free | **Gratis (MIT)** |
| **Addon requerido** | Sí (18/22 tools) | **No** |
| **WebSocket** | Sí (puerto 6007) | **No** |
| **LSP** | No | **Sí** |
| **DAP** | No | **Sí** |
| **Screenshots** | Sí | **Parcial** |
| **Input injection** | Sí | **No** |
| **Spatial intelligence** | Sí (Pro) | **No** (limitación Godot CLI) |
| **Code analysis** | Sí (Pro) | **Sí** (gratis) |
| **Dependency graph** | Sí (Pro) | **Sí** (gratis) |
| **Signal graph** | Sí (Pro) | **Sí** (gratis) |
| **Project memory** | Sí (Pro) | **Parcial** (sessions) |
| **Token optimization** | Sí (3 niveles) | **No** (pendiente) |
| **Parser nativo TSCN** | No | **Sí** |
| **Validación Poka-Yoke** | No | **Sí** |

---

## Limitaciones Conocidas v4.0.0

### Lo que NO podemos hacer (y por qué)

| Feature | Razón | Workaround |
|---------|-------|------------|
| **Screenshots instantáneos del editor** | Godot CLI no expone API de screenshot del editor | Usar `--write-movie` para capturar frames |
| **Input injection** | Requiere addon en proyecto ejecutándose | No disponible en v4.0.0 |
| **Inspección de escena en vivo** | `--script` ejecuta instancia headless separada | Usar `get_scene_info_runtime` con escena cargada |
| **Modificar escena del editor en tiempo real** | `--script` no afecta al editor abierto | Usar filesystem tools (ya implementado) |
| **Spatial intelligence 3D** | Requiere acceso al viewport del editor | No disponible en v4.0.0 |
| **Token optimization** | Requiere análisis de uso de contexto | Planificado para v4.1.0 |

### Lo que SÍ podemos hacer (y ellos no)

| Feature | Ventaja |
|---------|---------|
| **Zero addon** | No requiere modificar proyecto Godot |
| **Zero WebSocket** | No conflictos de puerto, no crasheos de conexión |
| **Parser TSCN nativo** | Más rápido que parsear vía Godot CLI |
| **Validación Poka-Yoke** | Previene errores antes de escribir |
| **Sesiones en memoria** | Workspace con dirty tracking y undo |
| **Cache LRU** | Operaciones repetitivas son instantáneas |
| **LSP/DAP nativos** | Usa protocolos nativos de Godot, no reimplementa |
| **Dependency graph** | Análisis estático sin ejecutar código |
| **Signal graph** | Detecta señales huérfanas y no conectadas |
| **Code analysis** | Métricas de complejidad, code smells |

---

## Plan de Implementación

### Sprint 1: Godot CLI Bridge (2 semanas)
- [ ] `export_tools.py` - 4 tools
- [ ] `runtime_tools.py` - 6 tools
- [ ] `import_tools.py` - 2 tools
- [ ] Tests para CLI bridge

### Sprint 2: LSP/DAP Native (2 semanas)
- [ ] `lsp_tools.py` - 3 tools
- [ ] `dap_tools.py` - 6 tools
- [ ] Cliente JSON-RPC para LSP/DAP
- [ ] Tests para LSP/DAP

### Sprint 3: Project Intelligence (2 semanas)
- [ ] `dependency_tools.py` - 2 tools
- [ ] `signal_graph_tools.py` - 2 tools
- [ ] `code_analysis_tools.py` - 3 tools
- [ ] Tests para intelligence

### Sprint 4: Screenshot/Movie (1 semana)
- [ ] `screenshot_tools.py` - 2 tools
- [ ] `movie_tools.py` - 2 tools
- [ ] Tests para screenshot/movie

### Sprint 5: Integración y Polish (1 semana)
- [ ] Integrar todos los módulos en `server.py`
- [ ] Documentación completa
- [ ] Tests E2E
- [ ] Release v4.0.0

**Total estimado: 8 semanas**

---

## Estructura de Archivos v4.0.0

```
godot-mcp-python/
├── src/godot_mcp/
│   ├── server.py                    # Entry point (actualizado)
│   ├── session_manager.py           # SessionManager
│   ├── core/
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── godot_api_4.6.json
│   │   │   └── godot_nodes_4.6.json
│   │   ├── tscn_parser.py
│   │   ├── tscn_validator.py
│   │   ├── gdscript_validator.py
│   │   ├── cache.py
│   │   └── models.py
│   ├── tools/                       # CAPA 1: Core (existente)
│   │   ├── session_tools.py
│   │   ├── scene_tools.py
│   │   ├── node_tools.py
│   │   ├── property_tools.py
│   │   ├── resource_tools.py
│   │   ├── signal_and_script_tools.py
│   │   ├── project_tools.py
│   │   ├── debug_tools.py
│   │   └── validation_tools.py
│   ├── godot_cli/                   # CAPA 2: CLI Bridge (nuevo)
│   │   ├── __init__.py
│   │   ├── export_tools.py
│   │   ├── runtime_tools.py
│   │   ├── import_tools.py
│   │   ├── screenshot_tools.py
│   │   ├── movie_tools.py
│   │   └── base.py                  # GodotCLIWrapper base
│   ├── lsp_dap/                     # CAPA 3: LSP/DAP (nuevo)
│   │   ├── __init__.py
│   │   ├── lsp_tools.py
│   │   ├── dap_tools.py
│   │   └── client.py                # JSON-RPC client
│   └── intelligence/                # CAPA 4: Intelligence (nuevo)
│       ├── __init__.py
│       ├── dependency_tools.py
│       ├── signal_graph_tools.py
│       └── code_analysis_tools.py
├── tests/
│   ├── test_*.py                    # Tests existentes
│   ├── test_godot_cli/              # Tests CLI Bridge
│   ├── test_lsp_dap/                # Tests LSP/DAP
│   └── test_intelligence/           # Tests Intelligence
└── docs/
    ├── ARCHITECTURE.md              # Este documento
    ├── TOOLS.md                     # Referencia de herramientas
    └── MIGRATION_v3_to_v4.md        # Guía de migración
```

---

*Documento de arquitectura v4.0.0*
*Fecha: 2026-04-21*
*Estado: Diseño completo, listo para implementación*
