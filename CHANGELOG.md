# Changelog

Todos los cambios notables en este proyecto se documentan en este archivo.

El formato se basa en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/).

---

## [3.1.0] - 2026-04-14

### Añadido
- **Búsqueda fuzzy** de nodos con `fuzzywuzzy` (tolerancia a typos)
- **Templates de nodos** (`node_templates.py`) para generación rápida de estructuras comunes
- **Templates de scripts** (`script_templates.py`) para boilerplate GDScript
- **Tests E2E** (`tests/e2e/`) con flujos completos de usuario
- **Tests de servidor** (`test_server.py`) - verificación de registro de 38 herramientas
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
