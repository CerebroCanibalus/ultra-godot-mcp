# 🛠️ Referencia de Herramientas MCP

Todas las herramientas disponibles en Ultra Godot MCP v4.5.0.

**Total: 106 herramientas** organizadas en 8 capas arquitectónicas.

---

## 📊 Índice de Herramientas por Capa

| Capa | Módulo | Herramientas | Requiere Godot |
|------|--------|--------------|----------------|
| **Core** | Sesión | 4 | ❌ |
| **Core** | Escenas | 5 | ❌ |
| **Core** | Nodos | 8 | ❌ |
| **Core** | Inspector Unificado | 1 | ❌ |
| **Core** | Recursos | 8 | ❌ |
| **Core** | Scripts y Señales | 2 | ❌ |
| **Core** | Proyecto | 5 | ❌ |
| **Core** | Validación | 3 | ✅ (opcional) |
| **Core** | Debug | 2 | ✅ |
| **CLI Bridge** | Export | 4 | ✅ |
| **CLI Bridge** | Runtime | 6 | ✅ |
| **CLI Bridge** | Import | 2 | ✅ |
| **CLI Bridge** | Screenshot | 2 | ✅ |
| **CLI Bridge** | Movie | 2 | ✅ |
| **LSP/DAP** | LSP | 4 | ✅ |
| **LSP/DAP** | DAP | 6 | ✅ |
| **Intelligence** | Dependencias | 2 | ❌ |
| **Intelligence** | Signal Graph | 2 | ❌ |
| **Intelligence** | Code Analysis | 3 | ❌ |
| **Skeleton** | Skeleton2D | 3 | ❌ |
| **Skeleton** | Skeleton3D | 3 | ❌ |
| **Array Ops** | Array Operations | 2 | ❌ |
| **Resource Builder** | Genéricos | 2 | ❌ |
| **Resource Builder** | Animation | 2 | ❌ |
| **Resource Builder** | AnimationTree | 3 | ❌ |
| **Resource Builder** | Assets | 2 | ❌ |
| **TileMap** | TileMap Tools | 7 | ✅ |

---

## Capa 1: Core (42 herramientas)

### Sesión

#### `start_session`
Crea una sesión para un proyecto Godot.

```python
start_session(project_path: str) -> dict
```

**Ejemplo:**
```python
result = start_session(project_path="/ruta/al/proyecto")
session_id = result["session_id"]
```

#### `end_session`
Cierra una sesión, opcionalmente guardando cambios.

```python
end_session(session_id: str, save: bool = True) -> dict
```

#### `get_session_info`
Obtiene información detallada de una sesión.

```python
get_session_info(session_id: str) -> dict
```

#### `list_sessions`
Lista todas las sesiones activas.

```python
list_sessions() -> dict
```

---

### Escenas

#### `create_scene`
Crea una nueva escena `.tscn`.

```python
create_scene(session_id: str, scene_path: str,
             root_type: str = "Node2D", root_name: str = "Root") -> dict
```

#### `get_scene_tree`
Obtiene la jerarquía completa de nodos de una escena.

```python
get_scene_tree(session_id: str, scene_path: str) -> dict
```

#### `save_scene`
Guarda una escena a disco.

```python
save_scene(session_id: str, scene_path: str, scene_data: dict) -> dict
```

#### `list_scenes`
Lista todas las escenas del proyecto.

```python
list_scenes(session_id: str, recursive: bool = True) -> dict
```

#### `instantiate_scene`
Instancia una escena como nodo dentro de otra escena.

```python
instantiate_scene(session_id: str, scene_path: str,
                  parent_scene_path: str, node_name: str,
                  parent_node_path: str = ".",
                  project_path: str = None) -> dict
```

**Parámetros:**
- `project_path`: Ruta absoluta al proyecto Godot. **Recomendado** para generar paths `res://` limpios y habilitar deduplicación por filesystem.

**Formato generado (Godot nativo):**
```
[node name="Enemy1" parent="." instance=ExtResource("1")]
```

**Deduplicación automática:** Si la escena padre ya tiene un ExtResource apuntando al mismo archivo (detectado por filesystem o fuzzy match), se reutiliza en lugar de crear uno duplicado.

**Ejemplo:**
```python
# Instanciar enemy.tscn dentro de battlefield.tscn
result = instantiate_scene(
    session_id=session_id,
    scene_path="res://scenes/enemy.tscn",
    parent_scene_path="res://scenes/battlefield.tscn",
    node_name="Enemy_Alpha",
    project_path="/ruta/al/proyecto"
)
```

---

### Nodos

#### `add_node`
Añade un nodo a una escena.

```python
add_node(session_id: str, scene_path: str,
         parent_path: str, node_type: str, node_name: str,
         properties: dict = None) -> dict
```

#### `remove_node`
Elimina un nodo de una escena.

```python
remove_node(session_id: str, scene_path: str, node_path: str) -> dict
```

#### `update_node`
Actualiza propiedades de un nodo (versión básica).

```python
update_node(session_id: str, scene_path: str,
            node_path: str, properties: dict) -> dict
```

> **Nota:** Para propiedades complejas (texturas, shapes, etc.) usa `set_node_properties`.

#### `get_node_properties`
Obtiene todas las propiedades de un nodo.

```python
get_node_properties(session_id: str, scene_path: str, node_path: str) -> dict
```

#### `rename_node`
Renombra un nodo.

```python
rename_node(session_id: str, scene_path: str,
            node_path: str, new_name: str) -> dict
```

#### `move_node`
Cambia el padre de un nodo (reparent).

```python
move_node(session_id: str, scene_path: str,
          node_path: str, new_parent_path: str) -> dict
```

#### `duplicate_node`
Duplica un nodo y sus hijos.

```python
duplicate_node(session_id: str, scene_path: str,
               node_path: str, new_name: str = None) -> dict
```

#### `find_nodes`
Busca nodos por nombre o tipo.

```python
find_nodes(session_id: str, scene_path: str,
           name_pattern: str = None, type_filter: str = None) -> dict
```

---

### 🔥 Inspector Unificado

#### `set_node_properties`

Configura **CUALQUIER** propiedad del inspector de **CUALQUIER** nodo. Esta es la herramienta principal para manipular propiedades.

```python
set_node_properties(session_id: str, scene_path: str,
                    node_path: str, properties: dict[str, Any]) -> dict
```

#### Tipos de valores soportados

| Tipo | Formato | Ejemplo |
|------|---------|---------|
| **String** | Valor directo | `"Hello World"` |
| **Número** | Valor directo | `42`, `3.14` |
| **Booleano** | Valor directo | `true`, `false` |
| **Vector2** | Dict con tipo | `{"type": "Vector2", "x": 100, "y": 200}` |
| **Vector3** | Dict con tipo | `{"type": "Vector3", "x": 1, "y": 2, "z": 3}` |
| **Color** | Dict con tipo | `{"type": "Color", "r": 1, "g": 0.5, "b": 0.5, "a": 1}` |
| **Rect2** | Dict con tipo | `{"type": "Rect2", "x": 0, "y": 0, "w": 100, "h": 50}` |
| **Archivo** | Path `res://` | `"res://sprites/player.png"` |
| **Shape** | Dict con propiedades | `{"radius": 16.0}` |
| **Shape explícito** | Dict con shape_type | `{"shape_type": "CircleShape2D", "radius": 16.0}` |
| **Ref SubResource** | Dict con ref | `{"type": "SubResource", "ref": "my_shape"}` |
| **Ref ExtResource** | Dict con ref | `{"type": "ExtResource", "ref": "1"}` |
| **NodePath** | Dict con ref | `{"type": "NodePath", "ref": "../Player"}` |

#### Ejemplos por tipo de nodo

**Sprite2D - Textura y posición:**
```python
set_node_properties(session_id, scene_path="game.tscn",
    node_path="Sprite",
    properties={
        "texture": "res://sprites/player.png",
        "position": {"type": "Vector2", "x": 100, "y": 200},
        "scale": {"type": "Vector2", "x": 2.0, "y": 2.0},
        "flip_h": True,
        "modulate": {"type": "Color", "r": 1, "g": 0.8, "b": 0.8, "a": 1},
    })
```

**CollisionShape2D - Shape:**
```python
# Rectangle
set_node_properties(session_id, scene_path="game.tscn",
    node_path="Collision",
    properties={
        "shape": {"size": {"type": "Vector2", "x": 32, "y": 32}}
    })

# Circle
set_node_properties(session_id, scene_path="game.tscn",
    node_path="Collision",
    properties={
        "shape": {"shape_type": "CircleShape2D", "radius": 16.0}
    })

# Capsule
set_node_properties(session_id, scene_path="game.tscn",
    node_path="Collision",
    properties={
        "shape": {"shape_type": "CapsuleShape2D", "radius": 12, "height": 40}
    })
```

**Label - Texto:**
```python
set_node_properties(session_id, scene_path="game.tscn",
    node_path="Label",
    properties={
        "text": "Game Over",
        "horizontal_alignment": "HORIZONTAL_ALIGNMENT_CENTER",
        "autowrap_mode": "AUTOWRAP_WORD_SMART",
    })
```

**Timer:**
```python
set_node_properties(session_id, scene_path="game.tscn",
    node_path="Timer",
    properties={
        "wait_time": 2.5,
        "one_shot": True,
        "autostart": True,
    })
```

**Camera2D:**
```python
set_node_properties(session_id, scene_path="game.tscn",
    node_path="Camera",
    properties={
        "current": True,
        "zoom": {"type": "Vector2", "x": 2, "y": 2},
        "position_smoothing_enabled": True,
        "position_smoothing_speed": 5.0,
    })
```

**AudioStreamPlayer:**
```python
set_node_properties(session_id, scene_path="game.tscn",
    node_path="Music",
    properties={
        "stream": "res://audio/music.ogg",
        "autoplay": True,
        "volume_db": -10.0,
    })
```

**PointLight2D:**
```python
set_node_properties(session_id, scene_path="game.tscn",
    node_path="Light",
    properties={
        "color": {"type": "Color", "r": 1, "g": 0.8, "b": 0.5, "a": 1},
        "energy": 2.0,
        "range": 200.0,
        "shadow_enabled": True,
    })
```

**RigidBody2D:**
```python
set_node_properties(session_id, scene_path="game.tscn",
    node_path="Ball",
    properties={
        "mass": 1.0,
        "gravity_scale": 1.0,
        "bounce": 0.5,
        "friction": 0.3,
        "lock_rotation": False,
    })
```

**MeshInstance3D:**
```python
set_node_properties(session_id, scene_path="game.tscn",
    node_path="Mesh",
    properties={
        "mesh": "res://models/player.glb",
        "material_override": "res://materials/player.tres",
    })
```

---

### Recursos

#### `create_resource`
Crea un recurso `.tres`.

```python
create_resource(session_id: str, resource_path: str,
                resource_type: str, properties: dict = None) -> dict
```

#### `read_resource`
Lee propiedades de un recurso `.tres`.

```python
read_resource(session_id: str, resource_path: str) -> dict
```

#### `update_resource`
Actualiza propiedades de un recurso.

```python
update_resource(session_id: str, resource_path: str, properties: dict) -> dict
```

#### `add_ext_resource`
Añade una referencia externa a una escena.

```python
add_ext_resource(session_id: str, scene_path: str,
                 resource_type: str, resource_path: str,
                 resource_id: str = None, uid: str = "") -> dict
```

#### `add_sub_resource`
Crea un recurso embebido en una escena.

```python
add_sub_resource(session_id: str, scene_path: str,
                 resource_type: str, properties: dict = None,
                 resource_id: str = None) -> dict
```

#### `get_uid`
Obtiene el UID de un recurso.

```python
get_uid(session_id: str, resource_path: str) -> dict
```

#### `update_project_uids`
Actualiza todos los UIDs del proyecto.

```python
update_project_uids(session_id: str) -> dict
```

#### `list_resources`
Lista recursos del proyecto.

```python
list_resources(session_id: str, resource_type: str = None,
               recursive: bool = True) -> dict
```

---

### Scripts y Señales

#### `set_script`
Adjunta un script `.gd` a un nodo.

```python
set_script(session_id: str, scene_path: str,
           node_path: str, script_path: str) -> dict
```

#### `connect_signal`
Conecta una señal entre nodos.

```python
connect_signal(session_id: str, scene_path: str,
               from_node: str, signal: str,
               to_node: str, method: str,
               flags: int = 0, binds: list = None) -> dict
```

---

### Proyecto

#### `get_project_info`
Obtiene información del proyecto.

```python
get_project_info(session_id: str) -> dict
```

#### `get_project_structure`
Obtiene la estructura completa del proyecto.

```python
get_project_structure(session_id: str) -> dict
```

#### `find_scripts`
Busca scripts `.gd` en el proyecto.

```python
find_scripts(session_id: str) -> dict
```

#### `find_resources`
Busca recursos `.tres` en el proyecto.

```python
find_resources(session_id: str, type_filter: str = None) -> dict
```

#### `list_projects`
Busca proyectos Godot en un directorio.

```python
list_projects(session_id: str, directory: str, recursive: bool = True) -> dict
```

---

### Validación

#### `validate_tscn`
Valida un archivo `.tscn`.

```python
validate_tscn(scene_path: str, project_path: str = None, strict: bool = False) -> dict
```

#### `validate_gdscript`
Valida un script `.gd` usando validación inteligente de 3 capas.

**Nuevos parámetros (v2.0):**
- `project_path`: Habilita validación de sintaxis con Godot real
- `use_godot_syntax`: Usa Godot para errores de compilación

```python
validate_gdscript(
    script_path: str = None,
    script_content: str = None,
    project_path: str = None,        # NEW: Habilita Godot syntax check
    strict: bool = False,
    use_godot_syntax: bool = True    # NEW
) -> dict
```

**Retorna (nuevo):**
- `validation_mode`: `"api_only"` o `"api_plus_godot"`

**Lo que detecta:**
- Decoradores deprecated (`@onready`)
- Métodos removidos en Godot 4 (`yield`, `test_move`)
- Métodos inexistentes en tipos específicos

**Lo que NO detecta (por diseño):**
- Variables no declaradas (GDScript es dinámico)

#### `validate_project`
Valida todos los archivos del proyecto.

```python
validate_project(project_path: str, strict: bool = False) -> dict
```

---

### Debug

#### `run_debug_scene`
Ejecuta una escena en modo headless y captura output.

```python
run_debug_scene(
    project_path: str,
    scene_path: str = None,
    timeout: int = 30,
    debug_collisions: bool = False,
    debug_paths: bool = False,
    debug_navigation: bool = False
) -> dict
```

**Retorna:**
```json
{
  "success": true,
  "errors": [],
  "warnings": [],
  "prints": ["Hello from Godot!"],
  "exit_code": 0
}
```

#### `check_script_syntax`
Valida sintaxis GDScript usando Godot (`--check-only`).

```python
check_script_syntax(
    project_path: str,
    script_path: str,
    timeout: int = 30
) -> dict
```

---

## Capa 2: Godot CLI Bridge (16 herramientas)

Herramientas que utilizan Godot CLI nativo (`godot --headless`, `--script`, `--export`, etc.).

**Requieren:** Godot instalado y accesible en PATH.

### Export

#### `export_project`
Exporta el proyecto usando un preset configurado.

```python
export_project(
    project_path: str,
    export_preset: str,
    output_path: str,
    export_mode: str = "release",  # "release" | "debug" | "pack"
    patches: list = None,
    options: dict = None
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
Lista los presets de exportación configurados.

```python
list_export_presets(project_path: str) -> dict
```

**Retorna:** Lista de presets de `export_presets.cfg`.

#### `validate_export_preset`
Valida que un preset de exportación existe y es válido.

```python
validate_export_preset(
    project_path: str,
    preset_name: str
) -> dict
```

#### `get_export_log`
Obtiene el log de la última exportación.

```python
get_export_log(project_path: str, lines: int = 50) -> dict
```

---

### Runtime

#### `run_gdscript`
Ejecuta código GDScript arbitrario en instancia headless de Godot.

```python
run_gdscript(
    project_path: str,
    script_content: str,
    timeout: int = 30,
    args: list = None
) -> dict
```

**Ejemplo - Inspeccionar escena:**
```python
script = """
extends SceneTree
func _init():
    var scene = load("res://scenes/Player.tscn").instantiate()
    print("NODES:", scene.get_child_count(true))
    for child in scene.get_children(true):
        print("NODE:", child.name, "TYPE:", child.get_class())
    quit()
"""
result = run_gdscript(project_path, script)
```

#### `get_scene_info_runtime`
Obtiene información detallada de una escena cargándola en runtime.

```python
get_scene_info_runtime(
    project_path: str,
    scene_path: str
) -> dict
```

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
Llama a un método en todos los nodos de un grupo.

```python
call_group_runtime(
    project_path: str,
    scene_path: str,
    group: str,
    method: str,
    args: list = None
) -> dict
```

#### `get_classdb_info`
Obtiene información de ClassDB (clases, métodos, propiedades).

```python
get_classdb_info(
    project_path: str,
    class_name: str = None
) -> dict
```

#### `get_performance_metrics`
Ejecuta escena y captura métricas de performance.

```python
get_performance_metrics(
    project_path: str,
    scene_path: str,
    run_seconds: int = 5
) -> dict
```

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
Verifica que una escena se puede cargar sin errores.

```python
test_scene_load(
    project_path: str,
    scene_path: str
) -> dict
```

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

### Import

#### `reimport_assets`
Reimporta assets del proyecto.

```python
reimport_assets(
    project_path: str,
    asset_paths: list = None  # None = reimportar todo
) -> dict
```

#### `get_import_settings`
Obtiene configuración de importación de un asset.

```python
get_import_settings(
    project_path: str,
    asset_path: str
) -> dict
```

---

### Screenshot

#### `capture_scene_frame`
Captura un frame específico de una escena ejecutándose.

```python
capture_scene_frame(
    project_path: str,
    scene_path: str,
    frame_number: int = 1,
    output_path: str = None,
    resolution: tuple = None
) -> dict
```

**Nota:** Usa `--write-movie` internamente. Requiere ejecutar la escena.

#### `capture_scene_sequence`
Captura una secuencia de frames.

```python
capture_scene_sequence(
    project_path: str,
    scene_path: str,
    frame_count: int = 30,
    output_dir: str = None,
    fps: int = 60
) -> dict
```

---

### Movie

#### `write_movie`
Captura video de una escena ejecutándose.

```python
write_movie(
    project_path: str,
    scene_path: str,
    output_path: str,
    duration_seconds: int = 5,
    fps: int = 60,
    resolution: tuple = None
) -> dict
```

#### `write_movie_with_script`
Captura video con script de setup (mover cámara, etc.).

```python
write_movie_with_script(
    project_path: str,
    scene_path: str,
    output_path: str,
    setup_script: str = None,
    duration_seconds: int = 5,
    fps: int = 60
) -> dict
```

---

## Capa 3: LSP/DAP Native (10 herramientas)

Herramientas que utilizan los protocolos nativos de Godot (LSP en puerto 6005, DAP en puerto 6006).

**Requieren:** Godot Editor abierto con LSP/DAP habilitado.

**No requieren instalación adicional** — son features nativas de Godot. Solo habilítalos en `Editor > Editor Settings > Network > Language Server` (puerto 6005) y `Debug Adapter` (puerto 6006).

### LSP (Language Server Protocol)

#### `lsp_get_completions`
Obtiene autocompletado de GDScript en posición específica.

```python
lsp_get_completions(
    project_path: str,
    file_path: str,
    line: int,
    column: int
) -> dict
```

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
Obtiene documentación hover para símbolo en posición.

```python
lsp_get_hover(
    project_path: str,
    file_path: str,
    line: int,
    column: int
) -> dict
```

#### `lsp_get_symbols`
Obtiene todos los símbolos de un archivo GDScript.

```python
lsp_get_symbols(
    project_path: str,
    file_path: str
) -> dict
```

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
Obtiene diagnósticos (errores, warnings) de un archivo.

```python
lsp_get_diagnostics(
    project_path: str,
    file_path: str
) -> dict
```

---

### DAP (Debug Adapter Protocol)

#### `dap_start_debugging`
Inicia sesión de debugging.

```python
dap_start_debugging(
    project_path: str,
    scene_path: str = None
) -> dict
```

**Retorna:**
```json
{
  "session_id": "dap_001",
  "status": "started",
  "breakpoints_supported": true
}
```

#### `dap_set_breakpoint`
Establece breakpoint en archivo y línea.

```python
dap_set_breakpoint(
    session_id: str,
    file_path: str,
    line: int,
    condition: str = None
) -> dict
```

#### `dap_continue`
Continúa ejecución hasta siguiente breakpoint.

```python
dap_continue(session_id: str) -> dict
```

#### `dap_step_over`
Step over (ejecuta línea actual sin entrar a funciones).

```python
dap_step_over(session_id: str) -> dict
```

#### `dap_step_into`
Step into (entra a funciones).

```python
dap_step_into(session_id: str) -> dict
```

#### `dap_get_stack_trace`
Obtiene stack trace actual con variables.

```python
dap_get_stack_trace(session_id: str) -> dict
```

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

## Capa 4: Project Intelligence (7 herramientas)

Herramientas de análisis estático del proyecto. **No requieren Godot.**

### Dependency Graph

#### `get_dependency_graph`
Construye grafo de dependencias entre archivos del proyecto.

```python
get_dependency_graph(
    project_path: str,
    file_path: str = None,  # None = todo el proyecto
    depth: int = 3
) -> dict
```

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
Encuentra assets no referenciados por ninguna escena o script.

```python
find_unused_assets(
    project_path: str,
    asset_types: list = None  # ["texture", "audio", "model"]
) -> dict
```

---

### Signal Graph

#### `get_signal_graph`
Construye grafo de conexiones de señales en el proyecto.

```python
get_signal_graph(
    project_path: str,
    scene_path: str = None  # None = todo el proyecto
) -> dict
```

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
  "orphan_signals": [],
  "unconnected_signals": ["button_pressed"]
}
```

#### `find_orphan_signals`
Encuentra señales conectadas a métodos que no existen.

```python
find_orphan_signals(project_path: str) -> dict
```

---

### Code Analysis

#### `analyze_script`
Análisis completo de un script GDScript.

```python
analyze_script(
    project_path: str,
    script_path: str
) -> dict
```

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
Encuentra "code smells" en todo el proyecto.

```python
find_code_smells(
    project_path: str,
    severity: str = "warning"  # "info" | "warning" | "error"
) -> dict
```

**Detecta:**
- Funciones demasiado largas (>50 líneas)
- Clases demasiado grandes (>300 líneas)
- Complejidad ciclomática alta (>10)
- Nesting profundo (>4 niveles)
- Magic numbers
- TODOs sin resolver
- Señales huérfanas

#### `get_project_metrics`
Métricas agregadas del proyecto completo.

```python
get_project_metrics(project_path: str) -> dict
```

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

## Nodos con propiedades mapeadas

El esquema de propiedades (`NODE_PROPERTY_SCHEMAS`) cubre **150+ tipos de nodo**, incluyendo:

### Física 2D/3D
`CollisionShape2D`, `CollisionShape3D`, `CollisionPolygon2D`, `CollisionPolygon3D`,
`Area2D`, `Area3D`, `RigidBody2D`, `RigidBody3D`, `StaticBody2D`, `StaticBody3D`,
`CharacterBody2D`, `CharacterBody3D`, `AnimatableBody2D`, `AnimatableBody3D`

### Rendering 2D
`Sprite2D`, `Sprite3D`, `AnimatedSprite2D`, `AnimatedSprite3D`, `TextureRect`,
`TextureButton`, `NinePatchRect`, `Polygon2D`, `Line2D`, `GPUParticles2D`,
`GPUParticles3D`, `CPUParticles2D`, `CPUParticles3D`

### Rendering 3D
`MeshInstance3D`, `CSGMesh3D`, `CSGBox3D`, `CSGSphere3D`, `CSGCylinder3D`,
`CSGCapsule3D`, `CSGTorus3D`

### Luces
`Light2D`, `PointLight2D`, `DirectionalLight2D`,
`DirectionalLight3D`, `OmniLight3D`, `SpotLight3D`

### Cámaras
`Camera2D`, `Camera3D`

### UI
`Label`, `RichTextLabel`, `Button`, `LineEdit`, `TextEdit`, `CodeEdit`,
`CheckBox`, `CheckButton`, `OptionButton`, `ColorRect`, `ColorPicker`,
`ColorPickerButton`, `ProgressBar`, `TextureProgressBar`, `HSlider`, `VSlider`,
`SpinBox`, `Panel`, `PanelContainer`, `VBoxContainer`, `HBoxContainer`,
`GridContainer`, `MarginContainer`, `CenterContainer`, `ScrollContainer`,
`TabContainer`, `TabBar`, `Tree`, `ItemList`, `ReferenceRect`

### Audio
`AudioStreamPlayer`, `AudioStreamPlayer2D`, `AudioStreamPlayer3D`

### Animación
`AnimationPlayer`, `AnimationTree`

### Mundo
`WorldEnvironment`, `Environment`, `CanvasLayer`, `YSort`,
`ParallaxBackground`, `ParallaxLayer`

### Navegación
`NavigationRegion2D`, `NavigationRegion3D`,
`NavigationAgent2D`, `NavigationAgent3D`

### TileMap
`TileMap`, `TileMapLayer`

### Materiales
`ShaderMaterial`, `StandardMaterial3D`, `ORMMaterial3D`

### Sky
`ProceduralSkyMaterial`, `PanoramaSkyMaterial`, `PhysicalSkyMaterial`

### Shapes (SubResources)
`RectangleShape2D`, `CircleShape2D`, `CapsuleShape2D`, `WorldBoundaryShape2D`,
`SegmentShape2D`, `ConvexPolygonShape2D`, `ConcavePolygonShape2D`,
`RectangleShape3D`, `SphereShape3D`, `CapsuleShape3D`, `CylinderShape3D`,
`WorldBoundaryShape3D`, `BoxShape3D`, `ConvexPolygonShape3D`, `ConcavePolygonShape3D`

### Meshes (SubResources)
`BoxMesh`, `SphereMesh`, `CylinderMesh`, `CapsuleMesh`, `PlaneMesh`,
`QuadMesh`, `PrismMesh`, `TorusMesh`, `RibbonTrailMesh`, `TubeTrailMesh`

### Otros
`Timer`, `RayCast2D`, `RayCast3D`, `ShapeCast2D`, `ShapeCast3D`,
`Path2D`, `Path3D`, `PathFollow2D`, `PathFollow3D`,
`SpringArm2D`, `SpringArm3D`, `Skeleton2D`, `Skeleton3D`, `Bone2D`,
`LightOccluder2D`, `OccluderPolygon2D`,
`VisibleOnScreenNotifier2D`, `VisibleOnScreenNotifier3D`,
`VisibilityEnabler2D`, `VisibilityEnabler3D`,
`RemoteTransform2D`, `RemoteTransform3D`,
`PinJoint2D`, `DampedSpringJoint2D`, `GrooveJoint2D`,
`HingeJoint3D`, `SliderJoint3D`, `ConeTwistJoint3D`, `Generic6DOFJoint3D`,
`VehicleBody2D`, `VehicleWheel2D`, `VehicleBody3D`, `VehicleWheel3D`,
`MultiplayerSpawner`, `SubViewport`, `SubViewportContainer`,
`ParticleProcessMaterial`

---

## Capa 5: Skeleton (6 herramientas)

Herramientas para crear y configurar esqueletos 2D y 3D.

### Skeleton2D

#### `create_skeleton2d`
Crea un nodo Skeleton2D en una escena.

```python
create_skeleton2d(
    session_id: str,
    scene_path: str,
    parent_path: str = ".",
    node_name: str = "Skeleton2D",
    properties: dict = None
) -> dict
```

**Ejemplo:**
```python
create_skeleton2d(
    session_id=session_id,
    scene_path="player.tscn",
    parent_path="Body",
    node_name="Skeleton2D"
)
```

#### `add_bone2d`
Añade un hueso (Bone2D) al Skeleton2D.

```python
add_bone2d(
    session_id: str,
    scene_path: str,
    skeleton_path: str,
    bone_name: str,
    parent_bone: str = None,
    rest: dict = None,  # {"position": {"x": 0, "y": 0}, "rotation": 0, "scale": {"x": 1, "y": 1}}
    length: float = 32.0,
    bone_angle: float = 0.0,
    autocalculate_length_and_angle: bool = True,
    enabled: bool = True,
    properties: dict = None
) -> dict
```

**Ejemplo - Brazo con 2 huesos:**
```python
# Hueso del brazo (padre)
add_bone2d(
    session_id=session_id,
    scene_path="player.tscn",
    skeleton_path="Skeleton2D",
    bone_name="UpperArm",
    rest={"position": {"x": 0, "y": 0}, "rotation": 0},
    length=40.0,
    bone_angle=-90.0
)

# Hueso del antebrazo (hijo)
add_bone2d(
    session_id=session_id,
    scene_path="player.tscn",
    skeleton_path="Skeleton2D",
    bone_name="ForeArm",
    parent_bone="UpperArm",
    rest={"position": {"x": 40, "y": 0}, "rotation": 0},
    length=35.0,
    bone_angle=0.0
)
```

#### `setup_polygon2d_skinning`
Vincula un Polygon2D a un Skeleton2D para deformación por huesos.

```python
setup_polygon2d_skinning(
    session_id: str,
    scene_path: str,
    polygon_path: str,
    skeleton_path: str,
    bone_weights: dict = None,  # {"BoneName": [w1, w2, w3, ...], ...}
    auto_calculate: bool = False
) -> dict
```

**Ejemplo:**
```python
setup_polygon2d_skinning(
    session_id=session_id,
    scene_path="player.tscn",
    polygon_path="Body/Sprite",
    skeleton_path="Body/Skeleton2D",
    bone_weights={
        "UpperArm": [1.0, 1.0, 0.5, 0.0, 0.0, 0.0],
        "ForeArm": [0.0, 0.0, 0.5, 1.0, 1.0, 1.0]
    }
)
```

---

### Skeleton3D

#### `create_skeleton3d`
Crea un nodo Skeleton3D en una escena.

```python
create_skeleton3d(
    session_id: str,
    scene_path: str,
    parent_path: str = ".",
    node_name: str = "Skeleton3D",
    properties: dict = None
) -> dict
```

#### `add_bone_attachment3d`
Añade un BoneAttachment3D para vincular nodos a huesos.

```python
add_bone_attachment3d(
    session_id: str,
    scene_path: str,
    skeleton_path: str,
    node_name: str,
    bone_name: str = None,
    bone_idx: int = None,
    override_pose: bool = False,
    properties: dict = None
) -> dict
```

**Ejemplo - Vincular espada al hueso de la mano:**
```python
add_bone_attachment3d(
    session_id=session_id,
    scene_path="player.tscn",
    skeleton_path="Skeleton3D",
    node_name="SwordAttachment",
    bone_name="RightHand",
    override_pose=False
)
```

#### `setup_mesh_skinning`
Vincula un MeshInstance3D a un Skeleton3D para deformación por huesos.

```python
setup_mesh_skinning(
    session_id: str,
    scene_path: str,
    mesh_path: str,
    skeleton_path: str,
    skin_resource_path: str = None,
    auto_generate_skin: bool = True
) -> dict
```

**Ejemplo:**
```python
setup_mesh_skinning(
    session_id=session_id,
    scene_path="player.tscn",
    mesh_path="Body/MeshInstance3D",
    skeleton_path="Skeleton3D",
    auto_generate_skin=True
)
```

---

---

## Capa 6: Array Operations (2 herramientas)

Operaciones quirúrgicas sobre arrays en escenas TSCN **sin reescribir el archivo completo**. Preserva el tipo del array (`Array[PackedScene]`, `Array[int]`, etc.) y todos los metadatos de la escena.

### Array Operations

#### `scene_array_operation`

Realiza operaciones sobre arrays de nodos en escenas.

```python
scene_array_operation(
    session_id: str,
    scene_path: str,
    node_path: str,
    property_name: str,
    operation: str,       # "append" | "remove" | "replace" | "insert" | "clear"
    value: Any = None,    # Para append, replace, insert
    index: int = -1       # Para remove, replace, insert
) -> dict
```

**Operaciones:**

| Operación | Descripción | Parámetros requeridos |
|-----------|-------------|----------------------|
| `append` | Añade elemento al final | `value` |
| `remove` | Elimina elemento por índice | `index` |
| `replace` | Reemplaza elemento en índice | `index`, `value` |
| `insert` | Inserta elemento en posición | `index`, `value` |
| `clear` | Vacía el array completo | Ninguno |

**Ejemplo - Añadir escena a un spawner:**
```python
scene_array_operation(
    session_id=session_id,
    scene_path="spawner.tscn",
    node_path="Spawner",
    property_name="scenes",
    operation="append",
    value={"type": "ExtResource", "ref": "3_newscene"}
)
```

**Ejemplo - Eliminar elemento:**
```python
scene_array_operation(
    session_id=session_id,
    scene_path="spawner.tscn",
    node_path="Spawner",
    property_name="scenes",
    operation="remove",
    index=2
)
```

#### `preview_array_operation`

Previsualiza qué cambios haría una operación de array **sin aplicarlos**.

```python
preview_array_operation(
    session_id: str,
    scene_path: str,
    node_path: str,
    property_name: str,
    operation: str,
    value: Any = None,
    index: int = -1
) -> dict
```

**Retorna:**
```json
{
  "preview": true,
  "operation": "append",
  "before": ["Scene1", "Scene2"],
  "after": ["Scene1", "Scene2", "NewScene"],
  "diff": "+ NewScene"
}
```

---

## Capa 7: Resource Builder (9 herramientas)

Sistema genérico de construcción de SubResources complejos. Usa un patrón de capas: desde genéricos hasta high-level helpers. **No requiere Godot.**

### Capa 7.1: Genéricos

#### `build_resource`

Crea cualquier SubResource genérico en una escena.

```python
build_resource(
    session_id: str,
    scene_path: str,
    resource_type: str,
    properties: dict = None,
    resource_id: str = None
) -> dict
```

**Ejemplo - Crear un RectangleShape2D:**
```python
build_resource(
    session_id=session_id,
    scene_path="player.tscn",
    resource_type="RectangleShape2D",
    properties={
        "size": {"type": "Vector2", "x": 32, "y": 48}
    },
    resource_id="player_shape"
)
```

#### `build_nested_resource`

Crea jerarquías de SubResources con referencias cruzadas entre ellos.

```python
build_nested_resource(
    session_id: str,
    scene_path: str,
    root_type: str,
    root_id: str,
    children: list,          # [{"type": "...", "id": "...", "properties": {...}}, ...]
    root_properties: dict = None,
    array_properties: set = None  # Keys que deben ser arrays planos
) -> dict
```

**Ejemplo - Animation con tracks:**
```python
build_nested_resource(
    session_id=session_id,
    scene_path="anim.tscn",
    root_type="Animation",
    root_id="my_anim",
    children=[
        {"type": "AnimationTrackKeyframeValue", "id": "kf_0", "properties": {...}},
        {"type": "AnimationTrackKeyframeValue", "id": "kf_1", "properties": {...}},
    ],
    root_properties={
        "tracks/0/keys/times": [0.0, 1.0],
        "tracks/0/keys/transitions": [1.0, 1.0],
        "tracks/0/keys/updates": [
            {"type": "SubResource", "ref": "kf_0"},
            {"type": "SubResource", "ref": "kf_1"},
        ],
    },
    array_properties={"tracks/0/keys/times", "tracks/0/keys/transitions"}
)
```

---

### Capa 7.2: Animation Helpers

#### `create_animation`

Crea un recurso `Animation` con tracks de keyframes.

```python
create_animation(
    session_id: str,
    scene_path: str,
    name: str,
    length: float,
    tracks: list,
    loop_mode: int = 0,
    step: float = 0.0
) -> dict
```

**Parámetros de track:**
```python
{
    "type": "value",          # "value" | "method" | "bezier" | "audio"
    "path": "Node:property",  # NodePath al nodo y propiedad
    "keys": [                 # Lista de keyframes
        {
            "time": 0.0,
            "value": 100.0,
            "transition": 1.0,
        },
    ],
}
```

**Ejemplo - Animación de posición:**
```python
create_animation(
    session_id=session_id,
    scene_path="player.tscn",
    name="walk",
    length=1.0,
    tracks=[{
        "type": "value",
        "path": "Sprite2D:position",
        "keys": [
            {"time": 0.0, "value": {"type": "Vector2", "x": 0, "y": 0}},
            {"time": 0.5, "value": {"type": "Vector2", "x": 10, "y": -5}},
            {"time": 1.0, "value": {"type": "Vector2", "x": 0, "y": 0}},
        ],
    }],
)
```

#### `create_state_machine`

Crea un `AnimationNodeStateMachine` con estados y transiciones.

```python
create_state_machine(
    session_id: str,
    scene_path: str,
    name: str,
    states: list,
    transitions: list = None,
    state_machine_type: int = 0
) -> dict
```

**Parámetros de estado:**
```python
{
    "name": "walk",
    "node_type": "AnimationNodeAnimation",  # Opcional
    "node_properties": {"animation": &"Walk"},  # Opcional
    "position": {"type": "Vector2", "x": 0, "y": 0},  # Posición en el editor
}
```

**Parámetros de transición:**
```python
{
    "from": "idle",
    "to": "walk",
    "switch_mode": 0,       # 0=immediate, 1=sync, 2=at_end
    "xfade_time": 0.0,
    "advance_mode": 1,      # 1=auto
    "reset": True,
    "priority": 1,
}
```

> **Nota:** Las transiciones se serializan en formato triplete de Godot:
> `["idle", "walk", SubResource("trans_idle_walk"), "walk", "run", SubResource("trans_walk_run")]`

**Ejemplo:**
```python
create_state_machine(
    session_id=session_id,
    scene_path="player.tscn",
    name="player_states",
    states=[
        {"name": "idle", "node_properties": {"animation": &"Idle"}},
        {"name": "walk", "node_properties": {"animation": &"Walk"}},
        {"name": "attack", "node_properties": {"animation": &"Attack"}},
    ],
    transitions=[
        {"from": "idle", "to": "walk"},
        {"from": "walk", "to": "idle"},
        {"from": "idle", "to": "attack", "switch_mode": 2},
    ],
)
```

---

### Capa 7.3: AnimationTree Helpers

#### `create_blend_space_1d`

Crea un `AnimationNodeBlendSpace1D` para mezclar animaciones en un eje (ej: idle→walk→run).

```python
create_blend_space_1d(
    session_id: str,
    scene_path: str,
    name: str,
    blend_points: list,
    blend_mode: int = 0,
    min_space: float = 0.0,
    max_space: float = 1.0,
    snap: float = 0.001
) -> dict
```

**Parámetros de blend point:**
```python
{
    "position": 0.5,
    "animation": "Walk",    # Nombre de la animación
}
```

**Ejemplo - Idle→Walk→Run:**
```python
create_blend_space_1d(
    session_id=session_id,
    scene_path="player.tscn",
    name="movement_blend",
    blend_points=[
        {"position": 0.0, "animation": "Idle"},
        {"position": 0.5, "animation": "Walk"},
        {"position": 1.0, "animation": "Run"},
    ],
)
```

#### `create_blend_space_2d`

Crea un `AnimationNodeBlendSpace2D` para mezclar animaciones en 2 ejes (ej: direcciones 4-way).

```python
create_blend_space_2d(
    session_id: str,
    scene_path: str,
    name: str,
    blend_points: list,
    blend_mode: int = 0,
    min_space: dict = None,   # {"x": -1.0, "y": -1.0}
    max_space: dict = None,   # {"x": 1.0, "y": 1.0}
    snap: float = 0.001
) -> dict
```

**Parámetros de blend point:**
```python
{
    "position": {"x": 0.0, "y": 1.0},
    "animation": "Walk_Up",
}
```

**Ejemplo - 4 direcciones:**
```python
create_blend_space_2d(
    session_id=session_id,
    scene_path="player.tscn",
    name="direction_blend",
    blend_points=[
        {"position": {"x": 0.0, "y": 1.0}, "animation": "Walk_Up"},
        {"position": {"x": 0.0, "y": -1.0}, "animation": "Walk_Down"},
        {"position": {"x": -1.0, "y": 0.0}, "animation": "Walk_Left"},
        {"position": {"x": 1.0, "y": 0.0}, "animation": "Walk_Right"},
    ],
)
```

#### `create_blend_tree`

Crea un `AnimationNodeBlendTree` con nodos y conexiones.

```python
create_blend_tree(
    session_id: str,
    scene_path: str,
    name: str,
    nodes: list,
    connections: list = None
) -> dict
```

**Parámetros de nodo:**
```python
{
    "name": "blend",
    "type": "AnimationNodeBlend2",
    "position": {"x": 200, "y": 0},
    "properties": {"blend_amount": 0.5},
}
```

**Parámetros de conexión:**
```python
{
    "from_node": "output",
    "from_port": 0,
    "to_node": "blend",
    "to_port": 0,
}
```

**Ejemplo - Blend2 con Animation:**
```python
create_blend_tree(
    session_id=session_id,
    scene_path="player.tscn",
    name="combat_blend",
    nodes=[
        {"name": "idle_anim", "type": "AnimationNodeAnimation",
         "position": {"x": 0, "y": 0},
         "properties": {"animation": &"Idle"}},
        {"name": "attack_anim", "type": "AnimationNodeAnimation",
         "position": {"x": 0, "y": 100},
         "properties": {"animation": &"Attack"}},
        {"name": "blend", "type": "AnimationNodeBlend2",
         "position": {"x": 200, "y": 50}},
    ],
    connections=[
        {"from_node": "idle_anim", "from_port": 0, "to_node": "blend", "to_port": 0},
        {"from_node": "attack_anim", "from_port": 0, "to_node": "blend", "to_port": 1},
    ],
)
```

---

### Capa 7.4: Asset Helpers

#### `create_sprite_frames`

Crea un recurso `SpriteFrames` con animaciones frame-by-frame.

```python
create_sprite_frames(
    session_id: str,
    scene_path: str,
    name: str,
    animations: list,
    resource_id: str = None
) -> dict
```

**Parámetros de animación:**
```python
{
    "name": "idle",
    "speed": 5.0,
    "loop": True,
    "frames": [
        {
            "texture": "res://sprites/player_idle_01.png",
            "hframes": 1,
            "vframes": 1,
            "frame": {"x": 0, "y": 0},
            "duration": 0.1,
        },
    ],
}
```

**Ejemplo:**
```python
create_sprite_frames(
    session_id=session_id,
    scene_path="player.tscn",
    name="player_frames",
    animations=[
        {
            "name": "idle",
            "speed": 5.0,
            "loop": True,
            "frames": [
                {"texture": "res://sprites/player_idle_01.png", "duration": 0.1},
                {"texture": "res://sprites/player_idle_02.png", "duration": 0.1},
            ],
        },
        {
            "name": "walk",
            "speed": 8.0,
            "loop": True,
            "frames": [
                {"texture": "res://sprites/player_walk_01.png", "duration": 0.08},
                {"texture": "res://sprites/player_walk_02.png", "duration": 0.08},
                {"texture": "res://sprites/player_walk_03.png", "duration": 0.08},
            ],
        },
    ],
)
```

#### `create_tile_set`

Crea un recurso `TileSet` con atlas de tiles y capas de colisión.

```python
create_tile_set(
    session_id: str,
    scene_path: str,
    name: str,
    tile_size: dict,
    atlas: str,
    tiles: list = None,
    resource_id: str = None
) -> dict
```

**Parámetros de tile:**
```python
{
    "id": 0,
    "texture_rect": {"x": 0, "y": 0, "w": 16, "h": 16},
    "collision": [  # Opcional: puntos del polígono de colisión
        {"x": 0, "y": 0},
        {"x": 16, "y": 0},
        {"x": 16, "y": 16},
        {"x": 0, "y": 16},
    ],
}
```

**Ejemplo:**
```python
create_tile_set(
    session_id=session_id,
    scene_path="level.tscn",
    name="ground_tiles",
    tile_size={"x": 16, "y": 16},
    atlas="res://tiles/ground_atlas.png",
    tiles=[
        {
            "id": 0,
            "texture_rect": {"x": 0, "y": 0, "w": 16, "h": 16},
            "collision": [
                {"x": 0, "y": 0}, {"x": 16, "y": 0},
                {"x": 16, "y": 16}, {"x": 0, "y": 16},
            ],
        },
        {"id": 1, "texture_rect": {"x": 16, "y": 0, "w": 16, "h": 16}},
    ],
)
```

---

---

## Capa 8: TileMap Tools (7 herramientas) — Requiere Godot

> Usa la API real de Godot (`run_gdscript`) para inspeccionar y manipular TileMaps/TileSets.
> Soporta `TileMap` (deprecated) y `TileMapLayer` (Godot 4.6+).
> Ver documentación completa en [TILEMAP_TOOLS.md](TILEMAP_TOOLS.md).

### `inspect_tileset`
Inspeccionar TileSet: sources, tiles, atlas, terrain sets, patterns.

```python
inspect_tileset(
    project_path="D:/MyGame",
    tileset_path="res://tilesets/ground.tres",
)
```

### `inspect_tilemap`
Inspeccionar TileMap/TileMapLayer: celdas usadas, bounds, layers.

```python
inspect_tilemap(
    project_path="D:/MyGame",
    scene_path="res://scenes/Level.tscn",
    tilemap_node_path="Background",
)
```

### `set_tilemap_cells`
Setear o borrar celdas individuales.

```python
set_tilemap_cells(
    project_path="D:/MyGame",
    scene_path="res://scenes/Level.tscn",
    cells=[
        {"coords": {"x": 5, "y": 3}, "source_id": 1, "atlas_coords": {"x": 2, "y": 0}},
        {"coords": {"x": 6, "y": 3}, "erase": True},
    ],
)
```

### `set_tilemap_layer_properties`
Configurar layer: z_index, y_sort_enabled, modulate.

```python
set_tilemap_layer_properties(
    project_path="D:/MyGame",
    scene_path="res://scenes/Level.tscn",
    layer=0,
    properties={"z_index": 10, "y_sort_enabled": True},
)
```

### `apply_tilemap_terrain`
Aplicar terrain set a un rango de celdas.

```python
apply_tilemap_terrain(
    project_path="D:/MyGame",
    scene_path="res://scenes/Level.tscn",
    cells=[{"x": 10, "y": 5}, {"x": 11, "y": 5}],
    terrain_set=0,
    terrain=1,
)
```

### `create_tilemap_pattern`
Crear pattern desde rango de celdas (guardado como `.tres`).

```python
create_tilemap_pattern(
    project_path="D:/MyGame",
    scene_path="res://scenes/Level.tscn",
    rect={"x": 0, "y": 0, "width": 4, "height": 4},
)
```

### `set_tilemap_pattern`
Aplicar pattern en posición (`pattern_path` o `pattern_index`).

```python
set_tilemap_pattern(
    project_path="D:/MyGame",
    scene_path="res://scenes/Level.tscn",
    position={"x": 10, "y": 10},
    pattern_path="res://patterns/room_corner.tres",
)
```

---

*Documento de herramientas v4.5.0*
*Fecha: 2026-04-30*
*Total: 106 herramientas*
