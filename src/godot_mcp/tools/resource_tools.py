"""
Resource Tools - Herramientas para gestión de recursos Godot (.tres)

Provee herramientas para:
- Crear nuevos archivos .tres
- Leer propiedades de recursos
- Actualizar recursos existentes
- Gestionar UIDs de recursos (Godot 4.4+)
- Actualizar UIDs del proyecto

Uses the native .tres parser for reading/writing.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Optional

from fastmcp import FastMCP

from godot_mcp.core.cache import LRUCache, get_cache as _get_cache_func
from godot_mcp.core.tres_parser import (
    Resource,
    ResourceHeader,
    extract_uid_from_tres,
    generate_uid_from_path,
    parse_tres,
)


# ==================== Cache Compartido ====================


def _get_resource_cache() -> LRUCache:
    """Obtiene el cache de recursos."""
    return _get_cache_func(max_size=100)


# ==================== Decoradores ====================

from godot_mcp.tools.decorators import require_session


# ==================== Herramientas MCP ====================


@require_session
def create_resource(
    session_id: str,
    resource_path: str,
    resource_type: str,
    properties: dict = None,
) -> dict:
    """
    Create a new .tres resource file.

    Args:
        session_id: Session ID from start_session.
        resource_path: Absolute path where to create the .tres file.
                      Can include the .tres extension or not.
        resource_type: Godot resource type (e.g., "Resource", "AudioStream", "Texture2D").
        properties: Optional dict of properties to set on the resource.

    Returns:
        Dict with success status and created resource info, or error message.
    """
    try:
        # Validate resource path
        if not resource_path:
            return {
                "success": False,
                "error": "Resource path cannot be empty",
            }

        # Add .tres extension if missing
        if not resource_path.endswith(".tres"):
            resource_path = resource_path + ".tres"

        # Check if file already exists
        if os.path.isfile(resource_path):
            return {
                "success": False,
                "error": f"Resource file already exists: {resource_path}",
            }

        # Create directory if needed
        resource_dir = os.path.dirname(resource_path)
        if resource_dir and not os.path.isdir(resource_dir):
            os.makedirs(resource_dir, exist_ok=True)

        # Generate UID for Godot 4.4+
        uid = generate_uid_from_path(resource_path)

        # Create resource header
        header = ResourceHeader(
            type=resource_type,
            load_steps=1,
            format=3,
            uid=uid,
        )

        # Create resource with properties
        resource = Resource(
            header=header,
            properties=properties if properties else {},
        )

        # Write to disk
        with open(resource_path, "w", encoding="utf-8") as f:
            f.write(resource.to_tres())

        return {
            "success": True,
            "resource_path": resource_path,
            "resource_type": resource_type,
            "uid": uid,
            "properties": properties if properties else {},
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


@require_session
def read_resource(session_id: str, resource_path: str) -> dict:
    """
    Read a .tres file and return its properties.

    Args:
        session_id: Session ID from start_session.
        resource_path: Absolute path to the .tres file.

    Returns:
        Dict with resource data or error message.
    """
    try:
        # Validate file exists
        if not os.path.isfile(resource_path):
            return {
                "success": False,
                "error": f"Resource file not found: {resource_path}",
            }

        # Validate file extension
        if not resource_path.endswith(".tres"):
            return {
                "success": False,
                "error": f"Not a .tres file: {resource_path}",
            }

        # Try cache first
        cache = _get_resource_cache()
        cached = cache.get(resource_path)

        if cached is not None:
            return {
                "success": True,
                "resource_path": resource_path,
                "from_cache": True,
                "data": cached.to_dict(),
            }

        # Parse the resource
        resource = parse_tres(resource_path)

        # Cache the result
        cache.set(resource_path, resource)

        return {
            "success": True,
            "resource_path": resource_path,
            "from_cache": False,
            "data": resource.to_dict(),
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


@require_session
def update_resource(session_id: str, resource_path: str, properties: dict) -> dict:
    """
    Update properties of a .tres file.

    Args:
        session_id: Session ID from start_session.
        resource_path: Absolute path to the .tres file.
        properties: Dict of properties to update.

    Returns:
        Dict with success status or error message.
    """
    try:
        # Validate file exists
        if not os.path.isfile(resource_path):
            return {
                "success": False,
                "error": f"Resource file not found: {resource_path}",
            }

        # Validate file extension
        if not resource_path.endswith(".tres"):
            return {
                "success": False,
                "error": f"Not a .tres file: {resource_path}",
            }

        # Parse existing resource
        cache = _get_resource_cache()
        resource = cache.get(resource_path)

        if resource is None:
            resource = parse_tres(resource_path)

        # Update properties (merge with existing)
        for key, value in properties.items():
            resource.properties[key] = value

        # Write back to disk
        with open(resource_path, "w", encoding="utf-8") as f:
            f.write(resource.to_tres())

        # Invalidate cache
        cache.invalidate(resource_path)

        return {
            "success": True,
            "resource_path": resource_path,
            "updated_properties": list(properties.keys()),
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


@require_session
def get_uid(session_id: str, resource_path: str) -> dict:
    """
    Get UID of a resource (Godot 4.4+).

    Args:
        session_id: Session ID from start_session.
        resource_path: Absolute path to the .tres file.

    Returns:
        Dict with UID or error message.
    """
    try:
        # Validate file exists
        if not os.path.isfile(resource_path):
            return {
                "success": False,
                "error": f"Resource file not found: {resource_path}",
            }

        # Try to extract UID from file
        uid = extract_uid_from_tres(resource_path)

        if uid:
            return {
                "success": True,
                "resource_path": resource_path,
                "uid": uid,
            }

        # Generate UID if not found
        generated_uid = generate_uid_from_path(resource_path)
        return {
            "success": True,
            "resource_path": resource_path,
            "uid": generated_uid,
            "generated": True,
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


@require_session
def update_project_uids(session_id: str, project_path: str) -> dict:
    """
    Update all UIDs in project (Godot 4.4+).

    Args:
        session_id: Session ID from start_session.
        project_path: Absolute path to the Godot project directory.

    Returns:
        Dict with summary of UIDs updated.
    """
    try:
        # Validate project path
        if not os.path.isdir(project_path):
            return {
                "success": False,
                "error": f"Project path does not exist: {project_path}",
            }

        # Check for project.godot
        project_file = os.path.join(project_path, "project.godot")
        if not os.path.isfile(project_file):
            return {
                "success": False,
                "error": f"Not a valid Godot project (no project.godot): {project_path}",
            }

        # Find all .tres files
        base_path = Path(project_path)
        tres_files = list(base_path.glob("**/*.tres"))

        updated_count = 0
        already_ok_count = 0
        errors: list[str] = []

        for tres_file in tres_files:
            try:
                file_path = str(tres_file)

                # Parse the resource
                resource = parse_tres(file_path)

                # Check if UID exists and is valid
                has_valid_uid = resource.header.uid and resource.header.uid.startswith(
                    "uid://"
                )

                if not has_valid_uid:
                    # Generate new UID
                    new_uid = generate_uid_from_path(file_path)
                    resource.header.uid = new_uid

                    # Write back
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(resource.to_tres())

                    # Invalidate cache
                    cache = _get_resource_cache()
                    cache.invalidate(file_path)

                    updated_count += 1
                else:
                    already_ok_count += 1

            except Exception as e:
                errors.append(f"{tres_file.name}: {str(e)}")

        return {
            "success": True,
            "project_path": project_path,
            "total_tres_files": len(tres_files),
            "uids_updated": updated_count,
            "uids_already_ok": already_ok_count,
            "errors": errors if errors else None,
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


@require_session
def list_resources(
    session_id: str,
    project_path: str,
    resource_type: str = None,
    recursive: bool = True,
) -> dict:
    """
    List all .tres resources in project.

    Args:
        session_id: Session ID from start_session.
        project_path: Absolute path to the Godot project directory.
        resource_type: Optional filter by resource type.
        recursive: If True, search subdirectories (default: True).

    Returns:
        Dict with list of resource files and their info.
    """
    try:
        # Validate project path
        if not os.path.isdir(project_path):
            return {
                "success": False,
                "error": f"Project path does not exist: {project_path}",
            }

        base_path = Path(project_path)

        # Search patterns
        if recursive:
            pattern = "**/*.tres"
        else:
            pattern = "*.tres"

        resources: list[dict] = []

        for tres_file in base_path.glob(pattern):
            if tres_file.is_file():
                rel_path = str(tres_file.relative_to(base_path)).replace(os.sep, "/")

                # Try to get resource type
                resource_type_info = ""
                try:
                    resource = parse_tres(str(tres_file))
                    resource_type_info = resource.header.type
                except Exception:
                    pass

                # Filter by type if specified
                if resource_type and resource_type != resource_type_info:
                    continue

                resources.append(
                    {
                        "path": rel_path,
                        "name": tres_file.stem,
                        "type": resource_type_info,
                    }
                )

        # Sort by path
        resources.sort(key=lambda x: x["path"])

        return {
            "success": True,
            "project_path": project_path,
            "count": len(resources),
            "resources": resources,
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


# ==================== Registro de Herramientas ====================


def register_resource_tools(mcp: FastMCP) -> None:
    """
    Register all resource tools with a FastMCP server.

    Args:
        mcp: FastMCP instance to register tools with
    """
    mcp.add_tool(create_resource)
    mcp.add_tool(read_resource)
    mcp.add_tool(update_resource)
    mcp.add_tool(get_uid)
    mcp.add_tool(update_project_uids)
    mcp.add_tool(list_resources)
