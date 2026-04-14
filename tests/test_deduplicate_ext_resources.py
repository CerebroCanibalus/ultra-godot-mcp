"""
Tests for Scene.deduplicate_ext_resources()

Covers edge cases:
1. Basic duplicate removal
2. Path normalization (res://a/../b → res://b)
3. Same path, different type (NOT duplicates)
4. Remap ExtResource in node properties
5. Remap ExtResource in sub-resource properties
6. Remap ExtResource in nested Arrays/Dicts
7. Remap ExtResource in raw strings
8. No duplicates (no-op)
"""

import pytest
from godot_mcp.core.tscn_parser import (
    Scene,
    ExtResource,
    SceneNode,
    SubResource,
    GdSceneHeader,
)


class TestDeduplicateExtResources:
    """Test suite for Scene.deduplicate_ext_resources()"""

    def _make_scene(self, ext_resources, nodes=None, sub_resources=None):
        """Helper to create a Scene with given resources."""
        scene = Scene(
            header=GdSceneHeader(load_steps=2, format=3),
            ext_resources=ext_resources,
            nodes=nodes or [],
            sub_resources=sub_resources or [],
        )
        return scene

    # === Test 1: Basic duplicate removal ===

    def test_basic_duplicate_removal(self):
        """Two ExtResources with same path → keep first, remove second."""
        scene = self._make_scene(
            ext_resources=[
                ExtResource(type="PackedScene", path="res://player.tscn", id="1"),
                ExtResource(type="PackedScene", path="res://player.tscn", id="2"),
            ],
            nodes=[
                SceneNode(
                    name="Player1",
                    type="PackedScene",
                    parent=".",
                    properties={"scene_file_path": {"type": "ExtResource", "ref": "1"}},
                ),
                SceneNode(
                    name="Player2",
                    type="PackedScene",
                    parent=".",
                    properties={"scene_file_path": {"type": "ExtResource", "ref": "2"}},
                ),
            ],
        )

        result = scene.deduplicate_ext_resources()

        assert result["removed"] == 1
        assert result["remapped"] == 1  # Player2 ref "2" → "1"
        assert len(scene.ext_resources) == 1
        assert scene.ext_resources[0].id == "1"

        # Both nodes should now reference "1"
        assert scene.nodes[0].properties["scene_file_path"]["ref"] == "1"
        assert scene.nodes[1].properties["scene_file_path"]["ref"] == "1"

    # === Test 2: Path normalization ===

    def test_path_normalization_collapses_dotdot(self):
        """res://a/b/../c.tscn should normalize to res://a/c.tscn."""
        scene = self._make_scene(
            ext_resources=[
                ExtResource(
                    type="PackedScene", path="res://scenes/player.tscn", id="1"
                ),
                ExtResource(
                    type="PackedScene",
                    path="res://scenes/../scenes/player.tscn",
                    id="2",
                ),
            ],
            nodes=[
                SceneNode(
                    name="P1",
                    type="PackedScene",
                    parent=".",
                    properties={"scene_file_path": {"type": "ExtResource", "ref": "2"}},
                ),
            ],
        )

        result = scene.deduplicate_ext_resources()

        assert result["removed"] == 1
        assert result["remapped"] == 1
        # Path should be normalized
        assert scene.ext_resources[0].path == "res://scenes/player.tscn"
        assert scene.nodes[0].properties["scene_file_path"]["ref"] == "1"

    def test_path_normalization_collapses_dot(self):
        """res://a/./b.tscn should normalize to res://a/b.tscn."""
        scene = self._make_scene(
            ext_resources=[
                ExtResource(type="Texture2D", path="res://sprites/icon.png", id="1"),
                ExtResource(type="Texture2D", path="res://sprites/./icon.png", id="2"),
            ],
        )

        result = scene.deduplicate_ext_resources()

        assert result["removed"] == 1
        assert scene.ext_resources[0].path == "res://sprites/icon.png"

    def test_path_normalization_collapses_double_slash(self):
        """res://a//b.tscn should normalize to res://a/b.tscn."""
        scene = self._make_scene(
            ext_resources=[
                ExtResource(type="Script", path="res://scripts/player.gd", id="1"),
                ExtResource(type="Script", path="res://scripts//player.gd", id="2"),
            ],
        )

        result = scene.deduplicate_ext_resources()

        assert result["removed"] == 1
        assert scene.ext_resources[0].path == "res://scripts/player.gd"

    # === Test 3: Same path, different type ===

    def test_same_path_different_type_not_duplicate(self):
        """Same path but different type → NOT duplicates."""
        scene = self._make_scene(
            ext_resources=[
                ExtResource(type="PackedScene", path="res://player.tscn", id="1"),
                ExtResource(type="Texture2D", path="res://player.tscn", id="2"),
            ],
        )

        result = scene.deduplicate_ext_resources()

        assert result["removed"] == 0
        assert len(scene.ext_resources) == 2

    # === Test 4: Remap in sub-resource properties ===

    def test_remap_in_sub_resource_properties(self):
        """ExtResource refs in sub-resources should be remapped."""
        scene = self._make_scene(
            ext_resources=[
                ExtResource(type="Texture2D", path="res://icon.png", id="1"),
                ExtResource(type="Texture2D", path="res://icon.png", id="2"),
            ],
            sub_resources=[
                SubResource(
                    type="StandardMaterial3D",
                    id="mat1",
                    properties={"albedo_texture": {"type": "ExtResource", "ref": "2"}},
                ),
            ],
        )

        result = scene.deduplicate_ext_resources()

        assert result["removed"] == 1
        assert result["remapped"] == 1
        assert scene.sub_resources[0].properties["albedo_texture"]["ref"] == "1"

    # === Test 5: Remap in nested Arrays ===

    def test_remap_in_nested_array(self):
        """ExtResource refs inside Array items should be remapped."""
        scene = self._make_scene(
            ext_resources=[
                ExtResource(type="Texture2D", path="res://a.png", id="1"),
                ExtResource(type="Texture2D", path="res://a.png", id="2"),
            ],
            nodes=[
                SceneNode(
                    name="Sprite",
                    type="Sprite2D",
                    parent=".",
                    properties={
                        "textures": {
                            "type": "Array",
                            "items": [
                                {"type": "ExtResource", "ref": "1"},
                                {"type": "ExtResource", "ref": "2"},
                            ],
                        }
                    },
                ),
            ],
        )

        result = scene.deduplicate_ext_resources()

        assert result["removed"] == 1
        assert result["remapped"] == 1  # Only "2" needs remapping
        items = scene.nodes[0].properties["textures"]["items"]
        assert items[0]["ref"] == "1"
        assert items[1]["ref"] == "1"

    # === Test 6: Remap in nested Dicts ===

    def test_remap_in_nested_dictionary(self):
        """ExtResource refs inside Dictionary items should be remapped."""
        scene = self._make_scene(
            ext_resources=[
                ExtResource(type="Texture2D", path="res://b.png", id="1"),
                ExtResource(type="Texture2D", path="res://b.png", id="2"),
            ],
            nodes=[
                SceneNode(
                    name="Atlas",
                    type="Node2D",
                    parent=".",
                    properties={
                        "atlas": {
                            "type": "Dictionary",
                            "items": {
                                "face": {"type": "ExtResource", "ref": "2"},
                                "body": {"type": "ExtResource", "ref": "1"},
                            },
                        }
                    },
                ),
            ],
        )

        result = scene.deduplicate_ext_resources()

        assert result["removed"] == 1
        assert result["remapped"] == 1  # Only "2" needs remapping
        items = scene.nodes[0].properties["atlas"]["items"]
        assert items["face"]["ref"] == "1"
        assert items["body"]["ref"] == "1"

    # === Test 7: Remap in raw strings ===

    def test_remap_in_raw_string(self):
        """Raw string 'ExtResource("2")' should be remapped."""
        scene = self._make_scene(
            ext_resources=[
                ExtResource(type="Script", path="res://player.gd", id="1"),
                ExtResource(type="Script", path="res://player.gd", id="2"),
            ],
            nodes=[
                SceneNode(
                    name="Player",
                    type="Node2D",
                    parent=".",
                    properties={"script": 'ExtResource("2")'},
                ),
            ],
        )

        result = scene.deduplicate_ext_resources()

        assert result["removed"] == 1
        assert result["remapped"] == 1
        assert scene.nodes[0].properties["script"] == 'ExtResource("1")'

    # === Test 8: No duplicates (no-op) ===

    def test_no_duplicates_is_noop(self):
        """Scene with no duplicates → nothing changes."""
        scene = self._make_scene(
            ext_resources=[
                ExtResource(type="PackedScene", path="res://a.tscn", id="1"),
                ExtResource(type="PackedScene", path="res://b.tscn", id="2"),
                ExtResource(type="Texture2D", path="res://c.png", id="3"),
            ],
            nodes=[
                SceneNode(
                    name="A",
                    type="PackedScene",
                    parent=".",
                    properties={"scene_file_path": {"type": "ExtResource", "ref": "1"}},
                ),
            ],
        )

        result = scene.deduplicate_ext_resources()

        assert result["removed"] == 0
        assert result["remapped"] == 0
        assert result["kept"] == 3
        assert len(scene.ext_resources) == 3

    # === Test 9: Multiple duplicates ===

    def test_multiple_duplicates_of_same_path(self):
        """3 duplicates of same path → keep 1, remove 2."""
        scene = self._make_scene(
            ext_resources=[
                ExtResource(type="PackedScene", path="res://enemy.tscn", id="1"),
                ExtResource(type="PackedScene", path="res://enemy.tscn", id="5"),
                ExtResource(type="PackedScene", path="res://enemy.tscn", id="10"),
            ],
            nodes=[
                SceneNode(
                    name="E1",
                    type="PackedScene",
                    parent=".",
                    properties={"scene_file_path": {"type": "ExtResource", "ref": "1"}},
                ),
                SceneNode(
                    name="E2",
                    type="PackedScene",
                    parent=".",
                    properties={"scene_file_path": {"type": "ExtResource", "ref": "5"}},
                ),
                SceneNode(
                    name="E3",
                    type="PackedScene",
                    parent=".",
                    properties={
                        "scene_file_path": {"type": "ExtResource", "ref": "10"}
                    },
                ),
            ],
        )

        result = scene.deduplicate_ext_resources()

        assert result["removed"] == 2
        assert result["remapped"] == 2  # "5" → "1", "10" → "1"
        assert len(scene.ext_resources) == 1
        assert scene.ext_resources[0].id == "1"

        for node in scene.nodes:
            assert node.properties["scene_file_path"]["ref"] == "1"

    # === Test 10: Empty scene ===

    def test_empty_scene(self):
        """Scene with no ext_resources → no-op."""
        scene = Scene(header=GdSceneHeader(load_steps=1, format=3))

        result = scene.deduplicate_ext_resources()

        assert result["removed"] == 0
        assert result["remapped"] == 0
        assert result["kept"] == 0
