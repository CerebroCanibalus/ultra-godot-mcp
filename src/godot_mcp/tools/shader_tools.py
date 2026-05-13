"""
Shader Tools - Herramientas centralizadas para gestión completa de shaders Godot.

Provee 4 herramientas FastMCP que cubren todo el ciclo de vida de un shader:
- manage_shader: Crear, editar, validar y leer archivos .gdshader
- manage_shader_material: Configurar ShaderMaterial y sus parámetros
- create_render_pipeline: Componer cadenas de efectos con SubViewports
- analyze_shader: Inteligencia, diagnóstico y optimización de shaders

Filosofía: 4 herramientas que hacen el trabajo de 20.
"""

import logging
import os
import re
import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import Any, Optional

from godot_mcp.tools.decorators import require_session
from godot_mcp.core.shader_parser import GDShaderParser, quick_parse_shader
from godot_mcp.core.tscn_parser import (
    Scene,
    SceneNode,
    ExtResource,
    SubResource,
    parse_tscn,
)
from godot_mcp.templates.shader_templates import (
    ShaderTemplateEngine,
    render_shader_template,
    list_available_templates,
)

logger = logging.getLogger(__name__)

# Instancia global del motor de templates
_template_engine = ShaderTemplateEngine()


# ============ UTILIDADES INTERNAS ============


def _resolve_path(project_path: str, path: str) -> str:
    """Resolver ruta res:// o relativa a absoluta."""
    if path.startswith("res://"):
        return os.path.join(project_path, path.replace("res://", "").replace("/", os.sep))
    if os.path.isabs(path):
        return path
    return os.path.join(project_path, path)


def _path_to_res(project_path: str, abs_path: str) -> str:
    """Convertir ruta absoluta a res://."""
    abs_path = os.path.abspath(abs_path)
    project_path = os.path.abspath(project_path)
    if abs_path.startswith(project_path):
        rel = os.path.relpath(abs_path, project_path).replace(os.sep, "/")
        return f"res://{rel}"
    return abs_path


def _find_godot_executable(project_path: str) -> Optional[str]:
    """Encontrar ejecutable de Godot en el sistema."""
    import shutil
    
    # Buscar en PATH
    godot_cmd = shutil.which("godot")
    if godot_cmd:
        return godot_cmd
    
    # Buscar en ubicaciones comunes de Windows
    common_paths = [
        r"C:\Program Files\Godot\Godot.exe",
        r"C:\Program Files (x86)\Godot\Godot.exe",
        r"D:\Godot\Godot.exe",
        r"D:\Program Files\Godot\Godot.exe",
    ]
    
    for path in common_paths:
        if os.path.isfile(path):
            return path
    
    return None


def _validate_with_godot(project_path: str, shader_path: str) -> tuple[bool, list[str]]:
    """
    Validar shader compilándolo con Godot CLI.
    
    Returns:
        (is_valid, list_of_messages)
    """
    godot = _find_godot_executable(project_path)
    if not godot:
        return True, ["Godot no encontrado - validación sintáctica básica únicamente"]
    
    # Crear script GDScript temporal para testear el shader
    shader_res = _path_to_res(project_path, shader_path)
    
    test_script = f'''
extends SceneTree
func _init():
    var shader = load("{shader_res}")
    if shader == null:
        print("SHADER_ERROR: No se pudo cargar el shader")
    elif not shader is Shader:
        print("SHADER_ERROR: El recurso no es un Shader válido")
    else:
        print("SHADER_OK: Shader cargado correctamente")
    quit()
'''
    
    script_path = ""
    try:
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.gd', delete=False, encoding='utf-8'
        ) as f:
            f.write(test_script)
            script_path = f.name
        
        result = subprocess.run(
            [godot, "--headless", "--path", project_path, "-s", script_path],
            capture_output=True,
            text=True,
            timeout=30,
        )
        
        output = result.stdout + result.stderr
        
        # Buscar errores de shader en la salida
        errors = []
        warnings = []
        
        for line in output.splitlines():
            if "SHADER_ERROR" in line:
                errors.append(line.split("SHADER_ERROR:", 1)[-1].strip())
            elif "SHADER_OK" in line:
                pass  # Todo bien
            elif "Shader" in line and ("error" in line.lower() or "failed" in line.lower()):
                errors.append(line.strip())
            elif "uniform" in line.lower() and "not found" in line.lower():
                warnings.append(line.strip())
        
        if errors:
            return False, errors
        
        messages = ["Shader válido"]
        if warnings:
            messages.extend(warnings)
        
        return True, messages
        
    except subprocess.TimeoutExpired:
        return False, ["Timeout al validar shader con Godot"]
    except Exception as e:
        return True, [f"Validación con Godot falló: {str(e)}"]
    finally:
        if script_path and os.path.exists(script_path):
            try:
                os.unlink(script_path)
            except:
                pass


def _mark_scene_dirty(scene_path: str) -> None:
    """Mark scene as dirty for session tracking."""
    try:
        from godot_mcp.tools.session_tools import get_session_manager
        from godot_mcp.core.cache import get_cache

        cache = get_cache()
        cache.invalidate(scene_path)

        manager = get_session_manager()
        for sid in list(manager._sessions.keys()):
            session = manager.get_session(sid)
            if session is not None:
                manager.mark_scene_dirty(sid, scene_path)
    except Exception as e:
        logger.warning(f"Failed to mark scene dirty: {e}")


# ============ REGISTRO DE TOOLS ============


def register_shader_tools(mcp) -> None:
    """
    Registrar todas las herramientas de shaders con FastMCP.
    
    Args:
        mcp: Instancia de FastMCP donde registrar las herramientas.
    """
    logger.info("Registrando shader_tools...")
    
    # ============ TOOL 1: manage_shader ============
    
    @require_session
    @mcp.tool()
    def manage_shader(
        session_id: str,
        project_path: str,
        mode: str,
        shader_path: str,
        template: str = "",
        code: str = "",
        uniforms: Optional[dict] = None,
        render_modes: Optional[list] = None,
        replace_section: str = "",
    ) -> dict:
        """
        Herramienta MADRE para gestión completa de archivos .gdshader.
        
        UNICO punto de entrada para crear, editar, leer, validar y eliminar shaders.
        
        Args:
            session_id: Session ID from start_session.
            project_path: Absolute path to the Godot project directory.
            mode: Operation mode - "create", "edit", "read", "validate", "delete", "list_templates"
            shader_path: Path to the shader file (res:// or absolute). For list_templates, leave empty.
            template: Template name for create mode (e.g., "water", "dissolve", "post_process_base")
            code: Raw shader code for create/edit modes (overrides template if provided)
            uniforms: Dict of uniforms to add when creating from template
            render_modes: List of render modes to add (e.g., ["blend_add", "unshaded"])
            replace_section: For edit mode: "vertex", "fragment", "globals", or "full"
            
        Returns:
            Dict with success status, shader info, and operation details.
            
        Examples:
            # Create shader from template
            manage_shader(
                mode="create",
                shader_path="res://shaders/water.gdshader",
                template="water",
                uniforms={"wave_speed": 2.0}
            )
            
            # Validate existing shader
            manage_shader(
                mode="validate",
                shader_path="res://shaders/effect.gdshader"
            )
            
            # Read shader metadata
            manage_shader(
                mode="read",
                shader_path="res://shaders/effect.gdshader"
            )
        """
        try:
            project_path = os.path.abspath(project_path)
            abs_shader_path = _resolve_path(project_path, shader_path)
            
            if mode == "list_templates":
                templates = list_available_templates()
                template_info = []
                for t in templates:
                    info = _template_engine.get_template_info(t)
                    template_info.append(info)
                
                return {
                    "success": True,
                    "templates": template_info,
                    "count": len(templates),
                }
            
            if mode == "create":
                # Crear directorio si no existe
                os.makedirs(os.path.dirname(abs_shader_path), exist_ok=True)
                
                # Generar código
                if code:
                    shader_code = code
                elif template:
                    try:
                        # Convertir uniforms a kwargs para el template
                        template_kwargs = {}
                        if uniforms:
                            for name, spec in uniforms.items():
                                if isinstance(spec, dict):
                                    template_kwargs[name] = spec.get("default", spec.get("value"))
                                else:
                                    template_kwargs[name] = spec
                        
                        shader_code = render_shader_template(template, **template_kwargs)
                    except Exception as e:
                        return {
                            "success": False,
                            "error": f"Error renderizando template '{template}': {str(e)}",
                        }
                else:
                    # Shader mínimo por defecto
                    shader_type = "spatial"
                    if "canvas" in shader_path.lower() or "2d" in shader_path.lower():
                        shader_type = "canvas_item"
                    elif "particle" in shader_path.lower():
                        shader_type = "particles"
                    
                    shader_code = f"shader_type {shader_type};\n\nvoid fragment() {{\n    // Shader generado automáticamente\n}}\n"
                
                # Añadir render modes si se especificaron
                if render_modes:
                    modes_str = ", ".join(render_modes)
                    lines = shader_code.splitlines()
                    new_lines = []
                    inserted = False
                    for line in lines:
                        new_lines.append(line)
                        if line.strip().startswith("shader_type") and not inserted:
                            new_lines.append(f"render_mode {modes_str};")
                            inserted = True
                    shader_code = "\n".join(new_lines) + "\n"
                
                # Añadir uniforms adicionales si se especificaron
                if uniforms:
                    uniform_lines = []
                    for name, spec in uniforms.items():
                        if isinstance(spec, dict):
                            u_type = spec.get("type", "float")
                            default = spec.get("default", "")
                            hint = spec.get("hint", "")
                            
                            line = f"uniform {u_type} {name}"
                            if hint:
                                line += f" : {hint}"
                            if default:
                                line += f" = {default}"
                            line += ";"
                        else:
                            line = f"uniform float {name} = {spec};"
                        
                        uniform_lines.append(line)
                    
                    lines = shader_code.splitlines()
                    new_lines = []
                    inserted = False
                    for line in lines:
                        new_lines.append(line)
                        if not inserted and (line.strip().startswith("shader_type") or line.strip().startswith("render_mode")):
                            pass
                        elif not inserted and not line.strip().startswith("render_mode"):
                            new_lines.extend(uniform_lines)
                            inserted = True
                    
                    if not inserted:
                        new_lines.extend(uniform_lines)
                    
                    shader_code = "\n".join(new_lines) + "\n"
                
                # Validación sintáctica antes de guardar
                is_valid, errors = GDShaderParser.validate_shader_code(shader_code)
                if not is_valid:
                    return {
                        "success": False,
                        "error": "Shader no pasa validación sintáctica",
                        "validation_errors": errors,
                        "generated_code_preview": shader_code[:500],
                    }
                
                # Guardar archivo
                with open(abs_shader_path, "w", encoding="utf-8") as f:
                    f.write(shader_code)
                
                return {
                    "success": True,
                    "mode": "create",
                    "shader_path": shader_path,
                    "absolute_path": abs_shader_path,
                    "template_used": template or "custom",
                    "line_count": len(shader_code.splitlines()),
                    "message": f"Shader creado exitosamente: {shader_path}",
                }
            
            elif mode == "read":
                if not os.path.isfile(abs_shader_path):
                    return {
                        "success": False,
                        "error": f"Shader no encontrado: {shader_path}",
                    }
                
                analysis = quick_parse_shader(abs_shader_path)
                
                with open(abs_shader_path, "r", encoding="utf-8") as f:
                    source_code = f.read()
                
                return {
                    "success": True,
                    "mode": "read",
                    "shader_path": shader_path,
                    "analysis": analysis,
                    "source_code": source_code,
                }
            
            elif mode == "validate":
                if not os.path.isfile(abs_shader_path):
                    return {
                        "success": False,
                        "error": f"Shader no encontrado: {shader_path}",
                    }
                
                with open(abs_shader_path, "r", encoding="utf-8") as f:
                    code = f.read()
                
                is_valid, syntax_errors = GDShaderParser.validate_shader_code(code)
                godot_valid, godot_messages = _validate_with_godot(project_path, abs_shader_path)
                
                parser = GDShaderParser()
                analysis = parser.parse_file(abs_shader_path)
                
                all_errors = []
                if not is_valid:
                    all_errors.extend(syntax_errors)
                if not godot_valid:
                    all_errors.extend(godot_messages)
                
                return {
                    "success": len(all_errors) == 0,
                    "mode": "validate",
                    "shader_path": shader_path,
                    "valid": len(all_errors) == 0,
                    "syntax_valid": is_valid,
                    "godot_valid": godot_valid,
                    "errors": all_errors,
                    "warnings": analysis.warnings,
                    "complexity": analysis.complexity,
                }
            
            elif mode == "edit":
                if not os.path.isfile(abs_shader_path):
                    return {
                        "success": False,
                        "error": f"Shader no encontrado: {shader_path}",
                    }
                
                with open(abs_shader_path, "r", encoding="utf-8") as f:
                    existing_code = f.read()
                
                if replace_section == "full" and code:
                    new_code = code
                elif replace_section in {"vertex", "fragment", "light"} and code:
                    pattern = rf'(\b{replace_section}\s*\([^)]*\)\s*\{{)'
                    match = re.search(pattern, existing_code)
                    if not match:
                        return {
                            "success": False,
                            "error": f"Función '{replace_section}()' no encontrada en el shader",
                        }
                    
                    start_idx = match.start()
                    brace_count = 0
                    end_idx = start_idx
                    for i, char in enumerate(existing_code[start_idx:]):
                        if char == '{':
                            brace_count += 1
                        elif char == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                end_idx = start_idx + i + 1
                                break
                    
                    new_code = existing_code[:start_idx] + code + existing_code[end_idx:]
                elif code:
                    new_code = existing_code + "\n" + code
                else:
                    return {
                        "success": False,
                        "error": "Modo 'edit' requiere parámetro 'code'",
                    }
                
                is_valid, errors = GDShaderParser.validate_shader_code(new_code)
                if not is_valid:
                    return {
                        "success": False,
                        "error": "Código editado no pasa validación",
                        "validation_errors": errors,
                    }
                
                with open(abs_shader_path, "w", encoding="utf-8") as f:
                    f.write(new_code)
                
                return {
                    "success": True,
                    "mode": "edit",
                    "shader_path": shader_path,
                    "replace_section": replace_section,
                    "new_line_count": len(new_code.splitlines()),
                    "message": f"Shader editado exitosamente",
                }
            
            elif mode == "delete":
                if not os.path.isfile(abs_shader_path):
                    return {
                        "success": False,
                        "error": f"Shader no encontrado: {shader_path}",
                    }
                
                os.remove(abs_shader_path)
                
                return {
                    "success": True,
                    "mode": "delete",
                    "shader_path": shader_path,
                    "message": f"Shader eliminado: {shader_path}",
                }
            
            else:
                return {
                    "success": False,
                    "error": f"Modo desconocido: {mode}. Use: create, edit, read, validate, delete, list_templates",
                }
        
        except Exception as e:
            logger.error(f"Error en manage_shader: {e}")
            return {
                "success": False,
                "error": f"Error inesperado: {str(e)}",
            }
    
    # ============ TOOL 2: manage_shader_material ============
    
    @require_session
    @mcp.tool()
    def manage_shader_material(
        session_id: str,
        project_path: str,
        mode: str,
        target_node: str,
        scene_path: str,
        shader_path: str = "",
        params: Optional[dict] = None,
        material_name: str = "",
        use_override: bool = True,
    ) -> dict:
        """
        Configurar ShaderMaterial y gestionar parámetros de shader.
        
        Puente entre shaders y nodos con workarounds de bugs integrados.
        
        Args:
            session_id: Session ID from start_session.
            project_path: Absolute path to the Godot project directory.
            mode: "create", "set_params", "read_params", "clear_params"
            target_node: Node path in scene (e.g., "Player/Sprite2D")
            scene_path: Path to the .tscn file (res:// or absolute)
            shader_path: Path to the .gdshader file (for create mode)
            params: Dict of shader parameters (e.g., {"u_speed": 2.5, "u_color": "red"})
            material_name: Name for the ShaderMaterial resource
            use_override: If True, uses material_override; else material
            
        Returns:
            Dict with success status, material info, and parameter details.
            
        Examples:
            # Create material with shader
            manage_shader_material(
                mode="create",
                target_node="Player/Sprite2D",
                scene_path="res://scenes/Player.tscn",
                shader_path="res://shaders/glow.gdshader"
            )
            
            # Set parameters (with double-set workaround)
            manage_shader_material(
                mode="set_params",
                target_node="Player/Sprite2D",
                scene_path="res://scenes/Player.tscn",
                params={"u_intensity": 1.5, "u_color": "#FF0000"}
            )
        """
        try:
            from godot_mcp.tools.node_tools import _ensure_tscn_path, _update_scene_file
            
            project_path = os.path.abspath(project_path)
            abs_scene_path = _ensure_tscn_path(_resolve_path(project_path, scene_path))
            
            if not os.path.isfile(abs_scene_path):
                return {
                    "success": False,
                    "error": f"Escena no encontrada: {scene_path}",
                }
            
            # Parsear escena
            scene = parse_tscn(abs_scene_path)
            
            # Encontrar nodo
            target_node_name = target_node.split("/")[-1]
            node = None
            for n in scene.nodes:
                if n.name == target_node_name:
                    node = n
                    break
            
            if not node:
                return {
                    "success": False,
                    "error": f"Nodo no encontrado: {target_node}",
                }
            
            if mode == "create":
                if not shader_path:
                    return {
                        "success": False,
                        "error": "mode='create' requiere shader_path",
                    }
                
                abs_shader = _resolve_path(project_path, shader_path)
                if not os.path.isfile(abs_shader):
                    return {
                        "success": False,
                        "error": f"Shader no encontrado: {shader_path}",
                    }
                
                shader_res_path = _path_to_res(project_path, abs_shader)
                
                # Crear o reutilizar ExtResource para shader
                shader_ext_id = None
                for ext in scene.ext_resources:
                    if ext.path == shader_res_path:
                        shader_ext_id = ext.id
                        break
                
                if not shader_ext_id:
                    shader_ext_id = f"ext_{uuid.uuid4().hex[:6]}"
                    scene.ext_resources.append(ExtResource(
                        id=shader_ext_id,
                        type="Shader",
                        path=shader_res_path,
                    ))
                
                # Crear SubResource para ShaderMaterial
                mat_id = material_name or f"ShaderMaterial_{uuid.uuid4().hex[:8]}"
                mat_resource = SubResource(
                    id=mat_id,
                    type="ShaderMaterial",
                    properties={
                        "shader": f'ExtResource("{shader_ext_id}")',
                    }
                )
                scene.sub_resources.append(mat_resource)
                
                # Asignar al nodo
                mat_prop = "material_override" if use_override else "material"
                node.properties[mat_prop] = f'SubResource("{mat_id}")'
                
                # Guardar
                scene.header.load_steps = 1 + len(scene.ext_resources) + len(scene.sub_resources)
                _update_scene_file(abs_scene_path, scene)
                _mark_scene_dirty(abs_scene_path)
                
                return {
                    "success": True,
                    "mode": "create",
                    "node": target_node,
                    "scene": scene_path,
                    "material_id": mat_id,
                    "shader": shader_path,
                    "message": f"ShaderMaterial creado y asignado a {target_node}",
                }
            
            elif mode == "set_params":
                if not params:
                    return {
                        "success": False,
                        "error": "mode='set_params' requiere params",
                    }
                
                mat_prop = "material_override" if use_override else "material"
                mat_ref = node.properties.get(mat_prop)
                
                if not mat_ref:
                    return {
                        "success": False,
                        "error": f"El nodo {target_node} no tiene material asignado",
                    }
                
                # Buscar el material en SubResources
                mat_resource = None
                for sub in scene.sub_resources:
                    if f'SubResource("{sub.id}")' == mat_ref or sub.id in mat_ref:
                        mat_resource = sub
                        break
                
                if not mat_resource:
                    return {
                        "success": False,
                        "error": "Material no encontrado en recursos de la escena",
                    }
                
                if mat_resource.type != "ShaderMaterial":
                    return {
                        "success": False,
                        "error": f"El material no es ShaderMaterial, es: {mat_resource.type}",
                    }
                
                # Añadir parámetros
                set_params = {}
                for param_name, value in params.items():
                    if not param_name.startswith("shader_parameter/"):
                        param_key = f"shader_parameter/{param_name}"
                    else:
                        param_key = param_name
                    
                    if isinstance(value, str) and value.startswith("#"):
                        value = f"Color{value}"
                    
                    mat_resource.properties[param_key] = value
                    set_params[param_name] = value
                
                # Workaround: añadir doble set
                for param_name, value in list(params.items()):
                    if not param_name.startswith("shader_parameter/"):
                        param_key = f"shader_parameter/{param_name}_workaround"
                    else:
                        param_key = f"{param_name}_workaround"
                    mat_resource.properties[param_key] = value
                
                scene.header.load_steps = 1 + len(scene.ext_resources) + len(scene.sub_resources)
                _update_scene_file(abs_scene_path, scene)
                _mark_scene_dirty(abs_scene_path)
                
                return {
                    "success": True,
                    "mode": "set_params",
                    "node": target_node,
                    "scene": scene_path,
                    "parameters_set": set_params,
                    "workaround_applied": "double_set",
                    "message": f"Parámetros seteados en {target_node} (con workaround)",
                }
            
            elif mode == "read_params":
                mat_prop = "material_override" if use_override else "material"
                mat_ref = node.properties.get(mat_prop)
                
                if not mat_ref:
                    return {
                        "success": False,
                        "error": f"El nodo {target_node} no tiene material",
                    }
                
                mat_resource = None
                for sub in scene.sub_resources:
                    if f'SubResource("{sub.id}")' == mat_ref or sub.id in mat_ref:
                        mat_resource = sub
                        break
                
                params = {}
                available_uniforms = []
                material_type = "unknown"
                
                if mat_resource:
                    material_type = mat_resource.type
                    for key, value in mat_resource.properties.items():
                        if key.startswith("shader_parameter/") and not key.endswith("_workaround"):
                            clean_key = key.replace("shader_parameter/", "")
                            params[clean_key] = value
                    
                    shader_ref = mat_resource.properties.get("shader")
                    if shader_ref:
                        for ext in scene.ext_resources:
                            if f'ExtResource("{ext.id}")' == shader_ref or ext.id in str(shader_ref):
                                abs_shader = _resolve_path(project_path, ext.path)
                                if os.path.isfile(abs_shader):
                                    parser = GDShaderParser()
                                    analysis = parser.parse_file(abs_shader)
                                    available_uniforms = [u.to_dict() for u in analysis.uniforms]
                                break
                
                return {
                    "success": True,
                    "mode": "read_params",
                    "node": target_node,
                    "scene": scene_path,
                    "current_params": params,
                    "available_uniforms": available_uniforms,
                    "material_type": material_type,
                }
            
            elif mode == "clear_params":
                mat_prop = "material_override" if use_override else "material"
                mat_ref = node.properties.get(mat_prop)
                
                if mat_ref:
                    for sub in scene.sub_resources:
                        if f'SubResource("{sub.id}")' == mat_ref or sub.id in mat_ref:
                            keys_to_remove = [k for k in sub.properties.keys() 
                                            if k.startswith("shader_parameter/")]
                            for k in keys_to_remove:
                                del sub.properties[k]
                            break
                
                scene.header.load_steps = 1 + len(scene.ext_resources) + len(scene.sub_resources)
                _update_scene_file(abs_scene_path, scene)
                _mark_scene_dirty(abs_scene_path)
                
                return {
                    "success": True,
                    "mode": "clear_params",
                    "node": target_node,
                    "message": "Parámetros de shader limpiados",
                }
            
            else:
                return {
                    "success": False,
                    "error": f"Modo desconocido: {mode}. Use: create, set_params, read_params, clear_params",
                }
        
        except Exception as e:
            logger.error(f"Error en manage_shader_material: {e}")
            return {
                "success": False,
                "error": f"Error inesperado: {str(e)}",
            }
    
    # ============ TOOL 3: create_render_pipeline ============
    
    @require_session
    @mcp.tool()
    def create_render_pipeline(
        session_id: str,
        project_path: str,
        pipeline_name: str,
        effects: list,
        resolution: Optional[dict] = None,
        output_to_screen: bool = True,
    ) -> dict:
        """
        Crear una cadena de efectos de post-procesado con SubViewports.
        
        Genera una escena .tscn completa con ColorRects encadenados,
        cada uno con su shader de post-procesado.
        
        Args:
            session_id: Session ID from start_session.
            project_path: Absolute path to the Godot project directory.
            pipeline_name: Path for the output scene (e.g., "res://pipelines/damage_postfx.tscn")
            effects: List of effect definitions. Each dict has:
                - shader: str - Path to .gdshader
                - params: dict - Shader parameters
                - blend_mode: str - "mix" | "add" | "multiply"
            resolution: Optional {"x": int, "y": int}. Default: 1280x720
            output_to_screen: If True, last effect renders to screen
            
        Returns:
            Dict with success status, scene path, and effect count.
            
        Example:
            create_render_pipeline(
                pipeline_name="res://pipelines/damage_postfx.tscn",
                effects=[
                    {"shader": "res://shaders/chromatic.gdshader", "params": {"u_offset": 3.0}},
                    {"shader": "res://shaders/vignette.gdshader", "params": {"u_intensity": 0.6}}
                ]
            )
        """
        try:
            from godot_mcp.tools.node_tools import (
                _ensure_tscn_path, _update_scene_file
            )
            
            project_path = os.path.abspath(project_path)
            abs_pipeline_path = _ensure_tscn_path(_resolve_path(project_path, pipeline_name))
            
            os.makedirs(os.path.dirname(abs_pipeline_path), exist_ok=True)
            
            res_width = resolution.get("x", 1280) if resolution else 1280
            res_height = resolution.get("y", 720) if resolution else 720
            
            # Crear escena base
            scene = Scene()
            scene.header.load_steps = 2
            scene.header.format = 3
            
            root = SceneNode(
                name="PostProcessPipeline",
                type="CanvasLayer",
                parent=".",
            )
            scene.nodes.append(root)
            
            # Añadir ColorRects para cada efecto
            effect_nodes = []
            
            for i, effect in enumerate(effects):
                effect_name = f"Effect{i}"
                
                rect = SceneNode(
                    name=effect_name,
                    type="ColorRect",
                    parent=".",
                    properties={
                        "offset_right": float(res_width),
                        "offset_bottom": float(res_height),
                        "mouse_filter": 2,
                    }
                )
                scene.nodes.append(rect)
                
                # Asignar shader
                shader_path = effect.get("shader", "")
                if shader_path:
                    abs_shader = _resolve_path(project_path, shader_path)
                    if os.path.isfile(abs_shader):
                        shader_res = _path_to_res(project_path, abs_shader)
                        
                        # ExtResource para shader
                        ext_id = f"ext_{uuid.uuid4().hex[:6]}"
                        scene.ext_resources.append(ExtResource(
                            id=ext_id,
                            type="Shader",
                            path=shader_res,
                        ))
                        
                        # SubResource para material
                        mat_id = f"mat_{effect_name}_{uuid.uuid4().hex[:4]}"
                        scene.sub_resources.append(SubResource(
                            id=mat_id,
                            type="ShaderMaterial",
                            properties={
                                "shader": f'ExtResource("{ext_id}")',
                            }
                        ))
                        
                        rect.properties["material"] = f'SubResource("{mat_id}")'
                        
                        # Setear parámetros
                        params = effect.get("params", {})
                        for param_name, value in params.items():
                            if not param_name.startswith("shader_parameter/"):
                                param_key = f"shader_parameter/{param_name}"
                            else:
                                param_key = param_name
                            
                            if isinstance(value, str) and value.startswith("#"):
                                value = f"Color{value}"
                            
                            for sub in scene.sub_resources:
                                if sub.id == mat_id:
                                    sub.properties[param_key] = value
                                    break
                
                effect_nodes.append({
                    "name": effect_name,
                    "shader": shader_path,
                    "params": effect.get("params", {}),
                })
            
            # Actualizar load_steps
            scene.header.load_steps = 1 + len(scene.ext_resources) + len(scene.sub_resources)
            
            # Guardar
            _update_scene_file(abs_pipeline_path, scene)
            _mark_scene_dirty(abs_pipeline_path)
            
            return {
                "success": True,
                "pipeline_name": pipeline_name,
                "absolute_path": abs_pipeline_path,
                "effect_count": len(effects),
                "effects": effect_nodes,
                "resolution": {"x": res_width, "y": res_height},
                "output_to_screen": output_to_screen,
                "message": f"Pipeline creado con {len(effects)} efectos",
            }
        
        except Exception as e:
            logger.error(f"Error en create_render_pipeline: {e}")
            return {
                "success": False,
                "error": f"Error inesperado: {str(e)}",
            }
    
    # ============ TOOL 4: analyze_shader ============
    
    @require_session
    @mcp.tool()
    def analyze_shader(
        session_id: str,
        project_path: str,
        shader_path: str,
        mode: str = "inspect",
        target_platform: str = "desktop",
        comparison_shader: str = "",
    ) -> dict:
        """
        Inteligencia y diagnóstico profundo de shaders.
        
        Analiza shaders existentes para extraer metadatos, detectar problemas
        y sugerir optimizaciones.
        
        Args:
            session_id: Session ID from start_session.
            project_path: Absolute path to the Godot project directory.
            shader_path: Path to the .gdshader file (res:// or absolute)
            mode: "inspect" | "optimize" | "compare" | "profile"
            target_platform: "desktop" | "mobile" | "web"
            comparison_shader: Path to second shader (for mode="compare")
            
        Returns:
            Dict with analysis results, warnings, and recommendations.
            
        Examples:
            # Full inspection
            analyze_shader(
                shader_path="res://shaders/water.gdshader",
                mode="inspect"
            )
            
            # Optimization suggestions
            analyze_shader(
                shader_path="res://shaders/expensive.gdshader",
                mode="optimize",
                target_platform="mobile"
            )
        """
        try:
            project_path = os.path.abspath(project_path)
            abs_shader_path = _resolve_path(project_path, shader_path)
            
            if not os.path.isfile(abs_shader_path):
                return {
                    "success": False,
                    "error": f"Shader no encontrado: {shader_path}",
                }
            
            parser = GDShaderParser()
            analysis = parser.parse_file(abs_shader_path)
            
            if mode == "inspect":
                return {
                    "success": True,
                    "mode": "inspect",
                    "shader_path": shader_path,
                    "analysis": analysis.to_dict(),
                    "summary": {
                        "type": analysis.shader_type,
                        "uniforms": len(analysis.uniforms),
                        "functions": len(analysis.functions),
                        "complexity_score": analysis.complexity["instruction_estimate"],
                        "warnings_count": len(analysis.warnings),
                    }
                }
            
            elif mode == "optimize":
                recommendations = []
                
                if target_platform == "mobile":
                    if analysis.complexity["texture_samples"] > 2:
                        recommendations.append({
                            "severity": "high",
                            "issue": f"{analysis.complexity['texture_samples']} texture samples",
                            "suggestion": "Reducir a máximo 2 en mobile. Considerar atlas texturas.",
                            "impact": "Alto - reduce fill rate",
                        })
                    
                    if analysis.complexity["branch_count"] > 3:
                        recommendations.append({
                            "severity": "medium",
                            "issue": f"{analysis.complexity['branch_count']} branches",
                            "suggestion": "Reemplazar if/else con step() y mix()",
                            "impact": "Medio - reduce divergencia de warps",
                        })
                    
                    if any("highp" not in str(w) for w in analysis.warnings):
                        recommendations.append({
                            "severity": "low",
                            "issue": "Precisión por defecto",
                            "suggestion": "Especificar mediump/highp explícitamente para mobile",
                            "impact": "Bajo - compatibilidad GLES",
                        })
                
                elif target_platform == "web":
                    if analysis.complexity["loop_count"] > 0:
                        recommendations.append({
                            "severity": "high",
                            "issue": "Loops en shader WebGL",
                            "suggestion": "WebGL 1.0 no soporta loops variables. Usar loops desenrollados.",
                            "impact": "Crítico - puede no compilar",
                        })
                
                if analysis.complexity["instruction_estimate"] > 200:
                    recommendations.append({
                        "severity": "high",
                        "issue": "Shader muy complejo",
                        "suggestion": "Considerar precalcular en vertex() o usar LOD de shaders",
                        "impact": "Alto - puede causar stalls",
                    })
                
                for varying in analysis.varyings:
                    if varying.type in {"vec3", "vec4"}:
                        recommendations.append({
                            "severity": "low",
                            "issue": f"Varying {varying.name} ({varying.type}) consume bandwidth",
                            "suggestion": "Usar vec2 si es posible, o pasar solo datos necesarios",
                            "impact": "Bajo - reduce interpolador usage",
                        })
                
                with open(abs_shader_path, "r") as f:
                    source = f.read()
                
                unused_uniforms = []
                for uniform in analysis.uniforms:
                    if source.count(uniform.name) <= 1:
                        unused_uniforms.append(uniform.name)
                
                if unused_uniforms:
                    recommendations.append({
                        "severity": "info",
                        "issue": f"Uniforms no usados: {', '.join(unused_uniforms)}",
                        "suggestion": "Eliminar uniforms no utilizados para reducir memory bandwidth",
                        "impact": "Info - cleanup",
                    })
                
                return {
                    "success": True,
                    "mode": "optimize",
                    "shader_path": shader_path,
                    "target_platform": target_platform,
                    "recommendations": recommendations,
                    "complexity": analysis.complexity,
                    "estimated_performance": {
                        "desktop": "good" if analysis.complexity["instruction_estimate"] < 100 else "acceptable" if analysis.complexity["instruction_estimate"] < 300 else "poor",
                        "mobile": "good" if analysis.complexity["instruction_estimate"] < 50 else "acceptable" if analysis.complexity["instruction_estimate"] < 150 else "poor",
                    }
                }
            
            elif mode == "compare":
                if not comparison_shader:
                    return {
                        "success": False,
                        "error": "mode='compare' requiere comparison_shader",
                    }
                
                abs_comp_path = _resolve_path(project_path, comparison_shader)
                if not os.path.isfile(abs_comp_path):
                    return {
                        "success": False,
                        "error": f"Shader de comparación no encontrado: {comparison_shader}",
                    }
                
                comp_parser = GDShaderParser()
                comp_analysis = comp_parser.parse_file(abs_comp_path)
                
                comparison = {
                    "shader_a": {
                        "path": shader_path,
                        "uniforms": len(analysis.uniforms),
                        "complexity": analysis.complexity["instruction_estimate"],
                    },
                    "shader_b": {
                        "path": comparison_shader,
                        "uniforms": len(comp_analysis.uniforms),
                        "complexity": comp_analysis.complexity["instruction_estimate"],
                    },
                    "diff": {
                        "uniforms_delta": len(comp_analysis.uniforms) - len(analysis.uniforms),
                        "complexity_delta": comp_analysis.complexity["instruction_estimate"] - analysis.complexity["instruction_estimate"],
                    },
                    "recommendation": "Shader A es más simple" if analysis.complexity["instruction_estimate"] < comp_analysis.complexity["instruction_estimate"] else "Shader B es más simple",
                }
                
                return {
                    "success": True,
                    "mode": "compare",
                    "comparison": comparison,
                }
            
            elif mode == "profile":
                return {
                    "success": True,
                    "mode": "profile",
                    "shader_path": shader_path,
                    "estimated_cost": {
                        "vertex_shader": "low" if analysis.complexity["function_count"] <= 2 else "medium",
                        "fragment_shader": "low" if analysis.complexity["instruction_estimate"] < 50 else "medium" if analysis.complexity["instruction_estimate"] < 200 else "high",
                        "bandwidth": "low" if len(analysis.uniforms) < 5 else "medium" if len(analysis.uniforms) < 15 else "high",
                        "fill_rate": "low" if analysis.complexity["texture_samples"] < 2 else "medium" if analysis.complexity["texture_samples"] < 5 else "high",
                    },
                    "bottleneck": "fragment" if analysis.complexity["instruction_estimate"] > 100 else "bandwidth" if len(analysis.uniforms) > 10 else "none",
                }
            
            else:
                return {
                    "success": False,
                    "error": f"Modo desconocido: {mode}. Use: inspect, optimize, compare, profile",
                }
        
        except Exception as e:
            logger.error(f"Error en analyze_shader: {e}")
            return {
                "success": False,
                "error": f"Error inesperado: {str(e)}",
            }
    
    logger.info("Shader tools registradas exitosamente")
