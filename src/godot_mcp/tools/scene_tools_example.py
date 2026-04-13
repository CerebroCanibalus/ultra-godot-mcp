"""
Ejemplo: Scene Tools con Arquitectura de Sesiones

Este archivo muestra cómo quedan las tools原有的 con session_id.
SCENE_TOOLS.PY ORIGINAL DEBE SER ACTUALIZADO A ESTE PATRÓN.
"""

from __future__ import annotations

import os
from typing import Any, Literal, Optional

from godot_mcp.core.tscn_parser import (
    GdSceneHeader,
    Scene,
    SceneNode,
    SubResource,
    parse_tscn,
)

# Import session manager y decorador
from godot_mcp.tools.session_tools import (
    get_session_manager,
    require_session,
)


# ==================== TOOLS CON session_id ====================


@require_session
def create_scene(
    session_id: str,
    scene_path: str,
    root_type: str = "Node2D",
    root_name: str = "Root",
) -> dict:
    """
    Crea una nueva escena .tscn en el proyecto.

    Args:
        session_id: ID de sesión activa.
        scene_path: Ruta relativa (res://Player.tscn) o nombre.
        root_type: Tipo del nodo raíz.
        root_name: Nombre del nodo raíz.

    Returns:
        Dict con éxito y datos de la escena creada.

    Flujo:
        1. Obtiene project_path de la sesión
        2. Valida que es un path relativo válido
        3. Crea la escena
        4. La carga en el workspace (dirty)
    """
    manager = get_session_manager()
    session = manager.get_session(session_id)

    if session is None:
        return {"success": False, "error": f"Session no encontrada: {session_id}"}

    project_path = session.project_path

    # Validar proyecto
    if not os.path.isdir(project_path):
        return {"success": False, "error": f"Proyecto no encontrado: {project_path}"}

    # Normalizar scene_path
    if not scene_path.endswith(".tscn"):
        scene_path = scene_path + ".tscn"

    full_scene_path = os.path.join(project_path, scene_path)

    # Ya existe?
    if os.path.isfile(full_scene_path):
        # Intentar cargarla si ya existe
        scene = manager.load_scene_into_session(session_id, full_scene_path)
        if scene:
            return {
                "success": True,
                "scene_path": scene_path,
                "message": "Escena ya existe, cargada en workspace",
                "loaded": True,
            }
        return {"success": False, "error": f"Escena ya existe: {scene_path}"}

    # Crear directorio si no existe
    scene_dir = os.path.dirname(full_scene_path)
    if scene_dir and not os.path.isdir(scene_dir):
        os.makedirs(scene_dir, exist_ok=True)

    # Crear escena en memoria
    scene = Scene(
        header=GdSceneHeader(load_steps=2, format=3),
        nodes=[
            SceneNode(
                name=root_name,
                type=root_type,
                parent=".",
            )
        ],
    )

    # Guardar en workspace (como dirty)
    session.loaded_scenes[full_scene_path] = scene
    session.dirty_scenes.add(full_scene_path)

    # Escribir a disco
    with open(full_scene_path, "w", encoding="utf-8") as f:
        f.write(scene.to_tscn())

    # Limpiar dirty (ya se guardó)
    session.dirty_scenes.discard(full_scene_path)

    # Agregar a open_scenes
    if full_scene_path not in session.open_scenes:
        session.open_scenes.append(full_scene_path)

    # Registrar operación
    manager.record_operation(
        session_id,
        operation_type="create",
        target=full_scene_path,
        description=f"Created scene {root_type}",
    )

    return {
        "success": True,
        "scene_path": scene_path,
        "root_type": root_type,
        "root_name": root_name,
    }


@require_session
def get_scene_tree(session_id: str, scene_path: str) -> dict:
    """
    Obtiene la jerarquía de nodos como JSON.

    Args:
        session_id: ID de sesión activa.
        scene_path: Ruta absoluta al archivo .tscn.

    Returns:
        Dict con datos de la escena o error.

    NOTA: Usa el workspace si está cargada, si no la carga.
    """
    manager = get_session_manager()
    session = manager.get_session(session_id)

    if session is None:
        return {"success": False, "error": f"Session no encontrada: {session_id}"}

    # Validar archivo existe
    if not os.path.isfile(scene_path):
        return {"success": False, "error": f"Archivo no encontrado: {scene_path}"}

    # Intentar obtener del workspace primero
    scene = manager.get_loaded_scene(session_id, scene_path)
    from_cache = False

    if scene is None:
        # Cargar en workspace
        scene = manager.load_scene_into_session(session_id, scene_path)
        if scene is None:
            return {"success": False, "error": f"Error al parsear: {scene_path}"}
    else:
        from_cache = True

    return {
        "success": True,
        "scene_path": scene_path,
        "from_cache": from_cache,
        "workspace": manager.is_scene_dirty(session_id, scene_path),
        "data": scene.to_dict(),
    }


@require_session
def save_scene(session_id: str, scene_path: str, scene_data: dict) -> dict:
    """
    Guarda los datos de escena a disco.

    Args:
        session_id: ID de sesión activa.
        scene_path: Ruta absoluta al .tscn.
        scene_data: Dict con estructura de escena.

    Returns:
        Dict con resultado.

    Nota:
        Actualiza el workspace en memoria, marca como dirty,
        y opcionalmente guarda a disco.
    """
    manager = get_session_manager()
    session = manager.get_session(session_id)

    if session is None:
        return {"success": False, "error": f"Session no encontrada: {session_id}"}

    # Reconstruir scene desde dict
    scene = _rebuild_scene_from_dict(scene_data)

    # Actualizar workspace
    session.loaded_scenes[scene_path] = scene
    session.dirty_scenes.add(scene_path)

    # Guardar a disco (commit)
    with open(scene_path, "w", encoding="utf-8") as f:
        f.write(scene.to_tscn())

    session.dirty_scenes.discard(scene_path)

    # Registrar operación
    manager.record_operation(
        session_id,
        operation_type="save",
        target=scene_path,
        description="Saved scene",
    )

    return {
        "success": True,
        "scene_path": scene_path,
    }


@require_session
def list_scenes(session_id: str, recursive: bool = True) -> dict:
    """
    Lista todas las escenas .tscn en el proyecto.

    Args:
        session_id: ID de sesión activa.
        recursive: Buscar subdirectorios.

    Returns:
        Lista de escenas.
    """
    manager = get_session_manager()
    session = manager.get_session(session_id)

    if session is None:
        return {"success": False, "error": f"Session no encontrada: {session_id}"}

    project_path = session.project_path
    from pathlib import Path

    scenes = []
    base_path = Path(project_path)

    pattern = "**/*.tscn" if recursive else "*.tscn"

    for tscn_file in base_path.glob(pattern):
        if tscn_file.is_file():
            rel_path = tscn_file.relative_to(base_path)
            scenes.append(
                {
                    "path": str(rel_path).replace(os.sep, "/"),
                    "name": tscn_file.stem,
                    "loaded": str(tscn_file) in session.loaded_scenes,
                    "dirty": str(tscn_file) in session.dirty_scenes,
                }
            )

    scenes.sort(key=lambda x: x["path"])

    return {
        "success": True,
        "project_path": project_path,
        "count": len(scenes),
        "scenes": scenes,
    }


def _rebuild_scene_from_dict(scene_data: dict) -> Scene:
    """重建Scene objeto desde dict (helper)."""
    scene = Scene()

    if "header" in scene_data:
        header_data = scene_data["header"]
        scene.header = GdSceneHeader(
            load_steps=header_data.get("load_steps", 2),
            format=header_data.get("format", 3),
            uid=header_data.get("uid", ""),
            scene_unique_name=header_data.get("scene_unique_name", ""),
        )

    # ... (resto de reconstrucción similar al código original)
    # ext_resources, sub_resources, nodes, connections

    if "nodes" in scene_data:
        for node_data in scene_data["nodes"]:
            scene.nodes.append(
                SceneNode(
                    name=node_data.get("name", ""),
                    type=node_data.get("type", ""),
                    parent=node_data.get("parent", "."),
                    unique_name_in_owner=node_data.get("unique_name_in_owner", False),
                    properties=node_data.get("properties", {}),
                )
            )

    return scene


# ==================== REGISTRO DE HERRAMIENTAS ====================


def register_scene_tools_v2(mcp) -> None:
    """
    Registra herramientas con soporte de sesión.

    Args:
        mcp: FastMCP instance.
    """
    # NO se usan decorators @mcp.tool aquí porque las funciones
    # ya tienen el decorador @require_session
    mcp.add_tool(create_scene)
    mcp.add_tool(get_scene_tree)
    mcp.add_tool(save_scene)
    mcp.add_tool(list_scenes)
