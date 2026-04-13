"""
Godot MCP - Core Module

Módulo principal que exporta todas las funcionalidades core del servidor MCP:
- Modelos de datos Godot (Scene, Node, ExtResource, SubResource, PropertyValue)
- Parsers TSCN (parse_tscn, parse_tscn_string)
- Cache LRU (LRUCache, get_cache)
- Indexación de proyectos (build_index, get_index)

Ejemplo de uso:
    >>> from godot_mcp.core import (
    ...     Scene, Node, ExtResource, SubResource, PropertyValue,
    ...     parse_tscn, parse_tscn_string,
    ...     LRUCache, get_cache,
    ...     build_index, get_index
    ... )

    >>> # Parsear una escena desde archivo
    >>> scene = parse_tscn("res://scenes/Player.tscn")
    >>> print(scene.root_type)
    'CharacterBody2D'

    >>> # Parsear directamente desde string TSCN
    >>> content = '''[gd_scene load_steps=2 format=3]
    ... [ext_resource path="res://player.gd" type="Script"]
    ... [node name="Player" type="CharacterBody2D"]
    ... '''
    >>> scene = parse_tscn_string(content)

    >>> # Usar cache LRU
    >>> cache = get_cache()
    >>> cached = cache.get("scene:Player", lambda: parse_tscn("res://scenes/Player.tscn"))

    >>> # Indexar proyecto
    >>> index = build_index("D:/MyGame")
    >>> scenes = index.list_scenes()
    >>> print(f"Indexadas {len(scenes)} escenas")
"""

# =============================================================================
# Models - Modelos de datos Godot
# =============================================================================

from godot_mcp.core.models import (
    Scene,
    Node,
    ExtResource,
    SubResource,
    PropertyValue,
)

# =============================================================================
# TSCN Parser - Parseo de archivos .tscn
# =============================================================================

from godot_mcp.core.tscn_parser import (
    parse_tscn,
    parse_tscn_string,
)

# =============================================================================
# Cache - Sistema de caché LRU
# =============================================================================

from godot_mcp.core.cache import (
    LRUCache,
    get_cache,
)

# =============================================================================
# Project Index - Indexación de proyectos
# =============================================================================

from godot_mcp.core.project_index import (
    build_index,
    get_index,
    ProjectIndex,
    ScriptInfo,
    SceneInfo,
    ResourceInfo,
    find_scenes_using_resource,
    find_scripts_extending,
    search_by_type,
    invalidate_file,
    get_unused_resources,
    start_watchdog,
    stop_watchdog,
)

__all__ = [
    # Models
    "Scene",
    "Node",
    "ExtResource",
    "SubResource",
    "PropertyValue",
    # Parser
    "parse_tscn",
    "parse_tscn_string",
    # Cache
    "LRUCache",
    "get_cache",
    # Index
    "build_index",
    "get_index",
    "ProjectIndex",
    "ScriptInfo",
    "SceneInfo",
    "ResourceInfo",
    "find_scenes_using_resource",
    "find_scripts_extending",
    "search_by_type",
    "invalidate_file",
    "get_unused_resources",
    "start_watchdog",
    "stop_watchdog",
]
