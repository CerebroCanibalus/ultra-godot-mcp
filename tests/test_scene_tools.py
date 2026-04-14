"""
Tests for scene_tools module.

Tests:
1. create_scene - success, duplicate, invalid project
2. get_scene_tree - cache hit/miss, not found
3. save_scene - success, validation failure
4. list_scenes - recursive, flat, empty project
5. instantiate_scene - success, duplicate sibling, outside project
6. modify_scene - change type, change name, no changes
"""

import sys
import os
import tempfile

import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from godot_mcp.tools.scene_tools import (
    create_scene,
    get_scene_tree,
    save_scene,
    list_scenes,
    instantiate_scene,
    modify_scene,
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


# ============ TEST SUITE: CREATE_SCENE ============


class TestCreateScene:
    """Tests for create_scene function."""

    def test_create_scene_success(self, session_id, temp_project):
        """Test creating a new scene successfully."""
        result = create_scene(
            session_id=session_id,
            project_path=temp_project,
            scene_path="scenes/Player.tscn",
            root_type="CharacterBody2D",
            root_name="Player",
        )
        assert result["success"] is True
        assert result["root_type"] == "CharacterBody2D"
        assert result["root_name"] == "Player"

        # Verify file was created
        full_path = os.path.join(temp_project, "scenes", "Player.tscn")
        assert os.path.exists(full_path)

    def test_create_scene_duplicate_fails(self, session_id, temp_project):
        """Test that creating a duplicate scene fails."""
        # First create
        result1 = create_scene(
            session_id=session_id,
            project_path=temp_project,
            scene_path="Player.tscn",
        )
        assert result1["success"] is True

        # Second create should fail
        result2 = create_scene(
            session_id=session_id,
            project_path=temp_project,
            scene_path="Player.tscn",
        )
        assert result2["success"] is False
        assert "already exists" in result2["error"]

    def test_create_scene_invalid_project(self, session_id):
        """Test creating scene with invalid project path fails."""
        result = create_scene(
            session_id=session_id,
            project_path="/nonexistent/path",
            scene_path="Player.tscn",
        )
        assert result["success"] is False
        assert "does not exist" in result["error"]

    def test_create_scene_not_godot_project(self, session_id, tmp_path):
        """Test creating scene in non-Godot project fails."""
        result = create_scene(
            session_id=session_id,
            project_path=str(tmp_path),
            scene_path="Player.tscn",
        )
        assert result["success"] is False
        assert "no project.godot" in result["error"]

    def test_create_scene_default_root(self, session_id, temp_project):
        """Test creating scene with default root type and name."""
        result = create_scene(
            session_id=session_id,
            project_path=temp_project,
            scene_path="Default.tscn",
        )
        assert result["success"] is True
        assert result["root_type"] == "Node2D"
        assert result["root_name"] == "Root"


# ============ TEST SUITE: GET_SCENE_TREE ============


class TestGetSceneTree:
    """Tests for get_scene_tree function."""

    def test_get_scene_tree_success(self, session_id, temp_project):
        """Test getting scene tree from file."""
        # Create a scene first
        create_scene(
            session_id=session_id,
            project_path=temp_project,
            scene_path="Test.tscn",
            root_type="Node2D",
            root_name="Root",
        )

        full_path = os.path.join(temp_project, "Test.tscn")
        result = get_scene_tree(
            session_id=session_id,
            scene_path=full_path,
        )
        assert result["success"] is True
        assert "data" in result
        assert len(result["data"]["nodes"]) >= 1

    def test_get_scene_tree_not_found(self, session_id, temp_project):
        """Test getting scene tree from non-existent file fails."""
        result = get_scene_tree(
            session_id=session_id,
            scene_path=os.path.join(temp_project, "nonexistent.tscn"),
        )
        assert result["success"] is False
        assert "not found" in result["error"]

    def test_get_scene_tree_cache_hit(self, session_id, temp_project):
        """Test that second call returns cached result."""
        # Create a scene (this also caches it)
        create_scene(
            session_id=session_id,
            project_path=temp_project,
            scene_path="CacheTest.tscn",
        )

        full_path = os.path.join(temp_project, "CacheTest.tscn")

        # First call - already cached by create_scene
        result1 = get_scene_tree(
            session_id=session_id,
            scene_path=full_path,
        )
        assert result1["success"] is True

        # Second call - definitely cache hit
        result2 = get_scene_tree(
            session_id=session_id,
            scene_path=full_path,
        )
        assert result2["success"] is True
        # Both calls may be from_cache since create_scene caches
        assert result1["data"] == result2["data"]


# ============ TEST SUITE: SAVE_SCENE ============


class TestSaveScene:
    """Tests for save_scene function."""

    def test_save_scene_success(self, session_id, temp_project):
        """Test saving a scene successfully."""
        # Create a scene first
        create_scene(
            session_id=session_id,
            project_path=temp_project,
            scene_path="SaveTest.tscn",
        )

        full_path = os.path.join(temp_project, "SaveTest.tscn")

        # Get the scene data
        tree = get_scene_tree(session_id=session_id, scene_path=full_path)
        scene_data = tree["data"]

        # Save it back
        result = save_scene(
            session_id=session_id,
            scene_path=full_path,
            scene_data=scene_data,
        )
        assert result["success"] is True

    def test_save_scene_validation_failure(self, session_id, temp_project):
        """Test saving invalid scene data fails validation."""
        full_path = os.path.join(temp_project, "InvalidSave.tscn")

        # Create invalid scene data (root with parent attribute)
        invalid_data = {
            "header": {"load_steps": 1, "format": 3},
            "nodes": [
                {
                    "name": "Root",
                    "type": "Node2D",
                    "parent": "SomeParent",  # Root shouldn't have parent
                    "properties": {},
                }
            ],
        }

        result = save_scene(
            session_id=session_id,
            scene_path=full_path,
            scene_data=invalid_data,
        )
        assert result["success"] is False
        assert "validation failed" in result["error"]


# ============ TEST SUITE: LIST_SCENES ============


class TestListScenes:
    """Tests for list_scenes function."""

    def test_list_scenes_recursive(self, session_id, temp_project):
        """Test listing scenes recursively."""
        # Create scenes in different directories
        create_scene(
            session_id=session_id,
            project_path=temp_project,
            scene_path="scenes/Player.tscn",
        )
        create_scene(
            session_id=session_id,
            project_path=temp_project,
            scene_path="scenes/levels/Level1.tscn",
        )
        create_scene(
            session_id=session_id,
            project_path=temp_project,
            scene_path="Main.tscn",
        )

        result = list_scenes(
            session_id=session_id,
            project_path=temp_project,
            recursive=True,
        )
        assert result["success"] is True
        assert result["count"] == 3

    def test_list_scenes_non_recursive(self, session_id, temp_project):
        """Test listing scenes only in root directory."""
        create_scene(
            session_id=session_id,
            project_path=temp_project,
            scene_path="Main.tscn",
        )
        create_scene(
            session_id=session_id,
            project_path=temp_project,
            scene_path="scenes/Player.tscn",
        )

        result = list_scenes(
            session_id=session_id,
            project_path=temp_project,
            recursive=False,
        )
        assert result["success"] is True
        assert result["count"] == 1  # Only Main.tscn in root

    def test_list_scenes_empty_project(self, session_id, temp_project):
        """Test listing scenes in empty project."""
        result = list_scenes(
            session_id=session_id,
            project_path=temp_project,
            recursive=True,
        )
        assert result["success"] is True
        assert result["count"] == 0

    def test_list_scenes_invalid_project(self, session_id):
        """Test listing scenes in invalid project."""
        result = list_scenes(
            session_id=session_id,
            project_path="/nonexistent/path",
        )
        assert result["success"] is False


# ============ TEST SUITE: INSTANTIATE_SCENE ============


class TestInstantiateScene:
    """Tests for instantiate_scene function."""

    def test_instantiate_scene_success(self, session_id, temp_project):
        """Test instantiating a scene successfully."""
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

        result = instantiate_scene(
            session_id=session_id,
            scene_path=child_path,
            parent_scene_path=parent_path,
            node_name="MyChild",
            parent_node_path=".",
            project_path=temp_project,
        )
        assert result["success"] is True

    def test_instantiate_scene_duplicate_sibling(self, session_id, temp_project):
        """Test that instantiating with duplicate sibling name fails."""
        # Create child scene
        child_path = os.path.join(temp_project, "Child.tscn")
        with open(child_path, "w", encoding="utf-8") as f:
            f.write("""[gd_scene load_steps=1 format=3]

[node name="ChildRoot" type="Node2D"]
""")

        # Create parent scene with existing node under "."
        parent_path = os.path.join(temp_project, "Parent.tscn")
        with open(parent_path, "w", encoding="utf-8") as f:
            f.write("""[gd_scene load_steps=1 format=3]

[node name="Root" type="Node2D"]

[node name="MyChild" type="Node2D" parent="."]
""")

        result = instantiate_scene(
            session_id=session_id,
            scene_path=child_path,
            parent_scene_path=parent_path,
            node_name="MyChild",
            parent_node_path=".",
            project_path=temp_project,
        )
        assert result["success"] is False
        assert "already exists" in result["error"]

    def test_instantiate_scene_child_not_found(self, session_id, temp_project):
        """Test instantiating non-existent child scene fails."""
        parent_path = os.path.join(temp_project, "Parent.tscn")
        with open(parent_path, "w", encoding="utf-8") as f:
            f.write("""[gd_scene load_steps=1 format=3]

[node name="Root" type="Node2D"]
""")

        result = instantiate_scene(
            session_id=session_id,
            scene_path=os.path.join(temp_project, "NonExistent.tscn"),
            parent_scene_path=parent_path,
            node_name="MyChild",
        )
        assert result["success"] is False

    def test_instantiate_scene_parent_not_found(self, session_id, temp_project):
        """Test instantiating into non-existent parent scene fails."""
        child_path = os.path.join(temp_project, "Child.tscn")
        with open(child_path, "w", encoding="utf-8") as f:
            f.write("""[gd_scene load_steps=1 format=3]

[node name="ChildRoot" type="Node2D"]
""")

        result = instantiate_scene(
            session_id=session_id,
            scene_path=child_path,
            parent_scene_path=os.path.join(temp_project, "NonExistent.tscn"),
            node_name="MyChild",
        )
        assert result["success"] is False

    def test_instantiate_scene_outside_project(self, session_id, temp_project):
        """Test instantiating scene outside project fails."""
        # Create child scene outside project
        with tempfile.TemporaryDirectory() as outside_dir:
            child_path = os.path.join(outside_dir, "Child.tscn")
            with open(child_path, "w", encoding="utf-8") as f:
                f.write("""[gd_scene load_steps=1 format=3]

[node name="ChildRoot" type="Node2D"]
""")

            parent_path = os.path.join(temp_project, "Parent.tscn")
            with open(parent_path, "w", encoding="utf-8") as f:
                f.write("""[gd_scene load_steps=1 format=3]

[node name="Root" type="Node2D"]
""")

            result = instantiate_scene(
                session_id=session_id,
                scene_path=child_path,
                parent_scene_path=parent_path,
                node_name="MyChild",
                project_path=temp_project,
            )
            assert result["success"] is False
            assert "outside" in result["error"].lower()


# ============ TEST SUITE: MODIFY_SCENE ============


class TestModifyScene:
    """Tests for modify_scene function."""

    def test_modify_scene_change_type(self, session_id, temp_project):
        """Test modifying scene root type."""
        # Create a scene
        create_scene(
            session_id=session_id,
            project_path=temp_project,
            scene_path="ModifyTest.tscn",
            root_type="Node2D",
            root_name="Root",
        )

        result = modify_scene(
            session_id=session_id,
            project_path=temp_project,
            scene_path="ModifyTest.tscn",
            new_root_type="CharacterBody2D",
        )
        assert result["success"] is True
        assert result["new_root_type"] == "CharacterBody2D"

    def test_modify_scene_change_name(self, session_id, temp_project):
        """Test modifying scene root name."""
        create_scene(
            session_id=session_id,
            project_path=temp_project,
            scene_path="ModifyName.tscn",
            root_type="Node2D",
            root_name="Root",
        )

        result = modify_scene(
            session_id=session_id,
            project_path=temp_project,
            scene_path="ModifyName.tscn",
            new_root_name="NewRoot",
        )
        assert result["success"] is True
        assert result["new_root_name"] == "NewRoot"

    def test_modify_scene_no_changes(self, session_id, temp_project):
        """Test modifying scene with no changes fails."""
        create_scene(
            session_id=session_id,
            project_path=temp_project,
            scene_path="NoChange.tscn",
        )

        result = modify_scene(
            session_id=session_id,
            project_path=temp_project,
            scene_path="NoChange.tscn",
        )
        assert result["success"] is False
        assert "No changes" in result["error"]

    def test_modify_scene_not_found(self, session_id, temp_project):
        """Test modifying non-existent scene fails."""
        result = modify_scene(
            session_id=session_id,
            project_path=temp_project,
            scene_path="NonExistent.tscn",
            new_root_type="Node2D",
        )
        assert result["success"] is False

    def test_modify_scene_invalid_project(self, session_id):
        """Test modifying scene with invalid project fails."""
        result = modify_scene(
            session_id=session_id,
            project_path="/nonexistent",
            scene_path="Test.tscn",
            new_root_type="Node2D",
        )
        assert result["success"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
