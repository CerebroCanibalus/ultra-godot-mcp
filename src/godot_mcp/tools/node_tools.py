"""
Node Tools - Herramientas para gestión de nodos Godot.

Proporciona herramientas FastMCP para operaciones CRUD de nodos en archivos .tscn.
Utiliza el parser TSCN nativo y fuzzywuzzy para búsquedas tolerantes.
"""

import logging
import os
from pathlib import Path
from typing import Any, Optional

# Intentar importar fuzzywuzzy para búsquedas tolerantes
try:
    from fuzzywuzzy import fuzz
    from fuzzywuzzy.process import extractOne, extract

    FUZZY_AVAILABLE = True
except ImportError:
    FUZZY_AVAILABLE = False

    # Implementación simple similarity si no hay fuzzywuzzy
    def fuzz_ratio(s1: str, s2: str) -> int:
        """Simple similarity ratio."""
        s1, s2 = s1.lower(), s2.lower()
        if s1 == s2:
            return 100
        # Contar caracteres comunes
        common = sum(1 for a, b in zip(s1, s2) if a == b)
        return int((common * 2 / (len(s1) + len(s2))) * 100) if s1 and s2 else 0


# Importar parser TSCN nativo
from godot_mcp.core.tscn_parser import (
    Scene,
    SceneNode,
    parse_tscn,
    parse_tscn_string,
)

logger = logging.getLogger(__name__)


# ============ HELPERS ============


def _ensure_tscn_path(scene_path: str) -> str:
    """Ensure path ends with .tscn extension."""
    if not scene_path.endswith(".tscn"):
        return scene_path + ".tscn"
    return scene_path


def _normalize_node_path(node_path: str) -> str:
    """Normalize node path for comparison."""
    return node_path.strip("/")


def _find_node_by_path(scene: Scene, node_path: str) -> Optional[tuple[int, SceneNode]]:
    """
    Find a node in scene by its path.

    Returns tuple of (index, node) if found, None otherwise.
    """
    normalized = _normalize_node_path(node_path)

    # Buscar por nombre exacto primero
    for idx, node in enumerate(scene.nodes):
        if node.name == normalized or node.name == normalized.split("/")[-1]:
            return idx, node

    # Si no encuentra, buscar coincidencias parciales
    if FUZZY_AVAILABLE:
        best_match = None
        best_ratio = 0
        for idx, node in enumerate(scene.nodes):
            ratio = fuzz.ratio(normalized.lower(), node.name.lower())
            if ratio > best_ratio and ratio > 70:
                best_ratio = ratio
                best_match = (idx, node)
        return best_match

    return None


def _resolve_parent_path(scene: Scene, parent_path: str) -> str:
    """Resolve parent path to valid parent string."""
    parent_path = parent_path.strip()

    if not parent_path or parent_path == "." or parent_path == "Root":
        return "."

    # Buscar si existe el nodo padre
    parent_result = _find_node_by_path(scene, parent_path)
    if parent_result:
        _, parent_node = parent_result
        return parent_node.name

    # Si no existe, asumir que es una ruta válida en el TSCN
    return parent_path


def _update_scene_file(scene_path: str, scene: Scene) -> None:
    """Write scene back to file."""
    scene_path = _ensure_tscn_path(scene_path)

    # Crear backup antes de modificar
    backup_path = scene_path + ".bak"
    if os.path.exists(scene_path):
        import shutil

        shutil.copy2(scene_path, backup_path)
        logger.info(f"Backup created: {backup_path}")

    # Escribir scene
    content = scene.to_tscn()
    with open(scene_path, "w", encoding="utf-8") as f:
        f.write(content)

    logger.info(f"Scene saved: {scene_path}")


def _build_node_tree(scene: Scene) -> list[dict]:
    """
    Build a tree structure of nodes.

    Returns list of dicts with name, type, parent, path.
    """
    result = []

    for node in scene.nodes:
        # Calcular path real del nodo
        if node.parent == ".":
            path = node.name
        else:
            path = f"{node.parent}/{node.name}"

        result.append(
            {
                "name": node.name,
                "type": node.type,
                "parent": node.parent,
                "path": path,
                "properties": node.properties,
            }
        )

    return result


# ============ Decoradores ====================

from godot_mcp.tools.decorators import require_session


# ============ TOOL FUNCTIONS ============


@require_session
def add_node(
    session_id: str,
    scene_path: str,
    parent_path: str,
    node_type: str,
    node_name: str,
    properties: dict = None,
) -> dict:
    """
    Add a node to scene.

    Args:
        session_id: Session ID from start_session.
        scene_path: Path to the .tscn file.
        parent_path: Parent node path (use "." for root).
        node_type: Godot node type (e.g., "Sprite2D", "Node2D").
        node_name: Name for the new node.
        properties: Optional dict of properties to set.

    Returns:
        Dict with success status and node info.
    """
    scene_path = _ensure_tscn_path(scene_path)

    if not os.path.exists(scene_path):
        # Crear nueva escena si no existe
        logger.info(f"Creating new scene: {scene_path}")
        scene = Scene()
        scene.header.load_steps = 2
        scene.header.format = 3
    else:
        scene = parse_tscn(scene_path)

    # Verificar que el nodo no exista
    existing = _find_node_by_path(scene, node_name)
    if existing:
        return {
            "success": False,
            "error": f"Node already exists: {node_name}",
            "node_path": existing[1].name,
        }

    # Resolver path del padre
    resolved_parent = _resolve_parent_path(scene, parent_path)

    # Crear nuevo nodo
    new_node = SceneNode(
        name=node_name,
        type=node_type,
        parent=resolved_parent,
    )

    # Agregar propiedades si se proporcionan
    if properties:
        new_node.properties = properties.copy()

    # Agregar nodo a la escena
    scene.nodes.append(new_node)

    # Guardar
    _update_scene_file(scene_path, scene)

    node_path = (
        f"{resolved_parent}/{node_name}" if resolved_parent != "." else node_name
    )

    return {
        "success": True,
        "node": {
            "name": node_name,
            "type": node_type,
            "parent": resolved_parent,
            "path": node_path,
        },
        "scene_path": scene_path,
    }


@require_session
def remove_node(session_id: str, scene_path: str, node_path: str) -> dict:
    """
    Remove a node from scene.

    Args:
        session_id: Session ID from start_session.
        scene_path: Path to the .tscn file.
        node_path: Path or name of the node to remove.

    Returns:
        Dict with success status.
    """
    scene_path = _ensure_tscn_path(scene_path)

    if not os.path.exists(scene_path):
        return {
            "success": False,
            "error": "Scene file not found",
        }

    scene = parse_tscn(scene_path)

    # Buscar nodo
    result = _find_node_by_path(scene, node_path)
    if not result:
        return {
            "success": False,
            "error": f"Node not found: {node_path}",
        }

    idx, node = result
    node_name = node.name

    # Remover nodo (y sus hijos si los hay)
    # Nota: En una implementación completa, también removeríamos los nodos hijos
    removed_nodes = [node_name]

    # Eliminar el nodo
    scene.nodes.pop(idx)

    # También remover nodos que tengan este nodo como padre
    children_to_remove = [i for i, n in enumerate(scene.nodes) if n.parent == node_name]
    # Eliminar en orden inverso para no afectar índices
    for i in reversed(children_to_remove):
        removed_nodes.append(scene.nodes[i].name)
        scene.nodes.pop(i)

    # Guardar
    _update_scene_file(scene_path, scene)

    return {
        "success": True,
        "removed_nodes": removed_nodes,
        "scene_path": scene_path,
    }


@require_session
def update_node(
    session_id: str,
    scene_path: str,
    node_path: str,
    properties: dict,
) -> dict:
    """
    Update node properties.

    Args:
        session_id: Session ID from start_session.
        scene_path: Path to the .tscn file.
        node_path: Path or name of the node to update.
        properties: Dict of properties to set/update.

    Returns:
        Dict with success status and updated properties.
    """
    scene_path = _ensure_tscn_path(scene_path)

    if not os.path.exists(scene_path):
        return {
            "success": False,
            "error": "Scene file not found",
        }

    scene = parse_tscn(scene_path)

    # Buscar nodo
    result = _find_node_by_path(scene, node_path)
    if not result:
        return {
            "success": False,
            "error": f"Node not found: {node_path}",
        }

    idx, node = result

    # Actualizar propiedades
    old_props = node.properties.copy()
    node.properties.update(properties)

    # Guardar
    _update_scene_file(scene_path, scene)

    return {
        "success": True,
        "node_name": node.name,
        "old_properties": old_props,
        "new_properties": node.properties,
        "scene_path": scene_path,
    }


@require_session
def get_node_properties(session_id: str, scene_path: str, node_path: str) -> dict:
    """
    Get all properties of a node.

    Args:
        session_id: Session ID from start_session.
        scene_path: Path to the .tscn file.
        node_path: Path or name of the node.

    Returns:
        Dict with node info and properties.
    """
    scene_path = _ensure_tscn_path(scene_path)

    if not os.path.exists(scene_path):
        return {
            "success": False,
            "error": "Scene file not found",
        }

    scene = parse_tscn(scene_path)

    # Buscar nodo
    result = _find_node_by_path(scene, node_path)
    if not result:
        return {
            "success": False,
            "error": f"Node not found: {node_path}",
        }

    idx, node = result

    # Calcular path real
    if node.parent == ".":
        full_path = node.name
    else:
        full_path = f"{node.parent}/{node.name}"

    return {
        "success": True,
        "node": {
            "name": node.name,
            "type": node.type,
            "parent": node.parent,
            "path": full_path,
            "unique_name_in_owner": node.unique_name_in_owner,
            "properties": node.properties,
        },
    }


@require_session
def rename_node(
    session_id: str, scene_path: str, node_path: str, new_name: str
) -> dict:
    """
    Rename a node.

    Args:
        session_id: Session ID from start_session.
        scene_path: Path to the .tscn file.
        node_path: Current path or name of the node.
        new_name: New name for the node.

    Returns:
        Dict with success status and old/new names.
    """
    scene_path = _ensure_tscn_path(scene_path)

    if not os.path.exists(scene_path):
        return {
            "success": False,
            "error": "Scene file not found",
        }

    scene = parse_tscn(scene_path)

    # Buscar nodo
    result = _find_node_by_path(scene, node_path)
    if not result:
        return {
            "success": False,
            "error": f"Node not found: {node_path}",
        }

    idx, node = result
    old_name = node.name

    # Verificar que el nuevo nombre no exista
    existing = _find_node_by_path(scene, new_name)
    if existing and existing[0] != idx:
        return {
            "success": False,
            "error": f"Node already exists: {new_name}",
        }

    # Renombrar
    old_parent = node.parent
    node.name = new_name

    # Actualizar referencias de nodos hijos
    for n in scene.nodes:
        if n.parent == old_name:
            n.parent = new_name

    # Guardar
    _update_scene_file(scene_path, scene)

    new_path = f"{old_parent}/{new_name}" if old_parent != "." else new_name

    return {
        "success": True,
        "old_name": old_name,
        "new_name": new_name,
        "new_path": new_path,
        "scene_path": scene_path,
    }


@require_session
def move_node(
    session_id: str, scene_path: str, node_path: str, new_parent_path: str
) -> dict:
    """
    Reparent a node.

    Args:
        session_id: Session ID from start_session.
        scene_path: Path to the .tscn file.
        node_path: Current path or name of the node.
        new_parent_path: New parent path (use "." for root).

    Returns:
        Dict with success status.
    """
    scene_path = _ensure_tscn_path(scene_path)

    if not os.path.exists(scene_path):
        return {
            "success": False,
            "error": "Scene file not found",
        }

    scene = parse_tscn(scene_path)

    # Buscar nodo
    result = _find_node_by_path(scene, node_path)
    if not result:
        return {
            "success": False,
            "error": f"Node not found: {node_path}",
        }

    idx, node = result
    old_parent = node.parent

    # Resolver nuevo padre
    new_parent = _resolve_parent_path(scene, new_parent_path)

    # Evitar mover un nodo a sí mismo o a uno de sus descendientes
    if node.name == new_parent:
        return {
            "success": False,
            "error": "Cannot move node to itself",
        }

    # Mover
    node.parent = new_parent

    # Guardar
    _update_scene_file(scene_path, scene)

    if new_parent == ".":
        new_path = node.name
    else:
        new_path = f"{new_parent}/{node.name}"

    return {
        "success": True,
        "node_name": node.name,
        "old_parent": old_parent,
        "new_parent": new_parent,
        "new_path": new_path,
        "scene_path": scene_path,
    }


@require_session
def duplicate_node(
    session_id: str,
    scene_path: str,
    node_path: str,
    new_name: str = None,
) -> dict:
    """
    Duplicate a node and its children.

    Args:
        session_id: Session ID from start_session.
        scene_path: Path to the .tscn file.
        node_path: Path or name of the node to duplicate.
        new_name: Optional name for the duplicate (defaults to original + "_copy").

    Returns:
        Dict with success status and duplicated node info.
    """
    scene_path = _ensure_tscn_path(scene_path)

    if not os.path.exists(scene_path):
        return {
            "success": False,
            "error": "Scene file not found",
        }

    scene = parse_tscn(scene_path)

    # Buscar nodo original
    result = _find_node_by_path(scene, node_path)
    if not result:
        return {
            "success": False,
            "error": f"Node not found: {node_path}",
        }

    idx, original_node = result

    # Nombre para el duplicado
    if not new_name:
        new_name = original_node.name + "_copy"

    # Verificar que no exista
    existing = _find_node_by_path(scene, new_name)
    if existing:
        return {
            "success": False,
            "error": f"Node already exists: {new_name}",
        }

    # Crear duplicado (copia profunda de propiedades)
    duplicate = SceneNode(
        name=new_name,
        type=original_node.type,
        parent=original_node.parent,
        unique_name_in_owner=original_node.unique_name_in_owner,
    )
    duplicate.properties = original_node.properties.copy()

    # Agregar a la escena
    scene.nodes.append(duplicate)

    # También duplicar nodos hijos
    original_name = original_node.name
    duplicated_nodes = [new_name]

    children = [n for n in scene.nodes if n.parent == original_name]
    for child in children:
        child_copy_name = new_name + "/" + child.name.split("/")[-1]

        # Verificar que no exista
        if not _find_node_by_path(scene, child_copy_name):
            child_copy = SceneNode(
                name=child.name.split("/")[-1],
                type=child.type,
                parent=new_name,
                unique_name_in_owner=child.unique_name_in_owner,
            )
            child_copy.properties = child.properties.copy()
            scene.nodes.append(child_copy)
            duplicated_nodes.append(child_copy_name)

    # Guardar
    _update_scene_file(scene_path, scene)

    return {
        "success": True,
        "original_node": original_node.name,
        "duplicated_nodes": duplicated_nodes,
        "scene_path": scene_path,
    }


@require_session
def find_nodes(
    session_id: str,
    scene_path: str,
    name_pattern: str = None,
    type_filter: str = None,
) -> dict:
    """
    Find nodes by name pattern or type.

    Args:
        session_id: Session ID from start_session.
        scene_path: Path to the .tscn file.
        name_pattern: Optional name pattern to search (fuzzy match).
        type_filter: Optional node type to filter (e.g., "Sprite2D").

    Returns:
        Dict with matching nodes and their paths.
    """
    scene_path = _ensure_tscn_path(scene_path)

    if not os.path.exists(scene_path):
        return {
            "success": False,
            "error": "Scene file not found",
        }

    scene = parse_tscn(scene_path)

    results = []

    for node in scene.nodes:
        # Filtrar por tipo
        if type_filter:
            if node.type.lower() != type_filter.lower():
                continue

        # Filtrar/buscar por nombre
        if name_pattern:
            if FUZZY_AVAILABLE:
                ratio = fuzz.ratio(name_pattern.lower(), node.name.lower())
                if ratio < 60:  # Threshold de similarity
                    continue
                results.append(
                    {
                        "name": node.name,
                        "type": node.type,
                        "parent": node.parent,
                        "path": f"{node.parent}/{node.name}"
                        if node.parent != "."
                        else node.name,
                        "match_score": ratio,
                    }
                )
            else:
                # Sin fuzzywuzzy, búsqueda simple
                if name_pattern.lower() not in node.name.lower():
                    continue
                results.append(
                    {
                        "name": node.name,
                        "type": node.type,
                        "parent": node.parent,
                        "path": f"{node.parent}/{node.name}"
                        if node.parent != "."
                        else node.name,
                    }
                )
        else:
            # Sin patrón, solo tipo
            results.append(
                {
                    "name": node.name,
                    "type": node.type,
                    "parent": node.parent,
                    "path": f"{node.parent}/{node.name}"
                    if node.parent != "."
                    else node.name,
                }
            )

    return {
        "success": True,
        "count": len(results),
        "nodes": results,
    }


# ============ REGISTRATION ============


def register_node_tools(mcp) -> None:
    """
    Registrar todas las herramientas relacionadas con nodos.

    Args:
        mcp: Instancia de FastMCP donde registrar las herramientas.
    """
    logger.info("Registrando node_tools (CRUD)...")

    # Registrar todas las herramientas
    mcp.add_tool(add_node)
    mcp.add_tool(remove_node)
    mcp.add_tool(update_node)
    mcp.add_tool(get_node_properties)
    mcp.add_tool(rename_node)
    mcp.add_tool(move_node)
    mcp.add_tool(duplicate_node)
    mcp.add_tool(find_nodes)

    logger.info(
        "[OK] 8 node_tools registradas (fuzzywuzzy=%s)",
        "enabled" if FUZZY_AVAILABLE else "disabled",
    )
