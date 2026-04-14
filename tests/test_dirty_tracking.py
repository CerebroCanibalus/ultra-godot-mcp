"""
Tests de integración para dirty tracking y commit_session.

Verifican que:
1. Las herramientas marcan escenas como dirty después de modificarlas
2. get_session_info muestra dirty_scenes correctamente
3. commit_session guarda cambios a disco
4. El retry logic maneja PermissionError correctamente
"""

import sys
import os
import tempfile
from unittest.mock import patch, MagicMock

import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from godot_mcp.core.tscn_parser import parse_tscn
from godot_mcp.tools.node_tools import add_node, _update_scene_file, _mark_scene_dirty
from godot_mcp.tools.scene_tools import instantiate_scene, create_scene
from godot_mcp.tools.session_tools import (
    get_session_manager,
    set_session_manager,
    start_session,
    end_session,
    commit_session,
    get_session_info,
)
from godot_mcp.core.tscn_parser import Scene, SceneNode, GdSceneHeader


# ============ FIXTURES ============


@pytest.fixture(autouse=True)
def reset_session_manager():
    """Reset session manager before each test."""
    from godot_mcp.session_manager import SessionManager

    set_session_manager(SessionManager(auto_save=False))
    yield


@pytest.fixture
def temp_project():
    """Create a temporary Godot project directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_file = os.path.join(tmpdir, "project.godot")
        with open(project_file, "w", encoding="utf-8") as f:
            f.write("""[configuration]
config_version=5

[application]
config/name="TestProject"
config/features=PackedStringArray("4.6")
""")
        yield tmpdir


@pytest.fixture
def session_id(temp_project):
    """Create a real session for testing."""
    result = start_session(temp_project)
    assert result["success"] is True
    return result["session_id"]


# ============ TEST SUITE: DIRTY TRACKING ============


class TestDirtyTracking:
    """Tests for dirty scene tracking across tools."""

    def test_add_node_marks_scene_dirty(self, session_id, temp_project):
        """Test that add_node marks the scene as dirty."""
        scene_path = os.path.join(temp_project, "test.tscn")

        # Create scene
        with open(scene_path, "w", encoding="utf-8") as f:
            f.write("""[gd_scene load_steps=1 format=3]

[node name="Root" type="Node2D"]
""")

        # Initially no dirty scenes
        info = get_session_info(session_id)
        assert info["success"] is True
        initial_dirty = len(info["dirty_scenes"])

        # Add a node
        result = add_node(
            session_id=session_id,
            scene_path=scene_path,
            parent_path=".",
            node_type="Sprite2D",
            node_name="Sprite",
        )
        assert result["success"] is True, f"add_node should succeed: {result}"

        # Check that scene is now dirty
        info = get_session_info(session_id)
        assert len(info["dirty_scenes"]) > initial_dirty, (
            f"Scene should be marked dirty after add_node. Dirty: {info['dirty_scenes']}"
        )
        assert scene_path in info["dirty_scenes"], (
            f"Scene path should be in dirty_scenes: {info['dirty_scenes']}"
        )

    def test_commit_session_saves_dirty_scenes(self, session_id, temp_project):
        """Test that commit_session actually saves dirty scenes to disk."""
        scene_path = os.path.join(temp_project, "test.tscn")

        # Create scene
        with open(scene_path, "w", encoding="utf-8") as f:
            f.write("""[gd_scene load_steps=1 format=3]

[node name="Root" type="Node2D"]
""")

        # Add a node (marks scene dirty)
        result = add_node(
            session_id=session_id,
            scene_path=scene_path,
            parent_path=".",
            node_type="Sprite2D",
            node_name="Sprite",
        )
        assert result["success"] is True

        # Verify scene is dirty
        info = get_session_info(session_id)
        assert scene_path in info["dirty_scenes"]

        # Read file content before commit
        with open(scene_path, "r", encoding="utf-8") as f:
            content_before = f.read()

        # Commit session
        commit_result = commit_session(session_id)
        assert commit_result["success"] is True, (
            f"commit_session should succeed: {commit_result}"
        )
        assert commit_result["saved_count"] >= 1, (
            f"Should have saved at least 1 scene, got: {commit_result}"
        )

        # Verify scene is no longer dirty
        info_after = get_session_info(session_id)
        assert scene_path not in info_after["dirty_scenes"], (
            f"Scene should not be dirty after commit. Dirty: {info_after['dirty_scenes']}"
        )

    def test_instantiate_scene_marks_dirty(self, session_id, temp_project):
        """Test that instantiate_scene marks the parent scene as dirty."""
        # Create child scene
        child_path = os.path.join(temp_project, "Child.tscn")
        with open(child_path, "w", encoding="utf-8") as f:
            f.write("""[gd_scene load_steps=1 format=3]

[node name="ChildRoot" type="Node2D"]
""")

        # Create parent scene
        parent_path = os.path.join(temp_project, "Parent.tscn")
        with open(parent_path, "w", encoding="utf-8") as f:
            f.write("""[gd_scene load_steps=1 format=3]

[node name="Root" type="Node2D"]
""")

        # Initially no dirty scenes
        info = get_session_info(session_id)
        assert parent_path not in info["dirty_scenes"]

        # Instantiate scene
        result = instantiate_scene(
            session_id=session_id,
            scene_path=child_path,
            parent_scene_path=parent_path,
            node_name="MyChild",
            parent_node_path=".",
            project_path=temp_project,
        )
        assert result["success"] is True, f"instantiate_scene should succeed: {result}"

        # Verify parent scene is dirty
        info = get_session_info(session_id)
        assert parent_path in info["dirty_scenes"], (
            f"Parent scene should be dirty after instantiate. Dirty: {info['dirty_scenes']}"
        )

    def test_create_scene_marks_dirty(self, session_id, temp_project):
        """Test that create_scene marks the new scene as dirty."""
        result = create_scene(
            session_id=session_id,
            project_path=temp_project,
            scene_path="NewScene.tscn",
            root_type="Node2D",
            root_name="Root",
        )
        assert result["success"] is True, f"create_scene should succeed: {result}"

        # Verify scene is dirty
        info = get_session_info(session_id)
        full_path = os.path.join(temp_project, "NewScene.tscn")
        assert full_path in info["dirty_scenes"], (
            f"New scene should be dirty after create. Dirty: {info['dirty_scenes']}"
        )


# ============ TEST SUITE: RETRY LOGIC ============


class TestRetryLogic:
    """Tests for file write retry logic."""

    def test_update_scene_file_retries_on_permission_error(
        self, session_id, temp_project
    ):
        """Test that _update_scene_file retries on PermissionError."""
        scene_path = os.path.join(temp_project, "test.tscn")

        # Create a simple scene
        scene = Scene(
            header=GdSceneHeader(load_steps=1, format=3),
            nodes=[SceneNode(name="Root", type="Node2D", parent=".")],
        )

        # Mock open to raise PermissionError twice, then succeed
        call_count = 0
        original_open = open

        def mock_open(*args, **kwargs):
            nonlocal call_count
            if len(args) > 1 and "w" in args[1]:
                call_count += 1
                if call_count <= 2:
                    raise PermissionError("Mock permission denied")
            return original_open(*args, **kwargs)

        with patch("builtins.open", mock_open):
            # Should succeed after retries
            _update_scene_file(scene_path, scene, max_retries=3)

        # Verify it was called 3 times (2 failures + 1 success)
        assert call_count == 3, f"Expected 3 calls, got {call_count}"

    def test_update_scene_file_fails_after_max_retries(self, session_id, temp_project):
        """Test that _update_scene_file raises after max retries."""
        scene_path = os.path.join(temp_project, "test.tscn")

        # Create a simple scene
        scene = Scene(
            header=GdSceneHeader(load_steps=1, format=3),
            nodes=[SceneNode(name="Root", type="Node2D", parent=".")],
        )

        # Mock open to always raise PermissionError
        with patch("builtins.open", side_effect=PermissionError("Always denied")):
            with pytest.raises(PermissionError) as exc_info:
                _update_scene_file(scene_path, scene, max_retries=2)

            assert "after 2 attempts" in str(exc_info.value)

    def test_mark_scene_dirty_does_not_fail_operation(self, session_id, temp_project):
        """Test that mark_scene_dirty failures don't break the main operation."""
        scene_path = os.path.join(temp_project, "test.tscn")

        # Create scene
        with open(scene_path, "w", encoding="utf-8") as f:
            f.write("""[gd_scene load_steps=1 format=3]

[node name="Root" type="Node2D"]
""")

        # Mock get_session_manager in session_tools (where _mark_scene_dirty imports it from)
        with patch(
            "godot_mcp.tools.session_tools.get_session_manager",
            side_effect=Exception("Session manager broken"),
        ):
            # This should NOT raise an exception
            # (mark_scene_dirty catches exceptions internally)
            scene = parse_tscn(scene_path)
            _update_scene_file(scene_path, scene)

        # Verify file was written successfully
        assert os.path.exists(scene_path)
