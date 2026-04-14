"""
Tests para Bug Reincidente - instantiate_scene genera paths res:// correctos.

Estos tests verifican que instantiate_scene genere paths res:// válidos
cuando las escenas están en directorios diferentes, usando project_path.

Bug histórico: El código original tenía un `pass` con comentario "For now"
que nunca se implementó, causando paths como res://../scenes/Character.tscn
que Godot rechaza.
"""

import sys
import os
import tempfile

import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from godot_mcp.core.tscn_parser import parse_tscn
from godot_mcp.tools.scene_tools import instantiate_scene
from godot_mcp.tools.session_tools import (
    get_session_manager,
    set_session_manager,
    start_session,
    end_session,
)


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


# ============ TEST SUITE: INSTANTIATE_SCENE PATHS ============


class TestInstantiateScenePaths:
    """Tests for correct res:// path generation in instantiate_scene."""

    def test_instantiate_same_directory_without_project_path(
        self, session_id, temp_project
    ):
        """Test that scenes in the same directory work without project_path (legacy behavior)."""
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

        # Instantiate without project_path - should work (same directory)
        result = instantiate_scene(
            session_id=session_id,
            scene_path=child_path,
            parent_scene_path=parent_path,
            node_name="MyChild",
            parent_node_path=".",
        )
        assert result["success"] is True, f"Should succeed: {result}"

        # Verify the ext_resource path is correct
        scene = parse_tscn(parent_path)
        assert len(scene.ext_resources) == 1
        ext_res = scene.ext_resources[0]
        assert ext_res.path == "res://Child.tscn", (
            f"Expected res://Child.tscn, got {ext_res.path}"
        )

    def test_instantiate_different_directories_with_project_path(
        self, session_id, temp_project
    ):
        """Test that scenes in different subdirectories work WITH project_path."""
        # Create subdirectories
        scenes_dir = os.path.join(temp_project, "scenes")
        levels_dir = os.path.join(temp_project, "levels")
        os.makedirs(scenes_dir)
        os.makedirs(levels_dir)

        # Create character scene in scenes/
        char_path = os.path.join(scenes_dir, "Character.tscn")
        with open(char_path, "w", encoding="utf-8") as f:
            f.write("""[gd_scene load_steps=1 format=3]

[node name="CharacterRoot" type="CharacterBody2D"]
""")

        # Create level scene in levels/
        level_path = os.path.join(levels_dir, "Level1.tscn")
        with open(level_path, "w", encoding="utf-8") as f:
            f.write("""[gd_scene load_steps=1 format=3]

[node name="LevelRoot" type="Node2D"]
""")

        # Instantiate WITH project_path - should work and generate clean res:// path
        result = instantiate_scene(
            session_id=session_id,
            scene_path=char_path,
            parent_scene_path=level_path,
            node_name="Player",
            parent_node_path=".",
            project_path=temp_project,
        )
        assert result["success"] is True, f"Should succeed: {result}"

        # Verify the ext_resource path is clean (no ..)
        scene = parse_tscn(level_path)
        assert len(scene.ext_resources) == 1
        ext_res = scene.ext_resources[0]
        assert ext_res.path == "res://scenes/Character.tscn", (
            f"Expected res://scenes/Character.tscn, got {ext_res.path}"
        )

    def test_instantiate_different_directories_without_project_path_fails(
        self, session_id, temp_project
    ):
        """Test that scenes in different subdirectories WITHOUT project_path fail gracefully."""
        # Create subdirectories
        scenes_dir = os.path.join(temp_project, "scenes")
        levels_dir = os.path.join(temp_project, "levels")
        os.makedirs(scenes_dir)
        os.makedirs(levels_dir)

        # Create character scene in scenes/
        char_path = os.path.join(scenes_dir, "Character.tscn")
        with open(char_path, "w", encoding="utf-8") as f:
            f.write("""[gd_scene load_steps=1 format=3]

[node name="CharacterRoot" type="CharacterBody2D"]
""")

        # Create level scene in levels/
        level_path = os.path.join(levels_dir, "Level1.tscn")
        with open(level_path, "w", encoding="utf-8") as f:
            f.write("""[gd_scene load_steps=1 format=3]

[node name="LevelRoot" type="Node2D"]
""")

        # Instantiate WITHOUT project_path - should fail with clear error
        result = instantiate_scene(
            session_id=session_id,
            scene_path=char_path,
            parent_scene_path=level_path,
            node_name="Player",
            parent_node_path=".",
            # No project_path!
        )
        assert result["success"] is False, "Should fail without project_path"
        assert "Cannot create valid res:// path" in result["error"], (
            f"Expected clear error message, got: {result['error']}"
        )
        assert "outside the project directory" in result["error"], (
            f"Expected hint about project directory, got: {result['error']}"
        )

    def test_instantiate_nested_directories_with_project_path(
        self, session_id, temp_project
    ):
        """Test deeply nested directory structure with project_path."""
        # Create nested structure: scenes/enemies/ and levels/world/
        enemies_dir = os.path.join(temp_project, "scenes", "enemies")
        world_dir = os.path.join(temp_project, "levels", "world")
        os.makedirs(enemies_dir)
        os.makedirs(world_dir)

        # Create enemy scene
        enemy_path = os.path.join(enemies_dir, "Goblin.tscn")
        with open(enemy_path, "w", encoding="utf-8") as f:
            f.write("""[gd_scene load_steps=1 format=3]

[node name="GoblinRoot" type="CharacterBody2D"]
""")

        # Create world level
        world_path = os.path.join(world_dir, "Forest.tscn")
        with open(world_path, "w", encoding="utf-8") as f:
            f.write("""[gd_scene load_steps=1 format=3]

[node name="ForestRoot" type="Node2D"]
""")

        # Instantiate with project_path
        result = instantiate_scene(
            session_id=session_id,
            scene_path=enemy_path,
            parent_scene_path=world_path,
            node_name="Goblin1",
            parent_node_path=".",
            project_path=temp_project,
        )
        assert result["success"] is True, f"Should succeed: {result}"

        # Verify the ext_resource path
        scene = parse_tscn(world_path)
        ext_res = scene.ext_resources[0]
        assert ext_res.path == "res://scenes/enemies/Goblin.tscn", (
            f"Expected res://scenes/enemies/Goblin.tscn, got {ext_res.path}"
        )

    def test_instantiate_preserves_existing_ext_resources(
        self, session_id, temp_project
    ):
        """Test that adding a new ext_resource doesn't break existing ones."""
        # Create two child scenes
        child1_path = os.path.join(temp_project, "Child1.tscn")
        child2_path = os.path.join(temp_project, "Child2.tscn")
        for path in [child1_path, child2_path]:
            with open(path, "w", encoding="utf-8") as f:
                f.write("""[gd_scene load_steps=1 format=3]

[node name="Root" type="Node2D"]
""")

        # Create parent with an existing ext_resource
        parent_path = os.path.join(temp_project, "Parent.tscn")
        with open(parent_path, "w", encoding="utf-8") as f:
            f.write("""[gd_scene load_steps=2 format=3]

[ext_resource type="Script" path="res://scripts/test.gd" id="1_script"]

[node name="Root" type="Node2D"]
script = ExtResource("1_script")
""")

        # Instantiate first child
        result1 = instantiate_scene(
            session_id=session_id,
            scene_path=child1_path,
            parent_scene_path=parent_path,
            node_name="Child1",
            parent_node_path=".",
            project_path=temp_project,
        )
        assert result1["success"] is True

        # Instantiate second child
        result2 = instantiate_scene(
            session_id=session_id,
            scene_path=child2_path,
            parent_scene_path=parent_path,
            node_name="Child2",
            parent_node_path=".",
            project_path=temp_project,
        )
        assert result2["success"] is True

        # Verify all ext_resources are present
        scene = parse_tscn(parent_path)
        assert len(scene.ext_resources) == 3, (
            f"Expected 3 ext_resources, got {len(scene.ext_resources)}"
        )

        # First one should be the original script
        assert scene.ext_resources[0].path == "res://scripts/test.gd"
        assert scene.ext_resources[0].type == "Script"

        # Next two should be the instantiated scenes
        paths = [r.path for r in scene.ext_resources[1:]]
        assert "res://Child1.tscn" in paths
        assert "res://Child2.tscn" in paths
