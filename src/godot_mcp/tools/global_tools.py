"""
Global Tools - Herramientas para gestión de configuración global del proyecto Godot.

Provee herramientas FastMCP para:
- Gestionar autoloads/singletons en project.godot
- Configurar shader globals (uniforms globales)
- Gestionar grupos globales del proyecto
- Manipular cualquier setting de project.godot

Todas las herramientas operan directamente sobre project.godot,
preservando comentarios y formato existente.
"""

import logging
import os
import re
from pathlib import Path
from typing import Any, Optional, Union

from godot_mcp.tools.decorators import require_session

logger = logging.getLogger(__name__)


# ============ PROJECT.GODOT PARSER/WRITER ============


class ProjectGodotEditor:
    """
    Editor quirúrgico de project.godot.
    
    Preserva comentarios, formato y orden de secciones.
    Opera a nivel de líneas para máxima fidelidad.
    """

    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.project_file = self.project_path / "project.godot"
        if not self.project_file.exists():
            raise FileNotFoundError(f"project.godot not found in {project_path}")
        self.lines: list[str] = []
        self._load()

    def _load(self):
        """Carga el archivo en memoria."""
        with open(self.project_file, "r", encoding="utf-8") as f:
            self.lines = f.read().splitlines()

    def save(self):
        """Guarda cambios a disco."""
        with open(self.project_file, "w", encoding="utf-8") as f:
            f.write("\n".join(self.lines) + "\n")

    def get_section_lines(self, section: str) -> tuple[int, int]:
        """
        Obtener rango de líneas de una sección [section].
        
        Returns:
            (start_idx, end_idx) donde end_idx es la primera línea
            de la siguiente sección o len(lines).
        """
        start = -1
        for i, line in enumerate(self.lines):
            stripped = line.strip()
            if stripped == f"[{section}]":
                start = i
                break
        
        if start == -1:
            return -1, -1

        # Encontrar fin de sección (inicio de siguiente sección o EOF)
        end = len(self.lines)
        for i in range(start + 1, len(self.lines)):
            stripped = self.lines[i].strip()
            if stripped.startswith("[") and stripped.endswith("]"):
                end = i
                break

        return start, end

    def has_section(self, section: str) -> bool:
        """Verificar si existe una sección."""
        start, _ = self.get_section_lines(section)
        return start != -1

    def get_section_entries(self, section: str) -> dict[str, str]:
        """
        Obtener todas las entradas key=value de una sección.
        
        Returns:
            Dict con {key: value_raw} donde value_raw incluye comillas si las tiene.
        """
        start, end = self.get_section_lines(section)
        if start == -1:
            return {}

        entries = {}
        for i in range(start + 1, end):
            line = self.lines[i].strip()
            if not line or line.startswith(";"):
                continue
            if "=" in line:
                key, value = line.split("=", 1)
                entries[key.strip()] = value.strip()

        return entries

    def set_entry(self, section: str, key: str, value: str):
        """
        Establece o actualiza una entrada en una sección.
        Crea la sección si no existe.
        """
        start, end = self.get_section_lines(section)
        
        if start == -1:
            # Crear nueva sección al final
            self.lines.append("")
            self.lines.append(f"[{section}]")
            self.lines.append(f"{key}={value}")
            return

        # Buscar si la key ya existe
        for i in range(start + 1, end):
            line = self.lines[i].strip()
            if not line or line.startswith(";"):
                continue
            if "=" in line:
                existing_key = line.split("=", 1)[0].strip()
                if existing_key == key:
                    # Actualizar valor existente preservando indentación
                    indent = self.lines[i][:len(self.lines[i]) - len(self.lines[i].lstrip())]
                    self.lines[i] = f"{indent}{key}={value}"
                    return

        # Key no existe, insertar al final de la sección
        insert_pos = end
        # Si end es len(lines), append; si no, insert antes de siguiente sección
        if insert_pos >= len(self.lines):
            self.lines.append(f"{key}={value}")
        else:
            self.lines.insert(insert_pos, f"{key}={value}")

    def remove_entry(self, section: str, key: str) -> bool:
        """
        Elimina una entrada de una sección.
        
        Returns:
            True si se eliminó, False si no existía.
        """
        start, end = self.get_section_lines(section)
        if start == -1:
            return False

        for i in range(start + 1, end):
            line = self.lines[i].strip()
            if not line or line.startswith(";"):
                continue
            if "=" in line:
                existing_key = line.split("=", 1)[0].strip()
                if existing_key == key:
                    del self.lines[i]
                    # Si la sección quedó vacía, eliminarla
                    self._cleanup_empty_section(section)
                    return True

        return False

    def _cleanup_empty_section(self, section: str):
        """Elimina una sección si quedó vacía (sin entradas)."""
        start, end = self.get_section_lines(section)
        if start == -1:
            return

        has_entries = False
        for i in range(start + 1, end):
            line = self.lines[i].strip()
            if line and not line.startswith(";") and "=" in line:
                has_entries = True
                break

        if not has_entries:
            # Eliminar sección completa
            del self.lines[start:end]

    def remove_section(self, section: str) -> bool:
        """Elimina una sección completa."""
        start, end = self.get_section_lines(section)
        if start == -1:
            return False
        del self.lines[start:end]
        return True


# ============ UTILIDADES ============


def _get_editor(project_path: str) -> ProjectGodotEditor:
    """Crear editor para project.godot."""
    return ProjectGodotEditor(project_path)


def _parse_godot_value(value: str) -> Any:
    """
    Parsear un valor de Godot a tipo Python.
    
    Maneja:
    - Strings con comillas: "value" -> str
    - true/false -> bool
    - números -> int/float
    - arrays: PackedStringArray("a", "b")
    """
    value = value.strip()
    
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1]
    
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    
    # Intentar int
    try:
        return int(value)
    except ValueError:
        pass
    
    # Intentar float
    try:
        return float(value)
    except ValueError:
        pass
    
    # Packed arrays
    if value.startswith("PackedStringArray("):
        inner = value[len("PackedStringArray("):].rstrip(")")
        items = []
        for item in inner.split(","):
            item = item.strip()
            if item.startswith('"') and item.endswith('"'):
                items.append(item[1:-1])
            elif item.startswith("'") and item.endswith("'"):
                items.append(item[1:-1])
        return items
    
    return value


def _format_godot_value(value: Any) -> str:
    """
    Formatear un valor Python a formato Godot.
    
    Maneja:
    - str -> "value"
    - bool -> true/false
    - int/float -> valor directo
    - list -> PackedStringArray("a", "b")
    """
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, list):
        items = ', '.join(f'"{str(v)}"' for v in value)
        return f"PackedStringArray({items})"
    if isinstance(value, str):
        return f'"{value}"'
    return f'"{str(value)}"'


# ============ AUTOLOAD TOOLS ============


@require_session
def add_autoload(
    session_id: str,
    project_path: str,
    name: str,
    script_path: str,
    singleton: bool = True,
) -> dict:
    """
    Add an autoload to project.godot.
    
    In Godot, autoloads are scripts that are automatically loaded
    when the game starts. If singleton=True, the script is loaded
    as a singleton (accessible globally with the given name).
    
    Args:
        session_id: Session ID from start_session.
        project_path: Absolute path to the Godot project directory.
        name: Name for the autoload (used as global reference).
        script_path: Path to the script/scene (e.g., "res://scripts/game_manager.gd").
        singleton: If True, the autoload is a singleton (prefixed with *).
    
    Returns:
        Dict with success status and autoload info.
    
    Example:
        add_autoload(
            project_path="D:/MyGame",
            name="GameManager",
            script_path="res://scripts/game_manager.gd",
            singleton=True
        )
    """
    try:
        editor = _get_editor(project_path)
        
        # Verificar que el script existe
        if script_path.startswith("res://"):
            relative_path = script_path.replace("res://", "")
            full_path = Path(project_path) / relative_path
            if not full_path.exists():
                return {
                    "success": False,
                    "error": f"Script not found: {script_path}",
                    "hint": "The script must exist before adding it as autoload.",
                }
        
        # Formatear valor: *res://... para singleton, res://... para normal
        prefix = "*" if singleton else ""
        value = _format_godot_value(f"{prefix}{script_path}")
        
        editor.set_entry("autoload", name, value)
        editor.save()
        
        return {
            "success": True,
            "name": name,
            "script_path": script_path,
            "singleton": singleton,
            "message": f"Autoload '{name}' added as {'singleton' if singleton else 'autoload'}",
        }
    except FileNotFoundError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": f"Error adding autoload: {str(e)}"}


@require_session
def remove_autoload(
    session_id: str,
    project_path: str,
    name: str,
) -> dict:
    """
    Remove an autoload from project.godot.
    
    Args:
        session_id: Session ID from start_session.
        project_path: Absolute path to the Godot project directory.
        name: Name of the autoload to remove.
    
    Returns:
        Dict with success status.
    """
    try:
        editor = _get_editor(project_path)
        
        removed = editor.remove_entry("autoload", name)
        if removed:
            editor.save()
            return {
                "success": True,
                "name": name,
                "message": f"Autoload '{name}' removed",
            }
        else:
            return {
                "success": False,
                "error": f"Autoload '{name}' not found",
            }
    except FileNotFoundError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": f"Error removing autoload: {str(e)}"}


@require_session
def list_autoloads(
    session_id: str,
    project_path: str,
) -> dict:
    """
    List all autoloads configured in project.godot.
    
    Args:
        session_id: Session ID from start_session.
        project_path: Absolute path to the Godot project directory.
    
    Returns:
        Dict with list of autoloads.
    """
    try:
        editor = _get_editor(project_path)
        entries = editor.get_section_entries("autoload")
        
        autoloads = []
        for name, value_raw in entries.items():
            value = _parse_godot_value(value_raw)
            singleton = False
            script_path = value
            
            if isinstance(value, str) and value.startswith("*"):
                singleton = True
                script_path = value[1:]
            
            autoloads.append({
                "name": name,
                "script_path": script_path,
                "singleton": singleton,
                "raw_value": value_raw,
            })
        
        return {
            "success": True,
            "count": len(autoloads),
            "autoloads": autoloads,
        }
    except FileNotFoundError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": f"Error listing autoloads: {str(e)}"}


@require_session
def set_autoload_enabled(
    session_id: str,
    project_path: str,
    name: str,
    enabled: bool = True,
) -> dict:
    """
    Enable or disable an autoload in project.godot.
    
    In Godot, disabled autoloads have a '!' prefix.
    
    Args:
        session_id: Session ID from start_session.
        project_path: Absolute path to the Godot project directory.
        name: Name of the autoload.
        enabled: True to enable, False to disable.
    
    Returns:
        Dict with success status.
    """
    try:
        editor = _get_editor(project_path)
        entries = editor.get_section_entries("autoload")
        
        if name not in entries:
            return {
                "success": False,
                "error": f"Autoload '{name}' not found",
            }
        
        current_value = entries[name]
        parsed = _parse_godot_value(current_value)
        
        if isinstance(parsed, str):
            # Quitar prefijos existentes
            clean_path = parsed.lstrip("*!")
            
            if enabled:
                # Restaurar prefijo * si era singleton (verificar si tenía *)
                # Por simplicidad, asumimos que si tenía * lo mantenemos
                if current_value.startswith("*!") or current_value.startswith("*"):
                    new_value = f"*{clean_path}"
                else:
                    new_value = clean_path
            else:
                # Deshabilitar: añadir !
                if current_value.startswith("*"):
                    new_value = f"*!{clean_path}"
                else:
                    new_value = f"!{clean_path}"
            
            editor.set_entry("autoload", name, new_value)
            editor.save()
            
            return {
                "success": True,
                "name": name,
                "enabled": enabled,
                "message": f"Autoload '{name}' {'enabled' if enabled else 'disabled'}",
            }
        
        return {
            "success": False,
            "error": f"Unexpected autoload value format: {current_value}",
        }
    except FileNotFoundError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": f"Error updating autoload: {str(e)}"}


# ============ SHADER GLOBAL TOOLS ============


@require_session
def set_shader_global(
    session_id: str,
    project_path: str,
    name: str,
    global_type: str,
    value: str,
) -> dict:
    """
    Set a shader global (uniform) in project.godot.
    
    Shader globals are automatically available in all shaders
    without needing to set them per-material.
    
    Args:
        session_id: Session ID from start_session.
        project_path: Absolute path to the Godot project directory.
        name: Name of the shader global.
        global_type: Type of the global. Valid types:
            - "bool", "bvec2", "bvec3", "bvec4"
            - "int", "ivec2", "ivec3", "ivec4"
            - "uint", "uvec2", "uvec3", "uvec4"
            - "float", "vec2", "vec3", "vec4"
            - "Color" (stored as vec4)
            - "Transform2D", "Transform3D"
            - "Projection"
            - "Sampler2D", "Sampler2DArray", "Sampler3D"
            - "SamplerCube", "SamplerExternalOES"
        value: Value in Godot format. Examples:
            - "true" (bool)
            - "1.0" (float)
            - "Vector3(1, 2, 3)" (vec3)
            - "Color(1, 0, 0, 1)" (Color)
            - "Transform2D(1, 0, 0, 1, 0, 0)"
    
    Returns:
        Dict with success status.
    
    Example:
        set_shader_global(
            project_path="D:/MyGame",
            name="time_of_day",
            global_type="float",
            value="12.0"
        )
    """
    try:
        editor = _get_editor(project_path)
        
        # Formato en project.godot: name="type,value"
        formatted_value = f'{global_type},{value}'
        
        editor.set_entry("shader_globals", name, formatted_value)
        editor.save()
        
        return {
            "success": True,
            "name": name,
            "type": global_type,
            "value": value,
            "message": f"Shader global '{name}' set to {global_type}={value}",
        }
    except FileNotFoundError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": f"Error setting shader global: {str(e)}"}


@require_session
def get_shader_globals(
    session_id: str,
    project_path: str,
) -> dict:
    """
    Get all shader globals configured in project.godot.
    
    Args:
        session_id: Session ID from start_session.
        project_path: Absolute path to the Godot project directory.
    
    Returns:
        Dict with list of shader globals.
    """
    try:
        editor = _get_editor(project_path)
        entries = editor.get_section_entries("shader_globals")
        
        globals_list = []
        for name, value_raw in entries.items():
            value = _parse_godot_value(value_raw)
            
            # Parsear "type,value"
            global_type = "unknown"
            global_value = value
            if isinstance(value, str) and "," in value:
                parts = value.split(",", 1)
                global_type = parts[0].strip()
                global_value = parts[1].strip()
            
            globals_list.append({
                "name": name,
                "type": global_type,
                "value": global_value,
                "raw_value": value_raw,
            })
        
        return {
            "success": True,
            "count": len(globals_list),
            "shader_globals": globals_list,
        }
    except FileNotFoundError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": f"Error getting shader globals: {str(e)}"}


@require_session
def remove_shader_global(
    session_id: str,
    project_path: str,
    name: str,
) -> dict:
    """
    Remove a shader global from project.godot.
    
    Args:
        session_id: Session ID from start_session.
        project_path: Absolute path to the Godot project directory.
        name: Name of the shader global to remove.
    
    Returns:
        Dict with success status.
    """
    try:
        editor = _get_editor(project_path)
        
        removed = editor.remove_entry("shader_globals", name)
        if removed:
            editor.save()
            return {
                "success": True,
                "name": name,
                "message": f"Shader global '{name}' removed",
            }
        else:
            return {
                "success": False,
                "error": f"Shader global '{name}' not found",
            }
    except FileNotFoundError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": f"Error removing shader global: {str(e)}"}


# ============ GLOBAL GROUP TOOLS ============


@require_session
def add_global_group(
    session_id: str,
    project_path: str,
    group_name: str,
) -> dict:
    """
    Add a global group to the project.
    
    Global groups in Godot are defined in project.godot under
    the [global_group] section. They are available project-wide.
    
    Args:
        session_id: Session ID from start_session.
        project_path: Absolute path to the Godot project directory.
        group_name: Name of the group to add.
    
    Returns:
        Dict with success status.
    """
    try:
        editor = _get_editor(project_path)
        
        # En Godot, los grupos globales usan el nombre como key con valor ""
        editor.set_entry("global_group", group_name, '""')
        editor.save()
        
        return {
            "success": True,
            "group": group_name,
            "message": f"Global group '{group_name}' added",
        }
    except FileNotFoundError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": f"Error adding global group: {str(e)}"}


@require_session
def remove_global_group(
    session_id: str,
    project_path: str,
    group_name: str,
) -> dict:
    """
    Remove a global group from the project.
    
    Args:
        session_id: Session ID from start_session.
        project_path: Absolute path to the Godot project directory.
        group_name: Name of the group to remove.
    
    Returns:
        Dict with success status.
    """
    try:
        editor = _get_editor(project_path)
        
        removed = editor.remove_entry("global_group", group_name)
        if removed:
            editor.save()
            return {
                "success": True,
                "group": group_name,
                "message": f"Global group '{group_name}' removed",
            }
        else:
            return {
                "success": False,
                "error": f"Global group '{group_name}' not found",
            }
    except FileNotFoundError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": f"Error removing global group: {str(e)}"}


@require_session
def list_global_groups(
    session_id: str,
    project_path: str,
) -> dict:
    """
    List all global groups in the project.
    
    Args:
        session_id: Session ID from start_session.
        project_path: Absolute path to the Godot project directory.
    
    Returns:
        Dict with list of global groups.
    """
    try:
        editor = _get_editor(project_path)
        entries = editor.get_section_entries("global_group")
        
        groups = []
        for name, value_raw in entries.items():
            groups.append({
                "name": name,
                "raw_value": value_raw,
            })
        
        return {
            "success": True,
            "count": len(groups),
            "groups": groups,
        }
    except FileNotFoundError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": f"Error listing global groups: {str(e)}"}


# ============ PROJECT SETTINGS TOOLS ============


@require_session
def set_project_setting(
    session_id: str,
    project_path: str,
    section: str,
    key: str,
    value: Any,
) -> dict:
    """
    Set any setting in project.godot.
    
    This is a generic tool that can modify any section/key
    in the project configuration file.
    
    Args:
        session_id: Session ID from start_session.
        project_path: Absolute path to the Godot project directory.
        section: Section name (e.g., "display", "rendering", "physics", "input").
        key: Setting key.
        value: Value to set. Can be:
            - str: stored as "value"
            - int/float: stored directly
            - bool: stored as true/false
            - list: stored as PackedStringArray("a", "b")
    
    Returns:
        Dict with success status.
    
    Examples:
        set_project_setting(
            project_path="D:/MyGame",
            section="display",
            key="window/size/viewport_width",
            value=1920
        )
        
        set_project_setting(
            project_path="D:/MyGame",
            section="rendering",
            key="renderer/rendering_method",
            value="mobile"
        )
    """
    try:
        editor = _get_editor(project_path)
        
        formatted = _format_godot_value(value)
        editor.set_entry(section, key, formatted)
        editor.save()
        
        return {
            "success": True,
            "section": section,
            "key": key,
            "value": value,
            "formatted_value": formatted,
            "message": f"Setting [{section}] {key}={formatted}",
        }
    except FileNotFoundError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": f"Error setting project setting: {str(e)}"}


@require_session
def get_project_setting(
    session_id: str,
    project_path: str,
    section: str,
    key: str,
) -> dict:
    """
    Get a specific setting from project.godot.
    
    Args:
        session_id: Session ID from start_session.
        project_path: Absolute path to the Godot project directory.
        section: Section name.
        key: Setting key.
    
    Returns:
        Dict with the setting value.
    """
    try:
        editor = _get_editor(project_path)
        entries = editor.get_section_entries(section)
        
        if key not in entries:
            return {
                "success": False,
                "error": f"Setting [{section}] {key} not found",
            }
        
        raw_value = entries[key]
        parsed = _parse_godot_value(raw_value)
        
        return {
            "success": True,
            "section": section,
            "key": key,
            "value": parsed,
            "raw_value": raw_value,
        }
    except FileNotFoundError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": f"Error getting project setting: {str(e)}"}


@require_session
def get_project_settings(
    session_id: str,
    project_path: str,
    section: Optional[str] = None,
) -> dict:
    """
    Get all settings from project.godot, optionally filtered by section.
    
    Args:
        session_id: Session ID from start_session.
        project_path: Absolute path to the Godot project directory.
        section: If provided, only return settings from this section.
    
    Returns:
        Dict with all settings organized by section.
    """
    try:
        editor = _get_editor(project_path)
        
        if section:
            entries = editor.get_section_entries(section)
            parsed = {k: _parse_godot_value(v) for k, v in entries.items()}
            return {
                "success": True,
                "section": section,
                "settings": parsed,
            }
        else:
            # Obtener todas las secciones
            all_sections = {}
            current_section = None
            
            for line in editor.lines:
                stripped = line.strip()
                if stripped.startswith("[") and stripped.endswith("]"):
                    current_section = stripped[1:-1]
                    all_sections[current_section] = {}
                elif current_section and "=" in stripped and not stripped.startswith(";"):
                    key, value = stripped.split("=", 1)
                    all_sections[current_section][key.strip()] = _parse_godot_value(value.strip())
            
            return {
                "success": True,
                "sections": all_sections,
            }
    except FileNotFoundError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": f"Error getting project settings: {str(e)}"}


@require_session
def remove_project_setting(
    session_id: str,
    project_path: str,
    section: str,
    key: str,
) -> dict:
    """
    Remove a setting from project.godot.
    
    Args:
        session_id: Session ID from start_session.
        project_path: Absolute path to the Godot project directory.
        section: Section name.
        key: Setting key to remove.
    
    Returns:
        Dict with success status.
    """
    try:
        editor = _get_editor(project_path)
        
        removed = editor.remove_entry(section, key)
        if removed:
            editor.save()
            return {
                "success": True,
                "section": section,
                "key": key,
                "message": f"Setting [{section}] {key} removed",
            }
        else:
            return {
                "success": False,
                "error": f"Setting [{section}] {key} not found",
            }
    except FileNotFoundError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": f"Error removing project setting: {str(e)}"}


# ============ REGISTRATION ============


def register_global_tools(mcp) -> None:
    """
    Registrar todas las herramientas de configuración global.
    
    Args:
        mcp: Instancia de FastMCP donde registrar las herramientas.
    """
    logger.info("Registrando global_tools...")

    # Autoload tools
    mcp.add_tool(add_autoload)
    mcp.add_tool(remove_autoload)
    mcp.add_tool(list_autoloads)
    mcp.add_tool(set_autoload_enabled)

    # Shader global tools
    mcp.add_tool(set_shader_global)
    mcp.add_tool(get_shader_globals)
    mcp.add_tool(remove_shader_global)

    # Global group tools
    mcp.add_tool(add_global_group)
    mcp.add_tool(remove_global_group)
    mcp.add_tool(list_global_groups)

    # Generic project settings tools
    mcp.add_tool(set_project_setting)
    mcp.add_tool(get_project_setting)
    mcp.add_tool(get_project_settings)
    mcp.add_tool(remove_project_setting)

    logger.info("[OK] 13 global_tools registradas")
