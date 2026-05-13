# 🏴 Ultra Godot MCP

[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Godot 4.6+](https://img.shields.io/badge/Godot-4.6+-478cbf?logo=godotengine&logoColor=white)](https://godotengine.org/)
[![Tests](https://img.shields.io/badge/Tests-512%20passing-2ea44f)](docs/TESTS.md)
[![Version](https://img.shields.io/badge/Version-4.6.0-6f42c1)](CHANGELOG.md)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> *"La técnica es una actividad compositora o destructora, violenta, y esto es lo que Aristóteles llamaba la poiesis, la poesía, precisamente."* — Gustavo Bueno

**Ultra Godot MCP** — *Plus Ultra*: ir más allá.

Servidor MCP para Godot Engine que permite a IAs y asistentes controlar proyectos directamente: crear escenas, manipular nodos, gestionar recursos, validar código, exportar builds, debuggear con breakpoints, y analizar la arquitectura del proyecto — **todo sin instalar addons en tu proyecto Godot**.

---

## ✨ Características

| Característica | Descripción |
|---|---|
| 🔍 **Parsing nativo TSCN** | Lee y escribe archivos `.tscn` directamente, sin Godot headless |
| 🛠️ **111 herramientas** | 9 capas: Core (45) + CLI Bridge (16) + LSP/DAP (10) + Intelligence (7) + Skeleton (6) + Array Ops (2) + Resource Builder (9) + TileMap (8) + **Shaders (4)** |
| 🎯 **Inspector unificado** | `set_node_properties` maneja TODOS los tipos de propiedad automáticamente |
| 🔄 **Sesiones en memoria** | Workspace con dirty tracking, lazy loading y cache LRU |
| ⚡ **Godot headless persistente** | Proceso Godot corriendo en background por sesión (10x más rápido) |
| 🛡️ **Validación Poka-Yoke** | Previene errores antes de escribir archivos |
| 🔎 **Búsqueda fuzzy** | Encuentra nodos tolerando typos con `fuzzywuzzy` |
| 📦 **Templates** | Genera estructuras de nodos y scripts GDScript desde plantillas |
| 🔧 **LSP/DAP nativos** | Autocompletado, hover, breakpoints, stepping — sin addons, solo Godot Editor abierto |
| 📊 **Project Intelligence** | Dependency graph, signal graph, code analysis, métricas |
 | 🎬 **Export & Screenshot** | Exportar builds, capturar frames, grabar movies |
 | 🗺️ **TileMap Tools** | Inspeccionar y manipular TileMaps/TileSets con la API real de Godot |
 | 🎨 **Shader Tools** | Crear, validar, analizar y gestionar shaders GDShader con 15 templates |
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
| **Herramientas** | ~15 | 110+ | 36 (22 free + 14 Pro) | **111** |
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

> **Nota:** GoPeak tiene más herramientas en número (110+), pero requiere addon GDScript + WebSocket + 4 puertos. Ultra Godot MCP prioriza **zero-config**: 111 herramientas que funcionan sin tocar tu proyecto Godot.

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

El LSP (Language Server Protocol) y DAP (Debug Adapter Protocol) son **features nativas de Godot**.

**Habilitar LSP en Godot Editor:**
1. `Editor > Editor Settings > Network > Language Server`
2. Activa **"Enable Language Server"** (puerto 6005)
3. Reinicia Godot Editor

**Habilitar DAP:**
1. `Editor > Editor Settings > Network > Debug Adapter`
2. Activa **"Enable Debug Adapter"** (puerto 6006)
3. Reinicia Godot Editor

**Configurar Bridge LSP en OpenCode:**
Añade a tu `opencode.jsonc`:
```json
{
  "lsp": {
    "gdscript": {
      "command": [
        "python",
        "D:/Mis Juegos/GodotMCP/godot-mcp-python/scripts/godot_lsp_bridge.py"
      ],
      "extensions": [".gd", ".gdshader"]
    }
  }
}
```

> **Nota:** El LSP/DAP requiere Godot Editor abierto. El bridge integrado conecta OpenCode (stdio) con Godot (TCP:6005). Sin dependencias de Node.js.

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

## 🛠️ Herramientas (111 en 9 capas)

| Capa | Herramientas | Requiere Godot |
|---|---|---|
| **1. Core** | Sesión, Escenas, Nodos, Recursos, Scripts, Señales, Proyecto, Validación | ❌ |
| **2. CLI Bridge** | Export, Runtime, Import, Screenshot, Movie | ✅ |
| **3. LSP/DAP** | Autocompletado, Hover, Breakpoints, Stepping | ✅ Editor abierto |
| **4. Intelligence** | Dependency Graph, Signal Graph, Code Analysis | ❌ |
| **5. Skeleton** | Skeleton2D, Skeleton3D, Skinning | ❌ |
| **6. Array Ops** | Operaciones quirúrgicas en arrays de escenas | ❌ |
| **7. Resource Builder** | Animation, StateMachine, BlendSpace, SpriteFrames, TileSet | ❌ |
| **8. TileMap** | Inspect, Edit, Terrain, Patterns | ✅ |
| **9. Shaders** | Crear, Validar, Material, Pipeline, Análisis | ❌ |

> 📖 **Referencia completa:** Ver [TOOLS.md](docs/TOOLS.md) para documentación detallada de las 111 herramientas.

### Destacados

**🔥 Inspector Unificado:** `set_node_properties()` maneja automáticamente texturas, shapes, scripts, colores, vectores, enums y valores simples.

**🧠 Zero-Godot:** Las capas 1, 4-7 funcionan sin Godot instalado (parser nativo + análisis estático).

**🎮 Full-Godot:** Las capas 2, 3, 8 usan Godot headless para funcionalidades avanzadas.

**🌉 Bridge LSP:** Incluye `scripts/godot_lsp_bridge.py` para conectar OpenCode ↔ Godot Editor (stdio↔TCP) sin dependencias de Node.js.

---

## 📚 Documentación

| Documento | Contenido |
|---|---|
| [TOOLS.md](docs/TOOLS.md) | Referencia completa de las 111 herramientas |
| [SHADERS.md](docs/SHADERS.md) | Guía de Shader Tools con ejemplos y templates |
| [TILEMAP_TOOLS.md](docs/TILEMAP_TOOLS.md) | Guía de TileMap Tools con ejemplos |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | Diseño interno, sesiones y cache |
| [ARCHITECTURE_v4.md](docs/ARCHITECTURE_v4.md) | Arquitectura v4.0.0 (4 capas) |
| [CLEANUP_v4.md](docs/CLEANUP_v4.md) | Análisis de limpieza e integración con sesiones |
| [COMMON_ERRORS.md](docs/COMMON_ERRORS.md) | Errores frecuentes y soluciones |
| [TESTS.md](docs/TESTS.md) | Métricas de testing y cobertura |
| [CHANGELOG.md](CHANGELOG.md) | Historial de versiones (v4.6.0) |

---

## 🧪 Testing

```bash
pytest tests/              # Todos los tests
pytest --cov=godot_mcp     # Con coverage
pytest tests/e2e/          # Solo E2E
pytest tests/test_server.py -v  # Tests específicos
```

**Estado:** 512 tests pasando · 24 módulos registrados en v4.6.0

---

## 🏗️ Arquitectura

```
src/godot_mcp/
├── server.py                    # Entry point FastMCP (23 módulos registrados)
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
├── tools/                       # Capas 1, 5, 6, 7, 8
│   ├── scene_tools.py           # Operaciones de escenas
│   ├── node_tools.py            # Operaciones de nodos
│   ├── resource_tools.py        # Gestión de recursos
│   ├── session_tools.py         # Gestión de sesiones
│   ├── project_tools.py         # Operaciones de proyecto
│   ├── validation_tools.py      # Validación
│   ├── signal_and_script_tools.py  # Señales y scripts
│   ├── property_tools.py        # Inspector unificado
│   ├── debug_tools.py           # Debug
│   ├── tilemap_tools.py         # Capa 8: TileMap/TileSet tools
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
├── templates/                   # Templates
│   ├── node_templates.py        # Templates de nodos
│   ├── script_templates.py      # Templates de scripts
│   └── shader_templates.py      # Templates de shaders (15 plantillas GDShader)
└── core/                        # Núcleo
    └── shader_parser.py         # Parser de GDShader (uniforms, funciones, complejidad)
```

---

## 📄 Licencia

**MIT** — ver [LICENSE](LICENSE) para detalles.

---

<div align="center">

**Por los trabajadores y los iberófonos del mundo** 🌍

🇪🇸🇲🇽🇦🇷🇨🇴🇵🇪🇨🇱🇻🇪🇧🇴🇪🇨🇬🇹🇭🇳🇳🇮🇵🇾🇸🇻🇺🇾🇩🇴🇵🇷🇬🇶🇵🇭🇦🇩🇧🇿🇵🇹🇧🇷🇦🇴🇲🇿🇨🇻🇬🇼🇸🇹🇹🇱🇲🇴

</div>
