"""
TileMap Tools - Herramientas avanzadas para TileMap y TileSet.

Usa Godot runtime (run_gdscript) para inspeccionar y manipular TileMaps
y TileSets con la API real de Godot 4.6, evitando la complejidad de
parsear tile_data comprimido o bitmask_flags.

Herramientas:
- inspect_tileset: Inspeccionar un TileSet (.tres o SubResource)
- inspect_tilemap: Inspeccionar un TileMap en una escena
- set_tilemap_cells: Setear/limpiar celdas individuales
- set_tilemap_layer_properties: Configurar layers (z-index, y-sort, modulate)
- apply_tilemap_terrain: Aplicar terrain a rangos de celdas
- create_tilemap_pattern: Crear un pattern desde un rango de celdas
- set_tilemap_pattern: Aplicar un pattern en una posición
- render_tileset_atlas: Capturar imagen del atlas con grid numerado
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
from typing import Any, Optional

from godot_mcp.godot_cli.runtime_tools import run_gdscript
from godot_mcp.godot_cli.base import GodotCLIWrapper

logger = logging.getLogger(__name__)


# ==================== CONSTANTES ====================

VISUAL_ACCESS_WARNING = (
    "⚠️  ATENCIÓN AGENTE: No tienes acceso visual a la imagen generada. "
    "El archivo se guardó en disco pero NO fue transmitido a tu contexto. "
    "Si necesitas analizar contenido visual (colores, formas, disposición de tiles, etc.), "
    "DEBES pedirle al usuario que adjunte/pegue la imagen en el chat. "
    "NO intentes describir o inferir el contenido visual basándote únicamente en metadatos."
)


# ==================== SCRIPTS GDSCRIPT ====================

INSPECT_TILESET_SCRIPT = '''
extends SceneTree

func _init():
    var tileset_path = "{tileset_path}"
    var is_res_path = tileset_path.begins_with("res://")
    
    var tileset = null
    if is_res_path:
        tileset = load(tileset_path)
    else:
        # Try as absolute path
        tileset = load(tileset_path)
    
    if tileset == null or not (tileset is TileSet):
        print("TEST_OUTPUT: " + JSON.stringify({{
            "success": false,
            "error": "Failed to load TileSet: " + tileset_path
        }}))
        quit()
        return
    
    # Collect sources
    var sources = []
    var source_count = tileset.get_source_count()
    for i in range(source_count):
        var source_id = tileset.get_source_id(i)
        var source = tileset.get_source(source_id)
        var source_info = {{
            "id": source_id,
            "type": source.get_class(),
            "has_tiles": false,
            "tile_count": 0
        }}
        
        if source is TileSetAtlasSource:
            source_info["has_tiles"] = true
            var atlas = source as TileSetAtlasSource
            source_info["texture"] = atlas.texture.resource_path if atlas.texture else ""
            source_info["margins"] = {{"x": atlas.margins.x, "y": atlas.margins.y}}
            source_info["separation"] = {{"x": atlas.separation.x, "y": atlas.separation.y}}
            source_info["texture_region_size"] = {{"x": atlas.texture_region_size.x, "y": atlas.texture_region_size.y}}
            
            if atlas.texture:
                var tex_size = atlas.texture.get_size()
                source_info["texture_size"] = {{"x": tex_size.x, "y": tex_size.y}}
                var region_w = atlas.texture_region_size.x
                var region_h = atlas.texture_region_size.y
                var sep_x = atlas.separation.x
                var sep_y = atlas.separation.y
                var margin_x = atlas.margins.x
                var margin_y = atlas.margins.y
                var cols = 0
                var rows = 0
                if region_w > 0 and region_h > 0:
                    cols = int((tex_size.x - margin_x + sep_x) / (region_w + sep_x))
                    rows = int((tex_size.y - margin_y + sep_y) / (region_h + sep_y))
                source_info["grid_dimensions"] = {{"cols": cols, "rows": rows}}
            else:
                source_info["texture_size"] = {{"x": 0, "y": 0}}
                source_info["grid_dimensions"] = {{"cols": 0, "rows": 0}}
            
            # Count tiles
            var tiles = atlas.get_tiles_count()
            source_info["tile_count"] = tiles
            var tile_list = []
            for t in range(tiles):
                var coords = atlas.get_tile_id(t)
                var alternatives = atlas.get_alternative_tiles_count(coords)
                tile_list.append({{
                    "coords": {{"x": coords.x, "y": coords.y}},
                    "alternatives": alternatives
                }})
            source_info["tiles"] = tile_list
            
        elif source is TileSetScenesCollectionSource:
            source_info["has_tiles"] = true
            var scenes = source as TileSetScenesCollectionSource
            source_info["tile_count"] = scenes.get_scenes_count()
            var scene_list = []
            for s in range(scenes.get_scenes_count()):
                var scene_tile = scenes.get_scene_tile_scene(s)
                scene_list.append({{
                    "index": s,
                    "scene": scene_tile.resource_path if scene_tile else ""
                }})
            source_info["scenes"] = scene_list
            
        sources.append(source_info)
    
    # Collect terrain sets
    var terrain_sets = []
    var terrain_set_count = tileset.get_terrain_sets_count()
    for ts in range(terrain_set_count):
        var mode = tileset.get_terrain_set_mode(ts)
        var terrains = []
        var terrain_count = tileset.get_terrains_count(ts)
        for t in range(terrain_count):
            terrains.append({{
                "index": t,
                "name": tileset.get_terrain_name(ts, t),
                "color": {{"r": tileset.get_terrain_color(ts, t).r, "g": tileset.get_terrain_color(ts, t).g, "b": tileset.get_terrain_color(ts, t).b}}
            }})
        terrain_sets.append({{
            "set_index": ts,
            "mode": mode,
            "terrains": terrains
        }})
    
    # Collect patterns
    var patterns = []
    var pattern_count = tileset.get_patterns_count()
    for p in range(pattern_count):
        var pat = tileset.get_pattern(p)
        patterns.append({{
            "index": p,
            "size": {{"x": pat.get_size().x, "y": pat.get_size().y}}
        }})
    
    var result = {{
        "success": true,
        "tile_size": {{"x": tileset.tile_size.x, "y": tileset.tile_size.y}},
        "tile_shape": tileset.tile_shape,
        "tile_layout": tileset.tile_layout,
        "tile_offset_axis": tileset.tile_offset_axis,
        "source_count": source_count,
        "sources": sources,
        "terrain_sets_count": terrain_set_count,
        "terrain_sets": terrain_sets,
        "pattern_count": pattern_count,
        "patterns": patterns,
        "physics_layers": tileset.get_physics_layers_count(),
        "navigation_layers": tileset.get_navigation_layers_count(),
        "custom_data_layers": tileset.get_custom_data_layers_count()
    }}
    
    print("TEST_OUTPUT: " + JSON.stringify(result))
    quit()
'''

INSPECT_TILEMAP_SCRIPT = '''
extends SceneTree

func _init():
    var scene_path = "{scene_path}"
    var tilemap_node_path = "{tilemap_node_path}"
    
    var scene = load(scene_path)
    if scene == null:
        print("TEST_OUTPUT: " + JSON.stringify({{
            "success": false,
            "error": "Failed to load scene"
        }}))
        quit()
        return
    
    var instance = scene.instantiate()
    
    var tilemap = instance.get_node(tilemap_node_path) if tilemap_node_path != "" else instance
    if tilemap == null:
        print("TEST_OUTPUT: " + JSON.stringify({{
            "success": false,
            "error": "Node not found: " + tilemap_node_path
        }}))
        quit()
        return
    
    var is_tilemap = tilemap is TileMap
    var is_tilemap_layer = tilemap is TileMapLayer
    
    if not is_tilemap and not is_tilemap_layer:
        print("TEST_OUTPUT: " + JSON.stringify({{
            "success": false,
            "error": "Node is not TileMap or TileMapLayer: " + tilemap.get_class()
        }}))
        quit()
        return
    
    # Layers
    var layers = []
    var used_cells = []
    var layer_count = 1
    var used_rect = null
    var all_cells = []
    
    if is_tilemap:
        layer_count = tilemap.get_layers_count()
        for l in range(layer_count):
            layers.append({{
                "index": l,
                "name": tilemap.get_layer_name(l),
                "enabled": tilemap.is_layer_enabled(l),
                "modulate": {{"r": tilemap.get_layer_modulate(l).r, "g": tilemap.get_layer_modulate(l).g, "b": tilemap.get_layer_modulate(l).b, "a": tilemap.get_layer_modulate(l).a}},
                "y_sort_enabled": tilemap.is_layer_y_sort_enabled(l),
                "y_sort_origin": tilemap.get_layer_y_sort_origin(l),
                "z_index": tilemap.get_layer_z_index(l),
                "navigation_enabled": tilemap.is_layer_navigation_enabled(l),
                "tile_count": tilemap.get_used_cells(l).size()
            }})
        
        # Used cells (first layer only, sample)
        all_cells = tilemap.get_used_cells(0)
        var limit = min(all_cells.size(), 100)
        for i in range(limit):
            var c = all_cells[i]
            used_cells.append({{
                "coords": {{"x": c.x, "y": c.y}},
                "source_id": tilemap.get_cell_source_id(0, c),
                "atlas_coords": {{"x": tilemap.get_cell_atlas_coords(0, c).x, "y": tilemap.get_cell_atlas_coords(0, c).y}},
                "alternative_tile": tilemap.get_cell_alternative_tile(0, c)
            }})
        used_rect = tilemap.get_used_rect()
    else:
        # TileMapLayer
        layers.append({{
            "index": 0,
            "name": tilemap.name,
            "enabled": tilemap.enabled,
            "modulate": {{"r": tilemap.modulate.r, "g": tilemap.modulate.g, "b": tilemap.modulate.b, "a": tilemap.modulate.a}},
            "y_sort_enabled": tilemap.y_sort_enabled,
            "y_sort_origin": tilemap.y_sort_origin,
            "z_index": tilemap.z_index,
            "navigation_enabled": tilemap.navigation_enabled,
            "tile_count": tilemap.get_used_cells().size()
        }})
        
        all_cells = tilemap.get_used_cells()
        var limit = min(all_cells.size(), 100)
        for i in range(limit):
            var c = all_cells[i]
            used_cells.append({{
                "coords": {{"x": c.x, "y": c.y}},
                "source_id": tilemap.get_cell_source_id(c),
                "atlas_coords": {{"x": tilemap.get_cell_atlas_coords(c).x, "y": tilemap.get_cell_atlas_coords(c).y}},
                "alternative_tile": tilemap.get_cell_alternative_tile(c)
            }})
        used_rect = tilemap.get_used_rect()
    
    # Build cell lookup for ASCII map
    var cell_lookup = {{}}
    for c in all_cells:
        var src_id = 0
        var atlas_c = Vector2i(-1, -1)
        if is_tilemap:
            src_id = tilemap.get_cell_source_id(0, c)
            atlas_c = tilemap.get_cell_atlas_coords(0, c)
        else:
            src_id = tilemap.get_cell_source_id(c)
            atlas_c = tilemap.get_cell_atlas_coords(c)
        cell_lookup[Vector2i(c.x, c.y)] = {{
            "source_id": src_id,
            "atlas_coords": atlas_c
        }}
    
    # Build ASCII map (used_rect is Rect2i, NOT Dictionary)
    var ascii_chars = " .-+=*#%@ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    var ascii_lines = []
    var ascii_map_truncated = false
    if used_rect != null and used_rect.size.x > 0 and used_rect.size.y > 0:
        var max_w = 80
        var max_h = 40
        var start_x = used_rect.position.x
        var start_y = used_rect.position.y
        var end_x = used_rect.position.x + used_rect.size.x
        var end_y = used_rect.position.y + used_rect.size.y
        var step_x = 1
        var step_y = 1
        
        if used_rect.size.x > max_w:
            step_x = int(used_rect.size.x / max_w) + 1
            ascii_map_truncated = true
        if used_rect.size.y > max_h:
            step_y = int(used_rect.size.y / max_h) + 1
            ascii_map_truncated = true
        
        for y in range(start_y, end_y, step_y):
            var line = ""
            for x in range(start_x, end_x, step_x):
                var key = Vector2i(x, y)
                if cell_lookup.has(key):
                    var info = cell_lookup[key]
                    var src = info.source_id
                    var atlas = info.atlas_coords
                    var idx = abs((src * 100 + atlas.x * 10 + atlas.y)) % ascii_chars.length()
                    line += ascii_chars[idx]
                else:
                    line += " "
            ascii_lines.append(line)
    
    # TileSet info
    var tileset_info = {{}}
    if tilemap.tile_set != null:
        var ts = tilemap.tile_set
        tileset_info = {{
            "resource_path": ts.resource_path if ts.resource_path else "(embedded)",
            "source_count": ts.get_source_count()
        }}
    
    var result = {{
        "success": true,
        "node_type": "TileMap" if is_tilemap else "TileMapLayer",
        "layer_count": layer_count,
        "layers": layers,
        "used_cells_count": all_cells.size(),
        "used_cells_sample": used_cells,
        "used_rect": {{"x": used_rect.position.x, "y": used_rect.position.y, "width": used_rect.size.x, "height": used_rect.size.y}} if used_rect != null else null,
        "ascii_lines": ascii_lines,
        "ascii_map_truncated": ascii_map_truncated,
        "tileset": tileset_info
    }}
    
    print("TEST_OUTPUT: " + JSON.stringify(result))
    quit()
'''

SET_TILEMAP_CELLS_SCRIPT = '''
extends SceneTree

# Helper to handle TileMap vs TileMapLayer API differences
func _set_cell(tilemap, layer: int, coords: Vector2i, source_id: int, atlas_coords: Vector2i, alternative: int):
    if tilemap is TileMap:
        tilemap.set_cell(layer, coords, source_id, atlas_coords, alternative)
    else:
        tilemap.set_cell(coords, source_id, atlas_coords, alternative)

func _erase_cell(tilemap, layer: int, coords: Vector2i):
    if tilemap is TileMap:
        tilemap.erase_cell(layer, coords)
    else:
        tilemap.erase_cell(coords)

func _init():
    var scene_path = "{scene_path}"
    var tilemap_node_path = "{tilemap_node_path}"
    var layer = {layer}
    var cells = {cells_json}
    
    var scene = load(scene_path)
    if scene == null:
        print("TEST_OUTPUT: " + JSON.stringify({{
            "success": false,
            "error": "Failed to load scene"
        }}))
        quit()
        return
    
    var instance = scene.instantiate()
    var tilemap = instance.get_node(tilemap_node_path) if tilemap_node_path != "" else instance
    
    if tilemap == null or (not (tilemap is TileMap) and not (tilemap is TileMapLayer)):
        print("TEST_OUTPUT: " + JSON.stringify({{
            "success": false,
            "error": "Node is not TileMap or TileMapLayer: " + (tilemap.get_class() if tilemap else "null")
        }}))
        quit()
        return
    
    var changed = 0
    
    for cell in cells:
        var coords = Vector2i(cell.coords.x, cell.coords.y)
        
        if cell.get("erase", false):
            _erase_cell(tilemap, layer, coords)
            changed += 1
        else:
            var source_id = cell.get("source_id", -1)
            var atlas_coords = Vector2i(
                cell.get("atlas_coords", {{}}).get("x", -1),
                cell.get("atlas_coords", {{}}).get("y", -1)
            )
            var alternative = cell.get("alternative_tile", 0)
            _set_cell(tilemap, layer, coords, source_id, atlas_coords, alternative)
            changed += 1
    
    # Save the modified scene
    var packed = PackedScene.new()
    var err = packed.pack(instance)
    if err == OK:
        var save_err = ResourceSaver.save(packed, scene_path)
        if save_err == OK:
            print("TEST_OUTPUT: " + JSON.stringify({{
                "success": true,
                "cells_changed": changed,
                "scene_saved": true
            }}))
        else:
            print("TEST_OUTPUT: " + JSON.stringify({{
                "success": false,
                "error": "Failed to save scene, error code: " + str(save_err)
            }}))
    else:
        print("TEST_OUTPUT: " + JSON.stringify({{
            "success": false,
            "error": "Failed to pack scene"
        }}))
    
    quit()
'''

SET_LAYER_PROPERTIES_SCRIPT = '''
extends SceneTree

# Helper: set property on either TileMap (by layer) or TileMapLayer (direct)
func _set_layer_prop(tilemap, layer: int, prop_name: String, value):
    if tilemap is TileMap:
        match prop_name:
            "name": tilemap.set_layer_name(layer, value)
            "enabled": tilemap.set_layer_enabled(layer, value)
            "modulate": tilemap.set_layer_modulate(layer, value)
            "y_sort_enabled": tilemap.set_layer_y_sort_enabled(layer, value)
            "y_sort_origin": tilemap.set_layer_y_sort_origin(layer, value)
            "z_index": tilemap.set_layer_z_index(layer, value)
            "navigation_enabled": tilemap.set_layer_navigation_enabled(layer, value)
    else:
        match prop_name:
            "name": tilemap.name = value
            "enabled": tilemap.enabled = value
            "modulate": tilemap.modulate = value
            "y_sort_enabled": tilemap.y_sort_enabled = value
            "y_sort_origin": tilemap.y_sort_origin = value
            "z_index": tilemap.z_index = value
            "navigation_enabled": tilemap.navigation_enabled = value

func _init():
    var scene_path = "{scene_path}"
    var tilemap_node_path = "{tilemap_node_path}"
    var layer = {layer}
    var properties = {properties_json}
    
    var scene = load(scene_path)
    if scene == null:
        print("TEST_OUTPUT: " + JSON.stringify({{
            "success": false,
            "error": "Failed to load scene"
        }}))
        quit()
        return
    
    var instance = scene.instantiate()
    var tilemap = instance.get_node(tilemap_node_path) if tilemap_node_path != "" else instance
    
    if tilemap == null or (not (tilemap is TileMap) and not (tilemap is TileMapLayer)):
        print("TEST_OUTPUT: " + JSON.stringify({{
            "success": false,
            "error": "Node is not TileMap or TileMapLayer: " + (tilemap.get_class() if tilemap else "null")
        }}))
        quit()
        return
    
    # For TileMap, validate layer index
    if tilemap is TileMap and (layer < 0 or layer >= tilemap.get_layers_count()):
        print("TEST_OUTPUT: " + JSON.stringify({{
            "success": false,
            "error": "Invalid layer index: " + str(layer)
        }}))
        quit()
        return
    
    var applied = []
    
    if properties.has("name"):
        _set_layer_prop(tilemap, layer, "name", properties.name)
        applied.append("name")
    
    if properties.has("enabled"):
        _set_layer_prop(tilemap, layer, "enabled", properties.enabled)
        applied.append("enabled")
    
    if properties.has("modulate"):
        var m = properties.modulate
        _set_layer_prop(tilemap, layer, "modulate", Color(m.r, m.g, m.b, m.a))
        applied.append("modulate")
    
    if properties.has("y_sort_enabled"):
        _set_layer_prop(tilemap, layer, "y_sort_enabled", properties.y_sort_enabled)
        applied.append("y_sort_enabled")
    
    if properties.has("y_sort_origin"):
        _set_layer_prop(tilemap, layer, "y_sort_origin", properties.y_sort_origin)
        applied.append("y_sort_origin")
    
    if properties.has("z_index"):
        _set_layer_prop(tilemap, layer, "z_index", properties.z_index)
        applied.append("z_index")
    
    if properties.has("navigation_enabled"):
        _set_layer_prop(tilemap, layer, "navigation_enabled", properties.navigation_enabled)
        applied.append("navigation_enabled")
    
    # Save
    var packed = PackedScene.new()
    var err = packed.pack(instance)
    if err == OK:
        ResourceSaver.save(packed, scene_path)
    
    print("TEST_OUTPUT: " + JSON.stringify({{
        "success": true,
        "properties_applied": applied
    }}))
    quit()
'''

APPLY_TERRAIN_SCRIPT = '''
extends SceneTree

# Helper: terrain connect on either TileMap (with layer) or TileMapLayer (no layer)
func _terrain_connect(tilemap, layer: int, cells: Array, terrain_set: int, terrain: int, ignore_empty: bool):
    if tilemap is TileMap:
        tilemap.set_cells_terrain_connect(layer, cells, terrain_set, terrain, ignore_empty)
    else:
        tilemap.set_cells_terrain_connect(cells, terrain_set, terrain, ignore_empty)

func _init():
    var scene_path = "{scene_path}"
    var tilemap_node_path = "{tilemap_node_path}"
    var layer = {layer}
    var cells = {cells_json}
    var terrain_set = {terrain_set}
    var terrain = {terrain}
    var ignore_empty = {ignore_empty}
    
    var scene = load(scene_path)
    if scene == null:
        print("TEST_OUTPUT: " + JSON.stringify({{
            "success": false,
            "error": "Failed to load scene"
        }}))
        quit()
        return
    
    var instance = scene.instantiate()
    var tilemap = instance.get_node(tilemap_node_path) if tilemap_node_path != "" else instance
    
    if tilemap == null or (not (tilemap is TileMap) and not (tilemap is TileMapLayer)):
        print("TEST_OUTPUT: " + JSON.stringify({{
            "success": false,
            "error": "Node is not TileMap or TileMapLayer: " + (tilemap.get_class() if tilemap else "null")
        }}))
        quit()
        return
    
    var cell_array = []
    for c in cells:
        cell_array.append(Vector2i(c.x, c.y))
    
    _terrain_connect(tilemap, layer, cell_array, terrain_set, terrain, ignore_empty)
    
    # Save
    var packed = PackedScene.new()
    var err = packed.pack(instance)
    if err == OK:
        ResourceSaver.save(packed, scene_path)
    
    print("TEST_OUTPUT: " + JSON.stringify({{
        "success": true,
        "cells_affected": cells.size()
    }}))
    quit()
'''

CREATE_PATTERN_SCRIPT = '''
extends SceneTree

# Helper: get used cells from either TileMap (by layer) or TileMapLayer (no layer)
func _get_used_cells(tilemap, layer: int) -> Array:
    if tilemap is TileMap:
        return tilemap.get_used_cells(layer)
    else:
        return tilemap.get_used_cells()

# Helper: get pattern from either TileMap (with layer) or TileMapLayer (no layer)
func _get_pattern(tilemap, layer: int, cells: Array):
    if tilemap is TileMap:
        return tilemap.get_pattern(layer, cells)
    else:
        return tilemap.get_pattern(cells)

# Helper: update all TileMap/TileMapLayer nodes using old_tileset to new_tileset
func _update_tileset_refs(node: Node, old_tileset, new_tileset):
    if node is TileMap or node is TileMapLayer:
        if node.tile_set == old_tileset:
            node.tile_set = new_tileset
    for child in node.get_children():
        _update_tileset_refs(child, old_tileset, new_tileset)

func _init():
    var scene_path = "{scene_path}"
    var tilemap_node_path = "{tilemap_node_path}"
    var layer = {layer}
    var rect = {rect_json}
    var pattern_name = "{pattern_name}"
    
    var scene = load(scene_path)
    if scene == null:
        print("TEST_OUTPUT: " + JSON.stringify({{
            "success": false,
            "error": "Failed to load scene"
        }}))
        quit()
        return
    
    var instance = scene.instantiate()
    var tilemap = instance.get_node(tilemap_node_path) if tilemap_node_path != "" else instance
    
    if tilemap == null or (not (tilemap is TileMap) and not (tilemap is TileMapLayer)):
        print("TEST_OUTPUT: " + JSON.stringify({{
            "success": false,
            "error": "Node is not TileMap or TileMapLayer: " + (tilemap.get_class() if tilemap else "null")
        }}))
        quit()
        return
    
    var used_cells = _get_used_cells(tilemap, layer)
    var pattern_cells = []
    
    var r = Rect2i(rect.x, rect.y, rect.width, rect.height)
    for c in used_cells:
        if r.has_point(c):
            pattern_cells.append(c)
    
    if pattern_cells.size() == 0:
        print("TEST_OUTPUT: " + JSON.stringify({{
            "success": false,
            "error": "No cells found in the specified rectangle"
        }}))
        quit()
        return
    
    var pattern = _get_pattern(tilemap, layer, pattern_cells)
    
    if pattern == null:
        print("TEST_OUTPUT: " + JSON.stringify({{
            "success": false,
            "error": "Failed to create pattern"
        }}))
        quit()
        return
    
    # Get the TileSet and add the pattern
    # Save pattern as standalone .tres for reliable persistence
    var scene_dir = scene_path.get_base_dir()
    var base_name = scene_path.get_file().get_basename()
    var pattern_path = scene_dir + "/" + base_name + "_pattern_" + str(randi()) + ".tres"
    
    var pattern_save_err = ResourceSaver.save(pattern, pattern_path)
    if pattern_save_err != OK:
        print("TEST_OUTPUT: " + JSON.stringify({{
            "success": false,
            "error": "Failed to save pattern as .tres, error code: " + str(pattern_save_err)
        }}))
        quit()
        return
    
    # Also add to TileSet if possible (for convenience), but don't rely on it
    var tileset = tilemap.tile_set
    var pattern_index = -1
    if tileset != null:
        pattern_index = tileset.add_pattern(pattern)
    
    # Save the modified scene
    var packed = PackedScene.new()
    var pack_err = packed.pack(instance)
    if pack_err == OK:
        ResourceSaver.save(packed, scene_path)
    
    var result = {{
        "success": true,
        "pattern_size": {{"x": pattern.get_size().x, "y": pattern.get_size().y}},
        "cells_in_pattern": pattern_cells.size(),
        "pattern_path": pattern_path,
        "tileset_pattern_index": pattern_index
    }}
    
    print("TEST_OUTPUT: " + JSON.stringify(result))
    quit()
'''

SET_PATTERN_SCRIPT = '''
extends SceneTree

# Helper: set pattern on either TileMap (with layer) or TileMapLayer (no layer)
func _set_pattern(tilemap, layer: int, pos: Vector2i, pattern):
    if tilemap is TileMap:
        tilemap.set_pattern(layer, pos, pattern)
    else:
        tilemap.set_pattern(pos, pattern)

func _init():
    var scene_path = "{scene_path}"
    var tilemap_node_path = "{tilemap_node_path}"
    var layer = {layer}
    var position = {position_json}
    var pattern_index = {pattern_index}
    var pattern_path = "{pattern_path}"
    
    var scene = load(scene_path)
    if scene == null:
        print("TEST_OUTPUT: " + JSON.stringify({{
            "success": false,
            "error": "Failed to load scene"
        }}))
        quit()
        return
    
    var instance = scene.instantiate()
    var tilemap = instance.get_node(tilemap_node_path) if tilemap_node_path != "" else instance
    
    if tilemap == null or (not (tilemap is TileMap) and not (tilemap is TileMapLayer)):
        print("TEST_OUTPUT: " + JSON.stringify({{
            "success": false,
            "error": "Node is not TileMap or TileMapLayer: " + (tilemap.get_class() if tilemap else "null")
        }}))
        quit()
        return
    
    var pattern = null
    
    # Try pattern_path first (most reliable)
    if pattern_path != "":
        pattern = load(pattern_path)
        if pattern == null:
            print("TEST_OUTPUT: " + JSON.stringify({{
                "success": false,
                "error": "Failed to load pattern from: " + pattern_path
            }}))
            quit()
            return
    else:
        # Fallback to tileset index
        var tileset = tilemap.tile_set
        if tileset == null:
            print("TEST_OUTPUT: " + JSON.stringify({{
                "success": false,
                "error": "TileMap has no TileSet"
            }}))
            quit()
            return
        
        pattern = tileset.get_pattern(pattern_index)
        if pattern == null:
            print("TEST_OUTPUT: " + JSON.stringify({{
                "success": false,
                "error": "Pattern not found at index: " + str(pattern_index)
            }}))
            quit()
            return
    
    var pos = Vector2i(position.x, position.y)
    _set_pattern(tilemap, layer, pos, pattern)
    
    # Save
    var packed = PackedScene.new()
    var err = packed.pack(instance)
    if err == OK:
        ResourceSaver.save(packed, scene_path)
    
    print("TEST_OUTPUT: " + JSON.stringify({{
        "success": true,
        "position": {{"x": pos.x, "y": pos.y}},
        "pattern_size": {{"x": pattern.get_size().x, "y": pattern.get_size().y}}
    }}))
    quit()
'''

# Script para renderizar atlas del TileSet con grid numerado
RENDER_TILESET_ATLAS_SCRIPT = '''
extends SceneTree

func _generate_ascii_preview(image, max_width: int = 80, max_height: int = 40) -> String:
    var w = image.get_width()
    var h = image.get_height()
    var step_x = max(1, w / max_width)
    var step_y = max(1, h / max_height)
    var chars = " .:-=+*#%@"
    var result = ""
    for y in range(0, h, step_y):
        var line = ""
        for x in range(0, w, step_x):
            var color = image.get_pixel(x, y)
            var brightness = (color.r + color.g + color.b) / 3.0
            var idx = int(brightness * (chars.length() - 1))
            line += chars[idx]
        result += line + "\\n"
    return result

func _init():
    var tileset_path = "{tileset_path}"
    var output_path = "{output_path}"
    var format = "{format}"
    var quality = {quality}
    var return_preview = {return_preview}
    
    if DisplayServer.get_name() == "headless":
        print("TEST_OUTPUT: " + JSON.stringify({{
            "success": false,
            "error": "Cannot render atlas in headless mode. Use a project with display server enabled."
        }}))
        quit()
        return
    
    var tileset = load(tileset_path)
    if tileset == null or not (tileset is TileSet):
        print("TEST_OUTPUT: " + JSON.stringify({{
            "success": false,
            "error": "Failed to load TileSet: " + tileset_path
        }}))
        quit()
        return
    
    # Find first atlas source
    var atlas_source = null
    var source_id = -1
    for i in range(tileset.get_source_count()):
        var sid = tileset.get_source_id(i)
        var source = tileset.get_source(sid)
        if source is TileSetAtlasSource:
            atlas_source = source
            source_id = sid
            break
    
    if atlas_source == null or atlas_source.texture == null:
        print("TEST_OUTPUT: " + JSON.stringify({{
            "success": false,
            "error": "No atlas source with texture found in TileSet"
        }}))
        quit()
        return
    
    var texture = atlas_source.texture
    var tex_size = texture.get_size()
    var tile_size = atlas_source.texture_region_size
    var margin = Vector2i(40, 30)
    
    # Grid dimensions
    var cols = 0
    var rows = 0
    if tile_size.x > 0 and tile_size.y > 0:
        cols = int((tex_size.x - atlas_source.margins.x + atlas_source.separation.x) / (tile_size.x + atlas_source.separation.x))
        rows = int((tex_size.y - atlas_source.margins.y + atlas_source.separation.y) / (tile_size.y + atlas_source.separation.y))
    
    # Create viewport
    var viewport = SubViewport.new()
    viewport.size = Vector2i(tex_size.x + margin.x, tex_size.y + margin.y)
    viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
    get_root().add_child(viewport)
    
    # Background
    var bg = ColorRect.new()
    bg.color = Color(0.1, 0.1, 0.1, 1.0)
    bg.size = viewport.size
    viewport.add_child(bg)
    
    # Atlas texture
    var sprite = TextureRect.new()
    sprite.texture = texture
    sprite.position = Vector2(margin.x, margin.y)
    viewport.add_child(sprite)
    
    # Grid lines and labels
    var grid_color = Color(1, 0, 0, 0.5)
    var text_color = Color(1, 1, 1, 1)
    
    # Vertical lines and X labels
    for x in range(0, int(tex_size.x) + 1, int(tile_size.x)):
        var line = Line2D.new()
        line.default_color = grid_color
        line.width = 1
        line.points = PackedVector2Array([
            Vector2(margin.x + x, margin.y),
            Vector2(margin.x + x, margin.y + tex_size.y)
        ])
        viewport.add_child(line)
        
        if x < tex_size.x:
            var label = Label.new()
            label.text = str(x / int(tile_size.x))
            label.position = Vector2(margin.x + x + 2, 2)
            label.add_theme_color_override("font_color", text_color)
            label.add_theme_font_size_override("font_size", 10)
            viewport.add_child(label)
    
    # Horizontal lines and Y labels
    for y in range(0, int(tex_size.y) + 1, int(tile_size.y)):
        var line = Line2D.new()
        line.default_color = grid_color
        line.width = 1
        line.points = PackedVector2Array([
            Vector2(margin.x, margin.y + y),
            Vector2(margin.x + tex_size.x, margin.y + y)
        ])
        viewport.add_child(line)
        
        if y < tex_size.y:
            var label = Label.new()
            label.text = str(y / int(tile_size.y))
            label.position = Vector2(2, margin.y + y + 2)
            label.add_theme_color_override("font_color", text_color)
            label.add_theme_font_size_override("font_size", 10)
            viewport.add_child(label)
    
    # Wait for render
    for i in range(3):
        await self.process_frame
    
    # Capture
    var captured = viewport.get_texture().get_image()
    
    # Save
    var err = OK
    if format == "jpg" or format == "jpeg":
        var buffer = captured.save_jpg_to_buffer(quality)
        var file = FileAccess.open(output_path, FileAccess.WRITE)
        if file:
            file.store_buffer(buffer)
            file.close()
        else:
            err = FAILED
    elif format == "webp":
        err = captured.save_webp(output_path, true, quality)
    else:
        err = captured.save_png(output_path)
    
    if err == OK:
        var result = {{
            "success": true,
            "image_path": output_path,
            "resolution": [captured.get_width(), captured.get_height()],
            "tileset_path": tileset_path,
            "source_id": source_id,
            "texture_size": {{"x": tex_size.x, "y": tex_size.y}},
            "tile_size": {{"x": tile_size.x, "y": tile_size.y}},
            "grid_dimensions": {{"cols": cols, "rows": rows}},
            "format": format
        }}
        if return_preview:
            result["preview_ascii"] = _generate_ascii_preview(captured, 80, 40)
        print("TEST_OUTPUT: " + JSON.stringify(result))
    else:
        print("TEST_OUTPUT: " + JSON.stringify({{
            "success": false,
            "error": "Failed to save atlas image, error code: " + str(err)
        }}))
    
    quit()
'''


# ==================== HELPER ====================

def _extract_test_output(result: dict[str, Any]) -> Optional[dict[str, Any]]:
    """Extract TEST_OUTPUT from run_command result (for render_tileset_atlas)."""
    for line in result.get("prints", []):
        if line.startswith("TEST_OUTPUT:"):
            try:
                return json.loads(line[12:].strip())
            except json.JSONDecodeError:
                continue
    return None


def _add_visual_warning(response: dict[str, Any]) -> dict[str, Any]:
    """Add anti-hallucination warning to successful visual tool responses."""
    if response.get("success"):
        response["agent_visual_access"] = False
        response["user_action_required"] = VISUAL_ACCESS_WARNING
    return response


# ==================== TOOLS ====================


def inspect_tileset(
    project_path: str,
    tileset_path: str,
    godot_path: Optional[str] = None,
    timeout: int = 30,
) -> dict[str, Any]:
    """
    Inspect a TileSet resource and return detailed information.

    Uses Godot runtime to load the TileSet and extract:
    - Sources (atlas, scenes) with tile counts, texture sizes, grid dimensions
    - Terrain sets and terrains
    - Patterns
    - Layer counts (physics, navigation, custom data)

    Args:
        project_path: Absolute path to the Godot project.
        tileset_path: Path to the TileSet (.tres or res://).
        godot_path: Optional path to Godot executable.
        timeout: Maximum seconds to wait.

    Returns:
        Dict with success, tile_size, sources (with texture_size, grid_dimensions),
        terrain_sets, patterns, etc.

    Example:
        inspect_tileset("D:/MyGame", "res://tilesets/ground.tres")
    """
    script = INSPECT_TILESET_SCRIPT.format(tileset_path=tileset_path)
    result = run_gdscript(project_path, script, godot_path, timeout)
    
    if result.get("test_output") and isinstance(result["test_output"], dict):
        return result["test_output"]
    
    return {
        "success": False,
        "error": "Failed to inspect TileSet",
        "raw_output": result.get("output", []),
        "errors": result.get("errors", []),
    }


def inspect_tilemap(
    project_path: str,
    scene_path: str,
    tilemap_node_path: str = "",
    godot_path: Optional[str] = None,
    timeout: int = 30,
) -> dict[str, Any]:
    """
    Inspect a TileMap node in a scene.

    Uses Godot runtime to load the scene and extract:
    - Layer configuration (name, enabled, z-index, y-sort, modulate)
    - Sample of used cells (first 100)
    - Used rect
    - ASCII art representation of the tilemap
    - TileSet reference

    Args:
        project_path: Absolute path to the Godot project.
        scene_path: Path to the scene (res://...).
        tilemap_node_path: NodePath to the TileMap (empty if root).
        godot_path: Optional path to Godot executable.
        timeout: Maximum seconds to wait.

    Returns:
        Dict with success, layer_count, layers, used_cells_sample, used_rect,
        ascii_map, ascii_map_truncated, tileset.

    Example:
        inspect_tilemap("D:/MyGame", "res://scenes/Level.tscn", "TileMap")
    """
    script = INSPECT_TILEMAP_SCRIPT.format(
        scene_path=scene_path,
        tilemap_node_path=tilemap_node_path,
    )
    result = run_gdscript(project_path, script, godot_path, timeout)
    
    if result.get("test_output") and isinstance(result["test_output"], dict):
        output = result["test_output"]
        # Build ascii_map from ascii_lines (GDScript can't safely include newlines in JSON)
        if "ascii_lines" in output and "ascii_map" not in output:
            output["ascii_map"] = "\n".join(output["ascii_lines"])
        return output
    
    return {
        "success": False,
        "error": "Failed to inspect TileMap",
        "raw_output": result.get("output", []),
        "errors": result.get("errors", []),
    }


def set_tilemap_cells(
    project_path: str,
    scene_path: str,
    cells: list[dict[str, Any]],
    layer: int = 0,
    tilemap_node_path: str = "",
    godot_path: Optional[str] = None,
    timeout: int = 30,
) -> dict[str, Any]:
    """
    Set or erase cells in a TileMap.

    Args:
        project_path: Absolute path to the Godot project.
        scene_path: Path to the scene (res://...).
        cells: List of cell definitions. Each dict has:
            - coords: {"x": int, "y": int} (required)
            - source_id: int (optional, -1 to erase)
            - atlas_coords: {"x": int, "y": int} (optional)
            - alternative_tile: int (optional, default 0)
            - erase: bool (optional, if true erases the cell)
        layer: Layer index.
        tilemap_node_path: NodePath to the TileMap (empty if root).
        godot_path: Optional path to Godot executable.
        timeout: Maximum seconds to wait.

    Returns:
        Dict with success, cells_changed.

    Example:
        set_tilemap_cells(
            project_path="D:/MyGame",
            scene_path="res://scenes/Level.tscn",
            cells=[
                {"coords": {"x": 0, "y": 0}, "source_id": 1, "atlas_coords": {"x": 1, "y": 2}},
                {"coords": {"x": 1, "y": 0}, "erase": true}
            ]
        )
    """
    script = SET_TILEMAP_CELLS_SCRIPT.format(
        scene_path=scene_path,
        tilemap_node_path=tilemap_node_path,
        layer=layer,
        cells_json=json.dumps(cells),
    )
    result = run_gdscript(project_path, script, godot_path, timeout)
    
    if result.get("test_output") and isinstance(result["test_output"], dict):
        return result["test_output"]
    
    return {
        "success": False,
        "error": "Failed to set TileMap cells",
        "raw_output": result.get("output", []),
        "errors": result.get("errors", []),
    }


def set_tilemap_layer_properties(
    project_path: str,
    scene_path: str,
    layer: int,
    properties: dict[str, Any],
    tilemap_node_path: str = "",
    godot_path: Optional[str] = None,
    timeout: int = 30,
) -> dict[str, Any]:
    """
    Configure properties of a TileMap layer.

    Args:
        project_path: Absolute path to the Godot project.
        scene_path: Path to the scene (res://...).
        layer: Layer index.
        properties: Dict of properties to set:
            - name: str
            - enabled: bool
            - modulate: {"r": float, "g": float, "b": float, "a": float}
            - y_sort_enabled: bool
            - y_sort_origin: int
            - z_index: int
            - navigation_enabled: bool
        tilemap_node_path: NodePath to the TileMap (empty if root).
        godot_path: Optional path to Godot executable.
        timeout: Maximum seconds to wait.

    Returns:
        Dict with success, properties_applied.

    Example:
        set_tilemap_layer_properties(
            project_path="D:/MyGame",
            scene_path="res://scenes/Level.tscn",
            layer=0,
            properties={"z_index": 10, "y_sort_enabled": true}
        )
    """
    script = SET_LAYER_PROPERTIES_SCRIPT.format(
        scene_path=scene_path,
        tilemap_node_path=tilemap_node_path,
        layer=layer,
        properties_json=json.dumps(properties),
    )
    result = run_gdscript(project_path, script, godot_path, timeout)
    
    if result.get("test_output") and isinstance(result["test_output"], dict):
        return result["test_output"]
    
    return {
        "success": False,
        "error": "Failed to set layer properties",
        "raw_output": result.get("output", []),
        "errors": result.get("errors", []),
    }


def apply_tilemap_terrain(
    project_path: str,
    scene_path: str,
    cells: list[dict[str, int]],
    terrain_set: int,
    terrain: int,
    layer: int = 0,
    tilemap_node_path: str = "",
    ignore_empty_terrains: bool = True,
    godot_path: Optional[str] = None,
    timeout: int = 30,
) -> dict[str, Any]:
    """
    Apply terrain to a group of cells in a TileMap.

    Uses TileMap.set_cells_terrain_connect() for smart terrain connectivity.

    Args:
        project_path: Absolute path to the Godot project.
        scene_path: Path to the scene (res://...).
        cells: List of {"x": int, "y": int} coordinates.
        terrain_set: Terrain set index.
        terrain: Terrain index within the set.
        layer: Layer index.
        tilemap_node_path: NodePath to the TileMap (empty if root).
        ignore_empty_terrains: Whether to ignore empty terrains.
        godot_path: Optional path to Godot executable.
        timeout: Maximum seconds to wait.

    Returns:
        Dict with success, cells_affected.

    Example:
        apply_tilemap_terrain(
            project_path="D:/MyGame",
            scene_path="res://scenes/Level.tscn",
            cells=[{"x": 0, "y": 0}, {"x": 1, "y": 0}, {"x": 0, "y": 1}],
            terrain_set=0,
            terrain=1
        )
    """
    script = APPLY_TERRAIN_SCRIPT.format(
        scene_path=scene_path,
        tilemap_node_path=tilemap_node_path,
        layer=layer,
        cells_json=json.dumps(cells),
        terrain_set=terrain_set,
        terrain=terrain,
        ignore_empty=str(ignore_empty_terrains).lower(),
    )
    result = run_gdscript(project_path, script, godot_path, timeout)
    
    if result.get("test_output") and isinstance(result["test_output"], dict):
        return result["test_output"]
    
    return {
        "success": False,
        "error": "Failed to apply terrain",
        "raw_output": result.get("output", []),
        "errors": result.get("errors", []),
    }


def create_tilemap_pattern(
    project_path: str,
    scene_path: str,
    rect: dict[str, int],
    layer: int = 0,
    tilemap_node_path: str = "",
    pattern_name: str = "",
    godot_path: Optional[str] = None,
    timeout: int = 30,
) -> dict[str, Any]:
    """
    Create a TileMapPattern from a rectangular region of cells.

    Args:
        project_path: Absolute path to the Godot project.
        scene_path: Path to the scene (res://...).
        rect: Rectangle {"x": int, "y": int, "width": int, "height": int}.
        layer: Layer index.
        tilemap_node_path: NodePath to the TileMap (empty if root).
        pattern_name: Optional name for the pattern.
        godot_path: Optional path to Godot executable.
        timeout: Maximum seconds to wait.

    Returns:
        Dict with success, pattern_size, tileset_pattern_index.

    Example:
        create_tilemap_pattern(
            project_path="D:/MyGame",
            scene_path="res://scenes/Level.tscn",
            rect={"x": 0, "y": 0, "width": 4, "height": 4}
        )
    """
    script = CREATE_PATTERN_SCRIPT.format(
        scene_path=scene_path,
        tilemap_node_path=tilemap_node_path,
        layer=layer,
        rect_json=json.dumps(rect),
        pattern_name=pattern_name,
    )
    result = run_gdscript(project_path, script, godot_path, timeout)
    
    if result.get("test_output") and isinstance(result["test_output"], dict):
        return result["test_output"]
    
    return {
        "success": False,
        "error": "Failed to create pattern",
        "raw_output": result.get("output", []),
        "errors": result.get("errors", []),
    }


def set_tilemap_pattern(
    project_path: str,
    scene_path: str,
    position: dict[str, int],
    pattern_index: int = -1,
    pattern_path: str = "",
    layer: int = 0,
    tilemap_node_path: str = "",
    godot_path: Optional[str] = None,
    timeout: int = 30,
) -> dict[str, Any]:
    """
    Apply a TileMapPattern at a specific position.

    Supports two ways to reference the pattern:
    - pattern_path: Path to a saved .tres pattern file (recommended, most reliable)
    - pattern_index: Index of the pattern in the TileSet (only works if TileSet is external .tres)

    Args:
        project_path: Absolute path to the Godot project.
        scene_path: Path to the scene (res://...).
        position: {"x": int, "y": int} where to place the pattern.
        pattern_index: Index of the pattern in the TileSet. Use -1 if providing pattern_path.
        pattern_path: Path to a .tres pattern file (e.g., "res://patterns/my_pattern.tres").
                      Preferred over pattern_index for reliability.
        layer: Layer index.
        tilemap_node_path: NodePath to the TileMap (empty if root).
        godot_path: Optional path to Godot executable.
        timeout: Maximum seconds to wait.

    Returns:
        Dict with success, position, pattern_size.

    Example:
        set_tilemap_pattern(
            project_path="D:/MyGame",
            scene_path="res://scenes/Level.tscn",
            position={"x": 10, "y": 10},
            pattern_path="res://patterns/room_corner.tres"
        )
    """
    if pattern_index < 0 and not pattern_path:
        return {
            "success": False,
            "error": "Provide either pattern_index or pattern_path",
        }
    
    script = SET_PATTERN_SCRIPT.format(
        scene_path=scene_path,
        tilemap_node_path=tilemap_node_path,
        layer=layer,
        position_json=json.dumps(position),
        pattern_index=pattern_index,
        pattern_path=pattern_path,
    )
    result = run_gdscript(project_path, script, godot_path, timeout)
    
    if result.get("test_output") and isinstance(result["test_output"], dict):
        return result["test_output"]
    
    return {
        "success": False,
        "error": "Failed to set pattern",
        "raw_output": result.get("output", []),
        "errors": result.get("errors", []),
    }


def render_tileset_atlas(
    project_path: str,
    tileset_path: str,
    output_path: Optional[str] = None,
    format: str = "jpeg",
    quality: float = 0.85,
    return_preview: bool = False,
    godot_path: Optional[str] = None,
    timeout: int = 60,
) -> dict[str, Any]:
    """
    Render an image of the TileSet atlas with a numbered grid overlay.

    Creates a visual reference showing the atlas texture with red grid lines
    and coordinate labels, making it easy to identify which atlas_coords
    correspond to which tile visually.

    IMPORTANT: The agent CANNOT see the generated image. If visual analysis is
    needed, the user must attach the image manually.

    Args:
        project_path: Absolute path to the Godot project.
        tileset_path: Path to the TileSet (.tres or res://...).
        output_path: Where to save the image. If None, uses temp directory.
        format: Image format: "png", "jpeg" (default), or "webp".
        quality: JPEG/WebP quality (0.0-1.0). Default: 0.85.
        return_preview: If True, generates an ASCII art preview.
        godot_path: Optional path to Godot executable.
        timeout: Maximum seconds to wait.

    Returns:
        Dict with success, image_path, resolution, texture_size, tile_size,
        grid_dimensions, format, and optionally preview_ascii.
        Includes anti-hallucination warning.

    Example:
        render_tileset_atlas(
            project_path="D:/MyGame",
            tileset_path="res://tilesets/ground.tres",
            output_path="D:/tmp/atlas.jpg"
        )
    """
    cli = GodotCLIWrapper(godot_path)
    
    is_valid, error = cli.validate_project(project_path)
    if not is_valid:
        return {"success": False, "error": error}
    
    if not output_path:
        ext = ".jpg" if format in ("jpeg", "jpg") else (".webp" if format == "webp" else ".png")
        output_path = os.path.join(
            tempfile.gettempdir(), f"tileset_atlas_{os.getpid()}{ext}"
        )
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    script = RENDER_TILESET_ATLAS_SCRIPT.format(
        tileset_path=tileset_path,
        output_path=output_path.replace("\\", "/"),
        format=format,
        quality=quality,
        return_preview=str(return_preview).lower(),
    )
    
    # Run WITHOUT --headless to allow GPU rendering
    script_file = os.path.join(tempfile.gettempdir(), f"atlas_script_{os.getpid()}.gd")
    try:
        with open(script_file, "w", encoding="utf-8") as f:
            f.write(script)
        
        args = ["--script", script_file]
        result = cli.run_command(args, project_path=project_path, timeout=timeout)
        
        test_output = _extract_test_output(result)
        
        if test_output and isinstance(test_output, dict):
            if test_output.get("success"):
                return _add_visual_warning(test_output)
            return test_output
        
        for line in result.get("prints", []):
            if "headless" in line.lower():
                return {
                    "success": False,
                    "error": "Atlas rendering requires a display/GPU.",
                    "raw_output": result.get("prints", []),
                }
        
        return {
            "success": False,
            "error": "Atlas rendering failed",
            "raw_output": result.get("prints", []),
            "errors": result.get("errors", []),
        }
    
    finally:
        try:
            if os.path.exists(script_file):
                os.remove(script_file)
        except:
            pass
        cli.cleanup()


# ==================== REGISTRATION ====================


def register_tilemap_tools(mcp) -> None:
    """Register all TileMap tools."""
    logger.info("Registrando tilemap tools...")
    
    mcp.add_tool(inspect_tileset)
    mcp.add_tool(inspect_tilemap)
    mcp.add_tool(set_tilemap_cells)
    mcp.add_tool(set_tilemap_layer_properties)
    mcp.add_tool(apply_tilemap_terrain)
    mcp.add_tool(create_tilemap_pattern)
    mcp.add_tool(set_tilemap_pattern)
    mcp.add_tool(render_tileset_atlas)
    
    logger.info("[OK] 8 tilemap tools registradas")
