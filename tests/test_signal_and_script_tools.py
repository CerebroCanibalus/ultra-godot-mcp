"""
Tests for signal, script, and subresource tools.

Tests:
1. connect_signal - Connect signals between nodes
2. set_script - Attach scripts to nodes
3. add_sub_resource - Create SubResources
"""

import sys
import os
import tempfile
from pathlib import Path

import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from godot_mcp.core.tscn_parser import parse_tscn_string, Scene, Connection
from godot_mcp.tools.signal_and_script_tools import (
    connect_signal,
    set_script,
    add_sub_resource,
)
from godot_mcp.tools.session_tools import (
    get_session_manager,
    set_session_manager,
    start_session,
    end_session,
)


# ============ FIXTURES ============


@pytest.fixture(autouse=True)
def reset_session_manager():
    """Reset session manager before each test to avoid cross-test pollution."""
    from godot_mcp.session_manager import SessionManager

    set_session_manager(SessionManager(auto_save=False))
    yield
    # Sessions use temp dirs that get cleaned up automatically


@pytest.fixture
def temp_project():
    """Create a temporary Godot project directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create project.godot
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
def temp_scene_file(temp_project):
    """Create a temporary TSCN file inside a temp project."""
    content = """[gd_scene load_steps=3 format=3]

[sub_resource type="RectangleShape2D" id="1_shape"]
size = Vector2(32, 32)

[sub_resource type="CircleShape2D" id="2_circle"]
radius = 16.0

[node name="Player" type="CharacterBody2D"]
position = Vector2(100, 200)

[node name="Sprite" type="Sprite2D" parent="Player"]
position = Vector2(0, -20)

[node name="Area2D" type="Area2D" parent="Player"]
position = Vector2(50, 0)

[node name="Hitbox" type="CollisionShape2D" parent="Player/Area2D"]
shape = SubResource("2_circle")
"""
    scene_path = os.path.join(temp_project, "test_scene.tscn")
    with open(scene_path, "w", encoding="utf-8") as f:
        f.write(content)

    yield scene_path


@pytest.fixture
def session_id(temp_project):
    """Create a real session for testing."""
    result = start_session(temp_project)
    assert result["success"] is True
    return result["session_id"]


# ============ CONNECT SIGNAL TESTS ============


class TestConnectSignal:
    """Tests for connect_signal tool."""

    def test_connect_signal_basic(self, temp_scene_file, session_id):
        """Test basic signal connection."""
        result = connect_signal(
            session_id=session_id,
            scene_path=temp_scene_file,
            from_node="Player/Area2D",
            signal="body_entered",
            to_node="Player",
            method="_on_area_body_entered",
        )

        assert result["success"] is True
        assert "body_entered" in result["message"]
        assert result["connection"]["from_node"] == "Player/Area2D"
        assert result["connection"]["signal"] == "body_entered"
        assert result["connection"]["to_node"] == "Player"
        assert result["connection"]["method"] == "_on_area_body_entered"

        # Verify persisted
        scene = parse_tscn_string(open(temp_scene_file, encoding="utf-8").read())
        assert len(scene.connections) == 1
        assert scene.connections[0].signal == "body_entered"

    def test_connect_signal_with_flags(self, temp_scene_file, session_id):
        """Test signal connection with flags."""
        result = connect_signal(
            session_id=session_id,
            scene_path=temp_scene_file,
            from_node="Player/Area2D",
            signal="body_entered",
            to_node="Player",
            method="_on_area_body_entered",
            flags=1,  # oneshot
        )

        assert result["success"] is True
        assert result["connection"]["flags"] == 1

    def test_connect_signal_with_binds(self, temp_scene_file, session_id):
        """Test signal connection with bound values."""
        result = connect_signal(
            session_id=session_id,
            scene_path=temp_scene_file,
            from_node="Player/Area2D",
            signal="body_entered",
            to_node="Player",
            method="_on_area_body_entered",
            binds=["arg1", 42],
        )

        assert result["success"] is True
        assert result["connection"]["binds"] == ["arg1", 42]

    def test_connect_signal_from_node_not_found(self, temp_scene_file, session_id):
        """Test error when source node doesn't exist."""
        result = connect_signal(
            session_id=session_id,
            scene_path=temp_scene_file,
            from_node="NonExistent",
            signal="body_entered",
            to_node="Player",
            method="_on_area_body_entered",
        )

        assert result["success"] is False
        assert "not found" in result["error"].lower()

    def test_connect_signal_to_node_not_found(self, temp_scene_file, session_id):
        """Test error when target node doesn't exist."""
        result = connect_signal(
            session_id=session_id,
            scene_path=temp_scene_file,
            from_node="Player",
            signal="body_entered",
            to_node="NonExistent",
            method="_on_area_body_entered",
        )

        assert result["success"] is False
        assert "not found" in result["error"].lower()

    def test_connect_signal_duplicate(self, temp_scene_file, session_id):
        """Test that duplicate connections are detected."""
        # First connection
        result1 = connect_signal(
            session_id=session_id,
            scene_path=temp_scene_file,
            from_node="Player/Area2D",
            signal="body_entered",
            to_node="Player",
            method="_on_area_body_entered",
        )
        assert result1["success"] is True

        # Duplicate connection
        result2 = connect_signal(
            session_id=session_id,
            scene_path=temp_scene_file,
            from_node="Player/Area2D",
            signal="body_entered",
            to_node="Player",
            method="_on_area_body_entered",
        )
        assert result2["success"] is True
        assert "already exists" in result2["message"]

    def test_connect_signal_file_not_found(self, session_id):
        """Test error when scene file doesn't exist."""
        result = connect_signal(
            session_id=session_id,
            scene_path="nonexistent.tscn",
            from_node="Player",
            signal="body_entered",
            to_node="Player",
            method="_on_area",
        )

        assert result["success"] is False
        assert "not found" in result["error"]

    def test_connect_multiple_signals(self, temp_scene_file, session_id):
        """Test connecting multiple different signals."""
        connect_signal(
            session_id=session_id,
            scene_path=temp_scene_file,
            from_node="Player/Area2D",
            signal="body_entered",
            to_node="Player",
            method="_on_body_entered",
        )

        connect_signal(
            session_id=session_id,
            scene_path=temp_scene_file,
            from_node="Player",
            signal="hit",
            to_node="Sprite",
            method="_on_hit",
        )

        scene = parse_tscn_string(open(temp_scene_file, encoding="utf-8").read())
        assert len(scene.connections) == 2


# ============ SET SCRIPT TESTS ============


class TestSetScript:
    """Tests for set_script tool."""

    def test_set_script_basic(self, temp_scene_file, session_id):
        """Test basic script attachment."""
        result = set_script(
            session_id=session_id,
            scene_path=temp_scene_file,
            node_path="Player",
            script_path="res://scripts/player.gd",
        )

        assert result["success"] is True
        assert result["node"] == "Player"
        assert result["script_path"] == "res://scripts/player.gd"
        assert "resource_id" in result

        # Verify persisted
        scene = parse_tscn_string(open(temp_scene_file, encoding="utf-8").read())
        player = next(n for n in scene.nodes if n.name == "Player")
        assert "script" in player.properties
        assert "ExtResource" in str(player.properties["script"])

    def test_set_script_reuses_existing_ext_resource(self, temp_scene_file, session_id):
        """Test that existing script ExtResource is reused."""
        # Set script first time
        result1 = set_script(
            session_id=session_id,
            scene_path=temp_scene_file,
            node_path="Player",
            script_path="res://scripts/player.gd",
        )
        id1 = result1["resource_id"]

        # Set same script on another node
        result2 = set_script(
            session_id=session_id,
            scene_path=temp_scene_file,
            node_path="Sprite",
            script_path="res://scripts/player.gd",
        )
        id2 = result2["resource_id"]

        # Should reuse the same ExtResource
        assert id1 == id2

    def test_set_script_node_not_found(self, temp_scene_file, session_id):
        """Test error when node doesn't exist."""
        result = set_script(
            session_id=session_id,
            scene_path=temp_scene_file,
            node_path="NonExistent",
            script_path="res://scripts/player.gd",
        )

        assert result["success"] is False
        assert "not found" in result["error"].lower()

    def test_set_script_invalid_path(self, temp_scene_file, session_id):
        """Test error when script path doesn't end with .gd."""
        result = set_script(
            session_id=session_id,
            scene_path=temp_scene_file,
            node_path="Player",
            script_path="res://scripts/player.txt",
        )

        assert result["success"] is False
        assert ".gd" in result["error"]

    def test_set_script_file_not_found(self, session_id):
        """Test error when scene file doesn't exist."""
        result = set_script(
            session_id=session_id,
            scene_path="nonexistent.tscn",
            node_path="Player",
            script_path="res://scripts/player.gd",
        )

        assert result["success"] is False

    def test_set_script_multiple_nodes_different_scripts(
        self, temp_scene_file, session_id
    ):
        """Test setting different scripts on different nodes."""
        set_script(
            session_id=session_id,
            scene_path=temp_scene_file,
            node_path="Player",
            script_path="res://scripts/player.gd",
        )

        set_script(
            session_id=session_id,
            scene_path=temp_scene_file,
            node_path="Sprite",
            script_path="res://scripts/sprite.gd",
        )

        scene = parse_tscn_string(open(temp_scene_file, encoding="utf-8").read())
        player = next(n for n in scene.nodes if n.name == "Player")
        sprite = next(n for n in scene.nodes if n.name == "Sprite")

        assert "script" in player.properties
        assert "script" in sprite.properties

        # Should have 2 different ExtResources
        script_exts = [e for e in scene.ext_resources if e.type == "Script"]
        assert len(script_exts) == 2


# ============ ADD SUB RESOURCE TESTS ============


class TestAddSubResource:
    """Tests for add_sub_resource tool."""

    def test_add_sub_resource_rectangle(self, temp_scene_file, session_id):
        """Test adding a RectangleShape2D."""
        result = add_sub_resource(
            session_id=session_id,
            scene_path=temp_scene_file,
            resource_type="RectangleShape2D",
            properties={"size": {"type": "Vector2", "x": 64, "y": 64}},
        )

        assert result["success"] is True
        assert result["resource_type"] == "RectangleShape2D"
        assert "reference" in result
        assert "SubResource" in result["reference"]

        # Verify persisted
        scene = parse_tscn_string(open(temp_scene_file, encoding="utf-8").read())
        rect_subs = [s for s in scene.sub_resources if s.type == "RectangleShape2D"]
        assert len(rect_subs) == 2  # 1 existing + 1 new

    def test_add_sub_resource_circle(self, temp_scene_file, session_id):
        """Test adding a CircleShape2D."""
        result = add_sub_resource(
            session_id=session_id,
            scene_path=temp_scene_file,
            resource_type="CircleShape2D",
            properties={"radius": 32.0},
        )

        assert result["success"] is True
        assert result["resource_type"] == "CircleShape2D"

        scene = parse_tscn_string(open(temp_scene_file, encoding="utf-8").read())
        circle_subs = [s for s in scene.sub_resources if s.type == "CircleShape2D"]
        assert len(circle_subs) == 2  # 1 existing + 1 new

    def test_add_sub_resource_with_custom_id(self, temp_scene_file, session_id):
        """Test adding SubResource with custom ID."""
        result = add_sub_resource(
            session_id=session_id,
            scene_path=temp_scene_file,
            resource_type="RectangleShape2D",
            properties={"size": {"type": "Vector2", "x": 32, "y": 32}},
            resource_id="my_custom_shape",
        )

        assert result["success"] is True
        assert result["resource_id"] == "my_custom_shape"

        scene = parse_tscn_string(open(temp_scene_file, encoding="utf-8").read())
        custom = next(
            (s for s in scene.sub_resources if s.id == "my_custom_shape"), None
        )
        assert custom is not None
        assert custom.type == "RectangleShape2D"

    def test_add_sub_resource_duplicate_id(self, temp_scene_file, session_id):
        """Test error when SubResource ID already exists."""
        add_sub_resource(
            session_id=session_id,
            scene_path=temp_scene_file,
            resource_type="RectangleShape2D",
            properties={"size": {"type": "Vector2", "x": 32, "y": 32}},
            resource_id="duplicate_test",
        )

        result = add_sub_resource(
            session_id=session_id,
            scene_path=temp_scene_file,
            resource_type="CircleShape2D",
            properties={"radius": 16.0},
            resource_id="duplicate_test",
        )

        assert result["success"] is False
        assert "already exists" in result["error"]

    def test_add_sub_resource_file_not_found(self, session_id):
        """Test error when scene file doesn't exist."""
        result = add_sub_resource(
            session_id=session_id,
            scene_path="nonexistent.tscn",
            resource_type="RectangleShape2D",
            properties={"size": {"type": "Vector2", "x": 32, "y": 32}},
        )

        assert result["success"] is False

    def test_add_sub_resource_no_properties(self, temp_scene_file, session_id):
        """Test adding SubResource with no properties."""
        result = add_sub_resource(
            session_id=session_id,
            scene_path=temp_scene_file,
            resource_type="TileSet",
        )

        assert result["success"] is True

        scene = parse_tscn_string(open(temp_scene_file, encoding="utf-8").read())
        tileset = next((s for s in scene.sub_resources if s.type == "TileSet"), None)
        assert tileset is not None
        assert tileset.properties == {}

    def test_add_sub_resource_updates_load_steps(self, temp_scene_file, session_id):
        """Test that load_steps is updated when adding SubResource."""
        scene_before = parse_tscn_string(open(temp_scene_file, encoding="utf-8").read())
        load_steps_before = scene_before.header.load_steps

        add_sub_resource(
            session_id=session_id,
            scene_path=temp_scene_file,
            resource_type="RectangleShape2D",
            properties={"size": {"type": "Vector2", "x": 32, "y": 32}},
        )

        scene_after = parse_tscn_string(open(temp_scene_file, encoding="utf-8").read())
        assert scene_after.header.load_steps == load_steps_before + 1

    def test_add_sub_resource_vector2_serialization(self, temp_scene_file, session_id):
        """Test that Vector2 properties are serialized correctly."""
        add_sub_resource(
            session_id=session_id,
            scene_path=temp_scene_file,
            resource_type="RectangleShape2D",
            properties={"size": {"type": "Vector2", "x": 64, "y": 48}},
        )

        content = open(temp_scene_file, encoding="utf-8").read()
        assert "size = Vector2(64, 48)" in content

    def test_add_sub_resource_color_serialization(self, temp_scene_file, session_id):
        """Test that Color properties are serialized correctly."""
        add_sub_resource(
            session_id=session_id,
            scene_path=temp_scene_file,
            resource_type="StandardMaterial3D",
            properties={
                "albedo_color": {
                    "type": "Color",
                    "r": 1.0,
                    "g": 0.5,
                    "b": 0.0,
                    "a": 1.0,
                }
            },
        )

        content = open(temp_scene_file, encoding="utf-8").read()
        assert "albedo_color = Color(1.0, 0.5, 0.0, 1.0)" in content


# ============ INTEGRATION TESTS ============


class TestIntegration:
    """Integration tests combining multiple tools."""

    def test_full_scene_workflow(self, session_id):
        """Test creating a complete scene with all tools."""
        content = """[gd_scene load_steps=1 format=3]

[node name="Player" type="CharacterBody2D"]
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".tscn", delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
            scene_path = f.name

        try:
            # 1. Add SubResource
            add_sub_resource(
                session_id=session_id,
                scene_path=scene_path,
                resource_type="CircleShape2D",
                properties={"radius": 16.0},
                resource_id="player_shape",
            )

            # 2. Add child node
            from godot_mcp.tools.node_tools import add_node

            add_node(
                session_id=session_id,
                scene_path=scene_path,
                parent_path="Player",
                node_type="CollisionShape2D",
                node_name="CollisionShape",
                properties={"shape": {"type": "SubResource", "ref": "player_shape"}},
            )

            # 3. Add Area2D for detection
            add_node(
                session_id=session_id,
                scene_path=scene_path,
                parent_path="Player",
                node_type="Area2D",
                node_name="DetectionArea",
            )

            # 4. Connect signal
            connect_signal(
                session_id=session_id,
                scene_path=scene_path,
                from_node="Player/DetectionArea",
                signal="body_entered",
                to_node="Player",
                method="_on_detection",
            )

            # 5. Attach script
            set_script(
                session_id=session_id,
                scene_path=scene_path,
                node_path="Player",
                script_path="res://scripts/player.gd",
            )

            # Verify final state
            scene = parse_tscn_string(open(scene_path, encoding="utf-8").read())

            assert len(scene.sub_resources) == 1
            assert scene.sub_resources[0].id == "player_shape"

            assert len(scene.nodes) == 3  # Player + CollisionShape + DetectionArea

            assert len(scene.connections) == 1
            assert scene.connections[0].signal == "body_entered"

            player = next(n for n in scene.nodes if n.name == "Player")
            assert "script" in player.properties

            assert len(scene.ext_resources) == 1
            assert scene.ext_resources[0].type == "Script"

        finally:
            if os.path.exists(scene_path):
                os.unlink(scene_path)
