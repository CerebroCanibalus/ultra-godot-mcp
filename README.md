# 🏴 Ultra Godot MCP

[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Godot 4.6+](https://img.shields.io/badge/Godot-4.6+-478cbf?logo=godotengine&logoColor=white)](https://godotengine.org/)
[![Tests](https://img.shields.io/badge/Tests-484%20passing-2ea44f)](docs/TESTS.md)
[![Version](https://img.shields.io/badge/Version-3.1.0-6f42c1)](CHANGELOG.md)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Ultra Godot MCP** — *Plus Ultra*: ir más allá. El servidor MCP más rápido y completo para Godot Engine.
Permite a IAs y asistentes controlar proyectos Godot directamente: crear escenas, manipular nodos, gestionar recursos y validar código, **todo sin abrir el editor**.

---

## ✨ Características

| Característica | Descripción |
|---|---|
| 🔍 **Parsing nativo TSCN** | Lee y escribe archivos `.tscn` directamente, sin Godot headless |
| 🛠️ **38 herramientas MCP** | Escenas, nodos, recursos, scripts, señales, validación y más |
| 🎯 **Inspector unificado** | `set_node_properties` maneja TODOS los tipos de propiedades automáticamente |
| 🔄 **Sesiones en memoria** | Workspace con dirty tracking, lazy loading y cache LRU |
| 🛡️ **Validación Poka-Yoke** | Previene errores antes de escribir archivos |
| 🔎 **Búsqueda fuzzy** | Encuentra nodos tolerando typos con `fuzzywuzzy` |
| 📦 **Templates** | Genera estructuras de nodos y scripts GDScript desde plantillas |

---

## 🏆 ¿Por qué Ultra Godot MCP?

### ⚡ Velocidad extrema

La principal ventaja frente a otros MCPs de Godot: **no lanzamos Godot nunca**. Mientras otros MCPs ejecutan `godot --headless --script` por cada operación (2-5 segundos de overhead), nuestro **parser nativo de TSCN** lee y escribe archivos `.tscn` directamente en milisegundos.

| Operación | Otros MCPs | Ultra Godot MCP |
|---|---|---|
| Leer escena | ~2-5s (lanza Godot) | <10ms (parser nativo) |
| Añadir nodo | ~2-5s | <5ms |
| Validar proyecto | ~10-30s | <500ms |

### 💪 Potencia sin sacrificar rendimiento

38 herramientas MCP completas — el conjunto más amplio disponible — corriendo a velocidad de parser nativo:

| Ventaja | Ultra Godot MCP | Otros MCPs |
|---|---|---|
| **Parsing** | Nativo Python (lee TSCN directo) | Godot headless por cada operación |
| **Herramientas** | 38 completas | 8-15 básicas |
| **Sesiones** | Workspace en memoria + cache LRU | Re-parsean todo cada vez |
| **Inspector unificado** | 1 herramienta para TODOS los tipos | Herramientas separadas por tipo |
| **Validación** | Poka-Yoke antes de escribir | Escriben y luego fallan |
| **Búsqueda** | Fuzzy matching (tolera typos) | Búsqueda exacta |
| **Dependencias** | Solo Python — sin Godot instalado | Requiere Godot en PATH |

### 🌎 Hecho para la comunidad hispanohablante

Ultra Godot MCP nació de una necesidad real: **la comunidad hispanohablante de Godot es enorme, pero las herramientas de IA para desarrollo de juegos están diseñadas exclusivamente en inglés**.

- **Documentación bilingüe**: README, guías y errores documentados en español
- **Soporte nativo**: Creado por y para desarrolladores de España, México, Argentina, Colombia y toda Latinoamérica
- **Sin barrera idiomática**: Mensajes de error, validación y logs en español cuando corres en tu entorno
- **Comunidad inclusiva**: Porque hacer juegos no debería requerir hablar inglés

> *"La técnica no es un simple instrumento, es la forma en que el ser humano se apropia de la realidad"* — Gustavo Bueno

Desarrollado con ❤️ por los trabajadores y los iberófonos del mundo 🌍

---

## 📥 Instalación

### Desde PyPI (próximamente)

```bash
pip install godot-mcp
```

### Desde fuente

```bash
# Clonar el repositorio
git clone https://github.com/lenin-iberofono/godot-mcp.git
cd godot-mcp

# Instalar
pip install -e .

# O con dependencias de desarrollo
pip install -e ".[dev]"
```

### Requisitos

- **Python 3.10+**
- **Godot 4.6+** (para validación con `--check-only`)

---

## 🚀 Inicio Rápido

### 1. Iniciar el servidor

```bash
# Como comando
godot-mcp

# O como módulo
python -m godot_mcp.server
```

### 2. Configurar en tu cliente MCP

Añade a tu configuración de cliente MCP (Claude Desktop, Cursor, etc.):

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

### 3. Usar con tu asistente IA

Una vez configurado, tu asistente podrá:

```
→ "Crea una escena Player con CharacterBody2D, CollisionShape2D y Sprite2D"
→ "Añade un script de movimiento al jugador"
→ "Conecta la señal body_entered del Area2D al jugador"
→ "Valida que todas las escenas del proyecto estén correctas"
```

---

## 🛠️ Herramientas Disponibles

### 📋 Sesión
| Herramienta | Descripción |
|---|---|
| `start_session` | Crear sesión para un proyecto Godot |
| `end_session` | Cerrar sesión y guardar cambios |
| `get_session_info` | Información de una sesión |
| `list_sessions` | Listar sesiones activas |

### 🎬 Escenas
| Herramienta | Descripción |
|---|---|
| `create_scene` | Crear nueva escena `.tscn` |
| `get_scene_tree` | Obtener jerarquía completa de nodos |
| `save_scene` | Guardar escena a disco |
| `list_scenes` | Listar todas las escenas del proyecto |
| `instantiate_scene` | Instanciar una escena como nodo hijo |

### 🧱 Nodos
| Herramienta | Descripción |
|---|---|
| `add_node` | Añadir nodo a una escena |
| `remove_node` | Eliminar nodo |
| `rename_node` | Renombrar nodo |
| `move_node` | Reparentar nodo |
| `duplicate_node` | Duplicar nodo y sus hijos |
| `find_nodes` | Buscar nodos por nombre o tipo (con fuzzy matching) |
| `get_node_properties` | Obtener todas las propiedades de un nodo |

### 🔥 Inspector Unificado
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

### 📦 Recursos
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

### 📜 Scripts y Señales
| Herramienta | Descripción |
|---|---|
| `set_script` | Adjuntar script `.gd` a un nodo |
| `connect_signal` | Conectar señal entre nodos |

### 🏗️ Proyecto
| Herramienta | Descripción |
|---|---|
| `get_project_info` | Metadata del proyecto |
| `get_project_structure` | Estructura completa (escenas, scripts, assets) |
| `find_scripts` | Buscar scripts `.gd` |
| `find_resources` | Buscar recursos `.tres` |
| `list_projects` | Encontrar proyectos Godot en un directorio |

### ✅ Validación
| Herramienta | Descripción |
|---|---|
| `validate_tscn` | Validar archivo `.tscn` |
| `validate_gdscript` | Validar script `.gd` |
| `validate_project` | Validar proyecto completo |

---

## 📚 Documentación

| Documento | Contenido |
|---|---|
| [TOOLS.md](docs/TOOLS.md) | Referencia completa de cada herramienta |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | Diseño interno, sesiones y cache |
| [COMMON_ERRORS.md](docs/COMMON_ERRORS.md) | Errores frecuentes y soluciones |
| [TESTS.md](docs/TESTS.md) | Métricas de testing y cobertura |
| [CHANGELOG.md](CHANGELOG.md) | Historial de versiones |

---

## 🧪 Testing

```bash
# Todos los tests
pytest tests/

# Con coverage
pytest --cov=godot_mcp tests/

# Solo tests E2E
pytest tests/e2e/

# Tests específicos
pytest tests/test_server.py -v
```

**Estado actual:** 484 tests pasando · 68 tests nuevos en v3.1.0

---

## 🏗️ Arquitectura

```
src/godot_mcp/
├── server.py              # Entry point FastMCP
├── session_manager.py     # Gestión de sesiones
├── core/                  # Núcleo
│   ├── tscn_parser.py     # Parser de escenas Godot
│   ├── tres_parser.py     # Parser de recursos
│   ├── tscn_validator.py  # Validador de escenas
│   ├── gdscript_validator.py  # Validador de scripts
│   ├── cache.py           # Cache LRU
│   ├── models.py          # Modelos Pydantic
│   └── project_index.py   # Índice de proyectos
├── tools/                 # Herramientas MCP
│   ├── scene_tools.py     # Operaciones de escenas
│   ├── node_tools.py      # Operaciones de nodos
│   ├── resource_tools.py  # Gestión de recursos
│   ├── session_tools.py   # Gestión de sesiones
│   ├── project_tools.py   # Operaciones de proyecto
│   ├── validation_tools.py  # Validación
│   ├── signal_and_script_tools.py  # Señales y scripts
│   ├── property_tools.py   # Inspector unificado
│   └── debug_tools.py     # Debug
└── templates/             # Templates
    ├── node_templates.py  # Templates de nodos
    └── script_templates.py  # Templates de scripts
```

---

## 📄 Licencia

**MIT** — ver [LICENSE](LICENSE) para detalles.

---

<div align="center">

**Por los trabajadores y los iberófonos del mundo** 🌍

🇪🇸🇲🇽🇦🇷🇨🇴🇵🇪🇨🇱🇻🇪🇧🇴🇪🇨🇬🇹🇭🇳🇳🇮🇵🇾🇸🇻🇺🇾🇩🇴🇵🇷🇬🇶🇵🇭🇦🇩🇧🇿🇵🇹🇧🇷🇦🇴🇲🇿🇨🇻🇬🇼🇸🇹🇹🇱🇲🇴

</div>
