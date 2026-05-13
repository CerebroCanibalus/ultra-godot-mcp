# AGENTS.md - Subagentes del MCP Godot Python

Define subagentes del servidor MCP Godot Python. Cada uno hace una cosa bien.

---

## 📋 Subagentes

| Agente | Qué hace |
|--------|----------|
| `@Parser` | Parsea .tscn, .gd, .tres. Lee y analiza escenas. |
| `@ArrayOps` | Añade/quita/reemplaza elementos de arrays sin reescribir el archivo. |
| `@LSPClient` | Autocompletado, hover, diagnósticos GDScript. |
| `@DAPClient` | Debugging, breakpoints, stack traces. |
| `@CacheMaster` | Cache LRU + TTL. Evita repetir operaciones. |
| `@TemplateEngine` | Genera código GDScript con templates Jinja2. |
| `@ToolSmith` | Crea herramientas FastMCP nuevas. |
| `@SessionKeeper` | Sesiones ligeras con estado temporal. |
| `@GodotSage` | Responde preguntas de Godot. Busca docs. |

---

## 🎯 @Parser

**Herramientas:** `get_scene_tree`, `list_scenes`, `find_nodes`, `get_node_properties`

**Flujo:** Identificar archivo → Seleccionar parser → Parsear → Transformar → Serializar.

```python
from godot_mcp.core.parser import TSCNParser
parser = TSCNParser()
scene_data = parser.parse("res://scenes/Player.tscn")
nodes = parser.find_nodes("res://scenes/Player.tscn", "Area2D")
```

---

## ⚡ @CacheMaster

**Herramientas:** `get_scene_tree`, `list_scenes`, `find_nodes`, `get_node_properties` (todas cacheadas).

**Flujo:** ¿Está en cache? → Sí: retornar. No: ejecutar → guardar → invalidar.

```python
from godot_mcp.core.cache import CacheManager
cache = CacheManager(max_size=100, ttl=300)
result = cache.get("scenes:/Player.tscn", fetch_scene_tree)
cache.invalidate("scenes:/Player.tscn")
cache.clear()
```

---

## 📝 @TemplateEngine

**Herramientas:** `create_scene`, `create_script`, `add_node`, `set_script`

**Flujo:** Elegir template → Dar variables → Renderizar Jinja2 → Escribir → Cachear.

```python
from godot_mcp.templates import TemplateEngine
engine = TemplateEngine()
player_script = engine.render("player_controller.gd.j2", {
    "class_name": "Player", "extends": "CharacterBody2D",
    "speed": 200.0, "jump_force": 400.0
})
health_template = engine.render("health_component.gd.j2", {
    "max_health": 100, "regen_rate": 5.0, "invincibility_time": 1.0
})
```

**Templates:**

| Template | Variables |
|----------|-----------|
| `player_controller.gd.j2` | speed, jump_force, extends |
| `health_component.gd.j2` | max_health, regen_rate |
| `state_machine.gd.j2` | states, initial_state |
| `hitbox_component.gd.j2` | damage, knockback |
| `character_body_2d.tscn.j2` | animations, stats |

---

## 🔧 @ToolSmith

**Herramientas:** `create_scene`, `add_node`, `connect_signal`, `create_resource`

**Flujo:** Definir herramienta → Implementar FastMCP → Registrar → Documentar → Testear.

```python
from godot_mcp.tools import tool, ToolRegistry
@tool(name="spawn_enemy", description="Creates an enemy at position")
def spawn_enemy(enemy_type: str, position: Vector2) -> dict:
    return {"enemy_id": "enemy_001", "type": enemy_type}
registry = ToolRegistry()
registry.register(spawn_enemy)
```

---

## 🔒 @SessionKeeper

**Herramientas:** `start_session`, `get_active_session`, `end_session`, `list_sessions`

**Flujo:** Crear sesión → Poner estado → Operar → Commit/rollback → Limpiar.

```python
from godot_mcp.core.session import SessionManager
manager = SessionManager()
session = manager.create_session(name="debug_player", auto_close=True)
session.set("player_hp", 100)
session.set("debug_mode", True)
hp = session.get("player_hp")
manager.close_session(session.id)
```

---

## 📚 @GodotSage

**Herramientas:** `context7_query_docs`, `get_godot_version`, `get_project_info`

**Flujo:** Consultar → Buscar en KB → Si no está, preguntar a Context7 → Responder → Guardar.

```python
from godot_mcp.knowledge import KnowledgeBase
sage = KnowledgeBase()
info = sage.query("CharacterBody2D movement")
info2 = sage.query("Area2D body_entered signal")
```

---

## ⚡ @ArrayOps

**Herramientas:** `scene_array_operation`, `preview_array_operation`

**Flujo:** Encontrar array → Elegir operación → Dar valor/índice → Previsualizar → Aplicar.

```python
from godot_mcp.tools.array_tools import scene_array_operation
result = scene_array_operation(
    scene_path="spawner.tscn", node_path="Spawner",
    property_name="scenes", operation="append",
    value={"type": "ExtResource", "ref": "3_newscene"}
)
preview = preview_array_operation(
    scene_path="spawner.tscn", node_path="Spawner",
    property_name="scenes", operation="remove", index=0
)
```

---

## 🔍 @LSPClient

**Herramientas:** `lsp_get_completions`, `lsp_get_hover`, `lsp_get_symbols`, `lsp_get_diagnostics`

**Requisitos:** Godot Editor abierto (puerto 6005) o bridge LSP.

**Bridge config (`opencode.jsonc`):**
```json
"lsp": {
    "gdscript": {
        "command": ["python", "D:/Mis Juegos/GodotMCP/godot-mcp-python/scripts/godot_lsp_bridge.py"],
        "extensions": [".gd", ".gdshader"]
    }
}
```

Bridge: sin dependencias, reescribe plaintext→gdscript, reconexión automática, sin auto-lanzamiento.

**Flujo:** Godot abierto → Configurar bridge (1 vez) → Abrir .gd → Autocompletado automático.

```python
completions = lsp_get_completions("D:/MyGame", "res://scripts/player.gd", 10, 5)
hover = lsp_get_hover("D:/MyGame", "res://scripts/player.gd", 15, 8)
```

---

## 🐛 @DAPClient

**Herramientas:** `dap_start_debugging`, `dap_set_breakpoint`, `dap_continue`, `dap_step_over`, `dap_step_into`, `dap_get_stack_trace`

**Requisitos:** Godot Editor con debugging (puerto 6006).

**Flujo:** Abrir Godot con debug → start_debugging → set_breakpoint → Ejecutar → step_over/step_into → stack_trace.

```python
session = dap_start_debugging("D:/MyGame")
breakpoint = dap_set_breakpoint("D:/MyGame", "res://scripts/player.gd", 42)
stack = dap_get_stack_trace("D:/MyGame")
```

---

## 🔄 Flujo Coordinado

```
@GodotSage → @Parser → @CacheMaster
                ↓
         @ArrayOps → @Parser (valida)
                ↓
         @TemplateEngine → @ToolSmith
                ↓
          @SessionKeeper
```

```python
from godot_mcp.knowledge import KnowledgeBase
sage = KnowledgeBase()
guidance = sage.query("create state pattern")

from godot_mcp.core.parser import GDScriptParser
parser = GDScriptParser()
example = parser.parse("res://scripts/states/EnemyState.gd")

from godot_mcp.templates import TemplateEngine
engine = TemplateEngine()
new_state = engine.render("state_base.gd.j2", {"state_name": "Attack", "transitions": ["Idle", "Chase"]})

from godot_mcp.core.cache import CacheManager
cache = CacheManager()
cache.set("states:Attack", new_state)
```

---

## 🆕 Nuevas Herramientas MCP (v4.1.0)

### Escenas Heredadas
```python
create_scene(project_path="D:/MyGame", scene_path="scenes/PlayerExtended.tscn", inherits="res://scenes/BasePlayer.tscn")
# Genera: [gd_scene load_steps=2 format=3 inherits="res://scenes/BasePlayer.tscn"] sin nodo root.
```

### Instanciación con Editable Children
```python
instantiate_scene(scene_path="res://scenes/Enemy.tscn", parent_scene_path="res://scenes/Level.tscn", node_name="Enemy1", editable_children=True)
# Genera [editable path="Enemy1"]
```

### Gestión de Grupos
```python
add_node_groups(scene_path="res://scenes/Player.tscn", node_path="Player", groups=["player", "damageable"])
remove_node_groups(scene_path="res://scenes/Player.tscn", node_path="Player", groups=["damageable"])
```

### Señales
```python
connect_signal(scene_path="res://scenes/Player.tscn", from_node="Player/Area2D", signal="body_entered", to_node="Player", method="_on_area_body_entered")
list_signals(scene_path="res://scenes/Player.tscn")
disconnect_signal(scene_path="res://scenes/Player.tscn", from_node="Player/Area2D", signal="body_entered", to_node="Player", method="_on_area_body_entered")
```

### Eliminación de Recursos
```python
remove_ext_resource(scene_path="res://scenes/Player.tscn", resource_id="5")
remove_sub_resource(scene_path="res://scenes/Player.tscn", resource_id="GradientTexture2D_abc123")
```

### Editable Paths
```python
set_editable_paths(scene_path="res://scenes/Level.tscn", paths=["Kitchen", "Kitchen/Door", "Kitchen/Entities/Table"])
```

### Atributos de Nodo Adicionales
`add_node` e `instantiate_scene` soportan:
- `unique_name_in_owner=True` → Referenciable con `%Name` en GDScript
- `owner="NodePath"` → Sistema de ownership de Godot

```python
add_node(scene_path="res://scenes/Player.tscn", parent_path=".", node_type="Area2D", node_name="Hitbox", unique_name_in_owner=True)
```

---

## 📖 Glosario

| Término | Definición |
|---------|------------|
| TSCN | Formato de escena Godot |
| .gd | Script GDScript |
| .tres | Formato de recursos Godot |
| LRU | Least Recently Used - estrategia de cache |
| TTL | Time-To-Live - tiempo de expiración |
| FastMCP | Framework para servidores MCP |
| Jinja2 | Motor de templates Python |

---

## 🔗 Referencias

- [Godot Engine Documentation](https://docs.godotengine.org/)
- [FastMCP Library](https://github.com/jlowin/fastmcp)
- [GDScript Language Reference](https://docs.godotengine.org/en/stable/tutorials/scripting/gdscript/)

*Última actualización: 2026-04-26 · Versión: 1.1*