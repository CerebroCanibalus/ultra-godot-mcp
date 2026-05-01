"""
Screenshot Tools - Herramientas para capturar frames de escenas.

Capa 1: render_thumbnail
    Usa SubViewport en un script GDScript para capturar un frame.
    No requiere movie writer configurado. Funciona en cualquier proyecto.

Capa 2: capture_scene_frame
    Captura un frame específico usando SubViewport + run_gdscript.
    No requiere movie writer.

Capa 3: capture_scene_sequence
    Captura una secuencia de frames usando SubViewport.
    No requiere movie writer.

IMPORTANTE: Todas las herramientas escriben los archivos directamente al
filesystem via GDScript (image.save_png). NUNCA devuelven bytes binarios
en la respuesta MCP — solo metadata (ruta, dimensiones, etc.).

ANTI-ALUCINACIÓN: Cada tool exitoso incluye un WARNING explícito indicando
al agente que NO puede ver la imagen. Si el agente necesita analizar el
contenido visual, DEBE pedir al usuario que adjunte la imagen.
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Any, Optional, Tuple

from .base import GodotCLIWrapper
from .runtime_tools import run_gdscript

logger = logging.getLogger(__name__)


# ==================== CONSTANTES ====================

VISUAL_ACCESS_WARNING = (
    "⚠️  ATENCIÓN AGENTE: No tienes acceso visual a la imagen generada. "
    "El archivo se guardó en disco pero NO fue transmitido a tu contexto. "
    "Si necesitas analizar contenido visual (colores, formas, disposición de tiles, etc.), "
    "DEBES pedirle al usuario que adjunte/pegue la imagen en el chat. "
    "NO intentes describir o inferir el contenido visual basándote únicamente en metadatos."
)


# ==================== GDSCRIPT TEMPLATES ====================

# Helper GDScript para generar ASCII art desde Image
ASCII_PREVIEW_HELPER = '''
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
'''


RENDER_THUMBNAIL_SCRIPT = '''
extends SceneTree

''' + ASCII_PREVIEW_HELPER + '''

func _init():
    var scene_path = "{scene_path}"
    var output_path = "{output_path}"
    var resolution = Vector2i({width}, {height})
    var wait_frames = {wait_frames}
    var return_preview = {return_preview}
    
    # Check if running headless (no rendering available)
    if DisplayServer.get_name() == "headless":
        print("TEST_OUTPUT: " + JSON.stringify({{
            "success": false,
            "error": "Cannot render thumbnail in headless mode. Use a project with display server enabled.",
            "hint": "Run without --headless, or use render_thumbnail on a machine with GPU/display."
        }}))
        quit()
        return
    
    # Create SubViewport
    var viewport = SubViewport.new()
    viewport.size = resolution
    viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
    get_root().add_child(viewport)
    
    # Load and instantiate scene
    var scene = load(scene_path)
    if scene == null:
        print("TEST_OUTPUT: " + JSON.stringify({{
            "success": false,
            "error": "Failed to load scene: " + scene_path
        }}))
        quit()
        return
    
    var instance = scene.instantiate()
    viewport.add_child(instance)
    
    # Wait for rendering
    for i in range(wait_frames):
        await self.process_frame
    
    # Capture texture
    var texture = viewport.get_texture()
    var image = texture.get_image()
    
    # Save image
    var format = "{format}"
    var quality = {quality}
    var err = OK
    
    if format == "jpg" or format == "jpeg":
        var buffer = image.save_jpg_to_buffer(quality)
        var file = FileAccess.open(output_path, FileAccess.WRITE)
        if file:
            file.store_buffer(buffer)
            file.close()
        else:
            err = FAILED
    elif format == "webp":
        err = image.save_webp(output_path, true, quality)
    else:
        err = image.save_png(output_path)
    
    if err == OK:
        var file_size = FileAccess.get_file_as_bytes(output_path).size() if FileAccess.file_exists(output_path) else 0
        var result = {{
            "success": true,
            "image_path": output_path,
            "resolution": [image.get_width(), image.get_height()],
            "frames_waited": wait_frames,
            "format": format,
            "file_size_bytes": file_size
        }}
        
        if return_preview:
            result["preview_ascii"] = _generate_ascii_preview(image, 80, 40)
        
        print("TEST_OUTPUT: " + JSON.stringify(result))
    else:
        print("TEST_OUTPUT: " + JSON.stringify({{
            "success": false,
            "error": "Failed to save image, error code: " + str(err)
        }}))
    
    quit()
'''


CAPTURE_FRAME_SCRIPT = '''
extends SceneTree

''' + ASCII_PREVIEW_HELPER + '''

func _init():
    var scene_path = "{scene_path}"
    var output_path = "{output_path}"
    var resolution = Vector2i({width}, {height})
    var target_frame = {frame_number}
    var format = "{format}"
    var quality = {quality}
    var return_preview = {return_preview}
    
    if DisplayServer.get_name() == "headless":
        print("TEST_OUTPUT: " + JSON.stringify({{
            "success": false,
            "error": "Cannot capture frame in headless mode."
        }}))
        quit()
        return
    
    # Create SubViewport
    var viewport = SubViewport.new()
    viewport.size = resolution
    viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
    get_root().add_child(viewport)
    
    # Load and instantiate scene
    var scene = load(scene_path)
    if scene == null:
        print("TEST_OUTPUT: " + JSON.stringify({{
            "success": false,
            "error": "Failed to load scene: " + scene_path
        }}))
        quit()
        return
    
    var instance = scene.instantiate()
    viewport.add_child(instance)
    
    # Wait for target frame
    for i in range(target_frame):
        await self.process_frame
    
    # Capture
    var texture = viewport.get_texture()
    var image = texture.get_image()
    
    # Save image
    var err = OK
    if format == "jpg" or format == "jpeg":
        var buffer = image.save_jpg_to_buffer(quality)
        var file = FileAccess.open(output_path, FileAccess.WRITE)
        if file:
            file.store_buffer(buffer)
            file.close()
        else:
            err = FAILED
    elif format == "webp":
        err = image.save_webp(output_path, true, quality)
    else:
        err = image.save_png(output_path)
    
    if err == OK:
        var result = {{
            "success": true,
            "image_path": output_path,
            "resolution": [image.get_width(), image.get_height()],
            "frame_captured": target_frame,
            "format": format
        }}
        
        if return_preview:
            result["preview_ascii"] = _generate_ascii_preview(image, 80, 40)
        
        print("TEST_OUTPUT: " + JSON.stringify(result))
    else:
        print("TEST_OUTPUT: " + JSON.stringify({{
            "success": false,
            "error": "Failed to save image, error code: " + str(err)
        }}))
    
    quit()
'''


CAPTURE_SEQUENCE_SCRIPT = '''
extends SceneTree

''' + ASCII_PREVIEW_HELPER + '''

func _init():
    var scene_path = "{scene_path}"
    var output_dir = "{output_dir}"
    var resolution = Vector2i({width}, {height})
    var frame_count = {frame_count}
    var fps = {fps}
    var format = "{format}"
    var quality = {quality}
    var return_preview = {return_preview}
    
    if DisplayServer.get_name() == "headless":
        print("TEST_OUTPUT: " + JSON.stringify({{
            "success": false,
            "error": "Cannot capture sequence in headless mode."
        }}))
        quit()
        return
    
    # Create SubViewport
    var viewport = SubViewport.new()
    viewport.size = resolution
    viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
    get_root().add_child(viewport)
    
    # Load and instantiate scene
    var scene = load(scene_path)
    if scene == null:
        print("TEST_OUTPUT: " + JSON.stringify({{
            "success": false,
            "error": "Failed to load scene: " + scene_path
        }}))
        quit()
        return
    
    var instance = scene.instantiate()
    viewport.add_child(instance)
    
    # Ensure output directory exists
    var dir = DirAccess.open("res://")
    if dir == null:
        pass
    
    # Capture frames
    var frame_paths = []
    var first_image = null
    for i in range(frame_count):
        await self.process_frame
        
        var texture = viewport.get_texture()
        var image = texture.get_image()
        
        if i == 0 and return_preview:
            first_image = image.duplicate()
        
        var ext = ".png"
        if format == "jpg" or format == "jpeg":
            ext = ".jpg"
        elif format == "webp":
            ext = ".webp"
        
        var frame_path = output_dir + "/frame_" + str(i + 1).pad_zeros(4) + ext
        var err = OK
        if format == "jpg" or format == "jpeg":
            var buffer = image.save_jpg_to_buffer(quality)
            var file = FileAccess.open(frame_path, FileAccess.WRITE)
            if file:
                file.store_buffer(buffer)
                file.close()
            else:
                err = FAILED
        elif format == "webp":
            err = image.save_webp(frame_path, true, quality)
        else:
            err = image.save_png(frame_path)
        
        if err == OK:
            frame_paths.append(frame_path)
    
    var result = {{
        "success": true,
        "frame_paths": frame_paths,
        "frame_count": frame_paths.size(),
        "requested_frames": frame_count,
        "output_dir": output_dir,
        "format": format
    }}
    
    if return_preview and first_image != null:
        result["preview_ascii"] = _generate_ascii_preview(first_image, 80, 40)
    
    print("TEST_OUTPUT: " + JSON.stringify(result))
    
    quit()
'''


# ==================== HELPER ====================

def _extract_test_output(result: dict[str, Any]) -> Optional[dict[str, Any]]:
    """Extract TEST_OUTPUT from run_command result.
    
    run_command returns prints in 'prints' list, not 'test_output'.
    This helper parses the first valid TEST_OUTPUT found.
    """
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


def render_thumbnail(
    project_path: str,
    scene_path: str,
    output_path: Optional[str] = None,
    resolution: Optional[Tuple[int, int]] = None,
    wait_frames: int = 3,
    format: str = "jpeg",
    quality: float = 0.85,
    return_preview: bool = False,
    godot_path: Optional[str] = None,
    timeout: int = 60,
) -> dict[str, Any]:
    """
    Render a thumbnail of a scene using SubViewport.

    Uses a SubViewport to render the scene and save as image.
    Supports PNG, JPEG, and WebP formats.
    Runs Godot WITHOUT --headless to allow GPU rendering.
    A brief window may appear.

    IMPORTANT: The agent CANNOT see the generated image. If visual analysis is
    needed, the user must attach the image manually.

    Args:
        project_path: Absolute path to the Godot project.
        scene_path: Path to the scene to render (res://...).
        output_path: Where to save the image. If None, uses temp directory.
        resolution: Optional (width, height). Default: 1280x720.
        wait_frames: Frames to wait before capturing (for shaders to compile).
        format: Image format: "png", "jpeg" (default), or "webp".
        quality: JPEG/WebP quality (0.0-1.0). Default: 0.85.
        return_preview: If True, generates an ASCII art preview of the image.
                        Useful for getting a rough idea of composition without
                        requiring the user to attach the image.
        godot_path: Optional path to Godot executable.
        timeout: Maximum seconds to wait.

    Returns:
        Dict with success, image_path, resolution, format, file_size_bytes,
        and optionally preview_ascii. Includes anti-hallucination warning.

    Example:
        render_thumbnail(
            project_path="D:/MyGame",
            scene_path="res://scenes/Main.tscn",
            output_path="D:/tmp/thumbnail.jpg",
            resolution=(1280, 720),
            format="jpeg",
            quality=0.85
        )
    """
    cli = GodotCLIWrapper(godot_path)
    
    is_valid, error = cli.validate_project(project_path)
    if not is_valid:
        return {"success": False, "error": error}
    
    if not output_path:
        ext = ".jpg" if format in ("jpeg", "jpg") else (".webp" if format == "webp" else ".png")
        output_path = os.path.join(
            tempfile.gettempdir(), f"thumbnail_{os.getpid()}{ext}"
        )
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    width = resolution[0] if resolution else 1280
    height = resolution[1] if resolution else 720
    
    script = RENDER_THUMBNAIL_SCRIPT.format(
        scene_path=scene_path,
        output_path=output_path.replace("\\", "/"),
        width=width,
        height=height,
        wait_frames=wait_frames,
        format=format,
        quality=quality,
        return_preview=str(return_preview).lower(),
    )
    
    # Run WITHOUT --headless to allow GPU rendering
    script_file = os.path.join(tempfile.gettempdir(), f"thumb_script_{os.getpid()}.gd")
    try:
        with open(script_file, "w", encoding="utf-8") as f:
            f.write(script)
        
        args = ["--script", script_file]
        result = cli.run_command(args, project_path=project_path, timeout=timeout)
        
        # Extract TEST_OUTPUT from prints (run_command uses 'prints', not 'output')
        test_output = _extract_test_output(result)
        
        if test_output and isinstance(test_output, dict):
            # If GDScript succeeded, return its result regardless of project errors
            if test_output.get("success"):
                return _add_visual_warning(test_output)
            # If GDScript explicitly failed, return its error
            return test_output
        
        # Check for headless error
        for line in result.get("prints", []):
            if "headless" in line.lower():
                return {
                    "success": False,
                    "error": "Thumbnail rendering requires a display/GPU. In headless environments, use a machine with GPU or configure Xvfb/virtual display.",
                    "raw_output": result.get("prints", []),
                }
        
        return {
            "success": False,
            "error": "Thumbnail rendering failed",
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


def capture_scene_frame(
    project_path: str,
    scene_path: str,
    frame_number: int = 1,
    output_path: Optional[str] = None,
    resolution: Optional[Tuple[int, int]] = None,
    format: str = "jpeg",
    quality: float = 0.85,
    return_preview: bool = False,
    godot_path: Optional[str] = None,
    timeout: int = 60,
) -> dict[str, Any]:
    """
    Capture a specific frame from a running scene.

    Uses SubViewport + run_gdscript. Does NOT require movie writer.

    IMPORTANT: The agent CANNOT see the generated image. If visual analysis is
    needed, the user must attach the image manually.

    Args:
        project_path: Absolute path to the Godot project.
        scene_path: Path to the scene to run.
        frame_number: Which frame to capture (1-based).
        output_path: Where to save the image. If None, uses temp directory.
        resolution: Optional (width, height) for the capture. Default: 1280x720.
        format: Image format: "png", "jpeg" (default), or "webp".
        quality: JPEG/WebP quality (0.0-1.0). Default: 0.85.
        return_preview: If True, generates an ASCII art preview.
        godot_path: Optional path to Godot executable.
        timeout: Maximum seconds to wait.

    Returns:
        Dict with success, image_path, resolution, frame_captured, format,
        and optionally preview_ascii. Includes anti-hallucination warning.

    Example:
        capture_scene_frame(
            project_path="D:/MyGame",
            scene_path="res://scenes/Main.tscn",
            frame_number=30,
            output_path="D:/tmp/screenshot.jpg",
            resolution=(1280, 720),
            format="jpeg"
        )
    """
    if not output_path:
        ext = ".jpg" if format in ("jpeg", "jpg") else (".webp" if format == "webp" else ".png")
        output_path = os.path.join(
            tempfile.gettempdir(), f"frame_capture_{os.getpid()}{ext}"
        )
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    width = resolution[0] if resolution else 1280
    height = resolution[1] if resolution else 720
    
    script = CAPTURE_FRAME_SCRIPT.format(
        scene_path=scene_path,
        output_path=output_path.replace("\\", "/"),
        width=width,
        height=height,
        frame_number=frame_number,
        format=format,
        quality=quality,
        return_preview=str(return_preview).lower(),
    )
    
    cli = GodotCLIWrapper(godot_path)
    
    is_valid, error = cli.validate_project(project_path)
    if not is_valid:
        return {"success": False, "error": error}
    
    # Run WITHOUT --headless to allow GPU rendering
    script_file = os.path.join(tempfile.gettempdir(), f"frame_script_{os.getpid()}.gd")
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
        
        return {
            "success": False,
            "error": "Frame capture failed",
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


def capture_scene_sequence(
    project_path: str,
    scene_path: str,
    frame_count: int = 30,
    output_dir: Optional[str] = None,
    fps: int = 60,
    resolution: Optional[Tuple[int, int]] = None,
    format: str = "jpeg",
    quality: float = 0.85,
    return_preview: bool = False,
    godot_path: Optional[str] = None,
    timeout: int = 120,
) -> dict[str, Any]:
    """
    Capture a sequence of frames from a running scene.

    Uses SubViewport + run_gdscript. Does NOT require movie writer.

    IMPORTANT: The agent CANNOT see the generated images. If visual analysis is
    needed, the user must attach images manually.

    Args:
        project_path: Absolute path to the Godot project.
        scene_path: Path to the scene to run.
        frame_count: Number of frames to capture.
        output_dir: Directory to save frames. If None, uses temp directory.
        fps: Frames per second.
        resolution: Optional (width, height). Default: 1280x720.
        format: Image format: "png", "jpeg" (default), or "webp".
        quality: JPEG/WebP quality (0.0-1.0). Default: 0.85.
        return_preview: If True, generates an ASCII art preview of the first frame.
        godot_path: Optional path to Godot executable.
        timeout: Maximum seconds to wait.

    Returns:
        Dict with success, frame_paths, frame_count, duration_seconds, format,
        and optionally preview_ascii. Includes anti-hallucination warning.

    Example:
        capture_scene_sequence(
            project_path="D:/MyGame",
            scene_path="res://scenes/Main.tscn",
            frame_count=60,
            output_dir="D:/tmp/frames",
            fps=30,
            resolution=(1280, 720),
            format="jpeg"
        )
    """
    if not output_dir:
        output_dir = os.path.join(tempfile.gettempdir(), f"sequence_{os.getpid()}")
    
    os.makedirs(output_dir, exist_ok=True)
    
    width = resolution[0] if resolution else 1280
    height = resolution[1] if resolution else 720
    
    script = CAPTURE_SEQUENCE_SCRIPT.format(
        scene_path=scene_path,
        output_dir=output_dir.replace("\\", "/"),
        width=width,
        height=height,
        frame_count=frame_count,
        fps=fps,
        format=format,
        quality=quality,
        return_preview=str(return_preview).lower(),
    )
    
    cli = GodotCLIWrapper(godot_path)
    
    is_valid, error = cli.validate_project(project_path)
    if not is_valid:
        return {"success": False, "error": error}
    
    # Run WITHOUT --headless to allow GPU rendering
    script_file = os.path.join(tempfile.gettempdir(), f"sequence_script_{os.getpid()}.gd")
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
        
        return {
            "success": False,
            "error": "Sequence capture failed",
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


def register_screenshot_tools(mcp) -> None:
    """Register all screenshot tools."""
    logger.info("Registrando screenshot tools...")
    
    mcp.add_tool(capture_scene_frame)
    mcp.add_tool(capture_scene_sequence)
    mcp.add_tool(render_thumbnail)
    
    logger.info("[OK] 3 screenshot tools registradas")
