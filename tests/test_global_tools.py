"""
Tests para global_tools.py

Ejecutar: pytest tests/test_global_tools.py -v
"""

import os
import tempfile
from pathlib import Path

import pytest

from godot_mcp.tools.global_tools import (
    ProjectGodotEditor,
    _format_godot_value,
    _parse_godot_value,
)


# ============ FIXTURES ============


@pytest.fixture
def temp_project():
    """Crear un proyecto Godot temporal con project.godot."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_file = Path(tmpdir) / "project.godot"
        project_file.write_text(
            """; Engine Configuration File.
; Godot version: 4.2.1.stable

[application]
config/name="Test Project"
config/features=PackedStringArray("4.2", "Mobile")
config/icon="res://icon.svg"

[autoload]

GameManager="*res://scripts/game_manager.gd"
AudioManager="*res://scripts/audio_manager.gd"
OldSystem="res://scripts/old_system.gd"

[display]

window/size/viewport_width=1280
window/size/viewport_height=720

[shader_globals]

time_of_day="float,12.0"
ambient_color="Color,Color(0.2, 0.3, 0.5, 1.0)"

[global_group]

enemies=""
player=""

[input]

ui_accept={
"deadzone": 0.5,
"events": [Object(InputEventKey,"resource_local_to_scene":false,"resource_name":"","device":0,"window_id":0,"alt_pressed":false,"shift_pressed":false,"ctrl_pressed":false,"meta_pressed":false,"pressed":false,"keycode":4194309,"physical_keycode":0,"key_label":0,"unicode":0,"echo":false,"script":null)
]
}
""",
            encoding="utf-8",
        )
        yield tmpdir


@pytest.fixture
def session_id(temp_project):
    """Crear una sesión de prueba y devolver su ID."""
    from godot_mcp.tools.session_tools import start_session
    
    result = start_session(temp_project)
    assert result["success"] is True
    yield result["session_id"]
    
    # Cleanup: cerrar sesión
    from godot_mcp.tools.session_tools import end_session
    end_session(result["session_id"], save=False)


@pytest.fixture
def editor(temp_project):
    """Crear un editor de project.godot."""
    return ProjectGodotEditor(temp_project)


# ============ TESTS: ProjectGodotEditor ============


class TestProjectGodotEditor:
    def test_load(self, editor):
        """Verificar que carga correctamente."""
        assert len(editor.lines) > 0
        assert "[application]" in editor.lines

    def test_get_section_lines(self, editor):
        """Verificar que encuentra secciones correctamente."""
        start, end = editor.get_section_lines("autoload")
        assert start != -1
        assert end > start
        # Buscar primera línea no vacía después del header de sección
        found = False
        for i in range(start + 1, end):
            if editor.lines[i].strip() and not editor.lines[i].strip().startswith(";"):
                assert "GameManager=" in editor.lines[i]
                found = True
                break
        assert found, "No se encontró GameManager= en la sección autoload"

    def test_get_section_lines_not_found(self, editor):
        """Verificar que devuelve -1 para secciones inexistentes."""
        start, end = editor.get_section_lines("nonexistent")
        assert start == -1
        assert end == -1

    def test_has_section(self, editor):
        """Verificar has_section."""
        assert editor.has_section("autoload")
        assert editor.has_section("display")
        assert not editor.has_section("nonexistent")

    def test_get_section_entries(self, editor):
        """Verificar que parsea entradas correctamente."""
        entries = editor.get_section_entries("autoload")
        assert "GameManager" in entries
        assert entries["GameManager"] == '"*res://scripts/game_manager.gd"'
        assert "OldSystem" in entries
        assert entries["OldSystem"] == '"res://scripts/old_system.gd"'

    def test_get_section_entries_not_found(self, editor):
        """Verificar que devuelve dict vacío para sección inexistente."""
        entries = editor.get_section_entries("nonexistent")
        assert entries == {}

    def test_set_entry_existing(self, editor, temp_project):
        """Verificar que actualiza entrada existente."""
        editor.set_entry("display", "window/size/viewport_width", "1920")
        editor.save()
        
        # Recargar y verificar
        editor2 = ProjectGodotEditor(temp_project)
        entries = editor2.get_section_entries("display")
        assert entries["window/size/viewport_width"] == "1920"

    def test_set_entry_new(self, editor, temp_project):
        """Verificar que añade entrada nueva."""
        editor.set_entry("display", "window/stretch/mode", "canvas_items")
        editor.save()
        
        editor2 = ProjectGodotEditor(temp_project)
        entries = editor2.get_section_entries("display")
        assert entries["window/stretch/mode"] == "canvas_items"

    def test_set_entry_new_section(self, editor, temp_project):
        """Verificar que crea sección nueva."""
        editor.set_entry("new_section", "new_key", "new_value")
        editor.save()
        
        editor2 = ProjectGodotEditor(temp_project)
        assert editor2.has_section("new_section")
        entries = editor2.get_section_entries("new_section")
        assert entries["new_key"] == "new_value"

    def test_remove_entry(self, editor, temp_project):
        """Verificar que elimina entrada."""
        result = editor.remove_entry("autoload", "OldSystem")
        assert result is True
        editor.save()
        
        editor2 = ProjectGodotEditor(temp_project)
        entries = editor2.get_section_entries("autoload")
        assert "OldSystem" not in entries

    def test_remove_entry_not_found(self, editor):
        """Verificar que devuelve False para entrada inexistente."""
        result = editor.remove_entry("autoload", "NonExistent")
        assert result is False

    def test_remove_section(self, editor, temp_project):
        """Verificar que elimina sección completa."""
        result = editor.remove_section("global_group")
        assert result is True
        editor.save()
        
        editor2 = ProjectGodotEditor(temp_project)
        assert not editor2.has_section("global_group")

    def test_preserve_comments(self, editor, temp_project):
        """Verificar que preserva comentarios."""
        editor.set_entry("display", "window/size/viewport_width", "1920")
        editor.save()
        
        content = (Path(temp_project) / "project.godot").read_text()
        assert "; Engine Configuration File." in content
        assert "; Godot version:" in content

    def test_preserve_sections_order(self, editor, temp_project):
        """Verificar que preserva orden de secciones."""
        editor.set_entry("new_section", "key", "value")
        editor.save()
        
        content = (Path(temp_project) / "project.godot").read_text()
        lines = content.splitlines()
        
        # Verificar que [application] viene antes que [new_section]
        app_idx = next(i for i, l in enumerate(lines) if l.strip() == "[application]")
        new_idx = next(i for i, l in enumerate(lines) if l.strip() == "[new_section]")
        assert app_idx < new_idx


# ============ TESTS: Value Parsing/Formatting ============


class TestValueParsing:
    def test_parse_string(self):
        assert _parse_godot_value('"hello"') == "hello"
        assert _parse_godot_value("'hello'") == "hello"

    def test_parse_bool(self):
        assert _parse_godot_value("true") is True
        assert _parse_godot_value("false") is False
        assert _parse_godot_value("True") is True

    def test_parse_int(self):
        assert _parse_godot_value("42") == 42
        assert _parse_godot_value("-10") == -10

    def test_parse_float(self):
        assert _parse_godot_value("3.14") == 3.14
        assert _parse_godot_value("-0.5") == -0.5

    def test_parse_packed_array(self):
        result = _parse_godot_value('PackedStringArray("4.2", "Mobile")')
        assert result == ["4.2", "Mobile"]

    def test_format_string(self):
        assert _format_godot_value("hello") == '"hello"'

    def test_format_bool(self):
        assert _format_godot_value(True) == "true"
        assert _format_godot_value(False) == "false"

    def test_format_int(self):
        assert _format_godot_value(42) == "42"

    def test_format_float(self):
        assert _format_godot_value(3.14) == "3.14"

    def test_format_list(self):
        assert _format_godot_value(["a", "b"]) == 'PackedStringArray("a", "b")'


# ============ TESTS: Autoload Tools ============


class TestAutoloadTools:
    def test_list_autoloads(self, temp_project, session_id):
        from godot_mcp.tools.global_tools import list_autoloads
    
        result = list_autoloads(session_id, temp_project)
        assert result["success"] is True
        assert result["count"] == 3
        
        names = [a["name"] for a in result["autoloads"]]
        assert "GameManager" in names
        assert "AudioManager" in names
        assert "OldSystem" in names
        
        # Verificar singletons
        game_manager = next(a for a in result["autoloads"] if a["name"] == "GameManager")
        assert game_manager["singleton"] is True
        
        old_system = next(a for a in result["autoloads"] if a["name"] == "OldSystem")
        assert old_system["singleton"] is False

    def test_add_autoload(self, temp_project, session_id):
        from godot_mcp.tools.global_tools import add_autoload
        
        # Crear script dummy
        script_path = Path(temp_project) / "scripts" / "new_manager.gd"
        script_path.parent.mkdir(parents=True, exist_ok=True)
        script_path.write_text("extends Node\n")
        
        result = add_autoload(
            session_id,
            temp_project,
            "NewManager",
            "res://scripts/new_manager.gd",
            singleton=True,
        )
        assert result["success"] is True
        assert result["name"] == "NewManager"
        assert result["singleton"] is True
        
        # Verificar que se guardó
        editor = ProjectGodotEditor(temp_project)
        entries = editor.get_section_entries("autoload")
        assert "NewManager" in entries
        assert entries["NewManager"] == '"*res://scripts/new_manager.gd"'

    def test_add_autoload_not_singleton(self, temp_project, session_id):
        from godot_mcp.tools.global_tools import add_autoload
        
        script_path = Path(temp_project) / "scripts" / "normal_manager.gd"
        script_path.parent.mkdir(parents=True, exist_ok=True)
        script_path.write_text("extends Node\n")
        
        result = add_autoload(
            session_id,
            temp_project,
            "NormalManager",
            "res://scripts/normal_manager.gd",
            singleton=False,
        )
        assert result["success"] is True
        
        editor = ProjectGodotEditor(temp_project)
        entries = editor.get_section_entries("autoload")
        assert entries["NormalManager"] == '"res://scripts/normal_manager.gd"'

    def test_add_autoload_script_not_found(self, temp_project, session_id):
        from godot_mcp.tools.global_tools import add_autoload
        
        result = add_autoload(
            session_id,
            temp_project,
            "MissingManager",
            "res://scripts/missing.gd",
            singleton=True,
        )
        assert result["success"] is False
        assert "not found" in result["error"].lower()

    def test_remove_autoload(self, temp_project, session_id):
        from godot_mcp.tools.global_tools import remove_autoload
        
        result = remove_autoload(session_id, temp_project, "OldSystem")
        assert result["success"] is True
        
        editor = ProjectGodotEditor(temp_project)
        entries = editor.get_section_entries("autoload")
        assert "OldSystem" not in entries

    def test_remove_autoload_not_found(self, temp_project, session_id):
        from godot_mcp.tools.global_tools import remove_autoload
        
        result = remove_autoload(session_id, temp_project, "NonExistent")
        assert result["success"] is False


# ============ TESTS: Shader Global Tools ============


class TestShaderGlobalTools:
    def test_get_shader_globals(self, temp_project, session_id):
        from godot_mcp.tools.global_tools import get_shader_globals
        
        result = get_shader_globals(session_id, temp_project)
        assert result["success"] is True
        assert result["count"] == 2
        
        names = [g["name"] for g in result["shader_globals"]]
        assert "time_of_day" in names
        assert "ambient_color" in names

    def test_set_shader_global(self, temp_project, session_id):
        from godot_mcp.tools.global_tools import set_shader_global
        
        result = set_shader_global(
            session_id,
            temp_project,
            "wind_speed",
            "float",
            "5.0",
        )
        assert result["success"] is True
        
        editor = ProjectGodotEditor(temp_project)
        entries = editor.get_section_entries("shader_globals")
        assert "wind_speed" in entries
        assert entries["wind_speed"] == "float,5.0"

    def test_remove_shader_global(self, temp_project, session_id):
        from godot_mcp.tools.global_tools import remove_shader_global
        
        result = remove_shader_global(session_id, temp_project, "time_of_day")
        assert result["success"] is True
        
        editor = ProjectGodotEditor(temp_project)
        entries = editor.get_section_entries("shader_globals")
        assert "time_of_day" not in entries


# ============ TESTS: Global Group Tools ============


class TestGlobalGroupTools:
    def test_list_global_groups(self, temp_project, session_id):
        from godot_mcp.tools.global_tools import list_global_groups
        
        result = list_global_groups(session_id, temp_project)
        assert result["success"] is True
        assert result["count"] == 2
        
        names = [g["name"] for g in result["groups"]]
        assert "enemies" in names
        assert "player" in names

    def test_add_global_group(self, temp_project, session_id):
        from godot_mcp.tools.global_tools import add_global_group
        
        result = add_global_group(session_id, temp_project, "items")
        assert result["success"] is True
        
        editor = ProjectGodotEditor(temp_project)
        entries = editor.get_section_entries("global_group")
        assert "items" in entries

    def test_remove_global_group(self, temp_project, session_id):
        from godot_mcp.tools.global_tools import remove_global_group
        
        result = remove_global_group(session_id, temp_project, "enemies")
        assert result["success"] is True
        
        editor = ProjectGodotEditor(temp_project)
        entries = editor.get_section_entries("global_group")
        assert "enemies" not in entries


# ============ TESTS: Project Setting Tools ============


class TestProjectSettingTools:
    def test_get_project_setting(self, temp_project, session_id):
        from godot_mcp.tools.global_tools import get_project_setting
        
        result = get_project_setting(
            session_id, temp_project, "application", "config/name"
        )
        assert result["success"] is True
        assert result["value"] == "Test Project"

    def test_set_project_setting(self, temp_project, session_id):
        from godot_mcp.tools.global_tools import set_project_setting
        
        result = set_project_setting(
            session_id,
            temp_project,
            "display",
            "window/stretch/mode",
            "canvas_items",
        )
        assert result["success"] is True
        
        editor = ProjectGodotEditor(temp_project)
        entries = editor.get_section_entries("display")
        assert entries["window/stretch/mode"] == '"canvas_items"'

    def test_get_project_settings_all(self, temp_project, session_id):
        from godot_mcp.tools.global_tools import get_project_settings
        
        result = get_project_settings(session_id, temp_project)
        assert result["success"] is True
        assert "sections" in result
        assert "application" in result["sections"]
        assert "autoload" in result["sections"]

    def test_get_project_settings_section(self, temp_project, session_id):
        from godot_mcp.tools.global_tools import get_project_settings
        
        result = get_project_settings(
            session_id, temp_project, section="display"
        )
        assert result["success"] is True
        assert result["section"] == "display"
        assert "window/size/viewport_width" in result["settings"]

    def test_remove_project_setting(self, temp_project, session_id):
        from godot_mcp.tools.global_tools import remove_project_setting
        
        result = remove_project_setting(
            session_id, temp_project, "display", "window/size/viewport_height"
        )
        assert result["success"] is True
        
        editor = ProjectGodotEditor(temp_project)
        entries = editor.get_section_entries("display")
        assert "window/size/viewport_height" not in entries


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
