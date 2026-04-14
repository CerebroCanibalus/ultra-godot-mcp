"""
Tests para Bug #4 - Validación de nombres duplicados en nodos hermanos.

Estos tests verifican que el sistema rechace correctamente nodos hermanos
con el mismo nombre y permita nodos con el mismo nombre bajo diferentes padres.
"""

import sys
import os
import tempfile

import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from godot_mcp.core.tscn_parser import parse_tscn_string, Scene, SceneNode
from godot_mcp.core.tscn_validator import TSCNValidator
from godot_mcp.tools.node_tools import add_node, rename_node, duplicate_node
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


# ============ TEST SUITE: SIBLING NAME VALIDATION ============


class TestSiblingNameValidation:
    """Tests for Bug #4 - Duplicate sibling node names validation."""

    def test_add_node_same_parent_rejected(self, session_id, temp_project):
        """Test that adding a node with same name as sibling under same parent fails."""
        scene_path = os.path.join(temp_project, "test.tscn")

        # Create scene with Player as root
        with open(scene_path, "w", encoding="utf-8") as f:
            f.write("""[gd_scene load_steps=1 format=3]

[node name="Root" type="Node2D"]

[node name="Player" type="Node2D" parent="."]
""")

        # Add first Sprite under Player - should succeed
        result = add_node(
            session_id=session_id,
            scene_path=scene_path,
            parent_path="Player",
            node_type="Sprite2D",
            node_name="Sprite",
        )
        assert result["success"] is True, f"First add_node failed: {result}"

        # Add second Sprite under Player - should fail (duplicate sibling)
        result = add_node(
            session_id=session_id,
            scene_path=scene_path,
            parent_path="Player",
            node_type="Sprite2D",
            node_name="Sprite",
        )
        assert result["success"] is False, "Second add_node should have failed"
        assert "already exists" in result["error"].lower()
        assert (
            "duplicate" in result["error"].lower()
            or "sibling" in result.get("hint", "").lower()
        )

    def test_add_node_different_parent_allowed(self, session_id, temp_project):
        """Test that same name under different parents is allowed."""
        scene_path = os.path.join(temp_project, "test.tscn")

        # Create scene with Player and Enemy as siblings under root
        with open(scene_path, "w", encoding="utf-8") as f:
            f.write("""[gd_scene load_steps=1 format=3]

[node name="Root" type="Node2D"]

[node name="Player" type="Node2D" parent="."]

[node name="Enemy" type="Node2D" parent="."]
""")

        # Add Sprite under Player - should succeed
        result = add_node(
            session_id=session_id,
            scene_path=scene_path,
            parent_path="Player",
            node_type="Sprite2D",
            node_name="Sprite",
        )
        assert result["success"] is True, f"First add_node failed: {result}"

        # Add Sprite under Enemy - should succeed (different parent)
        result = add_node(
            session_id=session_id,
            scene_path=scene_path,
            parent_path="Enemy",
            node_type="Sprite2D",
            node_name="Sprite",
        )
        assert result["success"] is True, (
            f"Second add_node should have succeeded: {result}"
        )

    def test_rename_node_sibling_check(self, session_id, temp_project):
        """Test that renaming a node to an existing sibling name fails."""
        scene_path = os.path.join(temp_project, "test.tscn")

        # Create scene with Player having Sprite and Animation children
        with open(scene_path, "w", encoding="utf-8") as f:
            f.write("""[gd_scene load_steps=1 format=3]

[node name="Root" type="Node2D"]

[node name="Player" type="Node2D" parent="."]

[node name="Sprite" type="Sprite2D" parent="Player"]

[node name="Animation" type="AnimationPlayer" parent="Player"]
""")

        # Try to rename Animation to Sprite - should fail
        result = rename_node(
            session_id=session_id,
            scene_path=scene_path,
            node_path="Player/Animation",
            new_name="Sprite",
        )
        assert result["success"] is False, "Renaming should have failed"
        assert "already exists" in result["error"].lower()

        # Rename Animation to Hitbox - should succeed
        result = rename_node(
            session_id=session_id,
            scene_path=scene_path,
            node_path="Player/Animation",
            new_name="Hitbox",
        )
        assert result["success"] is True, (
            f"Renaming to Hitbox should have succeeded: {result}"
        )
        assert result["new_name"] == "Hitbox"

    def test_duplicate_node_sibling_check(self, session_id, temp_project):
        """Test that duplicating a node with existing sibling name fails."""
        scene_path = os.path.join(temp_project, "test.tscn")

        # Create scene with Player having a Sprite child
        with open(scene_path, "w", encoding="utf-8") as f:
            f.write("""[gd_scene load_steps=1 format=3]

[node name="Root" type="Node2D"]

[node name="Player" type="Node2D" parent="."]

[node name="Sprite" type="Sprite2D" parent="Player"]
""")

        # Try to duplicate Sprite (creates Sprite_copy) - should fail since Sprite_copy doesn't exist
        result = duplicate_node(
            session_id=session_id,
            scene_path=scene_path,
            node_path="Player/Sprite",
        )
        # By default, new_name = "Sprite_copy" - this should fail if we try to create Sprite_copy
        # Actually, let's test explicitly with the same name
        result = duplicate_node(
            session_id=session_id,
            scene_path=scene_path,
            node_path="Player/Sprite",
            new_name="Sprite",  # Explicit same name
        )
        assert result["success"] is False, "Duplicating with same name should fail"
        assert "already exists" in result["error"].lower()

        # Duplicate with unique name should succeed
        result = duplicate_node(
            session_id=session_id,
            scene_path=scene_path,
            node_path="Player/Sprite",
            new_name="SpriteCopy",
        )
        assert result["success"] is True, (
            f"Duplicate with unique name should succeed: {result}"
        )
        assert "SpriteCopy" in result["duplicated_nodes"]

    def test_validator_detects_duplicate_siblings(self):
        """Test that TSCNValidator detects duplicate sibling names."""
        # Manually create scene with duplicate siblings
        scene = Scene()
        scene.header.format = 3
        scene.header.load_steps = 1

        # Add root
        root = SceneNode(name="Root", type="Node2D", parent=".")
        scene.nodes.append(root)

        # Add Player under root
        player = SceneNode(name="Player", type="Node2D", parent="Root")
        scene.nodes.append(player)

        # Add two Sprite nodes under Player (duplicate!)
        sprite1 = SceneNode(name="Sprite", type="Sprite2D", parent="Player")
        scene.nodes.append(sprite1)

        sprite2 = SceneNode(name="Sprite", type="Sprite2D", parent="Player")
        scene.nodes.append(sprite2)

        # Validate - should fail with unique_sibling_node_names error
        validator = TSCNValidator()
        result = validator.validate(scene)

        assert result.is_valid is False, "Scene should be invalid"

        # Check that error message mentions duplicate sibling names
        error_found = False
        for error in result.errors:
            if "duplicate" in error.lower() or "sibling" in error.lower():
                error_found = True
                break
        assert error_found, f"Expected sibling name error, got: {result.errors}"

    def test_validator_allows_same_name_different_parents(self):
        """Test that TSCNValidator allows same name under different parents."""
        # Create scene with Player/Sprite and Enemy/Sprite (same name, different parent)
        scene = Scene()
        scene.header.format = 3
        scene.header.load_steps = 1

        # Add root
        root = SceneNode(name="Root", type="Node2D", parent=".")
        scene.nodes.append(root)

        # Add Player and Enemy under root
        player = SceneNode(name="Player", type="Node2D", parent="Root")
        enemy = SceneNode(name="Enemy", type="Node2D", parent="Root")
        scene.nodes.append(player)
        scene.nodes.append(enemy)

        # Add Sprite under Player
        player_sprite = SceneNode(name="Sprite", type="Sprite2D", parent="Player")
        scene.nodes.append(player_sprite)

        # Add Sprite under Enemy (different parent - allowed)
        enemy_sprite = SceneNode(name="Sprite", type="Sprite2D", parent="Enemy")
        scene.nodes.append(enemy_sprite)

        # Validate - should pass
        validator = TSCNValidator()
        result = validator.validate(scene)

        # Check for sibling name errors
        sibling_error_found = False
        for error in result.errors:
            if "sibling" in error.lower():
                sibling_error_found = True
                break

        assert not sibling_error_found, (
            f"Should allow same name under different parents. Errors: {result.errors}"
        )
        assert result.is_valid is True, (
            f"Scene should be valid. Errors: {result.errors}"
        )

    def test_instantiate_scene_duplicate_check(self, session_id, temp_project):
        """Test that instantiating a scene with existing sibling name fails."""
        # Create child scene
        child_scene_path = os.path.join(temp_project, "Child.tscn")
        with open(child_scene_path, "w", encoding="utf-8") as f:
            f.write("""[gd_scene load_steps=1 format=3]

[node name="ChildRoot" type="Node2D"]
""")

        # Create parent scene with an existing node directly under root
        parent_scene_path = os.path.join(temp_project, "Parent.tscn")
        with open(parent_scene_path, "w", encoding="utf-8") as f:
            f.write("""[gd_scene load_steps=1 format=3]

[node name="Root" type="Node2D"]

[node name="ExistingChild" type="Node2D" parent="."]
""")

        # Try to instantiate Child scene as "ExistingChild" - should fail
        # Using "." because that's how the existing node is parented
        result = instantiate_scene(
            session_id=session_id,
            scene_path=child_scene_path,
            parent_scene_path=parent_scene_path,
            node_name="ExistingChild",  # Same name as existing sibling
            parent_node_path=".",
        )
        assert result["success"] is False, (
            "Instantiation with duplicate name should fail"
        )
        assert "already exists" in result["error"].lower()

        # Instantiate with unique name - should succeed
        result = instantiate_scene(
            session_id=session_id,
            scene_path=child_scene_path,
            parent_scene_path=parent_scene_path,
            node_name="NewChild",
            parent_node_path=".",
        )
        assert result["success"] is True, (
            f"Instantiation with unique name should succeed: {result}"
        )
        assert result["success"] is True, (
            f"Instantiation with unique name should succeed: {result}"
        )
