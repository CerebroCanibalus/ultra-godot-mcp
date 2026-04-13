"""
pytest fixtures for TSCN parser tests.
"""

import sys
import os
from pathlib import Path

import pytest

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from godot_mcp.core.tscn_parser import (
    Scene,
    SceneNode,
    GdSceneHeader,
    ExtResource,
    SubResource,
    Connection,
)


# =============================================================================
# Paths
# =============================================================================


@pytest.fixture
def test_data_dir() -> Path:
    """Return the test data directory path."""
    return Path(__file__).parent


@pytest.fixture
def test_scene_path(test_data_dir: Path) -> Path:
    """Return path to the example test scene."""
    return test_data_dir / "test_scene.tscn"


# =============================================================================
# Sample TSCN Content
# =============================================================================


SIMPLE_TSCN = """[gd_scene load_steps=1 format=3 uid="uid://simple_abc123"]

[node name="Root" type="Node2D"]
position = Vector2(10, 20)

[node name="Child" type="Sprite2D" parent="Root"]
position = Vector2(5, 5)
"""


COMPLEX_TSCN = """[gd_scene load_steps=3 format=3 uid="uid://complex_def456"

[ext_resource type="Script" path="res://scripts/player.gd" id="1_abc"]
[ext_resource type="PackedScene" uid="uid://sprite_def456" path="res://sprites/player.tscn" id="2_def"]

[sub_resource type="RectangleShape2D" id="1_shape"]
size = Vector2(32, 32)

[node name="Player" type="CharacterBody2D"]
position = Vector2(100, 200)
script = ExtResource("1_abc")

[node name="Sprite" type="Sprite2D" parent="Player"]
texture = ExtResource("2_def")

[node name="CollisionShape2D" type="CollisionShape2D" parent="Player"]
shape = SubResource("1_shape")

[connection signal="body_entered" from="Player" to="." method="_on_body_entered" flags=0]
"""


@pytest.fixture
def simple_tscn_content() -> str:
    """Return simple TSCN content for parsing."""
    return SIMPLE_TSCN


@pytest.fixture
def complex_tscn_content() -> str:
    """Return complex TSCN content for parsing."""
    return COMPLEX_TSCN


# =============================================================================
# Parsed Scene Objects (for testing to_dict/to_tscn round-trip)
# =============================================================================


@pytest.fixture
def sample_scene() -> Scene:
    """Create a sample Scene object with all components."""
    header = GdSceneHeader(
        load_steps=2,
        format=3,
        uid="uid://sample_abc123",
        scene_unique_name="SampleScene",
    )

    ext_resources = [
        ExtResource(
            type="Script",
            path="res://scripts/player.gd",
            id="1_abc",
            uid="uid://script_abc123",
        ),
        ExtResource(
            type="PackedScene",
            path="res://sprites/player.tscn",
            id="2_def",
            uid="uid://sprite_def456",
        ),
    ]

    sub_resources = [
        SubResource(
            type="RectangleShape2D",
            id="1_shape",
            properties={"size": {"type": "Vector2", "x": 32.0, "y": 32.0}},
        ),
        SubResource(type="CircleShape2D", id="2_circle", properties={"radius": 16.0}),
    ]

    nodes = [
        SceneNode(
            name="Player",
            type="CharacterBody2D",
            parent=".",
            properties={
                "position": {"type": "Vector2", "x": 100.0, "y": 200.0},
                "rotation": 0.5,
            },
        ),
        SceneNode(
            name="Sprite",
            type="Sprite2D",
            parent="Player",
            properties={
                "position": {"type": "Vector2", "x": 0.0, "y": -20.0},
                "modulate": {"type": "Color", "r": 1.0, "g": 0.5, "b": 0.5, "a": 1.0},
            },
        ),
    ]

    connections = [
        Connection(
            from_node="Player",
            signal="body_entered",
            to_node=".",
            method="_on_body_entered",
            flags=0,
        ),
    ]

    return Scene(
        header=header,
        ext_resources=ext_resources,
        sub_resources=sub_resources,
        nodes=nodes,
        connections=connections,
    )


@pytest.fixture
def minimal_scene() -> Scene:
    """Create a minimal Scene with just a root node."""
    header = GdSceneHeader(load_steps=1, format=3)
    nodes = [SceneNode(name="Root", type="Node2D", parent=".")]

    return Scene(header=header, nodes=nodes)


# =============================================================================
# Scene for get_node_by_path and find_nodes_by_type tests
# =============================================================================


@pytest.fixture
def nested_scene() -> Scene:
    """Create a nested scene for testing get_node_by_path."""
    header = GdSceneHeader(load_steps=1, format=3)

    nodes = [
        SceneNode(name="Root", type="Node2D", parent="."),
        SceneNode(name="Level", type="Node2D", parent="Root"),
        SceneNode(name="Player", type="CharacterBody2D", parent="Root"),
        SceneNode(name="Enemies", type="Node2D", parent="Root"),
        SceneNode(name="Enemy1", type="CharacterBody2D", parent="Root/Enemies"),
        SceneNode(name="Enemy2", type="CharacterBody2D", parent="Root/Enemies"),
    ]

    return Scene(header=header, nodes=nodes)


# =============================================================================
# Expected results for complex tests
# =============================================================================


@pytest.fixture
def expected_node_types() -> list[str]:
    """Expected node types in the complex scene."""
    return ["CharacterBody2D", "Sprite2D", "CollisionShape2D", "Area2D"]


@pytest.fixture
def expected_sprite_nodes() -> list[str]:
    """Expected node names that are Sprite2D type."""
    return ["Sprite"]
