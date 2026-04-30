# TileMap Tools

Herramientas avanzadas para manipular **TileMap** y **TileSet** en Godot 4.6+.

> **Requiere Godot instalado.** Estas herramientas usan `run_gdscript` (Godot headless) para interactuar con la API real de Godot, evitando la complejidad de parsear `tile_data` comprimido.

---

## Índice

- [Arquitectura](#arquitectura)
- [Soporte TileMap vs TileMapLayer](#soporte-tilemap-vs-tilemaplayer)
- [Herramientas](#herramientas)
  - [inspect_tileset](#inspect_tileset)
  - [inspect_tilemap](#inspect_tilemap)
  - [set_tilemap_cells](#set_tilemap_cells)
  - [set_tilemap_layer_properties](#set_tilemap_layer_properties)
  - [apply_tilemap_terrain](#apply_tilemap_terrain)
  - [create_tilemap_pattern](#create_tilemap_pattern)
  - [set_tilemap_pattern](#set_tilemap_pattern)
- [Patterns: Persistencia](#patterns-persistencia)
- [Ejemplos de uso](#ejemplos-de-uso)
- [Errores comunes](#errores-comunes)

---

## Arquitectura

```
┌─────────────────────────────────────┐
│  tilemap_tools.py                   │
│  ├── GDScript templates (strings)   │
│  ├── Python wrapper functions       │
│  └── register_tilemap_tools()       │
└──────────┬──────────────────────────┘
           │ run_gdscript()
           ▼
┌─────────────────────────────────────┐
│  Godot headless (runtime real)      │
│  ├── Carga TileSet / TileMap        │
│  ├── Ejecuta operaciones            │
│  └── Serializa resultado a JSON     │
└─────────────────────────────────────┘
```

**Ventajas sobre parsing nativo:**
- No hay que decodificar `tile_data` (formato comprimido interno de Godot)
- Soporta automáticamente cambios en la API de Godot 4.x
- Funciona con TileSets embebidos (SubResources) y externos (.tres)

---

## Soporte TileMap vs TileMapLayer

Godot 4.6 deprecó `TileMap` en favor de `TileMapLayer`. Todas las herramientas soportan **ambos**:

| Nodo | Detección | Notas |
|------|-----------|-------|
| `TileMap` | `is TileMap` | Deprecated pero funcional |
| `TileMapLayer` | `is TileMapLayer` | Recomendado en Godot 4.6+ |

Los scripts GDScript usan funciones helper que unifican la API:

```gdscript
func _set_cell(node, layer, coords, source_id, atlas_coords, alternative):
    if node is TileMapLayer:
        node.set_cell(coords, source_id, atlas_coords, alternative)
    else:
        node.set_cells_terrain_connect(layer, [coords], ...)
```

---

## Herramientas

### `inspect_tileset`

Inspeccionar un TileSet y obtener información detallada.

```python
inspect_tileset(
    project_path="D:/MyGame",
    tileset_path="res://tilesets/ground.tres",  # o path absoluto
    godot_path=None,      # opcional
    timeout=30
)
```

**Retorna:**
```json
{
  "success": true,
  "tile_size": {"x": 16, "y": 16},
  "sources": [
    {
      "id": 0,
      "type": "TileSetAtlasSource",
      "has_tiles": true,
      "tile_count": 56,
      "texture": "res://assets/tiles.png",
      "margins": {"x": 0, "y": 0},
      "separation": {"x": 0, "y": 0},
      "texture_region_size": {"x": 16, "y": 16},
      "tiles": [
        {"coords": {"x": 0, "y": 0}, "alternatives": 1},
        ...
      ]
    }
  ],
  "terrain_sets": [
    {
      "id": 0,
      "name": "Rooms",
      "terrain_count": 3,
      "terrains": [
        {"id": 0, "name": "Floor", "color": "#FF0000"},
        ...
      ]
    }
  ],
  "patterns": [
    {"index": 0, "size": {"x": 4, "y": 4}}
  ],
  "physics_layers": 1,
  "navigation_layers": 0,
  "custom_data_layers": 0
}
```

---

### `inspect_tilemap`

Inspeccionar un nodo TileMap/TileMapLayer en una escena.

```python
inspect_tilemap(
    project_path="D:/MyGame",
    scene_path="res://scenes/Level.tscn",
    tilemap_node_path="Background",  # vacío si es root
    godot_path=None,
    timeout=30
)
```

**Retorna:**
```json
{
  "success": true,
  "node_type": "TileMapLayer",
  "layer_count": 1,
  "layers": [
    {
      "name": "",
      "enabled": true,
      "modulate": "#FFFFFFFF",
      "y_sort_enabled": false,
      "y_sort_origin": 0,
      "z_index": 0,
      "navigation_enabled": true
    }
  ],
  "used_cells_sample": [
    {"x": 0, "y": 0, "source_id": 0, "atlas_coords": {"x": 1, "y": 2}}
  ],
  "used_cells_count": 313,
  "used_rect": {"x": 0, "y": 0, "width": 20, "height": 16},
  "tileset": "res://tilesets/bunker_tileset.tres"
}
```

---

### `set_tilemap_cells`

Setear o borrar celdas individuales.

```python
set_tilemap_cells(
    project_path="D:/MyGame",
    scene_path="res://scenes/Level.tscn",
    cells=[
        {
            "coords": {"x": 5, "y": 3},
            "source_id": 1,
            "atlas_coords": {"x": 2, "y": 0},
            "alternative_tile": 0
        },
        {
            "coords": {"x": 6, "y": 3},
            "erase": True  # borrar celda
        }
    ],
    layer=0,
    tilemap_node_path="Background"
)
```

**Parámetros de cada celda:**

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `coords` | `{"x": int, "y": int}` | **Requerido.** Coordenadas de la celda |
| `source_id` | `int` | ID del source. `-1` o omitir para borrar |
| `atlas_coords` | `{"x": int, "y": int}` | Coordenadas en el atlas (si aplica) |
| `alternative_tile` | `int` | Variante alternativa (default: 0) |
| `erase` | `bool` | Si es `true`, borra la celda |

**Retorna:** `{"success": true, "cells_changed": 2}`

---

### `set_tilemap_layer_properties`

Configurar propiedades de una capa (layer).

```python
set_tilemap_layer_properties(
    project_path="D:/MyGame",
    scene_path="res://scenes/Level.tscn",
    layer=0,
    properties={
        "z_index": 10,
        "y_sort_enabled": True,
        "modulate": {"r": 1.0, "g": 0.5, "b": 0.5, "a": 1.0}
    },
    tilemap_node_path="Background"
)
```

**Propiedades soportadas:**

| Propiedad | Tipo | Descripción |
|-----------|------|-------------|
| `name` | `str` | Nombre de la capa |
| `enabled` | `bool` | Activa/inactiva |
| `modulate` | `{"r": f, "g": f, "b": f, "a": f}` | Color multiplicador |
| `y_sort_enabled` | `bool` | Ordenar por Y |
| `y_sort_origin` | `int` | Offset de ordenamiento Y |
| `z_index` | `int` | Índice Z para rendering |
| `navigation_enabled` | `bool` | Navegación activa |

---

### `apply_tilemap_terrain`

Aplicar terrain set a un grupo de celdas con conectividad automática.

```python
apply_tilemap_terrain(
    project_path="D:/MyGame",
    scene_path="res://scenes/Level.tscn",
    cells=[
        {"x": 10, "y": 5},
        {"x": 11, "y": 5},
        {"x": 10, "y": 6},
        {"x": 11, "y": 6}
    ],
    terrain_set=0,
    terrain=1,
    layer=0,
    tilemap_node_path="Background",
    ignore_empty_terrains=True
)
```

**Retorna:** `{"success": true, "cells_affected": 4}`

> Usa `set_cells_terrain_connect()` de Godot para conectar automáticamente los bordes entre celdas vecinas.

---

### `create_tilemap_pattern`

Crear un pattern desde una región rectangular de celdas.

```python
create_tilemap_pattern(
    project_path="D:/MyGame",
    scene_path="res://scenes/Level.tscn",
    rect={"x": 0, "y": 0, "width": 4, "height": 4},
    layer=0,
    tilemap_node_path="Background",
    pattern_name="room_corner"
)
```

**Retorna:**
```json
{
  "success": true,
  "pattern_size": {"x": 4, "y": 4},
  "tileset_pattern_index": 0,
  "pattern_path": "res://scenes/Level_pattern_1234567890.tres"
}
```

> **El pattern se guarda como `.tres` externo** automáticamente (ver [Patterns: Persistencia](#patterns-persistencia)).

---

### `set_tilemap_pattern`

Aplicar un pattern en una posición específica.

```python
# Método recomendado: usar pattern_path
set_tilemap_pattern(
    project_path="D:/MyGame",
    scene_path="res://scenes/Level.tscn",
    position={"x": 10, "y": 5},
    pattern_path="res://patterns/room_corner.tres",
    layer=0,
    tilemap_node_path="Background"
)

# Método alternativo: usar pattern_index (solo con TileSet externo)
set_tilemap_pattern(
    project_path="D:/MyGame",
    scene_path="res://scenes/Level.tscn",
    position={"x": 10, "y": 5},
    pattern_index=0,
    layer=0
)
```

**Retorna:** `{"success": true, "position": {"x": 10, "y": 5}, "pattern_size": {"x": 4, "y": 4}}`

---

## Patterns: Persistencia

### El problema

Godot **no serializa** los patterns añadidos a un TileSet embebido (SubResource dentro de `.tscn`). Si creas un pattern en un TileSet embebido y guardas la escena, el pattern se pierde al recargar.

### La solución

`create_tilemap_pattern` guarda el pattern como archivo `.tres` externo automáticamente:

```gdscript
# En el script GDScript interno:
var pattern_path = scene_dir + "/" + base_name + "_pattern_" + str(randi()) + ".tres"
ResourceSaver.save(pattern, pattern_path)
```

### Uso recomendado

1. **Crear pattern:**
   ```python
   result = create_tilemap_pattern(...)
   pattern_path = result["pattern_path"]  # res://...pattern_123.tres
   ```

2. **Aplicar pattern:**
   ```python
   set_tilemap_pattern(..., pattern_path=pattern_path)
   ```

3. **Opcional: renombrar a algo más descriptivo:**
   ```bash
   mv Level_pattern_1234567890.tres room_corner.tres
   ```

### Dónde NO funciona `pattern_index`

Si el TileSet es un **SubResource embebido** en la escena (no un `.tres` externo), `pattern_index` **no funcionará** después de recargar el proyecto, porque Godot no guarda los patterns en el SubResource.

**Siempre usa `pattern_path` cuando sea posible.**

---

## Ejemplos de uso

### Flujo completo: crear y aplicar pattern

```python
# 1. Inspeccionar el TileSet
info = inspect_tileset("D:/MyGame", "res://tilesets/ground.tres")
print(f"Tiles: {info['sources'][0]['tile_count']}")

# 2. Inspeccionar el TileMap
map_info = inspect_tilemap("D:/MyGame", "res://scenes/Level.tscn", "Background")
print(f"Celdas usadas: {map_info['used_cells_count']}")

# 3. Crear pattern desde una habitación existente
pattern = create_tilemap_pattern(
    "D:/MyGame",
    "res://scenes/Level.tscn",
    rect={"x": 5, "y": 5, "width": 4, "height": 4},
    tilemap_node_path="Background"
)

# 4. Aplicar el pattern en otra parte del mapa
set_tilemap_pattern(
    "D:/MyGame",
    "res://scenes/Level.tscn",
    position={"x": 20, "y": 10},
    pattern_path=pattern["pattern_path"],
    tilemap_node_path="Background"
)
```

### Editar celdas individualmente

```python
# Pintar un muro
set_tilemap_cells(
    "D:/MyGame",
    "res://scenes/Level.tscn",
    cells=[
        {"coords": {"x": 5, "y": 3}, "source_id": 1, "atlas_coords": {"x": 2, "y": 0}},
        {"coords": {"x": 6, "y": 3}, "source_id": 1, "atlas_coords": {"x": 2, "y": 0}},
        {"coords": {"x": 7, "y": 3}, "source_id": 1, "atlas_coords": {"x": 2, "y": 0}},
    ],
    tilemap_node_path="Walls"
)

# Borrar una celda
set_tilemap_cells(
    "D:/MyGame",
    "res://scenes/Level.tscn",
    cells=[{"coords": {"x": 5, "y": 3}, "erase": True}],
    tilemap_node_path="Walls"
)
```

### Aplicar terrain a un área

```python
# Crear suelo con terrain automático
apply_tilemap_terrain(
    "D:/MyGame",
    "res://scenes/Level.tscn",
    cells=[{"x": i, "y": j} for i in range(10, 20) for j in range(5, 15)],
    terrain_set=0,
    terrain=1,  # ID del terrain "Floor"
    tilemap_node_path="Background"
)
```

---

## Errores comunes

### "Provide either pattern_index or pattern_path"

`set_tilemap_pattern` requiere al menos uno de los dos. Usa `pattern_path` (más confiable).

### "Failed to load TileSet"

Verifica que el path sea correcto. Puede ser:
- `res://tilesets/ground.tres` (relativo al proyecto)
- `D:/MyGame/tilesets/ground.tres` (absoluto)

### "Failed to create pattern" → pattern_path es null

Esto puede pasar si no hay celdas en el rectángulo especificado, o si el TileSet es embebido y no se puede guardar. Verifica:
1. Que el rectángulo tenga celdas válidas
2. Que la escena esté guardada en disco (no en memoria)

### TileMap vs TileMapLayer no detectado

Si `inspect_tilemap` retorna `"node_type": "Unknown"`, verifica:
- Que el `tilemap_node_path` sea correcto
- Que el nodo sea realmente un TileMap o TileMapLayer
- Que la escena tenga la extensión correcta (`.tscn`)

### Cambios no persisten

Todas las herramientas de TileMap **guardan automáticamente** la escena después de modificarla. Si no ves los cambios:
1. Verifica que Godot Editor no tenga la escena abierta con cambios sin guardar
2. Recarga la escena en Godot (`Scene > Reload Saved Scene`)

---

*Documentación generada para Ultra Godot MCP v4.5.0*
