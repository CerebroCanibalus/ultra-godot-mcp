"""
Node Templates for Godot Engine - Jinja2 Templates for Node Generation

This module provides templates for generating Godot node structures in .tscn format.
Each template supports customization through Jinja2 variables.

Usage:
    from godot_mcp.templates.node_templates import get_template, render_template, list_templates

    # Get a specific template
    template = get_template("character_body_2d")

    # Render with custom variables
    rendered = render_template("character_body_2d", {"name": "Player", "x": 100, "y": 200})

    # List all available templates
    templates = list_templates()
"""

from typing import Any, Callable
from jinja2 import BaseLoader, Environment, TemplateNotFound

# =============================================================================
# TEMPLATE REGISTRY
# =============================================================================

# Registry mapping template names to template strings
_TEMPLATE_REGISTRY: dict[str, str] = {}

# =============================================================================
# JINJA2 SETUP
# =============================================================================


class DictLoader(BaseLoader):
    """Jinja2 loader that loads templates from a dictionary."""

    def get_source(
        self, environment: Environment, template: str
    ) -> tuple[str, str, bool]:
        """Load template source from dictionary."""
        if template not in _TEMPLATE_REGISTRY:
            raise TemplateNotFound(template)
        source = _TEMPLATE_REGISTRY[template]
        return source, template, True


# =============================================================================
# TEMPLATE DEFINITIONS
# =============================================================================


def _register_templates() -> None:
    """Register all node templates."""

    # -------------------------------------------------------------------------
    # Node2D Basic Template
    # -------------------------------------------------------------------------
    _TEMPLATE_REGISTRY[
        "node2d_basic"
    ] = """[gd_scene load_steps=2 format=3 uid="uid://{{ uid }}"]

{% if script %}
[ext_resource type="Script" path="{{ script_path }}" id="{{ script_id }}"]
{% endif %}

[node name="{{ name }}" type="Node2D"]
position = Vector2({{ x }}, {{ y }})
z_index = {{ z_index }}
z_as_relative = {{ z_as_relative }}
{% if script %}script = ExtResource("{{ script_id }}"){% endif %}
"""

    # -------------------------------------------------------------------------
    # Node2D with Sprite Template
    # -------------------------------------------------------------------------
    _TEMPLATE_REGISTRY[
        "node2d_sprite"
    ] = """[gd_scene load_steps=3 format=3 uid="uid://{{ uid }}"]

[ext_resource type="Texture2D" path="{{ sprite_path }}" id="1"]

{% if script %}
[ext_resource type="Script" path="{{ script_path }}" id="{{ script_id }}"]
{% endif %}

[node name="{{ name }}" type="Node2D"]
position = Vector2({{ x }}, {{ y }})
z_index = {{ z_index }}
z_as_relative = {{ z_as_relative }}
{% if script %}script = ExtResource("{{ script_id }}"){% endif %}

[node name="Sprite2D" type="Sprite2D" parent="."]
texture = ExtResource("1")
hframes = {{ hframes }}
vframes = {{ vframes }}
frame = {{ frame }}

[node name="AnimationPlayer" type="AnimationPlayer" parent="Sprite2D"]
"""

    # -------------------------------------------------------------------------
    # Node2D with Collision Template
    # -------------------------------------------------------------------------
    _TEMPLATE_REGISTRY[
        "node2d_collision"
    ] = """[gd_scene load_steps=4 format=3 uid="uid://{{ uid }}"]

[ext_resource type="Texture2D" path="{{ sprite_path }}" id="1"]
[ext_resource type="Shape2D" path="{{ collision_shape_path }}" id="2"]

{% if script %}
[ext_resource type="Script" path="{{ script_path }}" id="{{ script_id }}"]
{% endif %}

[node name="{{ name }}" type="Node2D"]
position = Vector2({{ x }}, {{ y }})
z_index = {{ z_index }}
z_as_relative = {{ z_as_relative }}
{% if script %}script = ExtResource("{{ script_id }}"){% endif %}

[node name="Sprite2D" type="Sprite2D" parent="."]
texture = ExtResource("1")
hframes = {{ hframes }}
vframes = {{ vframes }}
frame = {{ frame }}

[node name="CollisionShape2D" type="CollisionShape2D" parent="."]
shape = ExtResource("2")
"""

    # -------------------------------------------------------------------------
    # CharacterBody2D Player Template
    # -------------------------------------------------------------------------
    _TEMPLATE_REGISTRY[
        "character_body_2d"
    ] = """[gd_scene load_steps=5 format=3 uid="uid://{{ uid }}"]

[ext_resource type="Texture2D" path="{{ sprite_path }}" id="1"]
[ext_resource type="Shape2D" path="{{ collision_shape_path }}" id="2"]

{% if script %}
[ext_resource type="Script" path="{{ script_path }}" id="{{ script_id }}"]
{% endif %}

[node name="{{ name }}" type="CharacterBody2D"]
position = Vector2({{ x }}, {{ y }})
z_index = {{ z_index }}
z_as_relative = {{ z_as_relative }}
floor_stop_on_slide = {{ floor_stop_on_slide }}
floor_max_angle = {{ floor_max_angle }}
floor_friction = {{ floor_friction }}
wall_slide_speed = {{ wall_slide_speed }}
max_slides = {{ max_slides }}
gravity = {{ gravity }}
jump_force = {{ jump_force }}
{% if script %}script = ExtResource("{{ script_id }}"){% endif %}

[node name="Sprite2D" type="Sprite2D" parent="."]
texture = ExtResource("1")
hframes = {{ hframes }}
vframes = {{ vframes }}
frame = {{ frame }}

[node name="CollisionShape2D" type="CollisionShape2D" parent="."]
shape = ExtResource("2")

[node name="AnimationPlayer" type="AnimationPlayer" parent="."]
"""

    # -------------------------------------------------------------------------
    # CharacterBody2D with State Machine
    # -------------------------------------------------------------------------
    _TEMPLATE_REGISTRY[
        "character_body_2d_state"
    ] = """[gd_scene load_steps=7 format=3 uid="uid://{{ uid }}"]

[ext_resource type="Texture2D" path="{{ sprite_path }}" id="1"]
[ext_resource type="Shape2D" path="{{ collision_shape_path }}" id="2"]
[ext_resource type="Script" path="{{ state_machine_path }}" id="3"]

{% if script %}
[ext_resource type="Script" path="{{ script_path }}" id="{{ script_id }}"]
{% endif %}

[node name="{{ name }}" type="CharacterBody2D"]
position = Vector2({{ x }}, {{ y }})
z_index = {{ z_index }}
z_as_relative = {{ z_as_relative }}
floor_stop_on_slide = {{ floor_stop_on_slide }}
floor_max_angle = {{ floor_max_angle }}
floor_friction = {{ floor_friction }}
wall_slide_speed = {{ wall_slide_speed }}
max_slides = {{ max_slides }}
gravity = {{ gravity }}
jump_force = {{ jump_force }}
{% if script %}script = ExtResource("{{ script_id }}"){% endif %}

[node name="Sprite2D" type="Sprite2D" parent="."]
texture = ExtResource("1")
hframes = {{ hframes }}
vframes = {{ vframes }}
frame = {{ frame }}

[node name="CollisionShape2D" type="CollisionShape2D" parent="."]
shape = ExtResource("2")

[node name="AnimationPlayer" type="AnimationPlayer" parent="."]

[node name="StateMachine" type="Node" parent="."]
script = ExtResource("3")
"""

    # -------------------------------------------------------------------------
    # Area2D Trigger Zone Template
    # -------------------------------------------------------------------------
    _TEMPLATE_REGISTRY[
        "area2d_trigger"
    ] = """[gd_scene load_steps=3 format=3 uid="uid://{{ uid }}"]

[ext_resource type="Shape2D" path="{{ collision_shape_path }}" id="1"]

{% if script %}
[ext_resource type="Script" path="{{ script_path }}" id="{{ script_id }}"]
{% endif %}

[node name="{{ name }}" type="Area2D"]
position = Vector2({{ x }}, {{ y }})
z_index = {{ z_index }}
z_as_relative = {{ z_as_relative }}
monitoring = {{ monitoring }}
monitorable = {{ monitorable }}
priority = {{ priority }}
collision_layer = {{ collision_layer }}
collision_mask = {{ collision_mask }}
{% if script %}script = ExtResource("{{ script_id }}"){% endif %}

[node name="CollisionShape2D" type="CollisionShape2D" parent="."]
shape = ExtResource("1")
"""

    # -------------------------------------------------------------------------
    # Area2D Detection Zone (for enemies/ collectors)
    # -------------------------------------------------------------------------
    _TEMPLATE_REGISTRY[
        "area2d_detection"
    ] = """[gd_scene load_steps=3 format=3 uid="uid://{{ uid }}"]

[ext_resource type="Shape2D" path="{{ collision_shape_path }}" id="1"]

{% if script %}
[ext_resource type="Script" path="{{ script_path }}" id="{{ script_id }}"]
{% endif %}

[node name="{{ name }}" type="Area2D"]
position = Vector2({{ x }}, {{ y }})
z_index = {{ z_index }}
z_as_relative = {{ z_as_relative }}
monitoring = {{ monitoring }}
monitorable = {{ monitorable }}
priority = {{ priority }}
collision_layer = {{ collision_layer }}
collision_mask = {{ collision_mask }}
{% if script %}script = ExtResource("{{ script_id }}"){% endif %}

[node name="CollisionShape2D" type="CollisionShape2D" parent="."]
shape = ExtResource("1")
modulate = Color({{ modulate_r }}, {{ modulate_g }}, {{ modulate_b }}, {{ modulate_a }})

[node name="DebugLabel" type="Label" parent="."]
visible = {{ show_debug }}
offset_left = -50.0
offset_top = -30.0
offset_right = 50.0
offset_bottom = -10.0
text = "{{ name }}"
horizontal_alignment = 1
"""

    # -------------------------------------------------------------------------
    # RigidBody2D Template
    # -------------------------------------------------------------------------
    _TEMPLATE_REGISTRY[
        "rigid_body_2d"
    ] = """[gd_scene load_steps=4 format=3 uid="uid://{{ uid }}"]

[ext_resource type="Texture2D" path="{{ sprite_path }}" id="1"]
[ext_resource type="Shape2D" path="{{ collision_shape_path }}" id="2"]

{% if script %}
[ext_resource type="Script" path="{{ script_path }}" id="{{ script_id }}"]
{% endif %}

[node name="{{ name }}" type="RigidBody2D"]
position = Vector2({{ x }}, {{ y }})
z_index = {{ z_index }}
z_as_relative = {{ z_as_relative }}
freeze = {{ freeze }}
freeze_mode = {{ freeze_mode }}
linear_damp = {{ linear_damp }}
angular_damp = {{ angular_damp }}
gravity_scale = {{ gravity_scale }}
can_sleep = {{ can_sleep }}
lock_rotation = {{ lock_rotation }}
priority = {{ priority }}
collision_layer = {{ collision_layer }}
collision_mask = {{ collision_mask }}
{% if script %}script = ExtResource("{{ script_id }}"){% endif %}

[node name="Sprite2D" type="Sprite2D" parent="."]
texture = ExtResource("1")
hframes = {{ hframes }}
vframes = {{ vframes }}
frame = {{ frame }}

[node name="CollisionShape2D" type="CollisionShape2D" parent="."]
shape = ExtResource("2")
"""

    # -------------------------------------------------------------------------
    # StaticBody2D Template
    # -------------------------------------------------------------------------
    _TEMPLATE_REGISTRY[
        "static_body_2d"
    ] = """[gd_scene load_steps=4 format=3 uid="uid://{{ uid }}"]

[ext_resource type="Texture2D" path="{{ sprite_path }}" id="1"]
[ext_resource type="Shape2D" path="{{ collision_shape_path }}" id="2"]

{% if script %}
[ext_resource type="Script" path="{{ script_path }}" id="{{ script_id }}"]
{% endif %}

[node name="{{ name }}" type="StaticBody2D"]
position = Vector2({{ x }}, {{ y }})
z_index = {{ z_index }}
z_as_relative = {{ z_as_relative }}
collision_layer = {{ collision_layer }}
collision_mask = {{ collision_mask }}
constant_linear_velocity = Vector2({{ constant_vel_x }}, {{ constant_vel_y }})
constant_angular_velocity = {{ constant_angular_vel }}
{% if script %}script = ExtResource("{{ script_id }}"){% endif %}

[node name="Sprite2D" type="Sprite2D" parent="."]
texture = ExtResource("1")
hframes = {{ hframes }}
vframes = {{ vframes }}
frame = {{ frame }}

[node name="CollisionShape2D" type="CollisionShape2D" parent="."]
shape = ExtResource("2")
"""

    # -------------------------------------------------------------------------
    # Control/Button Template
    # -------------------------------------------------------------------------
    _TEMPLATE_REGISTRY[
        "control_button"
    ] = """[gd_scene load_steps={% if script %}2{% else %}1{% endif %} format=3 uid="uid://{{ uid }}"]

{% if script %}
[ext_resource type="Script" path="{{ script_path }}" id="1"]

{% endif %}
[node name="{{ name }}" type="Button"]
anchors_preset = {{ anchors_preset }}
anchor_left = {{ anchor_left }}
anchor_top = {{ anchor_top }}
anchor_right = {{ anchor_right }}
anchor_bottom = {{ anchor_bottom }}
offset_left = {{ offset_left }}
offset_top = {{ offset_top }}
offset_right = {{ offset_right }}
offset_bottom = {{ offset_bottom }}
grow_horizontal = {{ grow_horizontal }}
grow_vertical = {{ grow_vertical }}
tooltip_text = "{{ tooltip_text }}"
focus_mode = {{ focus_mode }}
mouse_filter = {{ mouse_filter }}
pressed = {{ pressed }}
disabled = {{ disabled }}
toggle_mode = {{ toggle_mode }}
button_pressed = {{ button_pressed }}
action_mode = {{ action_mode }}
text = "{{ text }}"
{% if script %}
script = ExtResource("1")]
{% endif %}
"""

    # -------------------------------------------------------------------------
    # Control/Label Template
    # -------------------------------------------------------------------------
    _TEMPLATE_REGISTRY[
        "control_label"
    ] = """[gd_scene load_steps=1 format=3 uid="uid://{{ uid }}"]

[node name="{{ name }}" type="Label"]
anchors_preset = {{ anchors_preset }}
anchor_left = {{ anchor_left }}
anchor_top = {{ anchor_top }}
anchor_right = {{ anchor_right }}
anchor_bottom = {{ anchor_bottom }}
offset_left = {{ offset_left }}
offset_top = {{ offset_top }}
offset_right = {{ offset_right }}
offset_bottom = {{ offset_bottom }}
grow_horizontal = {{ grow_horizontal }}
grow_vertical = {{ grow_vertical }}
tooltip_text = "{{ tooltip_text }}"
mouse_filter = {{ mouse_filter }}
text = "{{ text }}"
horizontal_alignment = {{ horizontal_alignment }}
vertical_alignment = {{ vertical_alignment }}
autowrap_mode = {{ autowrap_mode }}
percent_visible = {{ percent_visible }}
lines_skipped = {{ lines_skipped }}
max_lines_visible = {{ max_lines_visible }}
"""

    # -------------------------------------------------------------------------
    # Control/Panel Template
    # -------------------------------------------------------------------------
    _TEMPLATE_REGISTRY[
        "control_panel"
    ] = """[gd_scene load_steps=1 format=3 uid="uid://{{ uid }}"]

[node name="{{ name }}" type="Panel"]
anchors_preset = {{ anchors_preset }}
anchor_left = {{ anchor_left }}
anchor_top = {{ anchor_top }}
anchor_right = {{ anchor_right }}
anchor_bottom = {{ anchor_bottom }}
offset_left = {{ offset_left }}
offset_top = {{ offset_top }}
offset_right = {{ offset_right }}
offset_bottom = {{ offset_bottom }}
grow_horizontal = {{ grow_horizontal }}
grow_vertical = {{ grow_vertical }}
tooltip_text = "{{ tooltip_text }}"
mouse_filter = {{ mouse_filter }}
focus_mode = {{ focus_mode }}
"""

    # -------------------------------------------------------------------------
    # Control/PanelContainer with child
    # -------------------------------------------------------------------------
    _TEMPLATE_REGISTRY[
        "control_panel_container"
    ] = """[gd_scene load_steps=1 format=3 uid="uid://{{ uid }}"]

[node name="{{ name }}" type="PanelContainer"]
anchors_preset = {{ anchors_preset }}
anchor_left = {{ anchor_left }}
anchor_top = {{ anchor_top }}
anchor_right = {{ anchor_right }}
anchor_bottom = {{ anchor_bottom }}
offset_left = {{ offset_left }}
offset_top = {{ offset_top }}
offset_right = {{ offset_right }}
offset_bottom = {{ offset_bottom }}
grow_horizontal = {{ grow_horizontal }}
grow_vertical = {{ grow_vertical }}
tooltip_text = "{{ tooltip_text }}"
mouse_filter = {{ mouse_filter }}

[node name="{{ child_name }}" type="{{ child_type }}" parent="."]
offset_left = 4.0
offset_top = 4.0
offset_right = 4.0
offset_bottom = 4.0
"""

    # -------------------------------------------------------------------------
    # Node3D Basic Template
    # -------------------------------------------------------------------------
    _TEMPLATE_REGISTRY[
        "node3d_basic"
    ] = """[gd_scene load_steps=2 format=3 uid="uid://{{ uid }}"]

{% if script %}
[ext_resource type="Script" path="{{ script_path }}" id="{{ script_id }}"]
{% endif %}

[node name="{{ name }}" type="Node3D"]
position = Vector3({{ x }}, {{ y }}, {{ z }})
rotation = Vector3({{ rot_x }}, {{ rot_y }}, {{ rot_z }})
scale = Vector3({{ scale_x }}, {{ scale_y }}, {{ scale_z }})
z_index = {{ z_index }}
z_as_relative = {{ z_as_relative }}
{% if script %}script = ExtResource("{{ script_id }}"){% endif %}
"""

    # -------------------------------------------------------------------------
    # Node3D with Mesh Template
    # -------------------------------------------------------------------------
    _TEMPLATE_REGISTRY[
        "node3d_mesh"
    ] = """[gd_scene load_steps=3 format=3 uid="uid://{{ uid }}"]

[ext_resource type="Mesh" path="{{ mesh_path }}" id="1"]

{% if script %}
[ext_resource type="Script" path="{{ script_path }}" id="{{ script_id }}"]
{% endif %}

[node name="{{ name }}" type="Node3D"]
position = Vector3({{ x }}, {{ y }}, {{ z }})
rotation = Vector3({{ rot_x }}, {{ rot_y }}, {{ rot_z }})
scale = Vector3({{ scale_x }}, {{ scale_y }}, {{ scale_z }})
z_index = {{ z_index }}
z_as_relative = {{ z_as_relative }}
{% if script %}script = ExtResource("{{ script_id }}"){% endif %}

[node name="MeshInstance3D" type="MeshInstance3D" parent="."]
mesh = ExtResource("1")
"""

    # -------------------------------------------------------------------------
    # CharacterBody3D Template
    # -------------------------------------------------------------------------
    _TEMPLATE_REGISTRY[
        "character_body_3d"
    ] = """[gd_scene load_steps=4 format=3 uid="uid://{{ uid }}"]

[ext_resource type="Mesh" path="{{ mesh_path }}" id="1"]
[ext_resource type="CapsuleShape3D" path="{{ collision_shape_path }}" id="2"]

{% if script %}
[ext_resource type="Script" path="{{ script_path }}" id="{{ script_id }}"]
{% endif %}

[node name="{{ name }}" type="CharacterBody3D"]
position = Vector3({{ x }}, {{ y }}, {{ z }})
rotation = Vector3({{ rot_x }}, {{ rot_y }}, {{ rot_z }})
z_index = {{ z_index }}
z_as_relative = {{ z_as_relative }}
floor_stop_on_slide = {{ floor_stop_on_slide }}
floor_max_angle = {{ floor_max_angle }}
floor_friction = {{ floor_friction }}
wall_slide_speed = {{ wall_slide_speed }}
max_slides = {{ max_slides }}
gravity = {{ gravity }}
{% if script %}script = ExtResource("{{ script_id }}"){% endif %}

[node name="MeshInstance3D" type="MeshInstance3D" parent="."]
mesh = ExtResource("1")

[node name="CollisionShape3D" type="CollisionShape3D" parent="."]
shape = ExtResource("2")
"""

    # -------------------------------------------------------------------------
    # RigidBody3D Template
    # -------------------------------------------------------------------------
    _TEMPLATE_REGISTRY[
        "rigid_body_3d"
    ] = """[gd_scene load_steps=4 format=3 uid="uid://{{ uid }}"]

[ext_resource type="Mesh" path="{{ mesh_path }}" id="1"]
[ext_resource type="CapsuleShape3D" path="{{ collision_shape_path }}" id="2"]

{% if script %}
[ext_resource type="Script" path="{{ script_path }}" id="{{ script_id }}"]
{% endif %}

[node name="{{ name }}" type="RigidBody3D"]
position = Vector3({{ x }}, {{ y }}, {{ z }})
rotation = Vector3({{ rot_x }}, {{ rot_y }}, {{ rot_z }})
z_index = {{ z_index }}
z_as_relative = {{ z_as_relative }}
freeze = {{ freeze }}
freeze_mode = {{ freeze_mode }}
linear_damp = {{ linear_damp }}
angular_damp = {{ angular_damp }}
gravity_scale = {{ gravity_scale }}
can_sleep = {{ can_sleep }}
lock_rotation = {{ lock_rotation }}
priority = {{ priority }}
{% if script %}script = ExtResource("{{ script_id }}"){% endif %}

[node name="MeshInstance3D" type="MeshInstance3D" parent="."]
mesh = ExtResource("1")

[node name="CollisionShape3D" type="CollisionShape3D" parent="."]
shape = ExtResource("2")
"""

    # -------------------------------------------------------------------------
    # Camera2D Template
    # -------------------------------------------------------------------------
    _TEMPLATE_REGISTRY[
        "camera2d"
    ] = """[gd_scene load_steps=1 format=3 uid="uid://{{ uid }}"]

[node name="{{ name }}" type="Camera2D"]
position = Vector2({{ x }}, {{ y }})
z_index = {{ z_index }}
z_as_relative = {{ z_as_relative }}
offset = Vector2({{ offset_x }}, {{ offset_y }})
anchor_mode = {{ anchor_mode }}
rotation_mode = {{ rotation_mode }}
position_mode = {{ position_mode }}
current = {{ current }}
zoom = Vector2({{ zoom_x }}, {{ zoom_y }})
limit_left = {{ limit_left }}
limit_top = {{ limit_top }}
limit_right = {{ limit_right }}
limit_bottom = {{ limit_bottom }}
limit_smoothed = {{ limit_smoothed }}
position_smoothing_enabled = {{ position_smoothing_enabled }}
position_smoothing_speed = {{ position_smoothing_speed }}
drag_margin_left = {{ drag_margin_left }}
drag_margin_top = {{ drag_margin_top }}
drag_margin_right = {{ drag_margin_right }}
drag_margin_bottom = {{ drag_margin_bottom }}
drag_horiz_enabled = {{ drag_horiz_enabled }}
drag_vert_enabled = {{ drag_vert_enabled }}
drag_left = {{ drag_left }}
drag_top = {{ drag_top }}
drag_right = {{ drag_right }}
drag_bottom = {{ drag_bottom }}
"""

    # -------------------------------------------------------------------------
    # Camera3D Template
    # -------------------------------------------------------------------------
    _TEMPLATE_REGISTRY[
        "camera3d"
    ] = """[gd_scene load_steps=1 format=3 uid="uid://{{ uid }}"]

[node name="{{ name }}" type="Camera3D"]
position = Vector3({{ x }}, {{ y }}, {{ z }})
rotation = Vector3({{ rot_x }}, {{ rot_y }}, {{ rot_z }})
z_index = {{ z_index }}
z_as_relative = {{ z_as_relative }}
current = {{ current }}
keep_aspect = {{ keep_aspect }}
fov = {{ fov }}
size = {{ size }}
near = {{ near }}
far = {{ far }}
fdof_filter_size = {{ fdof_filter_size }}
dof_blur = {{ dof_blur }}
dof_distance = {{ dof_distance }}
dof_split_factor = {{ dof_split_factor }}
dof_blur_pass = {{ dof_blur_pass }}
"""

    # -------------------------------------------------------------------------
    # AudioStreamPlayer2D Template
    # -------------------------------------------------------------------------
    _TEMPLATE_REGISTRY[
        "audio_stream_player_2d"
    ] = """[gd_scene load_steps=1 format=3 uid="uid://{{ uid }}"]

[node name="{{ name }}" type="AudioStreamPlayer2D"]
position = Vector2({{ x }}, {{ y }})
z_index = {{ z_index }}
z_as_relative = {{ z_as_relative }}
volume_db = {{ volume_db }}
pitch_scale = {{ pitch_scale }}
autoplay = {{ autoplay }}
max_distance = {{ max_distance }}
panning_strategy = {{ panning_strategy }}
max_polyphony = {{ max_polyphony }}
bus = "{{ bus }}"
"""

    # -------------------------------------------------------------------------
    # AudioStreamPlayer3D Template
    # -------------------------------------------------------------------------
    _TEMPLATE_REGISTRY[
        "audio_stream_player_3d"
    ] = """[gd_scene load_steps=1 format=3 uid="uid://{{ uid }}"]

[node name="{{ name }}" type="AudioStreamPlayer3D"]
position = Vector3({{ x }}, {{ y }}, {{ z }})
z_index = {{ z_index }}
z_as_relative = {{ z_as_relative }}
volume_db = {{ volume_db }}
pitch_scale = {{ pitch_scale }}
autoplay = {{ autoplay }}
unit_size = {{ unit_size }}
max_distance = {{ max_distance }}
panning_strategy = {{ panning_strategy }}
max_polyphony = {{ max_polyphony }}
bus = "{{ bus }}"
emission_angle_enabled = {{ emission_angle_enabled }}
emission_angle = {{ emission_angle }}
emission_angle_filter_attenuation = {{ emission_angle_filter_attenuation }}
"""

    # -------------------------------------------------------------------------
    # CanvasLayer Template (for UI)
    # -------------------------------------------------------------------------
    _TEMPLATE_REGISTRY[
        "canvas_layer"
    ] = """[gd_scene load_steps=1 format=3 uid="uid://{{ uid }}"]

[node name="{{ name }}" type="CanvasLayer"]
layer = {{ layer }}
follow_viewport_enabled = {{ follow_viewport_enabled }}
"""

    # -------------------------------------------------------------------------
    # Timer Template
    # -------------------------------------------------------------------------
    _TEMPLATE_REGISTRY[
        "timer"
    ] = """[gd_scene load_steps=1 format=3 uid="uid://{{ uid }}"]

[node name="{{ name }}" type="Timer"]
wait_time = {{ wait_time }}
one_shot = {{ one_shot }}
autostart = {{ autostart }}
"""

    # -------------------------------------------------------------------------
    # VisibilityNotifier2D Template
    # -------------------------------------------------------------------------
    _TEMPLATE_REGISTRY[
        "visibility_notifier_2d"
    ] = """[gd_scene load_steps=1 format=3 uid="uid://{{ uid }}"]

[node name="{{ name }}" type="VisibilityNotifier2D"]
position = Vector2({{ x }}, {{ y }})
rect = Rect2({{ rect_x }}, {{ rect_y }}, {{ rect_w }}, {{ rect_h }})
"""


# Ensure templates are registered on module import
_register_templates()


# =============================================================================
# DEFAULT CONTEXTS
# =============================================================================

# Default context values for each template type
DEFAULT_CONTEXTS: dict[str, dict[str, Any]] = {
    "node2d_basic": {
        "name": "Node2D",
        "x": 0,
        "y": 0,
        "z_index": 0,
        "z_as_relative": True,
        "uid": "cdfm8d8d9a0b0c1d2e3f4",
        "script": False,
        "script_path": "",
        "script_id": "",
    },
    "node2d_sprite": {
        "name": "SpriteNode",
        "x": 0,
        "y": 0,
        "z_index": 0,
        "z_as_relative": True,
        "uid": "cdfm8d8d9a0b0c1d2e3f4",
        "script": False,
        "script_path": "",
        "script_id": "",
        "sprite_path": "res://sprites/default.png",
        "hframes": 1,
        "vframes": 1,
        "frame": 0,
    },
    "node2d_collision": {
        "name": "CollidableObject",
        "x": 0,
        "y": 0,
        "z_index": 0,
        "z_as_relative": True,
        "uid": "cdfm8d8d9a0b0c1d2e3f4",
        "script": False,
        "script_path": "",
        "script_id": "",
        "sprite_path": "res://sprites/default.png",
        "collision_shape_path": "res://shapes/circle.tres",
        "hframes": 1,
        "vframes": 1,
        "frame": 0,
    },
    "character_body_2d": {
        "name": "Player",
        "x": 0,
        "y": 0,
        "z_index": 0,
        "z_as_relative": True,
        "uid": "cdfm8d8d9a0b0c1d2e3f4",
        "script": True,
        "script_path": "res://scripts/player.gd",
        "script_id": "1",
        "sprite_path": "res://sprites/player.png",
        "collision_shape_path": "res://shapes/player_collision.tres",
        "hframes": 4,
        "vframes": 4,
        "frame": 0,
        "floor_stop_on_slide": True,
        "floor_max_angle": 25.0,
        "floor_friction": 0.05,
        "wall_slide_speed": 128.0,
        "max_slides": 1,
        "gravity": 980.0,
        "jump_force": 350.0,
    },
    "character_body_2d_state": {
        "name": "PlayerWithState",
        "x": 0,
        "y": 0,
        "z_index": 0,
        "z_as_relative": True,
        "uid": "cdfm8d8d9a0b0c1d2e3f4",
        "script": True,
        "script_path": "res://scripts/player.gd",
        "script_id": "1",
        "state_machine_path": "res://scripts/state_machine.gd",
        "sprite_path": "res://sprites/player.png",
        "collision_shape_path": "res://shapes/player_collision.tres",
        "hframes": 4,
        "vframes": 4,
        "frame": 0,
        "floor_stop_on_slide": True,
        "floor_max_angle": 25.0,
        "floor_friction": 0.05,
        "wall_slide_speed": 128.0,
        "max_slides": 1,
        "gravity": 980.0,
        "jump_force": 350.0,
    },
    "area2d_trigger": {
        "name": "TriggerZone",
        "x": 0,
        "y": 0,
        "z_index": 0,
        "z_as_relative": True,
        "uid": "cdfm8d8d9a0b0c1d2e3f4",
        "script": False,
        "script_path": "",
        "script_id": "",
        "collision_shape_path": "res://shapes/circle.tres",
        "monitoring": True,
        "monitorable": True,
        "priority": 0,
        "collision_layer": 1,
        "collision_mask": 1,
    },
    "area2d_detection": {
        "name": "DetectionZone",
        "x": 0,
        "y": 0,
        "z_index": 0,
        "z_as_relative": True,
        "uid": "cdfm8d8d9a0b0c1d2e3f4",
        "script": False,
        "script_path": "",
        "script_id": "",
        "collision_shape_path": "res://shapes/circle.tres",
        "monitoring": True,
        "monitorable": True,
        "priority": 0,
        "collision_layer": 1,
        "collision_mask": 1,
        "modulate_r": 1.0,
        "modulate_g": 1.0,
        "modulate_b": 1.0,
        "modulate_a": 0.3,
        "show_debug": False,
    },
    "rigid_body_2d": {
        "name": "PhysicsObject",
        "x": 0,
        "y": 0,
        "z_index": 0,
        "z_as_relative": True,
        "uid": "cdfm8d8d9a0b0c1d2e3f4",
        "script": False,
        "script_path": "",
        "script_id": "",
        "sprite_path": "res://sprites/object.png",
        "collision_shape_path": "res://shapes/circle.tres",
        "hframes": 1,
        "vframes": 1,
        "frame": 0,
        "freeze": False,
        "freeze_mode": 0,
        "linear_damp": 1.0,
        "angular_damp": 1.0,
        "gravity_scale": 1.0,
        "can_sleep": True,
        "lock_rotation": False,
        "priority": 0,
        "collision_layer": 1,
        "collision_mask": 1,
    },
    "static_body_2d": {
        "name": "StaticWall",
        "x": 0,
        "y": 0,
        "z_index": 0,
        "z_as_relative": True,
        "uid": "cdfm8d8d9a0b0c1d2e3f4",
        "script": False,
        "script_path": "",
        "script_id": "",
        "sprite_path": "res://sprites/wall.png",
        "collision_shape_path": "res://shapes/box.tres",
        "hframes": 1,
        "vframes": 1,
        "frame": 0,
        "collision_layer": 1,
        "collision_mask": 1,
        "constant_vel_x": 0.0,
        "constant_vel_y": 0.0,
        "constant_angular_vel": 0.0,
    },
    "control_button": {
        "name": "Button",
        "anchors_preset": 2,
        "anchor_left": 0.5,
        "anchor_top": 0.5,
        "anchor_right": 0.5,
        "anchor_bottom": 0.5,
        "offset_left": -50.0,
        "offset_top": -25.0,
        "offset_right": 50.0,
        "offset_bottom": 25.0,
        "grow_horizontal": 2,
        "grow_vertical": 2,
        "tooltip_text": "",
        "focus_mode": 0,
        "mouse_filter": 2,
        "pressed": False,
        "disabled": False,
        "toggle_mode": False,
        "button_pressed": False,
        "action_mode": 0,
        "text": "Click Me",
        "script": False,
        "script_path": "",
    },
    "control_label": {
        "name": "LabelText",
        "anchors_preset": 0,
        "anchor_left": 0.0,
        "anchor_top": 0.0,
        "anchor_right": 1.0,
        "anchor_bottom": 0.0,
        "offset_left": 10.0,
        "offset_top": 10.0,
        "offset_right": -10.0,
        "offset_bottom": 30.0,
        "grow_horizontal": 1,
        "grow_vertical": 0,
        "tooltip_text": "",
        "mouse_filter": 2,
        "text": "Label",
        "horizontal_alignment": 0,
        "vertical_alignment": 0,
        "autowrap_mode": 0,
        "percent_visible": 1.0,
        "lines_skipped": 0,
        "max_lines_visible": -1,
    },
    "control_panel": {
        "name": "Panel",
        "anchors_preset": 0,
        "anchor_left": 0.0,
        "anchor_top": 0.0,
        "anchor_right": 1.0,
        "anchor_bottom": 1.0,
        "offset_left": 0.0,
        "offset_top": 0.0,
        "offset_right": 0.0,
        "offset_bottom": 0.0,
        "grow_horizontal": 1,
        "grow_vertical": 1,
        "tooltip_text": "",
        "mouse_filter": 2,
        "focus_mode": 0,
    },
    "control_panel_container": {
        "name": "PanelContainer",
        "anchors_preset": 0,
        "anchor_left": 0.0,
        "anchor_top": 0.0,
        "anchor_right": 1.0,
        "anchor_bottom": 1.0,
        "offset_left": 0.0,
        "offset_top": 0.0,
        "offset_right": 0.0,
        "offset_bottom": 0.0,
        "grow_horizontal": 1,
        "grow_vertical": 1,
        "tooltip_text": "",
        "mouse_filter": 2,
        "child_name": "MarginContainer",
        "child_type": "MarginContainer",
    },
    "node3d_basic": {
        "name": "Node3D",
        "x": 0.0,
        "y": 0.0,
        "z": 0.0,
        "rot_x": 0.0,
        "rot_y": 0.0,
        "rot_z": 0.0,
        "scale_x": 1.0,
        "scale_y": 1.0,
        "scale_z": 1.0,
        "z_index": 0,
        "z_as_relative": True,
        "uid": "cdfm8d8d9a0b0c1d2e3f4",
        "script": False,
        "script_path": "",
        "script_id": "",
    },
    "node3d_mesh": {
        "name": "MeshObject",
        "x": 0.0,
        "y": 0.0,
        "z": 0.0,
        "rot_x": 0.0,
        "rot_y": 0.0,
        "rot_z": 0.0,
        "scale_x": 1.0,
        "scale_y": 1.0,
        "scale_z": 1.0,
        "z_index": 0,
        "z_as_relative": True,
        "uid": "cdfm8d8d9a0b0c1d2e3f4",
        "script": False,
        "script_path": "",
        "script_id": "",
        "mesh_path": "res://meshes/cube.obj",
    },
    "character_body_3d": {
        "name": "Player3D",
        "x": 0.0,
        "y": 0.0,
        "z": 0.0,
        "rot_x": 0.0,
        "rot_y": 0.0,
        "rot_z": 0.0,
        "z_index": 0,
        "z_as_relative": True,
        "uid": "cdfm8d8d9a0b0c1d2e3f4",
        "script": False,
        "script_path": "",
        "script_id": "",
        "mesh_path": "res://meshes/player.obj",
        "collision_shape_path": "res://shapes/capsule.tres",
        "floor_stop_on_slide": True,
        "floor_max_angle": 25.0,
        "floor_friction": 0.05,
        "wall_slide_speed": 128.0,
        "max_slides": 1,
        "gravity": 9.8,
    },
    "rigid_body_3d": {
        "name": "PhysicsObject3D",
        "x": 0.0,
        "y": 0.0,
        "z": 0.0,
        "rot_x": 0.0,
        "rot_y": 0.0,
        "rot_z": 0.0,
        "z_index": 0,
        "z_as_relative": True,
        "uid": "cdfm8d8d9a0b0c1d2e3f4",
        "script": False,
        "script_path": "",
        "script_id": "",
        "mesh_path": "res://meshes/cube.obj",
        "collision_shape_path": "res://shapes/capsule.tres",
        "freeze": False,
        "freeze_mode": 0,
        "linear_damp": 0.1,
        "angular_damp": 0.1,
        "gravity_scale": 1.0,
        "can_sleep": True,
        "lock_rotation": False,
        "priority": 0,
    },
    "camera2d": {
        "name": "Camera2D",
        "x": 0,
        "y": 0,
        "z_index": 0,
        "z_as_relative": True,
        "uid": "cdfm8d8d9a0b0c1d2e3f4",
        "offset_x": 0.0,
        "offset_y": 0.0,
        "anchor_mode": 0,
        "rotation_mode": 0,
        "position_mode": 0,
        "current": True,
        "zoom_x": 1.0,
        "zoom_y": 1.0,
        "limit_left": -10000000,
        "limit_top": -10000000,
        "limit_right": 10000000,
        "limit_bottom": 10000000,
        "limit_smoothed": False,
        "position_smoothing_enabled": False,
        "position_smoothing_speed": 5.0,
        "drag_margin_left": 0.2,
        "drag_margin_top": 0.2,
        "drag_margin_right": 0.2,
        "drag_margin_bottom": 0.2,
        "drag_horiz_enabled": False,
        "drag_vert_enabled": False,
        "drag_left": -1.0,
        "drag_top": -1.0,
        "drag_right": 1.0,
        "drag_bottom": 1.0,
    },
    "camera3d": {
        "name": "Camera3D",
        "x": 0.0,
        "y": 0.0,
        "z": 1.0,
        "rot_x": 0.0,
        "rot_y": 0.0,
        "rot_z": 0.0,
        "z_index": 0,
        "z_as_relative": True,
        "uid": "cdfm8d8d9a0b0c1d2e3f4",
        "current": True,
        "keep_aspect": 0,
        "fov": 75.0,
        "size": 1.0,
        "near": 0.05,
        "far": 4000.0,
        "fdof_filter_size": 0,
        "dof_blur": 0,
        "dof_distance": 10.0,
        "dof_split_factor": 0.5,
        "dof_blur_pass": False,
    },
    "audio_stream_player_2d": {
        "name": "AudioStreamPlayer2D",
        "x": 0,
        "y": 0,
        "z_index": 0,
        "z_as_relative": True,
        "uid": "cdfm8d8d9a0b0c1d2e3f4",
        "volume_db": 0.0,
        "pitch_scale": 1.0,
        "autoplay": False,
        "max_distance": 2000.0,
        "panning_strategy": 0,
        "max_polyphony": 1,
        "bus": "Master",
    },
    "audio_stream_player_3d": {
        "name": "AudioStreamPlayer3D",
        "x": 0.0,
        "y": 0.0,
        "z": 0.0,
        "z_index": 0,
        "z_as_relative": True,
        "uid": "cdfm8d8d9a0b0c1d2e3f4",
        "volume_db": 0.0,
        "pitch_scale": 1.0,
        "autoplay": False,
        "unit_size": 10.0,
        "max_distance": 2000.0,
        "panning_strategy": 0,
        "max_polyphony": 1,
        "bus": "Master",
        "emission_angle_enabled": False,
        "emission_angle": 45.0,
        "emission_angle_filter_attenuation": 3.0,
    },
    "canvas_layer": {
        "name": "CanvasLayer",
        "layer": 1,
        "follow_viewport_enabled": False,
        "uid": "cdfm8d8d9a0b0c1d2e3f4",
    },
    "timer": {
        "name": "Timer",
        "wait_time": 1.0,
        "one_shot": False,
        "autostart": False,
        "uid": "cdfm8d8d9a0b0c1d2e3f4",
    },
    "visibility_notifier_2d": {
        "name": "VisibilityNotifier2D",
        "x": 0,
        "y": 0,
        "rect_x": -100.0,
        "rect_y": -100.0,
        "rect_w": 200.0,
        "rect_h": 200.0,
        "uid": "cdfm8d8d9a0b0c1d2e3f4",
    },
}


# =============================================================================
# PUBLIC FUNCTIONS
# =============================================================================


def get_template(template_name: str) -> str:
    """
    Get a template by name.

    Args:
        template_name: Name of the template to retrieve.

    Returns:
        The template string.

    Raises:
        TemplateNotFound: If template name doesn't exist.
    """
    if template_name not in _TEMPLATE_REGISTRY:
        raise TemplateNotFound(template_name)
    return _TEMPLATE_REGISTRY[template_name]


def list_templates() -> list[str]:
    """
    List all available template names.

    Returns:
        List of template names.
    """
    return sorted(_TEMPLATE_REGISTRY.keys())


def render_template(template_name: str, context: dict[str, Any] | None = None) -> str:
    """
    Render a template with the given context.

    Args:
        template_name: Name of the template to render.
        context: Dictionary of variable values for the template.

    Returns:
        The rendered template string.

    Raises:
        TemplateNotFound: If template name doesn't exist.
    """
    if template_name not in _TEMPLATE_REGISTRY:
        raise TemplateNotFound(template_name)

    # Merge default context with provided context
    ctx = {}
    if template_name in DEFAULT_CONTEXTS:
        ctx = DEFAULT_CONTEXTS[template_name].copy()
    if context:
        ctx.update(context)

    # Load and render template
    env = Environment(loader=DictLoader())
    template = env.get_template(template_name)

    return template.render(**ctx)


def get_node_snippet(node_type: str) -> str:
    """
    Get a quick node snippet for common node types.

    This returns a minimal .tscn format snippet for creating
    a specific node type quickly.

    Args:
        node_type: Type of node (e.g., "Sprite2D", "CollisionShape2D", "Label").

    Returns:
        A minimal node snippet in .tscn format.
    """
    snippets: dict[str, str] = {
        "Node2D": """[gd_scene format=3]

[node name="Node2D" type="Node2D"]""",
        "Sprite2D": """[gd_scene format=3]

[node name="Sprite2D" type="Sprite2D"]
texture = null""",
        "CollisionShape2D": """[gd_scene format=3]

[node name="CollisionShape2D" type="CollisionShape2D"]
shape = null""",
        "CollisionPolygon2D": """[gd_scene format=3]

[node name="CollisionPolygon2D" type="CollisionPolygon2D"]
build_mode = 0
polygon = PackedVector2Array()""",
        "Polygon2D": """[gd_scene format=3]

[node name="Polygon2D" type="Polygon2D"]
color = Color(1, 1, 1, 1)
polygon = PackedVector2Array()""",
        "Label": """[gd_scene format=3]

[node name="Label" type="Label"]
offset_left = 10.0
offset_top = 10.0
offset_right = 100.0
offset_bottom = 30.0
text = "Label"
""",
        "Button": """[gd_scene format=3]

[node name="Button" type="Button"]
offset_left = 10.0
offset_top = 10.0
offset_right = 100.0
offset_bottom = 40.0
text = "Button"
""",
        "TextureRect": """[gd_scene format=3]

[node name="TextureRect" type="TextureRect"]
offset_left = 0.0
offset_top = 0.0
offset_right = 100.0
offset_bottom = 100.0""",
        "Line2D": """[gd_scene format=3]

[node name="Line2D" type="Line2D"]
points = PackedVector2Array()
width = 2.0
default_color = Color(1, 1, 1, 1)""",
        "Marker2D": """[gd_scene format=3]

[node name="Marker2D" type="Marker2D"]""",
        "TileMap": """[gd_scene format=3]

[node name="TileMap" type="TileMap"]
format = 1""",
        "TileSet": """[gd_scene load_steps=1 format=3]

[ext_resource type="TileSet" id="1"]

[node name="TileMap" type="TileMap"]
tile_set = ExtResource("1")
format = 1""",
        "AnimationPlayer": """[gd_scene format=3]

[node name="AnimationPlayer" type="AnimationPlayer"]""",
        "Timer": """[gd_scene format=3]

[node name="Timer" type="Timer"]
wait_time = 1.0
one_shot = false
autostart = false""",
        "Tween": """[gd_scene format=3]

[node name="Tween" type="Tween"]""",
    }

    if node_type not in snippets:
        # Generic fallback - try to use the node type directly
        return f"""[gd_scene format=3]

[node name="{node_type}" type="{node_type}"]"""

    return snippets[node_type]


def get_template_names_by_category() -> dict[str, list[str]]:
    """
    Get templates organized by category.

    Returns:
        Dictionary mapping categories to template names.
    """
    return {
        "Node2D": [
            "node2d_basic",
            "node2d_sprite",
            "node2d_collision",
        ],
        "CharacterBody2D": [
            "character_body_2d",
            "character_body_2d_state",
        ],
        "Physics2D": [
            "rigid_body_2d",
            "static_body_2d",
        ],
        "Area2D": [
            "area2d_trigger",
            "area2d_detection",
        ],
        "Control/UI": [
            "control_button",
            "control_label",
            "control_panel",
            "control_panel_container",
        ],
        "Node3D": [
            "node3d_basic",
            "node3d_mesh",
            "character_body_3d",
            "rigid_body_3d",
        ],
        "Camera": [
            "camera2d",
            "camera3d",
        ],
        "Audio": [
            "audio_stream_player_2d",
            "audio_stream_player_3d",
        ],
        "Other": [
            "canvas_layer",
            "timer",
            "visibility_notifier_2d",
        ],
    }


def validate_context(template_name: str, context: dict[str, Any]) -> list[str]:
    """
    Validate that a context contains all required keys for a template.

    Args:
        template_name: Name of the template.
        context: Context dictionary to validate.

    Returns:
        List of missing keys (empty if valid).
    """
    if template_name not in DEFAULT_CONTEXTS:
        return ["template not found"]

    required_keys = set(DEFAULT_CONTEXTS[template_name].keys())
    provided_keys = set(context.keys())

    missing = required_keys - provided_keys
    return sorted(missing)


# =============================================================================
# CONVENIENCE CLASS
# =============================================================================


class NodeTemplateEngine:
    """
    Convenience class for template operations.

    Example:
        engine = NodeTemplateEngine()

        # Get all templates
        print(engine.list())

        # Render a template
        result = engine.render("character_body_2d", {"name": "MyPlayer", "x": 100})

        # Get a quick snippet
        snippet = engine.snippet("Sprite2D")
    """

    def __init__(self):
        """Initialize the template engine."""
        pass

    def get(self, name: str) -> str:
        """Get a template by name."""
        return get_template(name)

    def all(self) -> list[str]:
        """List all available templates."""
        return list_templates()

    def render(self, name: str, context: dict[str, Any] | None = None) -> str:
        """Render a template with context."""
        return render_template(name, context)

    def snippet(self, node_type: str) -> str:
        """Get a quick node snippet."""
        return get_node_snippet(node_type)

    def categories(self) -> dict[str, list[str]]:
        """Get templates by category."""
        return get_template_names_by_category()


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    # Demo/test the templates
    engine = NodeTemplateEngine()

    print("=== Available Templates ===")
    for name in engine.all():
        print(f"  - {name}")

    print("\n=== Templates by Category ===")
    for category, templates in engine.categories().items():
        print(f"\n{category}:")
        for t in templates:
            print(f"  - {t}")

    print("\n=== Render Example (character_body_2d) ===")
    result = engine.render(
        "character_body_2d",
        {
            "name": "Player",
            "x": 100,
            "y": 200,
            "sprite_path": "res://sprites/player.png",
        },
    )
    print(result)

    print("\n=== Node Snippets ===")
    for node_type in ["Sprite2D", "CollisionShape2D", "Label", "Button", "Timer"]:
        print(f"\n--- {node_type} ---")
        print(engine.snippet(node_type))
