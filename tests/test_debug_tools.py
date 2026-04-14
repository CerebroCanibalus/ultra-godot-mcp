"""Tests for debug tools."""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from godot_mcp.tools.debug_tools import (
    _find_godot_executable,
    _parse_log_output,
    run_debug_scene,
    check_script_syntax,
    GODOT_SEARCH_PATHS,
)


class TestFindGodotExecutable:
    def test_returns_string_when_found(self):
        # En el sistema del General, Godot existe
        result = _find_godot_executable()
        # Puede ser None si no está en PATH ni en paths comunes
        # Pero en el sistema del General debería encontrarlo
        if result is not None:
            assert isinstance(result, str)
            assert os.path.isfile(result)


class TestParseLogOutput:
    def test_parse_error_lines(self):
        log = """ERROR: Null instance detected
   At: res://scripts/player.gd:42
WARNING: Unused variable
USER SCRIPT: Player spawned
INFO: Godot Engine v4.6.1"""
        result = _parse_log_output(log)
        assert len(result["errors"]) == 1
        assert "Null instance" in result["errors"][0]
        assert len(result["warnings"]) == 1
        assert len(result["prints"]) == 1
        assert "Player spawned" in result["prints"][0]

    def test_parse_empty_log(self):
        result = _parse_log_output("")
        assert result["errors"] == []
        assert result["warnings"] == []
        assert result["prints"] == []

    def test_parse_multiple_errors(self):
        log = """ERROR: First error
ERROR: Second error
WARNING: A warning"""
        result = _parse_log_output(log)
        assert len(result["errors"]) == 2
        assert len(result["warnings"]) == 1

    def test_parse_stack_traces(self):
        log = """ERROR: Something failed
   At: res://scripts/player.gd:42 in function 'process'
   At: res://scripts/game.gd:100 in function '_ready'"""
        result = _parse_log_output(log)
        assert len(result["stack_traces"]) >= 1

    def test_parse_script_error(self):
        log = """SCRIPT ERROR: Invalid call
   at: res://scripts/player.gd:50"""
        result = _parse_log_output(log)
        assert len(result["errors"]) == 1
        assert "Invalid call" in result["errors"][0]


class TestRunDebugScene:
    def test_invalid_project_path(self):
        result = run_debug_scene(project_path="/nonexistent/path")
        assert result["success"] is False
        assert "not found" in result["error"].lower()

    def test_missing_project_godot(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_debug_scene(project_path=tmpdir)
            assert result["success"] is False
            assert "project.godot" in result["error"]

    @patch("godot_mcp.tools.debug_tools._find_godot_executable")
    @patch("subprocess.run")
    def test_successful_run(self, mock_run, mock_find_godot, tmp_path):
        with tempfile.TemporaryDirectory() as project_dir:
            project_file = Path(project_dir) / "project.godot"
            project_file.write_text("; Godot Project")

            mock_find_godot.return_value = "D:/Godot/Godot.exe"
            mock_run.return_value = MagicMock(
                returncode=0, stdout="INFO: Godot Engine", stderr=""
            )

            result = run_debug_scene(project_path=project_dir)
            assert result["exit_code"] == 0

    @patch("godot_mcp.tools.debug_tools._find_godot_executable")
    @patch("os.path.isfile")
    @patch("subprocess.run")
    def test_successful_run(self, mock_run, mock_isfile, mock_find_godot, tmp_path):
        with tempfile.TemporaryDirectory() as project_dir:
            project_file = Path(project_dir) / "project.godot"
            project_file.write_text("; Godot Project")

            mock_find_godot.return_value = "D:/Godot/Godot.exe"
            mock_isfile.return_value = True  # Godot exe exists
            mock_run.return_value = MagicMock(
                returncode=0, stdout="INFO: Godot Engine", stderr=""
            )

            result = run_debug_scene(project_path=project_dir)
            assert result["exit_code"] == 0

    @patch("godot_mcp.tools.debug_tools._find_godot_executable")
    @patch("os.path.isfile")
    @patch("subprocess.run")
    def test_run_with_errors(self, mock_run, mock_isfile, mock_find_godot, tmp_path):
        with tempfile.TemporaryDirectory() as project_dir:
            project_file = Path(project_dir) / "project.godot"
            project_file.write_text("; Godot Project")

            mock_find_godot.return_value = "D:/Godot/Godot.exe"
            mock_isfile.return_value = True  # Godot exe exists
            mock_run.return_value = MagicMock(
                returncode=1, stdout="ERROR: Something broke", stderr=""
            )

            result = run_debug_scene(project_path=project_dir)
            assert result["success"] is False
            assert result["exit_code"] == 1

    @patch("godot_mcp.tools.debug_tools._find_godot_executable")
    @patch("subprocess.run")
    def test_timeout(self, mock_run, mock_find_godot, tmp_path):
        with tempfile.TemporaryDirectory() as project_dir:
            project_file = Path(project_dir) / "project.godot"
            project_file.write_text("; Godot Project")

            mock_find_godot.return_value = "D:/Godot/Godot.exe"
            import subprocess

            mock_run.side_effect = subprocess.TimeoutExpired(cmd="godot", timeout=30)

            result = run_debug_scene(project_path=project_dir, timeout=1)
            assert result["success"] is False

    def test_godot_not_found_error(self):
        with tempfile.TemporaryDirectory() as project_dir:
            project_file = Path(project_dir) / "project.godot"
            project_file.write_text("; Godot Project")

            # Patch to return None (not found)
            with patch(
                "godot_mcp.tools.debug_tools._find_godot_executable", return_value=None
            ):
                result = run_debug_scene(project_path=project_dir)
                assert result["success"] is False
                assert "searched_paths" in result


class TestCheckScriptSyntax:
    def test_invalid_project(self):
        result = check_script_syntax(
            project_path="/nonexistent", script_path="res://test.gd"
        )
        assert result["success"] is False

    @patch("godot_mcp.tools.debug_tools._find_godot_executable")
    @patch("subprocess.run")
    def test_successful_check(self, mock_run, mock_find_godot, tmp_path):
        with tempfile.TemporaryDirectory() as project_dir:
            project_file = Path(project_dir) / "project.godot"
            project_file.write_text("; Godot Project")

            mock_find_godot.return_value = "D:/Godot/Godot.exe"
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

            result = check_script_syntax(
                project_path=project_dir, script_path="res://scripts/test.gd"
            )
            assert result["success"] is True

    @patch("godot_mcp.tools.debug_tools._find_godot_executable")
    @patch("subprocess.run")
    def test_failed_check(self, mock_run, mock_find_godot, tmp_path):
        with tempfile.TemporaryDirectory() as project_dir:
            project_file = Path(project_dir) / "project.godot"
            project_file.write_text("; Godot Project")

            mock_find_godot.return_value = "D:/Godot/Godot.exe"
            mock_run.return_value = MagicMock(
                returncode=1, stdout="", stderr="SCRIPT ERROR: Parse Error"
            )

            result = check_script_syntax(
                project_path=project_dir, script_path="res://scripts/broken.gd"
            )
            assert result["success"] is False

    @patch("godot_mcp.tools.debug_tools._find_godot_executable")
    @patch("os.path.isfile")
    @patch("subprocess.run")
    def test_successful_check(self, mock_run, mock_isfile, mock_find_godot, tmp_path):
        with tempfile.TemporaryDirectory() as project_dir:
            project_file = Path(project_dir) / "project.godot"
            project_file.write_text("; Godot Project")

            mock_find_godot.return_value = "D:/Godot/Godot.exe"
            mock_isfile.return_value = True  # Godot exe exists
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

            result = check_script_syntax(
                project_path=project_dir, script_path="res://scripts/test.gd"
            )
            assert result["success"] is True

    @patch("godot_mcp.tools.debug_tools._find_godot_executable")
    @patch("os.path.isfile")
    @patch("subprocess.run")
    def test_failed_check(self, mock_run, mock_isfile, mock_find_godot, tmp_path):
        with tempfile.TemporaryDirectory() as project_dir:
            project_file = Path(project_dir) / "project.godot"
            project_file.write_text("; Godot Project")

            mock_find_godot.return_value = "D:/Godot/Godot.exe"
            mock_isfile.return_value = True  # Godot exe exists
            mock_run.return_value = MagicMock(
                returncode=1, stdout="", stderr="SCRIPT ERROR: Parse Error"
            )

            result = check_script_syntax(
                project_path=project_dir, script_path="res://scripts/broken.gd"
            )
            assert result["success"] is False

    @patch("godot_mcp.tools.debug_tools._find_godot_executable")
    @patch("os.path.isfile")
    @patch("subprocess.run")
    def test_timeout(self, mock_run, mock_isfile, mock_find_godot, tmp_path):
        with tempfile.TemporaryDirectory() as project_dir:
            project_file = Path(project_dir) / "project.godot"
            project_file.write_text("; Godot Project")

            mock_find_godot.return_value = "D:/Godot/Godot.exe"
            mock_isfile.return_value = True  # Godot exe exists
            import subprocess

            mock_run.side_effect = subprocess.TimeoutExpired(cmd="godot", timeout=30)

            result = check_script_syntax(
                project_path=project_dir, script_path="res://test.gd", timeout=1
            )
            assert result["success"] is False
            assert "timed out" in result["error"]
