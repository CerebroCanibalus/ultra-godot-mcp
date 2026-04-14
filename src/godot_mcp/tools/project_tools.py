"""
Project Tools - Herramientas para información y gestión de proyectos Godot.

Provee herramientas para obtener metadata, estructura y encontrar archivos
en proyectos Godot Engine.
"""

import configparser
import logging
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Mapeo de tipos de recursos Godot a extensiones
RESOURCE_TYPE_MAP = {
    "Sprite2D": ["png", "jpg", "jpeg", "webp", "svg"],
    "Texture2D": ["png", "jpg", "jpeg", "webp", "svg"],
    "PackedScene": ["tscn"],
    "Script": ["gd"],
    "Shader": ["gdshader"],
    "AudioStream": ["ogg", "wav", "mp3"],
    "Font": ["ttf", "otf", "fnt"],
    "PhysicsMaterial": ["tres"],
    "RectangleShape2D": ["tres"],
    "CapsuleShape2D": ["tres"],
    "CircleShape2D": ["tres"],
    "ConvexPolygonShape2D": ["tres"],
    "ConcavePolygonShape2D": ["tres"],
    "Animation": ["anim"],
    "StyleBox": ["tres"],
}


# ============ PARSING FUNCTIONS ============


def parse_project_godot(project_path: str) -> dict:
    """
    Parse project.godot como archivo de configuración.

    El formato es similar a INI con secciones y key=value.

    Args:
        project_path: Ruta al directorio del proyecto.

    Returns:
        Diccionario con la metadata del proyecto.
    """
    project_file = Path(project_path) / "project.godot"

    if not project_file.exists():
        raise FileNotFoundError(f"project.godot not found in {project_path}")

    # Usar configparser pero con soporte para comentarios
    config = configparser.ConfigParser()
    config.optionxform = str  # Mantener case-sensitive

    # Leer con manejo de comentarios
    content = project_file.read_text(encoding="utf-8")

    # Filtrar comentarios y líneas vacías
    lines = []
    for line in content.split("\n"):
        stripped = line.strip()
        # Ignorar comentarios y líneas vacías
        if stripped and not stripped.startswith(";"):
            lines.append(line)

    # Escribir a configuración temporal
    import io

    config.read_file(io.StringIO("\n".join(lines)))

    result = {}

    # Extraer configuración global
    if config.has_section("config"):
        result["config"] = dict(config["config"])

    if config.has_section("config.name"):
        result["name"] = config.get("config.name", "name", fallback="")

    # Render info
    if config.has_section("config.render/rendering"):
        result["rendering"] = dict(config["config.render/rendering"])

    # Display
    if config.has_section("display"):
        result["display"] = dict(config["display"])

    # Input
    if config.has_section("input"):
        result["input"] = dict(config["input"])

    # Los demás secciones también
    for section in config.sections():
        if section not in [
            "config",
            "config.name",
            "config.render/rendering",
            "display",
            "input",
        ]:
            if section not in result:
                result[section] = {}
            result[section] = dict(config[section])

    return result


def get_project_metadata(project_path: str) -> dict:
    """
    Extraer metadata básica del proyecto.

    Args:
        project_path: Ruta al directorio del proyecto.

    Returns:
        Diccionario con información básica del proyecto.
    """
    project_file = Path(project_path) / "project.godot"

    if not project_file.exists():
        raise FileNotFoundError(f"project.godot not found in {project_path}")

    metadata = {
        "project_path": str(Path(project_path).resolve()),
        "exists": True,
    }

    content = project_file.read_text(encoding="utf-8")

    for line in content.split("\n"):
        line = line.strip()

        # Extraer nombre del proyecto
        if line.startswith("config/name="):
            metadata["name"] = line.split("=", 1)[1].strip('"')

        # Versión de Godot
        elif line.startswith("config/features="):
            metadata["features"] = line.split("=", 1)[1].strip('"')

        # Runs in editor
        elif line.startswith("config/run_in_editor="):
            metadata["run_in_editor"] = line.split("=", 1)[1] == "true"

        # Main scene
        elif line.startswith("application/main_scene="):
            metadata["main_scene"] = line.split("=", 1)[1].strip('"')

        # Author
        elif line.startswith("application/config/author="):
            metadata["author"] = line.split("=", 1)[1].strip('"')

    return metadata


# ============ PROJECT TOOLS ============


def get_directory_size(project_path: str) -> int:
    """Calcular tamaño total del proyecto en bytes."""
    total = 0
    for root, dirs, files in os.walk(project_path):
        for f in files:
            fp = Path(root) / f
            if fp.exists():
                total += fp.stat().st_size
    return total


def find_projects_recursive(directory: str) -> list:
    """
    Encontrar todos los proyectos Godot en un directorio recursivamente.

    Args:
        directory: Directorio a buscar.

    Returns:
        Lista de rutas a directorios con project.godot.
    """
    projects = []
    path = Path(directory)

    if not path.exists() or not path.is_dir():
        return projects

    # Buscar project.godot en subdirectorios
    for root, dirs, files in os.walk(path):
        if "project.godot" in files:
            projects.append(root)
        # No buscar en directorios ocultos o comuns
        dirs[:] = [d for d in dirs if not d.startswith(".")]

    return projects


def find_projects_flat(directory: str) -> list:
    """
    Encontrar proyectos Godot solo en el directorio directo.

    Args:
        directory: Directorio a buscar.

    Returns:
        Lista de rutas a directorios con project.godot.
    """
    projects = []
    path = Path(directory)

    if not path.exists() or not path.is_dir():
        return projects

    # Buscar solo en primer nivel
    for item in path.iterdir():
        if item.is_dir():
            if (item / "project.godot").exists():
                projects.append(str(item))

    return projects


def find_gd_files(project_path: str) -> list:
    """
    Encontrar todos los archivos .gd en el proyecto.

    Args:
        project_path: Ruta al proyecto.

    Returns:
        Lista de diccionarios con info de archivos .gd.
    """
    scripts = []
    path = Path(project_path)

    for gd_file in path.rglob("*.gd"):
        # Ignorar archivos ocultos
        if any(part.startswith(".") for part in gd_file.parts):
            continue

        relative_path = gd_file.relative_to(path)

        # Leer primeras líneas para detectar class_name
        class_name = None
        try:
            content = gd_file.read_text(encoding="utf-8")
            for line in content.split("\n")[:10]:
                line = line.strip()
                if line.startswith("class_name "):
                    class_name = line.split()[1].rstrip(",")
                    break
                elif line.startswith("extends "):
                    extends = line.split()[1].rstrip(",")
        except Exception:
            pass

        scripts.append(
            {
                "path": str(relative_path),
                "full_path": str(gd_file),
                "class_name": class_name,
            }
        )

    return scripts


def find_tres_files(project_path: str, type_filter: Optional[str] = None) -> list:
    """
    Encontrar archivos .tres opcionalmente filtrados por tipo.

    Args:
        project_path: Ruta al proyecto.
        type_filter: Filtrar por tipo de recurso (opcional).

    Returns:
        Lista de diccionarios con info de recursos.
    """
    resources = []
    path = Path(project_path)

    for tres_file in path.rglob("*.tres"):
        if any(part.startswith(".") for part in tres_file.parts):
            continue

        try:
            content = tres_file.read_text(encoding="utf-8")

            # Detectar tipo de recurso
            resource_type = None
            for line in content.split("\n"):
                line = line.strip()
                if line.startswith("[gd_resource"):
                    # Buscar type=
                    import re

                    match = re.search(r'type="([^"]+)"', line)
                    if match:
                        resource_type = match.group(1)
                    break
                elif line.startswith("[resource"):
                    # Es resource pero sin tipo específico
                    if type_filter is None or type_filter == "Resource":
                        resource_type = "Resource"
                    break

            # Aplicar filtro si se especifica
            if type_filter and resource_type != type_filter:
                if type_filter not in RESOURCE_TYPE_MAP:
                    continue
                # Los métodos de filtrado pueden venir de la lista
                allowed_exts = RESOURCE_TYPE_MAP.get(type_filter, [])
                if (
                    tres_file.suffix.lstrip(".") not in allowed_exts
                    and not type_filter == resource_type
                ):
                    continue

            relative_path = tres_file.relative_to(path)

            resources.append(
                {
                    "path": str(relative_path),
                    "full_path": str(tres_file),
                    "type": resource_type or "Resource",
                }
            )
        except Exception:
            continue

    return resources


def get_project_structure(project_path: str) -> dict:
    """
    Obtener estructura completa del proyecto.

    Args:
        project_path: Ruta al proyecto.

    Returns:
        Diccionario con estructura del proyecto.
    """
    path = Path(project_path)
    structure = {
        "project_path": str(path.resolve()),
        "directories": [],
        "scenes": [],
        "scripts": [],
        "resources": [],
        "assets": {},
    }

    # Encontrar directorios principales
    known_dirs = ["scenes", "scripts", "assets", "resources", "data", "addons"]
    for known_dir in known_dirs:
        dir_path = path / known_dir
        if dir_path.exists() and dir_path.is_dir():
            structure["directories"].append(known_dir)

            # Listar contenido
            try:
                items = list(dir_path.iterdir())
                if "scenes" in known_dir:
                    structure["scenes"] = [
                        str(f.relative_to(path)) for f in items if f.suffix == ".tscn"
                    ]
                elif "scripts" in known_dir:
                    structure["scripts"] = [
                        str(f.relative_to(path)) for f in items if f.suffix == ".gd"
                    ]
                elif "resources" in known_dir:
                    structure["resources"] = [
                        str(f.relative_to(path)) for f in items if f.suffix == ".tres"
                    ]
            except PermissionError:
                pass

    # Buscar en raíz también
    for item in path.rglob("*"):
        if item.is_file() and not any(p.startswith(".") for p in item.parts):
            if item.suffix == ".tscn":
                rel = str(item.relative_to(path))
                if rel not in structure["scenes"]:
                    structure["scenes"].append(rel)
            elif item.suffix == ".gd":
                rel = str(item.relative_to(path))
                if rel not in structure["scripts"]:
                    structure["scripts"].append(rel)
            elif item.suffix == ".tres":
                rel = str(item.relative_to(path))
                if rel not in structure["resources"]:
                    structure["resources"].append(rel)

    # Assets por extensión
    asset_exts = {
        "sprites": ["png", "jpg", "jpeg", "webp", "svg"],
        "audio": ["ogg", "wav", "mp3"],
        "fonts": ["ttf", "otf", "fnt"],
    }

    for category, exts in asset_exts.items():
        files = []
        for ext in exts:
            for file in path.rglob(f"*.{ext}"):
                if not any(p.startswith(".") for p in file.parts):
                    rel = str(file.relative_to(path))
                    files.append(rel)
        structure["assets"][category] = files

    return structure


# ============ Decoradores ====================

from godot_mcp.tools.decorators import require_session


# ============ FASTMCP TOOLS ============


def register_project_tools(mcp) -> None:
    """
    Registrar todas las herramientas de proyecto.

    Args:
        mcp: Instancia de FastMCP donde registrar las herramientas.
    """
    logger.info("Registrando project_tools...")

    # Tool: get_project_info
    @require_session
    @mcp.tool()
    def get_project_info(session_id: str, project_path: str) -> dict:
        """
        Get project metadata from project.godot.

        Args:
            session_id: Session ID from start_session.
            project_path: Absolute path to the Godot project directory.

        Returns:
            Dictionary with project metadata.
        """
        try:
            metadata = get_project_metadata(project_path)

            # Agregar tamaño del proyecto
            try:
                metadata["size_bytes"] = get_directory_size(project_path)
            except Exception:
                pass

            return {
                "success": True,
                "project_path": project_path,
                "data": metadata,
            }
        except FileNotFoundError as e:
            return {
                "success": False,
                "error": str(e),
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error reading project: {str(e)}",
            }

    # Tool: list_projects
    @require_session
    @mcp.tool()
    def list_projects(session_id: str, directory: str, recursive: bool = True) -> dict:
        """
        Find all Godot projects in directory.

        Args:
            session_id: Session ID from start_session.
            directory: Directory to search in.
            recursive: If True, search recursively.

        Returns:
            Dict with list of project paths found.
        """
        try:
            if recursive:
                projects = find_projects_recursive(directory)
            else:
                projects = find_projects_flat(directory)

            # Obtener metadata básica de cada proyecto
            result = []
            for proj_path in projects:
                try:
                    info = get_project_metadata(proj_path)
                    result.append(
                        {
                            "path": proj_path,
                            "name": info.get("name", "Unknown"),
                        }
                    )
                except Exception:
                    result.append(
                        {
                            "path": proj_path,
                            "name": Path(proj_path).name,
                        }
                    )

            return {
                "success": True,
                "directory": directory,
                "recursive": recursive,
                "count": len(result),
                "projects": result,
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error listing projects: {str(e)}",
            }

    # Tool: get_project_structure
    @require_session
    @mcp.tool()
    def get_project_structure(session_id: str, project_path: str) -> dict:
        """
        Get full project structure (scenes, scripts, assets).

        Args:
            session_id: Session ID from start_session.
            project_path: Absolute path to the Godot project directory.

        Returns:
            Dictionary with project structure.
        """
        try:
            structure = get_project_structure(project_path)

            return {
                "success": True,
                "data": structure,
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error getting structure: {str(e)}",
            }

    # Tool: find_scripts
    @require_session
    @mcp.tool()
    def find_scripts(session_id: str, project_path: str) -> dict:
        """
        Find all .gd files.

        Args:
            session_id: Session ID from start_session.
            project_path: Absolute path to the Godot project directory.

        Returns:
            Dict with script info including path and class_name.
        """
        try:
            scripts = find_gd_files(project_path)

            return {
                "success": True,
                "count": len(scripts),
                "scripts": scripts,
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error finding scripts: {str(e)}",
            }

    # Tool: find_resources
    @require_session
    @mcp.tool()
    def find_resources(
        session_id: str, project_path: str, type_filter: str = None
    ) -> dict:
        """
        Find all .tres files, optionally filtered by type.

        Args:
            session_id: Session ID from start_session.
            project_path: Absolute path to the Godot project directory.
            type_filter: Optional resource type to filter.

        Returns:
            Dict with resource info including path and type.
        """
        try:
            resources = find_tres_files(project_path, type_filter)

            return {
                "success": True,
                "count": len(resources),
                "type_filter": type_filter,
                "resources": resources,
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error finding resources: {str(e)}",
            }

    logger.info("project_tools registradas exitosamente")
