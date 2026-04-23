# Changelog

Todos los cambios notables en este proyecto se documentan en este archivo.

El formato se basa en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/).

---

## [4.3.0] - 2026-04-23 - Resource Builder

### Añadido - Capa 7: Resource Builder (9 tools)
- **`tools/resource_builder_tools.py`** - Sistema genérico de construcción de SubResources complejos
- **Capa 1 (Genéricos):** `build_resource` (cualquier SubResource), `build_nested_resource` (jerarquías con referencias cruzadas)
- **Capa 3 (High-level):** `create_animation` (Animation con tracks), `create_state_machine` (AnimationNodeStateMachine con transiciones en tripletes)
- **Capa 4 (AnimationTree):** `create_blend_space_1d`, `create_blend_space_2d`, `create_blend_tree`
- **Capa 5 (Assets):** `create_sprite_frames` (animaciones frame-by-frame), `create_tile_set` (atlas + colisiones)
- Parser de `StringName` (`&"nombre"`) en `tscn_parser.py`
- Soporte `Vector2i`, `Vector3i`, `Rect2i` en parser y formatter
- Serialización correcta de dicts genéricos como GDScript dictionaries

### Añadido - Capa 6: Array Operations (2 tools)
- **`tools/array_tools.py`** - Operaciones quirúrgicas sobre arrays sin reescribir escenas
- `scene_array_operation` (append, remove, replace, insert, clear)
- `preview_array_operation` (previsualizar cambios antes de aplicar)

### Corregido
- **StateMachine transitions**: Formato real de Godot usa tripletes `[from, to, SubResource(transition)]`, no pares `[from, to]`. Corregido para coincidir con escenas reales (verificado contra Jellyboom.tscn)
- **`validate_project` tuple bug**: 5 archivos (`runtime_tools.py`, `movie_tools.py`, `screenshot_tools.py`, `import_tools.py`, `export_tools.py`) trataban el retorno como dict en vez de tuple. Corregido
- **`create_blend_tree` typo**: `conns` → `connections`
- **`array_properties` en flattener**: Propiedades como `transitions` ahora se serializan como arrays planos, no como claves indexadas

### Mejorado
- **98 herramientas totales** (87 anteriores + 11 nuevas)
- **22 módulos registrados** en server.py
- Validación de formato TSCN contra escenas reales del proyecto Devil's Kitchen
- Zero modificaciones al juego durante validaciones (solo lectura)

---

## [4.0.0] - 2026-04-22 - Plus Ultra

### Añadido - Godot CLI Bridge (16 tools)
- **`godot_cli/base.py`** - `GodotCLIWrapper` unificado para operaciones CLI
- **`export_tools.py`** (4 tools): `export_project`, `list_export_presets`, `validate_export_preset`, `get_export_log`
- **`runtime_tools.py`** (6 tools): `run_gdscript`, `get_scene_info_runtime`, `get_performance_metrics`, `test_scene_load`, `get_classdb_info`, `call_group_runtime`
- **`import_tools.py`** (2 tools): `reimport_assets`, `get_import_settings`
- **`screenshot_tools.py`** (2 tools): `capture_scene_frame`, `capture_scene_sequence`
- **`movie_tools.py`** (2 tools): `write_movie`, `write_movie_with_script`

### Añadido - LSP/DAP Native (10 tools)
- **`lsp_dap/client.py`** - Cliente JSON-RPC para LSP/DAP con auto-reconexión
- **`lsp_tools.py`** (4 tools): `lsp_get_completions`, `lsp_get_hover`, `lsp_get_symbols`, `lsp_get_diagnostics`
- **`dap_tools.py`** (6 tools): `dap_start_debugging`, `dap_set_breakpoint`, `dap_continue`, `dap_step_over`, `dap_step_into`, `dap_get_stack_trace`

### Añadido - Project Intelligence (7 tools)
- **`intelligence/dependency_tools.py`** (2 tools): `get_dependency_graph`, `find_unused_assets`
- **`intelligence/signal_graph_tools.py`** (2 tools): `get_signal_graph`, `find_orphan_signals`
- **`intelligence/code_analysis_tools.py`** (3 tools): `analyze_script`, `find_code_smells`, `get_project_metrics`

### Añadido - Sesiones con Godot Headless
- `Session.godot_process` - Proceso headless persistente por sesión
- `SessionManager.start_godot_headless()` - Inicia Godot en background
- `SessionManager.stop_godot_headless()` - Detiene proceso Godot
- `SessionManager.execute_gdscript_quick()` - Ejecuta scripts 10x más rápido
- Godot headless se mata automáticamente al cerrar sesión

### Añadido - Registro dinámico de módulos
- `server.py` con `REGISTERED_MODULES` - lista de 19 módulos
- Import dinámico con graceful degradation (módulos opcionales no fallan)
- Fácil extensión: añadir tupla a la lista

### Mejorado
- **Zero addon** - Ninguna tool requiere instalar addon en proyecto Godot
- **Zero WebSocket** - Sin conflictos de puerto, sin crasheos de conexión
- **81 herramientas totales** (42 core + 16 CLI + 10 LSP/DAP + 7 intelligence + 6 misc)
- Auto-detección de ejecutable Godot (prioriza `_console.exe` en Windows)
- `pyproject.toml` actualizado a versión 4.0.0

---

## [3.1.0] - 2026-04-14

### Añadido
- **Búsqueda fuzzy** de nodos con `fuzzywuzzy` (tolerancia a typos)
- **Templates de nodos** (`node_templates.py`) para generación rápida de estructuras comunes
- **Templates de scripts** (`script_templates.py`) para boilerplate GDScript
- **Tests E2E** (`tests/e2e/`) con flujos completos de usuario
- **Tests de servidor** (`test_server.py`) - verificación de registro de 40 herramientas
- **Tests de templates** (`test_templates.py`) - 35 tests de validación
- **Tests de búsqueda fuzzy** (`test_fuzzy_search.py`) - 11 tests
- **Documentación de tests** (`docs/TESTS.md`) con métricas de cobertura
- Herramienta `debug_tools` para depuración de sesiones

### Mejorado
- **Inspector unificado** (`set_node_properties`) ahora maneja TODOS los tipos de propiedades
- Validación automática de archivos TSCN antes de escribir (Poka-Yoke)
- Sesiones con dirty tracking y lazy loading optimizado
- Manejo de recursos externos (ExtResource) con deduplicación automática

### Corregido
- Formato de retorno de `list_scenes` (ahora `list[dict]` con `path` y `name`)
- Excepciones en `script_templates.py` (`KeyError` para templates inexistentes)
- Validación de headers en archivos TSCN

---

## [3.0.0] - 2026-04-10

### Añadido
- **Inspector unificado** (`set_node_properties`) - configura CUALQUIER propiedad del inspector
- **Validación automática** de TSCN, GDScript y proyectos completos
- **Gestión de UIDs** (Godot 4.4+)
- **Conexión de señales** entre nodos
- **Adjuntar scripts** a nodos en un paso (`set_script`)
- **SubResources** embebidos en escenas
- **Índice de proyectos** con detección automática

### Mejorado
- Parser TSCN reescrito con soporte completo para todas las secciones
- Sesiones ligeras con workspace en memoria
- Cache LRU para operaciones repetitivas
- Documentación expandida (`TOOLS.md`, `ARCHITECTURE.md`, `COMMON_ERRORS.md`)

---

## [2.0.0] - 2026-04-05

### Añadido
- **Parsing nativo de TSCN** sin necesidad de Godot headless
- **20+ herramientas MCP** para gestión de escenas, nodos y recursos
- **Sesiones** con estado persistente en memoria
- **Gestión de proyectos** Godot (crear, explorar, validar)
- **Templates Jinja2** para generación de código
- **Cache** para optimización de consultas

### Cambiado
- Migración de Node.js a Python con FastMCP
- Arquitectura modular con `core/`, `tools/`, `templates/`

---

## [1.0.0] - 2026-03-28

### Añadido
- Primera versión del MCP Server en Node.js
- Soporte básico para escenas y nodos
- Parser TSCN inicial
