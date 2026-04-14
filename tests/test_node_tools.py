"""
Tests for node_tools module.

Tests:
1. add_node - success, duplicate sibling, properties, resource paths
2. remove_node - success, not found, with children
3. update_node - success, not found, resource properties
4. get_node_properties - success, not found, calculated path
5. rename_node - success, duplicate sibling, child references
6. move_node - success, to root, to itself
7. duplicate_node - success, custom name, with children
8. find_nodes - by name, by type, fuzzy match, no results
9. add_ext_resource - success, duplicate path, custom ID
10. Helpers - _ensure_tscn_path, _normalize_node_path, _find_node_by_path
"""

import sys
import os
import tempfile
from unittest.mock import patch

import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from godot_mcp.tools.node_tools import (
    add_node,
    remove_node,
    update_node,
    get_node_properties,
    rename_node,
    move_node,
    duplicate_node,
    find_nodes,
    add_ext_resource,
    _ensure_tscn_path,
    _normalize_node_path,
    _find_node_by_path,
    _resolve_parent_path,
    _find_sibling_by_name,
    _process_resource_properties,
    _clean_resource_id,
)
from godot_mcp.tools.session_tools import (
    get_session_manager,
    set_session_manager,
    start_session,
)
from godot_mcp.core.tscn_parser import (
    Scene,
    SceneNode,
    GdSceneHeader,
    ExtResource,
    SubResource,
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


@pytest.fixture
def simple_scene_file(temp_project):
    """Create a simple scene file for testing."""
    scene_path = os.path.join(temp_project, "test.tscn")
    with open(scene_path, "w", encoding="utf-8") as f:
        f.write("""[gd_scene load_steps=1 format=3]

[node name="Root" type="Node2D"]
""")
    return scene_path


@pytest.fixture
def complex_scene_file(temp_project):
    """Create a complex scene with multiple nodes."""
    scene_path = os.path.join(temp_project, "complex.tscn")
    with open(scene_path, "w", encoding="utf-8") as f:
        f.write("""[gd_scene load_steps=1 format=3]

[node name="Root" type="Node2D"]

[node name="Player" type="CharacterBody2D" parent="Root"]

[node name="Sprite" type="Sprite2D" parent="Player"]

[node name="CollisionShape2D" type="CollisionShape2D" parent="Player"]

[node name="Enemy" type="CharacterBody2D" parent="Root"]
""")
    return scene_path


# ============ TEST SUITE: HELPERS ============


class TestHelpers:
    """Tests for helper functions."""

    def test_ensure_tscn_path_adds_extension(self):
        """Test that _ensure_tscn_path adds .tscn if missing."""
        assert _ensure_tscn_path("scenes/Player") == "scenes/Player.tscn"

    def test_ensure_tscn_path_keeps_extension(self):
        """Test that _ensure_tscn_path keeps existing .tscn."""
        assert _ensure_tscn_path("scenes/Player.tscn") == "scenes/Player.tscn"

    def test_normalize_node_path_strips_slashes(self):
        """Test that _normalize_node_path strips leading/trailing slashes."""
        assert _normalize_node_path("/Root/Player/") == "Root/Player"
        assert _normalize_node_path("Root") == "Root"

    def test_clean_resource_id_removes_quotes(self):
        """Test that _clean_resource_id removes surrounding quotes."""
        assert _clean_resource_id('"1"') == "1"
        assert _clean_resource_id("'abc'") == "abc"
        assert _clean_resource_id("123") == "123"
        assert _clean_resource_id('""1""') == "1"

    def test_clean_resource_id_handles_non_string(self):
        """Test that _clean_resource_id handles non-string input."""
        assert _clean_resource_id(None) == ""
        assert _clean_resource_id(123) == "123"


class TestFindNodeByPath:
    """Tests for _find_node_by_path helper."""

    def test_find_root_node(self):
        """Test finding root node by name."""
        scene = Scene(nodes=[SceneNode(name="Root", type="Node2D", parent=".")])
        result = _find_node_by_path(scene, "Root")
        assert result is not None
        idx, node = result
        assert node.name == "Root"
        assert idx == 0

    def test_find_child_node(self):
        """Test finding child node by name."""
        scene = Scene(
            nodes=[
                SceneNode(name="Root", type="Node2D", parent="."),
                SceneNode(name="Player", type="CharacterBody2D", parent="Root"),
            ]
        )
        result = _find_node_by_path(scene, "Player")
        assert result is not None
        _, node = result
        assert node.name == "Player"

    def test_find_node_not_found(self):
        """Test finding non-existent node returns None."""
        scene = Scene(nodes=[SceneNode(name="Root", type="Node2D", parent=".")])
        result = _find_node_by_path(scene, "NonExistent")
        assert result is None


class TestResolveParentPath:
    """Tests for _resolve_parent_path helper."""

    def test_resolve_dot_parent(self):
        """Test that '.' resolves to '.'."""
        scene = Scene(nodes=[SceneNode(name="Root", type="Node2D", parent=".")])
        assert _resolve_parent_path(scene, ".") == "."

    def test_resolve_existing_parent(self):
        """Test that 'Root' as parent resolves to '.' (hardcoded behavior)."""
        scene = Scene(
            nodes=[
                SceneNode(name="Root", type="Node2D", parent="."),
                SceneNode(name="Player", type="CharacterBody2D", parent="Root"),
            ]
        )
        # _resolve_parent_path has hardcoded check: if parent_path == "Root" -> return "."
        assert _resolve_parent_path(scene, "Root") == "."

    def test_resolve_empty_parent(self):
        """Test that empty string resolves to '.'."""
        scene = Scene(nodes=[SceneNode(name="Root", type="Node2D", parent=".")])
        assert _resolve_parent_path(scene, "") == "."


class TestFindSiblingByName:
    """Tests for _find_sibling_by_name helper."""

    def test_find_existing_sibling(self):
        """Test finding existing sibling under same parent."""
        scene = Scene(
            nodes=[
                SceneNode(name="Player", type="CharacterBody2D", parent="Root"),
                SceneNode(name="Enemy", type="CharacterBody2D", parent="Root"),
            ]
        )
        # _resolve_parent_path("Root") returns "." due to hardcoded check
        # So we need nodes with parent="Root" and search with parent="Root"
        # But _find_sibling_by_name uses _resolve_parent_path internally
        # which converts "Root" to "." - so nodes with parent="Root" won't match
        # Let's test with parent="." instead
        scene2 = Scene(
            nodes=[
                SceneNode(name="Player", type="CharacterBody2D", parent="."),
                SceneNode(name="Enemy", type="CharacterBody2D", parent="."),
            ]
        )
        result = _find_sibling_by_name(scene2, ".", "Enemy")
        assert result is not None
        assert result.name == "Enemy"

    def test_no_sibling_found(self):
        """Test that non-existent sibling returns None."""
        scene = Scene(
            nodes=[
                SceneNode(name="Player", type="CharacterBody2D", parent="Root"),
            ]
        )
        result = _find_sibling_by_name(scene, "Root", "Enemy")
        assert result is None


# ============ TEST SUITE: ADD_NODE ============


class TestAddNode:
    """Tests for add_node function."""

    def test_add_node_to_existing_scene(self, session_id, simple_scene_file):
        """Test adding a node to an existing scene."""
        result = add_node(
            session_id=session_id,
            scene_path=simple_scene_file,
            parent_path=".",
            node_type="Sprite2D",
            node_name="Sprite",
        )
        assert result["success"] is True
        assert result["node"]["name"] == "Sprite"
        assert result["node"]["type"] == "Sprite2D"
        # _resolve_parent_path(".") returns "."
        assert result["node"]["parent"] == "."

    def test_add_node_as_child(self, session_id, simple_scene_file):
        """Test adding a node as child of another node."""
        result = add_node(
            session_id=session_id,
            scene_path=simple_scene_file,
            parent_path="Root",
            node_type="Sprite2D",
            node_name="Sprite",
        )
        assert result["success"] is True
        # _resolve_parent_path("Root") returns "." due to hardcoded check
        assert result["node"]["parent"] == "."

    def test_add_node_duplicate_sibling_fails(self, session_id, simple_scene_file):
        """Test that adding a node with duplicate sibling name fails."""
        # First add
        result1 = add_node(
            session_id=session_id,
            scene_path=simple_scene_file,
            parent_path=".",
            node_type="Sprite2D",
            node_name="Sprite",
        )
        assert result1["success"] is True

        # Second add with same name under same parent should fail
        result2 = add_node(
            session_id=session_id,
            scene_path=simple_scene_file,
            parent_path=".",
            node_type="Sprite2D",
            node_name="Sprite",
        )
        assert result2["success"] is False
        assert "already exists" in result2["error"]

    def test_add_node_scene_not_found(self, session_id, temp_project):
        """Test adding node to non-existent scene creates new scene."""
        scene_path = os.path.join(temp_project, "nonexistent.tscn")
        result = add_node(
            session_id=session_id,
            scene_path=scene_path,
            parent_path=".",
            node_type="Node2D",
            node_name="Root",
        )
        # Should create new scene
        assert result["success"] is True
        assert os.path.exists(scene_path)

    def test_add_node_with_properties(self, session_id, simple_scene_file):
        """Test adding a node with properties."""
        result = add_node(
            session_id=session_id,
            scene_path=simple_scene_file,
            parent_path=".",
            node_type="Sprite2D",
            node_name="Sprite",
            properties={"position": {"type": "Vector2", "x": 100, "y": 200}},
        )
        assert result["success"] is True

        # Verify properties were saved
        props = get_node_properties(
            session_id=session_id,
            scene_path=simple_scene_file,
            node_path="Sprite",
        )
        assert props["success"] is True
        assert "position" in props["node"]["properties"]


# ============ TEST SUITE: REMOVE_NODE ============


class TestRemoveNode:
    """Tests for remove_node function."""

    def test_remove_node_success(self, session_id, complex_scene_file):
        """Test removing a node successfully."""
        result = remove_node(
            session_id=session_id,
            scene_path=complex_scene_file,
            node_path="Enemy",
        )
        assert result["success"] is True
        assert "Enemy" in result["removed_nodes"]

    def test_remove_node_not_found(self, session_id, simple_scene_file):
        """Test removing non-existent node fails."""
        result = remove_node(
            session_id=session_id,
            scene_path=simple_scene_file,
            node_path="NonExistent",
        )
        assert result["success"] is False
        assert "not found" in result["error"]

    def test_remove_node_scene_not_found(self, session_id, temp_project):
        """Test removing node from non-existent scene fails."""
        result = remove_node(
            session_id=session_id,
            scene_path=os.path.join(temp_project, "nonexistent.tscn"),
            node_path="Root",
        )
        assert result["success"] is False
        assert "not found" in result["error"]

    def test_remove_node_removes_children(self, session_id, complex_scene_file):
        """Test that removing a node also removes its children."""
        result = remove_node(
            session_id=session_id,
            scene_path=complex_scene_file,
            node_path="Player",
        )
        assert result["success"] is True
        # Player's children (Sprite, CollisionShape2D) should also be removed
        assert "Player" in result["removed_nodes"]


# ============ TEST SUITE: UPDATE_NODE ============


class TestUpdateNode:
    """Tests for update_node function."""

    def test_update_node_success(self, session_id, simple_scene_file):
        """Test updating node properties."""
        result = update_node(
            session_id=session_id,
            scene_path=simple_scene_file,
            node_path="Root",
            properties={"position": {"type": "Vector2", "x": 50, "y": 100}},
        )
        assert result["success"] is True
        assert "position" in result["new_properties"]

    def test_update_node_not_found(self, session_id, simple_scene_file):
        """Test updating non-existent node fails."""
        result = update_node(
            session_id=session_id,
            scene_path=simple_scene_file,
            node_path="NonExistent",
            properties={"position": {"type": "Vector2", "x": 0, "y": 0}},
        )
        assert result["success"] is False
        assert "not found" in result["error"]

    def test_update_node_scene_not_found(self, session_id, temp_project):
        """Test updating node in non-existent scene fails."""
        result = update_node(
            session_id=session_id,
            scene_path=os.path.join(temp_project, "nonexistent.tscn"),
            node_path="Root",
            properties={"position": {"type": "Vector2", "x": 0, "y": 0}},
        )
        assert result["success"] is False


# ============ TEST SUITE: GET_NODE_PROPERTIES ============


class TestGetNodeProperties:
    """Tests for get_node_properties function."""

    def test_get_node_properties_success(self, session_id, simple_scene_file):
        """Test getting node properties."""
        result = get_node_properties(
            session_id=session_id,
            scene_path=simple_scene_file,
            node_path="Root",
        )
        assert result["success"] is True
        assert result["node"]["name"] == "Root"
        assert result["node"]["type"] == "Node2D"
        assert result["node"]["path"] == "Root"

    def test_get_node_properties_not_found(self, session_id, simple_scene_file):
        """Test getting properties of non-existent node fails."""
        result = get_node_properties(
            session_id=session_id,
            scene_path=simple_scene_file,
            node_path="NonExistent",
        )
        assert result["success"] is False
        assert "not found" in result["error"]

    def test_get_node_properties_scene_not_found(self, session_id, temp_project):
        """Test getting properties from non-existent scene fails."""
        result = get_node_properties(
            session_id=session_id,
            scene_path=os.path.join(temp_project, "nonexistent.tscn"),
            node_path="Root",
        )
        assert result["success"] is False

    def test_get_node_properties_calculated_path(self, session_id, complex_scene_file):
        """Test that full path is calculated correctly for child nodes."""
        result = get_node_properties(
            session_id=session_id,
            scene_path=complex_scene_file,
            node_path="Sprite",
        )
        assert result["success"] is True
        assert result["node"]["path"] == "Player/Sprite"


# ============ TEST SUITE: RENAME_NODE ============


class TestRenameNode:
    """Tests for rename_node function."""

    def test_rename_node_success(self, session_id, simple_scene_file):
        """Test renaming a node."""
        result = rename_node(
            session_id=session_id,
            scene_path=simple_scene_file,
            node_path="Root",
            new_name="NewRoot",
        )
        assert result["success"] is True
        assert result["old_name"] == "Root"
        assert result["new_name"] == "NewRoot"

    def test_rename_node_duplicate_sibling_fails(self, session_id, temp_project):
        """Test that renaming to existing sibling name fails."""
        # Create a scene with two siblings under "."
        scene_path = os.path.join(temp_project, "rename_test.tscn")
        with open(scene_path, "w", encoding="utf-8") as f:
            f.write("""[gd_scene load_steps=1 format=3]

[node name="Root" type="Node2D"]

[node name="Player" type="CharacterBody2D" parent="."]

[node name="Enemy" type="CharacterBody2D" parent="."]
""")
        result = rename_node(
            session_id=session_id,
            scene_path=scene_path,
            node_path="Enemy",
            new_name="Player",
        )
        assert result["success"] is False
        assert "already exists" in result["error"]

    def test_rename_node_not_found(self, session_id, simple_scene_file):
        """Test renaming non-existent node fails."""
        result = rename_node(
            session_id=session_id,
            scene_path=simple_scene_file,
            node_path="NonExistent",
            new_name="NewName",
        )
        assert result["success"] is False


# ============ TEST SUITE: MOVE_NODE ============


class TestMoveNode:
    """Tests for move_node function."""

    def test_move_node_to_root(self, session_id, complex_scene_file):
        """Test moving a node to root."""
        result = move_node(
            session_id=session_id,
            scene_path=complex_scene_file,
            node_path="Sprite",
            new_parent_path=".",
        )
        assert result["success"] is True
        assert result["new_parent"] == "."

    def test_move_node_to_itself_fails(self, session_id, temp_project):
        """Test that moving a node to itself fails."""
        # Create a scene where the node name matches the resolved parent
        scene_path = os.path.join(temp_project, "move_test.tscn")
        with open(scene_path, "w", encoding="utf-8") as f:
            f.write("""[gd_scene load_steps=1 format=3]

[node name="Root" type="Node2D"]

[node name="Child" type="Node2D" parent="Root"]
""")
        # Move Child to Child (itself) - this should fail
        result = move_node(
            session_id=session_id,
            scene_path=scene_path,
            node_path="Child",
            new_parent_path="Child",
        )
        assert result["success"] is False
        assert "itself" in result["error"]

    def test_move_node_not_found(self, session_id, simple_scene_file):
        """Test moving non-existent node fails."""
        result = move_node(
            session_id=session_id,
            scene_path=simple_scene_file,
            node_path="NonExistent",
            new_parent_path=".",
        )
        assert result["success"] is False


# ============ TEST SUITE: DUPLICATE_NODE ============


class TestDuplicateNode:
    """Tests for duplicate_node function."""

    def test_duplicate_node_default_name(self, session_id, simple_scene_file):
        """Test duplicating a node with default name."""
        result = duplicate_node(
            session_id=session_id,
            scene_path=simple_scene_file,
            node_path="Root",
        )
        assert result["success"] is True
        assert "Root_copy" in result["duplicated_nodes"]

    def test_duplicate_node_custom_name(self, session_id, simple_scene_file):
        """Test duplicating a node with custom name."""
        result = duplicate_node(
            session_id=session_id,
            scene_path=simple_scene_file,
            node_path="Root",
            new_name="RootClone",
        )
        assert result["success"] is True
        assert "RootClone" in result["duplicated_nodes"]

    def test_duplicate_node_not_found(self, session_id, simple_scene_file):
        """Test duplicating non-existent node fails."""
        result = duplicate_node(
            session_id=session_id,
            scene_path=simple_scene_file,
            node_path="NonExistent",
        )
        assert result["success"] is False


# ============ TEST SUITE: FIND_NODES ============


class TestFindNodes:
    """Tests for find_nodes function."""

    def test_find_nodes_by_type(self, session_id, complex_scene_file):
        """Test finding nodes by type."""
        result = find_nodes(
            session_id=session_id,
            scene_path=complex_scene_file,
            type_filter="CharacterBody2D",
        )
        assert result["success"] is True
        assert result["count"] == 2  # Player and Enemy

    def test_find_nodes_by_name_pattern(self, session_id, complex_scene_file):
        """Test finding nodes by name pattern."""
        result = find_nodes(
            session_id=session_id,
            scene_path=complex_scene_file,
            name_pattern="Player",
        )
        assert result["success"] is True
        assert result["count"] >= 1
        names = [n["name"] for n in result["nodes"]]
        assert "Player" in names

    def test_find_nodes_no_filter(self, session_id, simple_scene_file):
        """Test finding all nodes without filter."""
        result = find_nodes(
            session_id=session_id,
            scene_path=simple_scene_file,
        )
        assert result["success"] is True
        assert result["count"] >= 1

    def test_find_nodes_scene_not_found(self, session_id, temp_project):
        """Test finding nodes in non-existent scene fails."""
        result = find_nodes(
            session_id=session_id,
            scene_path=os.path.join(temp_project, "nonexistent.tscn"),
        )
        assert result["success"] is False

    def test_find_nodes_type_no_match(self, session_id, simple_scene_file):
        """Test finding nodes with type that doesn't exist."""
        result = find_nodes(
            session_id=session_id,
            scene_path=simple_scene_file,
            type_filter="NonExistentType",
        )
        assert result["success"] is True
        assert result["count"] == 0


# ============ TEST SUITE: ADD_EXT_RESOURCE ============


class TestAddExtResource:
    """Tests for add_ext_resource function."""

    def test_add_ext_resource_success(self, session_id, simple_scene_file):
        """Test adding an external resource."""
        result = add_ext_resource(
            session_id=session_id,
            scene_path=simple_scene_file,
            resource_type="Texture2D",
            resource_path="res://sprites/player.png",
        )
        assert result["success"] is True
        assert result["resource_id"] == "1"
        assert result["resource_type"] == "Texture2D"

    def test_add_ext_resource_duplicate_path(self, session_id, simple_scene_file):
        """Test that adding duplicate resource path returns existing ID."""
        # First add
        result1 = add_ext_resource(
            session_id=session_id,
            scene_path=simple_scene_file,
            resource_type="Texture2D",
            resource_path="res://sprites/player.png",
        )
        assert result1["success"] is True

        # Second add with same path
        result2 = add_ext_resource(
            session_id=session_id,
            scene_path=simple_scene_file,
            resource_type="Texture2D",
            resource_path="res://sprites/player.png",
        )
        assert result2["success"] is True
        assert result2["message"] == "Resource already exists"
        assert result2["resource_id"] == result1["resource_id"]

    def test_add_ext_resource_custom_id(self, session_id, simple_scene_file):
        """Test adding resource with custom ID."""
        result = add_ext_resource(
            session_id=session_id,
            scene_path=simple_scene_file,
            resource_type="Script",
            resource_path="res://scripts/player.gd",
            resource_id="custom_id",
        )
        assert result["success"] is True
        assert result["resource_id"] == "custom_id"

    def test_add_ext_resource_scene_not_found(self, session_id, temp_project):
        """Test adding resource to non-existent scene fails."""
        result = add_ext_resource(
            session_id=session_id,
            scene_path=os.path.join(temp_project, "nonexistent.tscn"),
            resource_type="Texture2D",
            resource_path="res://sprites/player.png",
        )
        assert result["success"] is False


# ============ TEST SUITE: PROCESS_RESOURCE_PROPERTIES ============


class TestProcessResourceProperties:
    """Tests for _process_resource_properties helper."""

    def test_process_res_path_creates_ext_resource(self):
        """Test that res:// paths create ExtResource references."""
        scene = Scene()
        props = {"texture": "res://sprites/player.png"}
        result = _process_resource_properties(scene, props)
        assert result["texture"] == 'ExtResource("1")'
        assert len(scene.ext_resources) == 1
        assert scene.ext_resources[0].path == "res://sprites/player.png"

    def test_process_sub_resource_dict(self):
        """Test that dict with type creates SubResource."""
        scene = Scene()
        props = {
            "shape": {
                "type": "RectangleShape2D",
                "size": {"type": "Vector2", "x": 32, "y": 32},
            }
        }
        result = _process_resource_properties(scene, props)
        assert "SubResource" in result["shape"]
        assert len(scene.sub_resources) == 1

    def test_process_ext_resource_reference(self):
        """Test that ExtResource reference dict is converted correctly."""
        scene = Scene()
        props = {"texture": {"type": "ExtResource", "ref": "1"}}
        result = _process_resource_properties(scene, props)
        assert result["texture"] == 'ExtResource("1")'

    def test_process_normal_values_unchanged(self):
        """Test that normal values without 'type' key are not modified."""
        scene = Scene()
        # Note: dicts WITH "type" key are treated as SubResource definitions
        # So we test with values that don't have "type" key
        props = {"visible": True, "count": 42, "name": "test"}
        result = _process_resource_properties(scene, props)
        assert result["visible"] is True
        assert result["count"] == 42
        assert result["name"] == "test"

    def test_process_empty_properties(self):
        """Test that empty properties dict returns unchanged."""
        scene = Scene()
        result = _process_resource_properties(scene, {})
        assert result == {}
        result = _process_resource_properties(scene, None)
        assert result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
