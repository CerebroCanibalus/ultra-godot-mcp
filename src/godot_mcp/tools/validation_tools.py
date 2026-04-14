"""
Validation Tools - Herramientas MCP para validar escenas y scripts.

Expone los validadores TSCN y GDScript como herramientas MCP
para que los LLMs puedan verificar archivos antes de guardarlos.
"""

from __future__ import annotations

import logging
import os

from fastmcp import FastMCP

from godot_mcp.core.gdscript_validator import (
    GDScriptValidator,
    validate_gdscript as _validate_gdscript_core,
)
from godot_mcp.core.tscn_parser import parse_tscn
from godot_mcp.core.tscn_validator import (
    TSCNValidator,
    validate_scene as _validate_tscn_core,
)

logger = logging.getLogger(__name__)


def validate_tscn(
    scene_path: str,
    project_path: str | None = None,
    strict: bool = False,
) -> dict:
    """
    Validate a TSCN scene file for common errors.

    Checks:
    - Root node has no parent attribute
    - Unique ExtResource/SubResource IDs
    - Valid resource references (no orphaned SubResources)
    - Valid node types
    - Valid parent paths (hierarchical chains)
    - ExtResource files exist on disk (if project_path provided)
    - Valid gd_scene header (load_steps, format)

    Args:
        scene_path: Absolute or relative path to the .tscn file.
        project_path: Absolute path to the Godot project (for file existence checks).
        strict: If True, warnings also block validation.

    Returns:
        Dict with validation results:
        - success: True if scene is valid
        - errors: List of error messages
        - warnings: List of warning messages
        - infos: List of informational messages
        - scene_path: The validated scene path

    Example:
        result = validate_tscn("scenes/Player.tscn", project_path="D:/MyGame")
        if not result["success"]:
            print(f"Errors: {result['errors']}")
    """
    try:
        # Normalize path
        if not scene_path.endswith(".tscn"):
            scene_path = scene_path + ".tscn"

        # Check file exists
        if not os.path.isfile(scene_path):
            return {
                "success": False,
                "error": f"Scene file not found: {scene_path}",
            }

        # Parse scene
        scene = parse_tscn(scene_path)

        # Validate
        validator = TSCNValidator(project_path=project_path)
        result = validator.validate(scene)

        # In strict mode, warnings also count as failures
        is_valid = result.is_valid
        if strict and result.warnings:
            is_valid = False

        return {
            "success": is_valid,
            "scene_path": scene_path,
            "errors": result.errors,
            "warnings": result.warnings,
            "infos": result.infos,
            "error_count": len(result.errors),
            "warning_count": len(result.warnings),
            "info_count": len(result.infos),
        }

    except Exception as e:
        logger.exception(f"Error validating TSCN: {e}")
        return {
            "success": False,
            "error": str(e),
            "scene_path": scene_path,
        }


def validate_gdscript(
    script_path: str | None = None,
    script_content: str | None = None,
    strict: bool = False,
) -> dict:
    """
    Validate a GDScript file for common errors.

    Checks:
    - Undeclared variables (warnings)
    - Undeclared functions (warnings)
    - Node references with $ (info)
    - Built-in function recognition

    NOTE: This is static analysis, not a full parser.
    It may produce false positives for complex patterns.

    Args:
        script_path: Path to the .gd file (mutually exclusive with script_content).
        script_content: Raw GDScript content (mutually exclusive with script_path).
        strict: If True, warnings also block validation.

    Returns:
        Dict with validation results:
        - success: True if script is valid
        - issues: List of {line, severity, message, suggestion}
        - error_count: Number of errors
        - warning_count: Number of warnings
        - info_count: Number of info messages

    Example:
        result = validate_gdscript(script_path="scripts/player.gd")
        for issue in result["issues"]:
            print(f"Line {issue['line']}: {issue['message']}")
    """
    try:
        # Get script content
        if script_path and script_content:
            return {
                "success": False,
                "error": "Provide either script_path OR script_content, not both",
            }

        if script_path:
            if not script_path.endswith(".gd"):
                script_path = script_path + ".gd"

            if not os.path.isfile(script_path):
                return {
                    "success": False,
                    "error": f"Script file not found: {script_path}",
                }

            with open(script_path, "r", encoding="utf-8") as f:
                content = f.read()
        elif script_content:
            content = script_content
        else:
            return {
                "success": False,
                "error": "Provide either script_path or script_content",
            }

        # Validate
        result = _validate_gdscript_core(content)

        # In strict mode, warnings also count as failures
        has_errors = any(i.severity == "error" for i in result.issues)
        has_warnings = any(i.severity == "warning" for i in result.issues)

        is_valid = not has_errors
        if strict and has_warnings:
            is_valid = False

        # Convert issues to dicts for JSON serialization
        issues = [
            {
                "line": issue.line,
                "severity": issue.severity,
                "message": issue.message,
                "suggestion": issue.suggestion,
            }
            for issue in result.issues
        ]

        error_count = sum(1 for i in result.issues if i.severity == "error")
        warning_count = sum(1 for i in result.issues if i.severity == "warning")
        info_count = sum(1 for i in result.issues if i.severity == "info")

        return {
            "success": is_valid,
            "script_path": script_path or "(inline content)",
            "issues": issues,
            "error_count": error_count,
            "warning_count": warning_count,
            "info_count": info_count,
        }

    except Exception as e:
        logger.exception(f"Error validating GDScript: {e}")
        return {
            "success": False,
            "error": str(e),
            "script_path": script_path or "(inline content)",
        }


def validate_project(
    project_path: str,
    strict: bool = False,
) -> dict:
    """
    Validate all TSCN and GDScript files in a Godot project.

    Scans the project directory recursively for .tscn and .gd files
    and validates each one.

    Args:
        project_path: Absolute path to the Godot project directory.
        strict: If True, warnings also count as failures.

    Returns:
        Dict with summary of validation results across all files.

    Example:
        result = validate_project("D:/MyGame")
        print(f"Validated {result['files_checked']} files")
        print(f"Errors: {result['total_errors']}, Warnings: {result['total_warnings']}")
    """
    try:
        if not os.path.isdir(project_path):
            return {
                "success": False,
                "error": f"Project path does not exist: {project_path}",
            }

        # Check for project.godot
        if not os.path.isfile(os.path.join(project_path, "project.godot")):
            return {
                "success": False,
                "error": f"Not a valid Godot project (no project.godot): {project_path}",
            }

        results = {
            "success": True,
            "project_path": project_path,
            "files_checked": 0,
            "total_errors": 0,
            "total_warnings": 0,
            "total_infos": 0,
            "file_results": [],
        }

        # Find all .tscn and .gd files
        from pathlib import Path

        base = Path(project_path)
        tscn_files = list(base.glob("**/*.tscn"))
        gd_files = list(base.glob("**/*.gd"))

        # Validate TSCN files
        for tscn_file in tscn_files:
            file_result = validate_tscn(
                str(tscn_file), project_path=project_path, strict=strict
            )
            results["files_checked"] += 1
            results["total_errors"] += file_result.get("error_count", 0)
            results["total_warnings"] += file_result.get("warning_count", 0)
            results["total_infos"] += file_result.get("info_count", 0)

            if not file_result.get("success", True):
                results["success"] = False

            results["file_results"].append(
                {
                    "file": str(tscn_file.relative_to(base)),
                    "type": "tscn",
                    "success": file_result.get("success", False),
                    "errors": file_result.get("errors", []),
                    "warnings": file_result.get("warnings", []),
                }
            )

        # Validate GDScript files
        for gd_file in gd_files:
            file_result = validate_gdscript(script_path=str(gd_file), strict=strict)
            results["files_checked"] += 1
            results["total_errors"] += file_result.get("error_count", 0)
            results["total_warnings"] += file_result.get("warning_count", 0)
            results["total_infos"] += file_result.get("info_count", 0)

            if not file_result.get("success", True):
                results["success"] = False

            results["file_results"].append(
                {
                    "file": str(gd_file.relative_to(base)),
                    "type": "gd",
                    "success": file_result.get("success", False),
                    "issues": file_result.get("issues", []),
                }
            )

        return results

    except Exception as e:
        logger.exception(f"Error validating project: {e}")
        return {
            "success": False,
            "error": str(e),
            "project_path": project_path,
        }


# ============ REGISTRATION ============


def register_validation_tools(mcp: FastMCP) -> None:
    """
    Register all validation tools with a FastMCP server.

    Args:
        mcp: FastMCP instance to register tools with
    """
    mcp.add_tool(validate_tscn)
    mcp.add_tool(validate_gdscript)
    mcp.add_tool(validate_project)
    logger.info("[OK] 3 validation tools registered")
