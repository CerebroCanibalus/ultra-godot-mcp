"""
Debug Tools - Herramienta para ejecutar Godot headless y capturar debug output.

Permite validar escenas y scripts ejecutándolos con el motor Godot real,
capturando errores, warnings y prints del output del motor.
"""

from __future__ import annotations

import logging
import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Rutas comunes donde buscar el ejecutable de Godot
GODOT_SEARCH_PATHS = [
    # Windows - versiones específicas del General
    r"D:\Mis Juegos\Godot",
    # Windows - ubicaciones comunes
    r"C:\Program Files\Godot",
    r"C:\Program Files (x86)\Godot",
    # Linux
    "/usr/local/bin",
    "/usr/bin",
    # macOS
    "/Applications",
]

# Nombres de ejecutables a buscar (orden de preferencia: más reciente primero)
GODOT_EXECUTABLE_NAMES = [
    "Godot_v4.6.1-stable_win64_console.exe",
    "Godot_v4.6.1-stable_win64.exe",
    "Godot_v4.5.1-stable_win64_console.exe",
    "Godot_v4.5.1-stable_win64.exe",
    "Godot_v4.5-stable_win64_console.exe",
    "Godot_v4.5-stable_win64.exe",
    "godot",  # Linux/macOS
    "Godot",  # macOS
]


def _find_godot_executable() -> Optional[str]:
    """
    Find Godot executable in common locations.

    Returns:
        Absolute path to Godot executable, or None if not found.
    """
    # First check if godot is in PATH
    import shutil

    godot_in_path = shutil.which("godot") or shutil.which("Godot")
    if godot_in_path:
        return godot_in_path

    # Search in common paths
    for search_path in GODOT_SEARCH_PATHS:
        if not os.path.exists(search_path):
            continue

        for exe_name in GODOT_EXECUTABLE_NAMES:
            candidate = os.path.join(search_path, exe_name)
            if os.path.isfile(candidate):
                return candidate

    return None


def _parse_log_output(log_content: str) -> dict[str, list[str]]:
    """
    Parse Godot log output into categorized messages.

    Godot output format:
    - ERROR: ...
    - WARNING: ...
    - USER SCRIPT: ... (prints from print())
    - At: ... (stack trace lines)
    - Other lines (info, debug, etc.)

    Returns:
        Dict with keys: errors, warnings, prints, info, stack_traces
    """
    errors = []
    warnings = []
    prints = []
    info = []
    stack_traces = []

    for line in log_content.splitlines():
        line = line.strip()
        if not line:
            continue

        # Error lines
        if line.startswith("ERROR:") or line.startswith("ERROR "):
            errors.append(line)
        elif line.startswith("At:"):
            stack_traces.append(line)
        elif line.startswith("WARNING:") or line.startswith("WARNING "):
            warnings.append(line)
        elif line.startswith("USER SCRIPT:") or line.startswith("   at"):
            # Script prints often have this format
            prints.append(line)
        elif line.startswith("SCRIPT ERROR:"):
            errors.append(line)
        elif line.startswith("   "):
            # Indented lines are usually stack traces or continuation
            stack_traces.append(line)
        else:
            info.append(line)

    return {
        "errors": errors,
        "warnings": warnings,
        "prints": prints,
        "info": info,
        "stack_traces": stack_traces,
    }


def run_debug_scene(
    project_path: str,
    scene_path: Optional[str] = None,
    godot_path: Optional[str] = None,
    timeout: int = 30,
    debug_collisions: bool = False,
    debug_paths: bool = False,
    debug_navigation: bool = False,
) -> dict[str, Any]:
    """
    Run a Godot scene in headless mode and capture debug output.

    This executes Godot with --headless --log-file to capture all output,
    then parses the log for errors, warnings, and prints.

    Args:
        project_path: Absolute path to the Godot project (must contain project.godot).
        scene_path: Optional scene path to run (res://... or relative). If None, runs main scene.
        godot_path: Optional path to Godot executable. If None, auto-detects.
        timeout: Maximum seconds to wait for Godot to finish (default: 30).
        debug_collisions: Enable --debug-collisions flag.
        debug_paths: Enable --debug-paths flag.
        debug_navigation: Enable --debug-navigation flag.

    Returns:
        Dict with:
        - success: bool
        - errors: list of error messages
        - warnings: list of warning messages
        - prints: list of print() output from scripts
        - info: list of other log messages
        - stack_traces: list of stack trace lines
        - exit_code: Godot process exit code
        - godot_path: Path to Godot executable used
        - log_file: Path to the generated log file (for inspection)
        - error: Error message if something went wrong

    Examples:
        # Run main scene
        run_debug_scene(project_path="D:/MyGame")

        # Run specific scene with collision debug
        run_debug_scene(
            project_path="D:/MyGame",
            scene_path="res://scenes/Player.tscn",
            debug_collisions=True,
            timeout=10
        )

        # With explicit Godot path
        run_debug_scene(
            project_path="D:/MyGame",
            godot_path="D:/Godot/Godot_v4.6.1-stable_win64.exe"
        )
    """
    # Validate project path
    project_path = os.path.abspath(project_path)
    if not os.path.isdir(project_path):
        return {"success": False, "error": f"Project path not found: {project_path}"}

    project_godot = os.path.join(project_path, "project.godot")
    if not os.path.isfile(project_godot):
        return {
            "success": False,
            "error": f"Not a valid Godot project (no project.godot): {project_path}",
        }

    # Find Godot executable
    godot_exe = godot_path or _find_godot_executable()
    if not godot_exe:
        return {
            "success": False,
            "error": "Godot executable not found. Provide godot_path or install Godot in a common location.",
            "searched_paths": GODOT_SEARCH_PATHS,
        }

    if not os.path.isfile(godot_exe):
        return {
            "success": False,
            "error": f"Godot executable not found at: {godot_exe}",
        }

    # Create temporary log file
    log_file = os.path.join(tempfile.gettempdir(), f"godot_debug_{os.getpid()}.log")

    # Build command
    cmd = [
        godot_exe,
        "--headless",
        "--path",
        project_path,
        "--log-file",
        log_file,
        "--quit-after",
        "1",  # Quit after 1 iteration (fast validation)
    ]

    # Add scene if specified
    if scene_path:
        cmd.append(scene_path)

    # Add debug flags
    if debug_collisions:
        cmd.append("--debug-collisions")
    if debug_paths:
        cmd.append("--debug-paths")
    if debug_navigation:
        cmd.append("--debug-navigation")

    logger.info(f"Running Godot: {' '.join(cmd)}")

    try:
        # Execute Godot
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
        )

        # Read log file
        log_content = ""
        if os.path.exists(log_file):
            with open(log_file, "r", encoding="utf-8", errors="replace") as f:
                log_content = f.read()

        # Also capture stdout/stderr
        stdout_content = result.stdout or ""
        stderr_content = result.stderr or ""

        # Combine all output
        combined_output = log_content + "\n" + stdout_content + "\n" + stderr_content

        # Parse output
        parsed = _parse_log_output(combined_output)

        return {
            "success": result.returncode == 0,
            "errors": parsed["errors"],
            "warnings": parsed["warnings"],
            "prints": parsed["prints"],
            "info": parsed["info"],
            "stack_traces": parsed["stack_traces"],
            "exit_code": result.returncode,
            "godot_path": godot_exe,
            "log_file": log_file,
            "scene_path": scene_path,
            "project_path": project_path,
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": f"Godot timed out after {timeout} seconds",
            "godot_path": godot_exe,
            "log_file": log_file,
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to run Godot: {e}",
            "godot_path": godot_exe,
        }


def check_script_syntax(
    project_path: str,
    script_path: str,
    godot_path: Optional[str] = None,
    timeout: int = 30,
) -> dict[str, Any]:
    """
    Check GDScript syntax by parsing it with Godot's --check-only flag.

    Args:
        project_path: Absolute path to the Godot project.
        script_path: Path to the script (res://... or relative).
        godot_path: Optional path to Godot executable.
        timeout: Maximum seconds to wait.

    Returns:
        Dict with success, errors, warnings, etc.

    Examples:
        check_script_syntax(
            project_path="D:/MyGame",
            script_path="res://scripts/player.gd"
        )
    """
    project_path = os.path.abspath(project_path)
    if not os.path.isdir(project_path):
        return {"success": False, "error": f"Project path not found: {project_path}"}

    project_godot = os.path.join(project_path, "project.godot")
    if not os.path.isfile(project_godot):
        return {"success": False, "error": f"Not a valid Godot project: {project_path}"}

    godot_exe = godot_path or _find_godot_executable()
    if not godot_exe:
        return {
            "success": False,
            "error": "Godot executable not found.",
        }

    log_file = os.path.join(tempfile.gettempdir(), f"godot_syntax_{os.getpid()}.log")

    cmd = [
        godot_exe,
        "--headless",
        "--path",
        project_path,
        "--log-file",
        log_file,
        "--check-only",
        "--script",
        script_path,
    ]

    logger.info(f"Checking script syntax: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
        )

        log_content = ""
        if os.path.exists(log_file):
            with open(log_file, "r", encoding="utf-8", errors="replace") as f:
                log_content = f.read()

        combined = (
            log_content + "\n" + (result.stdout or "") + "\n" + (result.stderr or "")
        )
        parsed = _parse_log_output(combined)

        # --check-only returns 0 if syntax is OK
        return {
            "success": result.returncode == 0,
            "errors": parsed["errors"],
            "warnings": parsed["warnings"],
            "exit_code": result.returncode,
            "script_path": script_path,
            "godot_path": godot_exe,
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": f"Godot timed out after {timeout} seconds",
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to check script: {e}",
        }


# ============ REGISTRATION ============


def register_debug_tools(mcp) -> None:
    """
    Register all debug tools.

    Args:
        mcp: FastMCP instance to register tools on.
    """
    logger.info("Registrando debug tools...")

    mcp.add_tool(run_debug_scene)
    mcp.add_tool(check_script_syntax)

    logger.info("[OK] 2 debug tools registradas")
