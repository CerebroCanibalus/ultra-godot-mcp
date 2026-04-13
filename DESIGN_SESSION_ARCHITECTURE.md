# 🎮Diseño: Arquitectura de Sesiones para MCP Godot Python

## Resumen Ejecutivo

Este documento especifica la nueva arquitectura de sesiones que integra el `SessionManager` existente con las tools MCP, permitiendo workspace en memoria, lazy loading, y dirty tracking.

---

## 1. Nuevas Tools de Sesión

### Ubicación: `src/godot_mcp/tools/session_tools.py`

| Tool | Firma | Descripción |
|------|-------|-------------|
| `start_session` | `start_session(project_path: str) -> dict` | Crea nueva sesión para proyecto |
| `end_session` | `end_session(session_id: str, save: bool = True) -> dict` | Cierra sesión, opcionalmente guarda |
| `get_active_session` | `get_active_session() -> dict` | Obtiene sesión activa |
| `list_sessions` | `list_sessions() -> dict` | Lista todas las sesiones |
| `get_session_info` | `get_session_info(session_id: str) -> dict` | Info detallada de sesión |
| `commit_session` | `commit_session(session_id: str, scene_path: str = None) -> dict` | Guarda escena(s) a disco |
| `discard_changes` | `discard_changes(session_id: str, scene_path: str = None) -> dict` | Descarta cambios sin guardar |

### Ejemplo de Uso

```python
# 1. Iniciar sesión
result = start_session(project_path="D:/Mis Juegos/MyProject")
session_id = result["session_id"]

# 2. Todas las operaciones usan session_id
scene = create_scene(session_id, scene_path="res://Player.tscn", ...)
add_node(session_id, scene_path="res://Player.tscn", ...)
update_node(session_id, scene_path="res://Player.tscn", node_path="Sprite2D", ...)

# 3. Guardar cambios
commit_session(session_id)

# 4. Cerrar sesión
end_session(session_id, save=True)
```

---

## 2. Modificaciones al SessionManager

### Nuevos Métodos

```python
class SessionManager:
    # ... métodos existentes ...
    
    # === Workspace (In-Memory Scene Cache) ===
    
    def load_scene_into_session(
        self, 
        session_id: str, 
        scene_path: str,
        parser_func = None  # Callable opcional
    ) -> Optional["Scene"]:
        """Carga escena en workspace de la sesión."""
    
    def get_loaded_scene(
        self, 
        session_id: str, 
        scene_path: str
    ) -> Optional["Scene"]:
        """Obtiene escena ya cargada (sin re-parse)."""
    
    def mark_scene_dirty(self, session_id: str, scene_path: str) -> bool:
        """Marca escena como modificada."""
    
    def is_scene_dirty(self, session_id: str, scene_path: str) -> bool:
        """Verifica si tiene cambios sin guardar."""
    
    def get_dirty_scenes(self, session_id: str) -> List[str]:
        """Lista escenas modificadas."""
    
    def commit_scene(
        self, 
        session_id: str, 
        scene_path: str,
        writer_func = None
    ) -> bool:
        """Guarda escena dirty a disco."""
    
    def unload_scene(self, session_id: str, scene_path: str) -> bool:
        """Descarga escena del workspace."""
    
    def unload_all_scenes(self, session_id: str) -> bool:
        """Descarga todas las escenas."""
    
    # === File Locks (Concurrency) ===
    
    def _get_file_lock(self, file_path: str) -> threading.Lock:
        """Obtiene lock para archivo específico."""
```

### Nuevos Campos en Session

```python
@dataclass
class Session:
    # ... campos existentes ...
    
    # Nuevos campos para workspace
    loaded_scenes: Dict[str, "Scene"]  # Escenas parseadas en memoria
    dirty_scenes: set  # Escenas modificadas pendientes
```

---

## 3. Decorador `@require_session`

### Ubicación: `src/godot_mcp/tools/session_tools.py`

### Implementación

```python
def require_session(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorador que valida session_id antes de ejecutar la tool.
    
    El decorador:
    1. Valida que session_id no esté vacío
    2. Verifica que la sesión existe
    3. Pasa la validación antes de llamar la función
    
    Returns:
        dict con error si validación falla
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Extraer session_id
        session_id = kwargs.get('session_id') or (args[0] if args else None)
        
        if not session_id:
            return {
                "success": False,
                "error": "session_id es requerido como primer parámetro"
            }
        
        # Validar sesión existe
        manager = get_session_manager()
        session = manager.get_session(session_id)
        
        if session is None:
            return {
                "success": False,
                "error": f"Session no encontrada. Usa start_session() primero."
            }
        
        return func(*args, **kwargs)
    
    return wrapper
```

### Uso

```python
@require_session
def create_scene(session_id: str, scene_path: str, ...) -> dict:
    # session_id ya validado, sesión disponible
    manager = get_session_manager()
    session = manager.get_session(session_id)
    # ...
    return {"success": True, ...}
```

---

## 4. Firma de Todas las Tools Existentes (CON session_id)

### scene_tools.py

| Función Anterior | Nueva Firma |
|-----------------|-------------|
| `create_scene(project_path, scene_path, ...)` | `create_scene(session_id: str, scene_path: str, root_type: str = "Node2D", root_name: str = "Root") -> dict` |
| `get_scene_tree(scene_path)` | `get_scene_tree(session_id: str, scene_path: str) -> dict` |
| `save_scene(scene_path, scene_data)` | `save_scene(session_id: str, scene_path: str, scene_data: dict) -> dict` |
| `list_scenes(project_path, recursive)` | `list_scenes(session_id: str, recursive: bool = True) -> dict` |
| `instantiate_scene(scene_path, ...)` | `instantiate_scene(session_id: str, scene_path: str, parent_scene_path: str, node_name: str, parent_node_path: str = ".") -> dict` |

### node_tools.py

| Función Anterior | Nueva Firma |
|-----------------|-------------|
| `add_node(scene_path, ...)` | `add_node(session_id: str, scene_path: str, parent_path: str, node_type: str, node_name: str, properties: dict = None) -> dict` |
| `remove_node(scene_path, node_path)` | `remove_node(session_id: str, scene_path: str, node_path: str) -> dict` |
| `update_node(scene_path, node_path, properties)` | `update_node(session_id: str, scene_path: str, node_path: str, properties: dict) -> dict` |
| `get_node_properties(scene_path, node_path)` | `get_node_properties(session_id: str, scene_path: str, node_path: str) -> dict` |
| `rename_node(scene_path, node_path, new_name)` | `rename_node(session_id: str, scene_path: str, node_path: str, new_name: str) -> dict` |
| `move_node(scene_path, node_path, new_parent_path)` | `move_node(session_id: str, scene_path: str, node_path: str, new_parent_path: str) -> dict` |
| `duplicate_node(scene_path, node_path, new_name)` | `duplicate_node(session_id: str, scene_path: str, node_path: str, new_name: str = None) -> dict` |
| `find_nodes(scene_path, name_pattern, type_filter)` | `find_nodes(session_id: str, scene_path: str, name_pattern: str = None, type_filter: str = None) -> dict` |

### resource_tools.py

| Función Anterior | Nueva Firma |
|-----------------|-------------|
| `create_resource(resource_path, ...)` | `create_resource(session_id: str, resource_path: str, resource_type: str, properties: dict = None) -> dict` |
| `read_resource(resource_path)` | `read_resource(session_id: str, resource_path: str) -> dict` |
| `update_resource(resource_path, properties)` | `update_resource(session_id: str, resource_path: str, properties: dict) -> dict` |
| `get_uid(resource_path)` | `get_uid(session_id: str, resource_path: str) -> dict` |
| `update_project_uids(project_path)` | `update_project_uids(session_id: str) -> dict` |
| `list_resources(project_path, ...)` | `list_resources(session_id: str, resource_type: str = None, recursive: bool = True) -> dict` |

### project_tools.py

| Función Anterior | Nueva Firma |
|-----------------|-------------|
| Las project tools **NO** requieren session_id porque operan sobre el proyecto sin modificar archivos de escena |
| `get_project_info(project_path)` | `get_project_info(session_id: str) -> dict` (puede inferir project_path de sesión) |
| `list_projects(directory, recursive)` | `list_projects(session_id: str, directory: str, recursive: bool = True) -> dict` |
| `get_project_structure(project_path)` | `get_project_structure(session_id: str) -> dict` |
| `find_scripts(project_path)` | `find_scripts(session_id: str) -> dict` |
| `find_resources(project_path, type_filter)` | `find_resources(session_id: str, type_filter: str = None) -> dict` |

---

## 5. Ejemplo Completo: create_scene (Modificado)

```python
@require_session
def create_scene(
    session_id: str,
    scene_path: str,
    root_type: str = "Node2D",
    root_name: str = "Root",
) -> dict:
    """
    Creates a new scene .tscn in the project.
    
    Args:
        session_id: Active session ID.
        scene_path: Relative path (e.g., "Player.tscn" or "res://Player.tscn").
        root_type: Type of the root node.
        root_name: Name of the root node.
    """
    # 1. Get session and project path
    manager = get_session_manager()
    session = manager.get_session(session_id)
    
    if session is None:
        return {"success": False, "error": "Session not found"}
    
    project_path = session.project_path
    
    # 2. Normalize path
    if not scene_path.endswith(".tscn"):
        scene_path = scene_path + ".tscn"
    
    full_path = os.path.join(project_path, scene_path)
    
    # 3. Check if exists
    if os.path.isfile(full_path):
        scene = manager.load_scene_into_session(session_id, full_path)
        if scene:
            return {"success": True, "scene_path": scene_path, "loaded": True}
        return {"success": False, "error": "Scene already exists"}
    
    # 4. Create in workspace
    from godot_mcp.core.tscn_parser import Scene, GdSceneHeader, SceneNode
    
    scene = Scene(
        header=GdSceneHeader(load_steps=2, format=3),
        nodes=[SceneNode(name=root_name, type=root_type, parent=".")],
    )
    
    # 5. Save to workspace
    session.loaded_scenes[full_path] = scene
    session.dirty_scenes.add(full_path)
    
    # 6. Commit to disk
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(scene.to_tscn())
    
    session.dirty_scenes.discard(full_path)
    
    # 7. Track operation
    manager.record_operation(
        session_id, "create", full_path, f"Created {root_type}"
    )
    
    return {"success": True, "scene_path": scene_path}
```

---

## 6. Flujo de Trabajo Completo

```
┌─────────────────────────────────────────────────────────────────────┐
│                    FLUJO DE SESIÓN                           │
├───────────────────────────────────────────���─���───────────────────────┤
│                                                             │
│  1. start_session(project_path)                             │
│     ├─ Valida proyecto                                      │
│     ├─ Crea Session en SessionManager                       │
│     └─ Retorna session_id                                    │
│                                                             │
│  2. [OPERACIONES CON session_id]                              │
│     ├─ create_scene(session_id, ...)                       │
│     ├─ add_node(session_id, scene_path, ...)               │
│     ├─ update_node(session_id, scene_path, ...)            │
│     │                                                         │
│     │  [EN WORKSPACE]                                        │
│     │  - Scene parseada en memoria (loaded_scenes)          │
│     │  - Modifications tracked (dirty_scenes)              │
│     │  - Cache en memoria (get_loaded_scene)               │
│     │                                                         │
│     └─ (Sin re-parsear para reads repetidos)                │
│                                                             │
│  3. [OPCIONAL] commit_session(session_id)                  │
│     ├─ Guarda todas las dirty scenes a disco             │
│     └─ Limpia dirty flags                                  │
│                                                             │
│  4. end_session(session_id, save=True)                     │
│     ├─ (Opcional) auto-commit dirty                        │
│     ├─ Unload all scenes from workspace                      │
│     └─ Close session                                       │
│                                                             │
└───────────────────────────────────────────────────────���─────────────┘
```

---

## 7. Beneficios de la Arquitectura

| Beneficio | Descripción |
|-----------|------------|
| **Lazy Loading** | Las escenas solo se parsean cuando se necesitan |
| **Dirty Tracking** | Se sabe exactamente qué archivos tienen cambios |
| **Memory Efficiency** | Evita re-parsear la misma escena múltiples veces |
| **Concurrency** | Locks por archivo para operaciones paralelas |
| **Undo/Redo** | Operación history ya integrada |
| **Error Recovery** | No se pierden cambios no guardados |

---

## 8. Migración Paso a Paso

### Fase 1: Actualizar SessionManager
- [x] Agregar campos `loaded_scenes`, `dirty_scenes`
- [x] Agregar métodos workspace
- [x] Agregar `_file_locks`
- [x] Actualizar `to_dict`/`from_dict`

### Fase 2: Implementar Tools de Sesión
- [x] tools en `session_tools.py`
- [x] Decorador `@require_session`
- [x] `SessionContext` helper

### Fase 3: Migrar scene_tools.py
- [ ] Cambiar firmas de funciones
- [ ] Agregar `@require_session`
- [ ] Usar workspace en lugar de cache global

### Fase 4: Migrar node_tools.py
- [ ] Cambiar firmas con session_id
- [ ] Usar `load_scene_into_session`

### Fase 5: Migrar resource_tools.py
- [ ] Similar a node_tools

### Fase 6: Testing
- [ ] Tests de integración
- [ ] Validar concurrencia
- [ ] Validar dirty tracking

---

## 9. Notas de Implementación

### Error Handling
```python
# Todas las funciones retornan dict con estructura:
{
    "success": bool,
    "error": str,  # Solo si success=False
    ...  # altri campi specifici
}
```

### Thread Safety
- SessionManager usa `threading.RLock()` para operaciones internas
- `_file_locks` permite operaciones paralelas en diferentes archivos

### Path Handling
- **session_id** siempre primer parámetro
- **scene_path** puede ser absoluto o relativo al proyecto
- El proyecto se infiere de la sesión

---

*Documento de diseño v1.0*
*Fecha: 2026-04-13*