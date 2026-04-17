# 🏗️ Arquitectura de Ultra Godot MCP

## Resumen

Ultra Godot MCP usa una arquitectura basada en **sesiones** que proporciona workspace en memoria, lazy loading y dirty tracking para operaciones eficientes sobre archivos `.tscn`.

---

## Componentes Principales

```
┌─────────────────────────────────────────────────────────┐
│                    CLIENT (AI/LLM)                       │
└──────────────────────────┬──────────────────────────────┘
                           │ JSON-RPC (MCP)
                           ▼
┌─────────────────────────────────────────────────────────┐
│                  GODOT MCP SERVER                        │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐ │
│  │  Session     │  │  TSCN        │  │  Validator    │ │
│  │  Manager     │  │  Parser      │  │  (Poka-Yoke)  │ │
│  └──────────────┘  └──────────────┘  └───────────────┘ │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐ │
│  │  Node Tools  │  │  Property    │  │  Resource     │ │
│  │              │  │  Tools       │  │  Tools        │ │
│  └──────────────┘  └──────────────┘  └───────────────┘ │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐                    │
│  │  Signal &    │  │  Project     │                    │
│  │  Script      │  │  Tools       │                    │
│  └──────────────┘  └──────────────┘                    │
└──────────────────────────┬──────────────────────────────┘
                           │ Lectura/Escritura directa
                           ▼
┌─────────────────────────────────────────────────────────┐
│              SISTEMA DE ARCHIVOS (.tscn, .tres, .gd)     │
└─────────────────────────────────────────────────────────┘
```

---

## 1. SessionManager

Gestiona sesiones con workspace en memoria.

### Campos de Session

```python
@dataclass
class Session:
    id: str                          # ID único
    project_path: str                # Ruta al proyecto
    created_at: float                # Timestamp
    loaded_scenes: Dict[str, Scene]  # Escenas parseadas en memoria
    dirty_scenes: set                # Escenas con cambios sin guardar
    operations: list                 # Historial de operaciones
```

### Métodos principales

| Método | Descripción |
|--------|-------------|
| `start_session(project_path)` | Crea nueva sesión |
| `end_session(session_id, save)` | Cierra sesión |
| `load_scene_into_session(session_id, scene_path)` | Carga escena en memoria |
| `get_loaded_scene(session_id, scene_path)` | Obtiene escena cacheada |
| `mark_scene_dirty(session_id, scene_path)` | Marca escena como modificada |
| `commit_scene(session_id, scene_path)` | Guarda escena a disco |

### Decorador `@require_session`

Todas las tools que modifican archivos usan este decorador:

```python
@require_session
def add_node(session_id: str, scene_path: str, ...) -> dict:
    # session_id ya validado
    ...
```

---

## 2. TSCN Parser

Parser nativo de archivos `.tscn` sin necesidad de Godot Editor.

### Clases principales

| Clase | Descripción |
|-------|-------------|
| `Scene` | Escena completa (header, recursos, nodos, conexiones) |
| `SceneNode` | Nodo individual con propiedades |
| `ExtResource` | Referencia a archivo externo |
| `SubResource` | Recurso embebido en la escena |
| `Connection` | Conexión de señal entre nodos |

### SceneNode - Campo `instance`

Los nodos que instancian escenas usan el campo `instance` en lugar de una propiedad:

```python
@dataclass
class SceneNode:
    name: str = ""
    type: str = ""           # Vacío para nodos instanciados
    parent: str = "."
    unique_name_in_owner: bool = False
    instance: str = ""       # ExtResource ID para instanciación
    properties: dict = field(default_factory=dict)
```

Esto genera el formato nativo de Godot:
```
[node name="Enemy" parent="." instance=ExtResource("1")]
```

En lugar del formato incorrecto:
```
[node name="Enemy" type="PackedScene" parent="."]
scene_file_path = ExtResource("1")
```

### Scene - Método `deduplicate_ext_resources()`

Elimina ExtResources duplicados y remapea referencias automáticamente:

```python
scene.deduplicate_ext_resources(project_path="/ruta/proyecto")
# Returns: {"removed": 1, "remapped": 1, "kept": 4,
#           "resolved_paths": 4, "fuzzy_matched": 1}
```

**Estrategias de detección:**
1. **Filesystem resolution**: Resuelve `res://` a path real en disco
2. **Fuzzy match**: Detecta recursos con mismo filename + tipo
3. **Path normalization**: Colapsa `..`, `.`, `//`

**Remapeo recursivo:** Actualiza referencias en:
- Propiedades de nodos (dict, Array, Dictionary anidados)
- Propiedades de sub-recursos
- Strings raw (ej: `'ExtResource("1")'`)

### Serialización

`Scene.to_tscn()` convierte la estructura de vuelta a formato TSCN:
- El nodo raíz **no** lleva atributo `parent`
- Los nodos instanciados usan `instance=ExtResource("id")` en el header (sin `type`)
- Los recursos se serializan como `ExtResource("id")` o `SubResource("id")`
- Los tipos tipados (Vector2, Color, etc.) se formatean correctamente
- `scene_file_path` se omite como propiedad cuando `instance` está presente

---

## 3. Validator (Poka-Yoke)

Validación automática que previene errores **antes** de escribir archivos.

### Reglas de validación

| Regla | Nivel | Descripción |
|-------|-------|-------------|
| `root_no_parent` | ERROR | El nodo raíz no puede tener `parent` |
| `unique_extresource_ids` | ERROR | IDs de ExtResource deben ser únicos |
| `unique_subresource_ids` | ERROR | IDs de SubResource deben ser únicos |
| `valid_resource_refs` | ERROR | Las referencias a recursos deben existir |
| `has_root_node` | ERROR | La escena debe tener al menos un nodo |
| `non_empty_node_names` | WARNING | Los nodos deben tener nombre |
| `valid_parent_paths` | WARNING | Las rutas de padre deben ser válidas |
| `ext_resource_files_exist` | ERROR | Los archivos de ExtResource deben existir |

---

## 3.1. GDScript Validator (v2.0)

Validación inteligente de scripts GDScript usando una arquitectura de **3 capas**.

### Arquitectura de 3 Capas

```
┌─────────────────────────────────────────────────────────────┐
│                    VALIDACIÓN EN 3 CAPAS                    │
├─────────────────────────────────────────────────────────────┤
│  CAPA 1: Godot Real (Sintaxis + Errores Reales)            │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ godot_check_script_syntax()                           │  │
│  │ → Parser completo de Godot                           │  │
│  │ → Errores reales de compilación                      │  │
│  │ → Habilitado con project_path                        │  │
│  └───────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│  CAPA 2: API de Godot 4.6 (Métodos/Propiedades)          │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ godot_api_4.6.json                                   │  │
│  │ → Detectar métodos inexistentes en tipos específicos  │  │
│  │ → Verificar decoradores deprecated                    │  │
│  │ → Detectar métodos/propiedades removidos en Godot 4   │  │
│  └───────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│  CAPA 3: Análisis de Patrones (Patterns Comunes)           │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ gdscript_validator.py                                 │  │
│  │ → @export sin tipo hint (info)                       │  │
│  │ → Decoradores deprecated (@onready)                   │  │
│  │ → Funciones removidas (yield, test_move)              │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Archivos del módulo

```
src/godot_mcp/core/
├── api/
│   ├── __init__.py              # GodotAPI + NodeAPI classes
│   ├── godot_api_4.6.json        # API de Godot 4.6.1 (GDScript)
│   └── godot_nodes_4.6.json      # Tipos de nodos TSCN
└── gdscript_validator.py        # Validador inteligente GDScript
```

### Lo que SÍ detecta

| Tipo | Ejemplo | Severidad |
|------|---------|-----------|
| Decoradores deprecated | `@onready` | WARNING |
| Métodos removidos | `test_move()`, `yield()` | ERROR |
| Funciones removidas | `OS.get_screen_size()` | ERROR |
| Métodos inexistentes en tipo | `CharacterBody2D.overlaps_body()` | WARNING |

### Lo que NO detecta (y por qué)

| Tipo | Razón |
|------|-------|
| Variables no declaradas | **Imposible** - GDScript es dinámico |
| Llamadas a funciones en objetos desconocidos | Podría ser cualquier tipo |

### Decisión de diseño: Variables no declaradas

El validador **NO intenta** detectar "variables no declaradas" porque:

1. **GDScript es dinámico**: Una variable puede venir de:
   - `@export` de otra clase
   - `get_node()` o `instantiate()`
   - Señales o callbacks
   - Herencia o mixins

2. **Análisis estático es imposible**: Sin ejecutar el código o parsear toda la escena, es imposible saber qué variables existirán en tiempo de ejecución.

3. **Falsos positivos son dañinos**: Intentar adivinar causa más ruido que utilidad.

Para detectar errores reales de sintaxis, usa `validate_gdscript(script_path, project_path=...)` que invoca a Godot.

### API de Godot 4.6

El archivo `godot_api_4.6.json` contiene:

- **Tipos de nodos**: `CharacterBody2D`, `Area2D`, `Sprite2D`, etc.
- **Tipos integrados**: `Vector2`, `String`, `Array`, etc.
- **Singletons**: `Input`, `Engine`, `Time`, etc.
- **Funciones globales**: `abs()`, `clamp()`, `print()`, etc.
- **Decoradores**: `@export`, `@onready`, `@tool`, etc.
- **Métodos virtuales**: `_ready()`, `_process()`, etc.
- **Removidos en Godot 4**: `yield`, `test_move`, `OS.get_screen_size()`

### Actualización de la API

Para actualizar a una nueva versión de Godot:

1. Descargar la documentación de la nueva versión
2. Regenerar `godot_api_4.6.json` con el nuevo contenido
3. Actualizar el número de versión en el JSON

---

## 3.2. NodeAPI (TSCN Validator v2.0)

Validación inteligente de tipos de nodos en archivos `.tscn` usando datos externos.

### Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                    TSCN VALIDATOR                            │
├─────────────────────────────────────────────────────────────┤
│  TSCNValidator                                               │
│  ├── Usa NodeAPI para validación inteligente                │
│  ├── VALID_NODE_TYPES hardcodeado ELIMINADO                 │
│  └── Reglas de validación basadas en NodeAPI               │
├─────────────────────────────────────────────────────────────┤
│  NodeAPI (Singleton)                                        │
│  ├── Carga godot_nodes_4.6.json                            │
│  ├── Fallback con lista mínima si JSON no existe           │
│  └── Búsqueda O(1) con set de tipos válidos                │
├─────────────────────────────────────────────────────────────┤
│  godot_nodes_4.6.json                                       │
│  ├── 200+ tipos de nodos válidos por categoría             │
│  ├── Tipos REMOVIDOS en Godot 4 (KinematicBody → Character)│
│  ├── Tipos DEPRECADOS (AnimatorPlayer)                     │
│  └── Recursos que NO son nodos (RectangleShape2D, etc.)     │
└─────────────────────────────────────────────────────────────┘
```

### Nuevas reglas de validación TSCN

| Regla | Nivel | Descripción |
|-------|-------|-------------|
| `valid_node_types` | WARNING | Tipo de nodo no es conocido (puede ser class_name) |
| `removed_node_types` | ERROR | Tipo fue **removido** en Godot 4 |
| `resource_not_node` | ERROR | Recurso usado incorrectamente como tipo de nodo |

### Detección de tipos removidos

| Godot 3 (Removido) | Godot 4 (Correcto) |
|--------------------|--------------------|
| `KinematicBody2D` | `CharacterBody2D` |
| `KinematicBody3D` | `CharacterBody3D` |

### Detección de recursos vs nodos

| Recurso (NO es nodo) | Uso correcto |
|---------------------|-------------|
| `RectangleShape2D` | Hijo de `CollisionShape2D` |
| `NavigationMesh` | Recurso de `NavigationRegion3D` |
| `FogMaterial` | Recurso de `FogVolume` |

### API de NodeAPI

```python
from godot_mcp.core.api import NodeAPI, get_node_api

api = get_node_api()

# Validar tipo de nodo
api.is_valid_node_type("CharacterBody2D")  # True

# Detectar tipos removidos
api.is_removed_node("KinematicBody2D")  # (True, "Use 'CharacterBody2D' instead")

# Detectar recursos incorrectos
api.is_resource_not_node("NavigationMesh")  # True

# Validación completa
api.validate_type("Sprite2D")
# {'is_valid': True, 'issues': [], 'suggestions': []}

api.validate_type("KinematicBody2D")
# {'is_valid': False, 'issues': ["'KinematicBody2D' was removed..."], 
#  'suggestions': ["Replace with: CharacterBody2D"]}
```

---

## 4. Property Tools (Inspector Unificado)

`set_node_properties` es la herramienta central para manipular propiedades.

### Flujo de procesamiento

```
properties dict
       │
       ▼
┌─────────────────────────┐
│ _validate_properties()  │ ← Valida contra NODE_PROPERTY_SCHEMAS
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│ _process_property_value │ ← Convierte valores a formato TSCN
│                         │
│ • "res://..." → ExtResource
│ • {"size": ...} → SubResource
│ • {"type": "SubResource", "ref": "id"} → SubResource("id")
│ • {"type": "Vector2", ...} → Vector2(x, y)
│ • "Hello" → string directo
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│ node.properties.update()│ ← Aplica propiedades al nodo
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│ _update_scene_file()    │ ← Serializa y escribe a disco
└─────────────────────────┘
```

### NODE_PROPERTY_SCHEMAS

Diccionario que mapea tipos de nodo → propiedades válidas:

```python
NODE_PROPERTY_SCHEMAS = {
    "Sprite2D": {
        "texture": {"type": "ext_resource", "resource_type": "Texture2D"},
        "position": {"type": "Vector2"},
        "flip_h": {"type": "bool"},
        ...
    },
    "CollisionShape2D": {
        "shape": {"type": "sub_resource", "resource_type": "Shape2D"},
        "disabled": {"type": "bool"},
        ...
    },
    ...
}
```

Cubre **150+ tipos de nodo** incluyendo física, rendering, UI, audio, animación, etc.

---

## 6. Estructura de Archivos

```
godot-mcp-python/
├── src/godot_mcp/
│   ├── server.py                    # Entry point del servidor
│   ├── session_manager.py           # SessionManager
│   ├── core/
│   │   ├── api/
│   │   │   ├── __init__.py         # GodotAPI + NodeAPI classes
│   │   │   ├── godot_api_4.6.json  # API de Godot 4.6.1 (GDScript)
│   │   │   └── godot_nodes_4.6.json # Tipos de nodos 4.6.1 (TSCN)
│   │   ├── tscn_parser.py           # Parser y serializador TSCN
│   │   ├── tscn_validator.py        # Validador Poka-Yoke (v2.0)
│   │   └── gdscript_validator.py    # Validador inteligente GDScript (v2.0)
│   └── tools/
│       ├── session_tools.py         # start_session, end_session
│       ├── scene_tools.py           # create_scene, get_scene_tree
│       ├── node_tools.py            # add_node, update_node, find_nodes
│       ├── property_tools.py        # set_node_properties (inspector)
│       ├── resource_tools.py        # create_resource, add_ext_resource
│       ├── signal_and_script_tools.py # connect_signal, set_script
│       ├── project_tools.py         # get_project_info, find_scripts
│       ├── debug_tools.py           # check_script_syntax, run_debug_scene
│       └── validation_tools.py      # validate_tscn, validate_gdscript
├── tests/
│   ├── test_parser.py
│   ├── test_property_tools.py
│   ├── test_signal_and_script_tools.py
│   ├── test_tscn_validator.py       # Tests del TSCN validator + NodeAPI
│   ├── test_new_features.py         # Tests del GDScript validator
│   └── ...
└── docs/
    ├── TOOLS.md                     # Referencia de herramientas
    ├── ARCHITECTURE.md              # Este documento
    └── COMMON_ERRORS.md             # Errores comunes
```

---

## 6. Flujo de Trabajo Típico

```
1. start_session(project_path)
   └─→ session_id

2. create_scene(session_id, "Player.tscn", root_type="CharacterBody2D")
   └─→ Escena creada con nodo raíz

3. add_node(session_id, "Player.tscn", parent_path=".",
            node_type="Sprite2D", node_name="Sprite")
   └─→ Nodo añadido

4. set_node_properties(session_id, "Player.tscn",
    node_path="Sprite",
    properties={
        "texture": "res://sprites/player.png",
        "position": {"type": "Vector2", "x": 0, "y": -20},
    })
   └─→ ExtResource creado, propiedades aplicadas

5. add_node(session_id, "Player.tscn", parent_path=".",
            node_type="CollisionShape2D", node_name="Collision")

6. set_node_properties(session_id, "Player.tscn",
    node_path="Collision",
    properties={"shape": {"radius": 16.0}})
   └─→ SubResource CircleShape2D creado

7. set_script(session_id, "Player.tscn",
             node_path="Player", script_path="res://scripts/player.gd")
   └─→ Script adjuntado

8. connect_signal(session_id, "Player.tscn",
                  from_node="Player/Area2D", signal="body_entered",
                  to_node="Player", method="_on_body_entered")
   └─→ Conexión de señal creada

9. end_session(session_id, save=True)
   └─→ Sesión cerrada, cambios guardados
```

---

*Documento de arquitectura v2.2*
*Fecha: 2026-04-17*

### Changelog v2.1
- `SceneNode` ahora tiene campo `instance` para instanciación nativa de Godot
- `instantiate_scene` genera formato `instance=ExtResource("id")` en header
- `Scene.deduplicate_ext_resources()` elimina duplicados y remapea referencias
- Parser lee y serializa `instance=` del header de nodos
- Parser preserva canal alpha en `Color(r, g, b, a)`

### Changelog v2.2 (TSCN Validator + NodeAPI)
- `TSCNValidator` ahora usa `NodeAPI` para validación inteligente de tipos de nodos
- `VALID_NODE_TYPES` hardcodeado eliminado (~260 líneas)
- Detección de tipos **removidos** en Godot 4 (KinematicBody2D/3D → CharacterBody2D/3D)
- Detección de **recursos usados incorrectamente** como tipos de nodos (NavigationMesh, RectangleShape2D, etc.)
- Tipos personalizados (`class_name`) permitidos sin errores
- `godot_nodes_4.6.json` contiene lista completa de tipos válidos
- Fallback con lista mínima si JSON no está disponible
