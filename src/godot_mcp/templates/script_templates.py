"""
Templates module - stores GDScript templates as encoded strings
"""

from jinja2 import BaseLoader, Environment, TemplateNotFound
from typing import Any

# Templates are stored with a special delimiter that won't conflict with Python
# Format: each template is a list of strings that get joined


def _make_template(lines: list[str]) -> str:
    """Join template lines."""
    return "\n".join(lines)


# Base Node Template
TEMPLATE_NODE = _make_template(
    [
        "extends Node",
        'class_name {{ class_name|default("MyNode") }}',
        "",
        "## Docstring",
        "{% if docstring %}{{ docstring }}{% else %}A custom Node script.{% endif %}",
        "",
        "## Signals",
        "signal initialized",
        "signal cleanup_requested",
        "",
        "",
        "## Export Variables",
        '@export_group("Settings")',
        "@export var enabled: bool = true",
        "@export var debug_mode: bool = false",
        "",
        "",
        "## Onready Variables",
        "var _internal_data: Dictionary = {}",
        "",
        "",
        "## Built-in Virtual Functions",
        "func _ready() -> void:",
        '    """Called when the node enters the scene tree."""',
        "    if debug_mode:",
        '        print("[DEBUG] %s: _ready() called" % name)',
        "    initialized.emit()",
        "",
        "",
        "func _process(delta: float) -> void:",
        '    """Called every frame."""',
        "    pass",
        "",
        "",
        "func _exit_tree() -> void:",
        '    """Called when the node is removed from the scene tree."""',
        "    cleanup_requested.emit()",
        "    _internal_data.clear()",
    ]
)


# Node2D Template
TEMPLATE_NODE_2D = _make_template(
    [
        "extends Node2D",
        'class_name {{ class_name|default("MyNode2D") }}',
        "",
        "## Docstring",
        "{% if docstring %}{{ docstring }}{% else %}A 2D scene node.{% endif %}",
        "",
        "## Signals",
        "signal position_changed(new_position: Vector2)",
        "signal visibility_toggled(is_visible: bool)",
        "",
        "",
        "## Export Variables",
        '@export_group("Transform")',
        "@export var position_offset: Vector2 = Vector2.ZERO",
        "@export var rotation_degrees: float = 0.0",
        "@export var scale_factor: Vector2 = Vector2.ONE",
        "",
        '@export_group("Appearance")',
        "@export var visible: bool = true",
        "@export var modulate: Color = Color.WHITE",
        "",
        "",
        "## Onready Variables",
        "@onready var _original_position: Vector2 = position",
        "",
        "",
        "## Built-in Virtual Functions",
        "func _ready() -> void:",
        '    """Called when the node enters the scene tree."""',
        "    _original_position = position",
        "    apply_transform()",
        "",
        "",
        "func _process(delta: float) -> void:",
        '    """Called every frame."""',
        "    pass",
        "",
        "",
        "func _draw() -> void:",
        '    """Called to draw custom graphics."""',
        "    pass",
        "",
        "",
        "## Public Methods",
        "func apply_transform() -> void:",
        '    """Apply position, rotation, and scale transforms."""',
        "    position = _original_position + position_offset",
        "    rotation_degrees = rotation_degrees",
        "    scale = scale_factor",
        "",
        "",
        "func reset_transform() -> void:",
        '    """Reset to original position."""',
        "    position = _original_position",
        "    rotation_degrees = 0.0",
        "    scale = Vector2.ONE",
    ]
)


# CharacterBody2D Template
TEMPLATE_CHARACTER_BODY_2D = _make_template(
    [
        "extends CharacterBody2D",
        'class_name {{ class_name|default("MyCharacter") }}',
        "",
        "## Docstring",
        "{% if docstring %}{{ docstring }}{% else %}A character body with physics.{% endif %}",
        "",
        "## Signals",
        "signal velocity_changed(velocity: Vector2)",
        "signal ground_state_changed(is_on_ground: bool)",
        "signal direction_changed(facing_right: bool)",
        "",
        "",
        "## Export Variables",
        '@export_group("Movement")',
        "@export var speed: float = {{ speed|default(300.0) }}",
        "@export var acceleration: float = 1000.0",
        "@export var friction: float = 800.0",
        "",
        '@export_group("Jump")',
        "@export var jump_velocity: float = {{ jump_velocity|default(-400.0) }}",
        "@export var double_jump_enabled: bool = true",
        "var _can_double_jump: bool = true",
        "",
        '@export_group("Physics")',
        "@export var gravity: float = 980.0",
        "@export var max_fall_speed: float = 1000.0",
        "",
        "",
        "## Onready Variables",
        "@onready var _velocity: Vector2 = Vector2.ZERO",
        "@onready var _facing_right: bool = true",
        "@onready var _is_on_ground: bool = false",
        "",
        "",
        "## Built-in Virtual Functions",
        "func _ready() -> void:",
        '    """Called when the node enters the scene tree."""',
        "    pass",
        "",
        "",
        "func _physics_process(delta: float) -> void:",
        '    """Called every physics frame."""',
        "    _apply_gravity(delta)",
        "    _handle_movement(delta)",
        "    move_and_slide()",
        "    _check_ground_state()",
        "",
        "",
        "func _apply_gravity(delta: float) -> void:",
        '    """Apply gravity when in air."""',
        "    if not is_on_floor():",
        "        _velocity.y += gravity * delta",
        "        _velocity.y = min(_velocity.y, max_fall_speed)",
        "",
        "",
        "func _handle_movement(delta: float) -> void:",
        '    """Handle horizontal movement."""',
        "    pass",
        "",
        "",
        "func _check_ground_state() -> void:",
        '    """Check and emit ground state changes."""',
        "    var was_on_ground = _is_on_floor()",
        "    _is_on_floor()",
        "    if was_on_ground != _is_on_floor():",
        "        ground_state_changed.emit(_is_on_floor())",
        "        if _is_on_floor():",
        "            _can_double_jump = double_jump_enabled",
        "",
        "",
        "func get_velocity() -> Vector2:",
        '    """Get current velocity."""',
        "    return _velocity",
        "",
        "",
        "func set_velocity(new_velocity: Vector2) -> void:",
        '    """Set velocity and emit signal."""',
        "    _velocity = new_velocity",
        "    velocity_changed.emit(_velocity)",
        "",
        "",
        "func get_facing_direction() -> bool:",
        '    """Get facing direction (true = right, false = left)."""',
        "    return _facing_right",
        "",
        "",
        "func flip() -> void:",
        '    """Flip facing direction."""',
        "    _facing_right = not _facing_right",
        "    direction_changed.emit(_facing_right)",
    ]
)


# Player Controller Template
TEMPLATE_PLAYER_CONTROLLER = _make_template(
    [
        "extends CharacterBody2D",
        'class_name {{ class_name|default("Player") }}',
        "",
        "## Docstring",
        "{% if docstring %}{{ docstring }}{% else %}Player controller with movement, jump, and attack.{% endif %}",
        "",
        "## Signals",
        "signal health_changed(current_health: float, max_health: float)",
        "signal died",
        "signal attack_executed(attack_name: String)",
        "signal dash_executed",
        "",
        "",
        "## Export Variables",
        '@export_group("Movement")',
        "@export var speed: float = {{ speed|default(300.0) }}",
        "@export var acceleration: float = 1200.0",
        "@export var friction: float = 800.0",
        "@export var air_control: float = 0.5",
        "",
        '@export_group("Jump")',
        "@export var jump_velocity: float = {{ jump_velocity|default(-400.0) }}",
        "@export var variable_jump: bool = true",
        "@export var wall_slide_enabled: bool = true",
        "@export var wall_jump_enabled: bool = true",
        "",
        '@export_group("Dash")',
        "@export var dash_enabled: bool = true",
        "@export var dash_speed: float = 600.0",
        "@export var dash_duration: float = 0.2",
        "@export var dash_cooldown: float = 0.5",
        "",
        '@export_group("Combat")',
        "@export var max_health: float = 100.0",
        "@export var current_health: float = 100.0",
        "@export var invincibility_time: float = 0.5",
        "",
        "",
        "## Onready Variables",
        "@onready var _current_health: float = max_health",
        "@onready var _input_direction: Vector2 = Vector2.ZERO",
        "@onready var _is_attacking: bool = false",
        "@onready var _is_dashing: bool = false",
        "@onready var _dash_timer: float = 0.0",
        "@onready var _dash_cooldown_timer: float = 0.0",
        "@onready var _invincibility_timer: float = 0.0",
        "@onready var _coyote_time: float = 0.0",
        "@onready var _jump_buffer: float = 0.0",
        "",
        "@onready var sprite: Sprite2D = $Sprite2D",
        '@onready var animation_player: AnimationPlayer = $AnimationPlayer if has_node("AnimationPlayer") else null',
        '@onready var hitbox: Area2D = $Hitbox if has_node("Hitbox") else null',
        '@onready var health_bar: ProgressBar = $HealthBar if has_node("HealthBar") else null',
        "",
        "",
        "## Built-in Virtual Functions",
        "func _ready() -> void:",
        '    """Called when the node enters the scene tree."""',
        "    _current_health = max_health",
        "    _coyote_time = 0.0",
        "",
        "",
        "func _physics_process(delta: float) -> void:",
        '    """Called every physics frame."""',
        "    _update_timers(delta)",
        "    _handle_input()",
        "    _handle_movement(delta)",
        "    _handle_jump(delta)",
        "    _handle_dash(delta)",
        "    _apply_gravity(delta)",
        "    move_and_slide()",
        "    _check_ground_state()",
        "",
        "",
        "func _handle_input() -> void:",
        '    """Process player input."""',
        '    _input_direction.x = Input.get_axis("ui_left", "ui_right")',
        '    _input_direction.y = Input.get_axis("ui_up", "ui_down")',
        "    ",
        "    if _input_direction.x != 0:",
        "        _input_direction.x = sign(_input_direction.x)",
        "",
        "",
        "func _handle_movement(delta: float) -> void:",
        '    """Handle horizontal movement."""',
        "    var target_speed: float = _input_direction.x * speed",
        "    var current_acceleration: float = acceleration if is_on_floor() else acceleration * air_control",
        "    ",
        "    if _input_direction.x != 0:",
        "        _velocity.x = move_toward(_velocity.x, target_speed, current_acceleration * delta)",
        "    else:",
        "        var current_friction: float = friction if is_on_floor() else friction * 0.5",
        "        _velocity.x = move_toward(_velocity.x, 0, current_friction * delta)",
        "    ",
        "    # Update sprite direction",
        "    if _input_direction.x > 0:",
        "        sprite.scale.x = abs(sprite.scale.x)",
        "    elif _input_direction.x < 0:",
        "        sprite.scale.x = -abs(sprite.scale.x)",
        "",
        "",
        "func _handle_jump(delta: float) -> void:",
        '    """Handle jump input."""',
        '    if Input.is_action_just_pressed("ui_accept"):',
        "        _jump_buffer = 0.1",
        "    ",
        "    _jump_buffer -= delta",
        "    ",
        "    if _jump_buffer > 0 and (is_on_floor() or _coyote_time > 0):",
        "        _velocity.y = jump_velocity",
        "        _jump_buffer = 0.0",
        "        _coyote_time = 0.0",
        "    elif _jump_buffer > 0 and not is_on_floor() and _can_double_jump:",
        "        _velocity.y = jump_velocity * 0.8",
        "        _jump_buffer = 0.0",
        "        _can_double_jump = false",
        "",
        "",
        "func _handle_dash(delta: float) -> void:",
        '    """Handle dash ability."""',
        '    if dash_enabled and _dash_cooldown_timer <= 0 and Input.is_action_just_pressed("ui_select"):',
        "        _is_dashing = true",
        "        _dash_timer = dash_duration",
        "        _dash_cooldown_timer = dash_cooldown",
        "        dash_executed.emit()",
        "    ",
        "    if _is_dashing:",
        "        _velocity.x = dash_speed * sign(_velocity.x) if _velocity.x != 0 else dash_speed * (1 if sprite.scale.x > 0 else -1)",
        "        _velocity.y = 0",
        "        _dash_timer -= delta",
        "        if _dash_timer <= 0:",
        "            _is_dashing = false",
        "",
        "",
        "func _apply_gravity(delta: float) -> void:",
        '    """Apply gravity."""',
        "    if not is_on_floor() and not _is_dashing:",
        "        _velocity.y += gravity * delta",
        "        _velocity.y = min(_velocity.y, max_fall_speed)",
        "",
        "",
        "func _update_timers(delta: float) -> void:",
        '    """Update all timers."""',
        "    if _dash_cooldown_timer > 0:",
        "        _dash_cooldown_timer -= delta",
        "    if _invincibility_timer > 0:",
        "        _invincibility_timer -= delta",
        "    if not is_on_floor() and _coyote_time > 0:",
        "        _coyote_time -= delta",
        "    elif not is_on_floor() and _coyote_time <= 0:",
        "        _coyote_time = 0.1  # Coyote time",
        "",
        "",
        "func _check_ground_state() -> void:",
        '    """Check ground state."""',
        "    if is_on_floor():",
        "        _can_double_jump = true",
        "        _coyote_time = 0.1",
        "",
        "",
        "## Public Methods",
        "func take_damage(damage: float) -> void:",
        '    """Take damage if not invincible."""',
        "    if _invincibility_timer <= 0:",
        "        _current_health -= damage",
        "        _invincibility_timer = invincibility_time",
        "        health_changed.emit(_current_health, max_health)",
        "        ",
        "        if _current_health <= 0:",
        "            die()",
        "",
        "",
        "func heal(amount: float) -> void:",
        '    """Heal the player."""',
        "    _current_health = min(_current_health + amount, max_health)",
        "    health_changed.emit(_current_health, max_health)",
        "",
        "",
        "func die() -> void:",
        '    """Handle player death."""',
        "    died.emit()",
        "    set_physics_process(false)",
        "",
        "",
        "func get_health() -> float:",
        '    """Get current health."""',
        "    return _current_health",
        "",
        "",
        "func is_invincible() -> bool:",
        '    """Check if player is invincible."""',
        "    return _invincibility_timer > 0",
    ]
)


# Enemy AI Template
TEMPLATE_ENEMY_AI = _make_template(
    [
        "extends CharacterBody2D",
        'class_name {{ class_name|default("Enemy") }}',
        "",
        "## Docstring",
        "{% if docstring %}{{ docstring }}{% else %}Basic enemy AI with patrol, chase, and attack states.{% endif %}",
        "",
        "## Signals",
        "signal player_detected(player: Node)",
        "signal attack_started",
        "signal attack_finished",
        "signal health_changed(current: float, maximum: float)",
        "signal died",
        "",
        "",
        "## Export Variables",
        '@export_group("Stats")',
        "@export var max_health: float = 50.0",
        "@export var damage: float = 10.0",
        "",
        '@export_group("Movement")',
        "@export var speed: float = 100.0",
        "@export var chase_speed: float = 150.0",
        "",
        '@export_group("Detection")',
        "@export var detection_range: float = 200.0",
        "@export var attack_range: float = 50.0",
        "@export var lose_sight_range: float = 300.0",
        "",
        '@export_group("Patrol")',
        "@export var patrol_enabled: bool = true",
        "@export var patrol_points: Array[Vector2] = []",
        "@export var wait_time: float = 1.0",
        "",
        "",
        "## Onready Variables",
        "@onready var _health: float = max_health",
        '@onready var _state: String = "PATROL"',
        "@onready var _player: Node2D = null",
        "@onready var _wait_timer: float = 0.0",
        "@onready var _patrol_index: int = 0",
        "",
        "@onready var sprite: Sprite2D = $Sprite2D",
        '@onready var player_detector: Area2D = $PlayerDetector if has_node("PlayerDetector") else null',
        "",
        "",
        "## Enums",
        "enum State { PATROL, CHASE, ATTACK, IDLE }",
        "",
        "",
        "## Built-in Virtual Functions",
        "func _ready() -> void:",
        '    """Called when the node enters the scene tree."""',
        "    if patrol_points.is_empty():",
        "        # Create default patrol points based on initial position",
        "        patrol_points = [global_position, global_position + Vector2(200, 0)]",
        "",
        "",
        "func _physics_process(delta: float) -> void:",
        '    """Called every physics frame."""',
        "    match _state:",
        "        State.PATROL:",
        "            _update_patrol(delta)",
        "        State.CHASE:",
        "            _update_chase(delta)",
        "        State.ATTACK:",
        "            _update_attack(delta)",
        "        State.IDLE:",
        "            _update_idle(delta)",
        "",
        "",
        "func _update_patrol(delta: float) -> void:",
        '    """Patrol between points."""',
        "    if not patrol_enabled:",
        "        _state = State.IDLE",
        "        return",
        "    ",
        "    var target: Vector2 = patrol_points[_patrol_index]",
        "    var direction: Vector2 = (target - global_position).normalized()",
        "    ",
        "    _velocity.x = direction.x * speed",
        "    move_and_slide()",
        "    ",
        "    if global_position.distance_to(target) < 10.0:",
        "        _velocity.x = 0",
        "        _wait_timer = wait_time",
        "        _patrol_index = (_patrol_index + 1) % patrol_points.size()",
        "        _state = State.IDLE",
        "",
        "",
        "func _update_chase(delta: float) -> void:",
        '    """Chase the player."""',
        "    if _player == null:",
        "        _state = State.PATROL",
        "        return",
        "    ",
        "    var direction: Vector2 = (_player.global_position - global_position).normalized()",
        "    _velocity.x = direction.x * chase_speed",
        "    ",
        "    # Update facing direction",
        "    sprite.scale.x = sign(direction.x)",
        "    ",
        "    move_and_slide()",
        "    ",
        "    if global_position.distance_to(_player.global_position) <= attack_range:",
        "        _state = State.ATTACK",
        "    elif global_position.distance_to(_player.global_position) > lose_sight_range:",
        "        _player = null",
        "        _state = State.PATROL",
        "",
        "",
        "func _update_attack(delta: float) -> void:",
        '    """Attack the player."""',
        "    if _player == null or global_position.distance_to(_player.global_position) > attack_range:",
        "        _state = State.CHASE",
        "        return",
        "    ",
        "    attack_started.emit()",
        "    # Attack logic here",
        "    await get_tree().create_timer(0.5).timeout",
        "    attack_finished.emit()",
        "",
        "",
        "func _update_idle(delta: float) -> void:",
        '    """Idle state."""',
        "    _wait_timer -= delta",
        "    if _wait_timer <= 0:",
        "        _state = State.PATROL",
        "    ",
        "    # Check for player",
        "    if _player != null:",
        "        _state = State.CHASE",
        "",
        "",
        "## Public Methods",
        "func _on_player_detector_body_entered(body: Node2D) -> void:",
        '    """Called when player enters detection area."""',
        "    _player = body",
        "    _state = State.CHASE",
        "    player_detected.emit(body)",
        "",
        "",
        "func _on_player_detector_body_exited(body: Node2D) -> void:",
        '    """Called when player exits detection area."""',
        "    if body == _player:",
        "        _player = null",
        "        _state = State.PATROL",
        "",
        "",
        "func take_damage(amount: float) -> void:",
        '    """Take damage."""',
        "    _health -= amount",
        "    health_changed.emit(_health, max_health)",
        "    ",
        "    if _health <= 0:",
        "        die()",
        "",
        "",
        "func die() -> void:",
        '    """Handle death."""',
        "    died.emit()",
        "    queue_free()",
        "",
        "",
        "func get_health() -> float:",
        '    """Get current health."""',
        "    return _health",
    ]
)


# UI Controller Template
TEMPLATE_UI_CONTROLLER = _make_template(
    [
        "extends Control",
        'class_name {{ class_name|default("UIController") }}',
        "",
        "## Docstring",
        "{% if docstring %}{{ docstring }}{% else %}UI controller for menus and HUD.{% endif %}",
        "",
        "## Signals",
        "signal button_pressed(button_name: String)",
        "signal menu_opened(menu_name: String)",
        "signal menu_closed(menu_name: String)",
        "signal value_changed(value_name: String, value: Variant)",
        "",
        "",
        "## Export Variables",
        '@export_group("Menus")',
        '@export var start_menu_path: String = "res://ui/start_menu.tscn"',
        '@export var hud_path: String = "res://ui/hud.tscn"',
        "",
        "",
        "## Onready Variables",
        "@onready var _current_menu: Control = null",
        "@onready var _menus: Dictionary = {}",
        "@onready var _is_paused: bool = false",
        "",
        "",
        "## Built-in Virtual Functions",
        "func _ready() -> void:",
        '    """Called when the node enters the scene tree."""',
        "    _load_menus()",
        "    _connect_signals()",
        "",
        "",
        "func _load_menus() -> void:",
        '    """Load all menu scenes."""',
        "    var menu_scene: PackedScene = load(hud_path)",
        "    if menu_scene:",
        "        var hud: Control = menu_scene.instantiate()",
        "        add_child(hud)",
        '        _menus["hud"] = hud',
        "",
        "",
        "func _connect_signals() -> void:",
        '    """Connect UI signals."""',
        "    pass",
        "",
        "",
        "func _unhandled_input(event: InputEvent) -> void:",
        '    """Handle input for menu navigation."""',
        '    if event.is_action_pressed("ui_cancel"):',
        "        if _is_paused:",
        "            resume_game()",
        "        else:",
        "            pause_game()",
        "",
        "",
        "## Public Methods",
        "func open_menu(menu_name: String) -> void:",
        '    """Open a menu by name."""',
        "    if _menus.has(menu_name):",
        "        if _current_menu:",
        "            _current_menu.hide()",
        "        _current_menu = _menus[menu_name]",
        "        _current_menu.show()",
        "        menu_opened.emit(menu_name)",
        "",
        "",
        "func close_menu(menu_name: String) -> void:",
        '    """Close a menu by name."""',
        "    if _menus.has(menu_name):",
        "        _menus[menu_name].hide()",
        "        menu_closed.emit(menu_name)",
        "",
        "",
        "func pause_game() -> void:",
        '    """Pause the game."""',
        "    _is_paused = true",
        "    get_tree().paused = true",
        '    open_menu("pause")',
        "",
        "",
        "func resume_game() -> void:",
        '    """Resume the game."""',
        "    _is_paused = false",
        "    get_tree().paused = false",
        "    if _current_menu:",
        "        _current_menu.hide()",
        "",
        "",
        "func update_health_bar(current: float, maximum: float) -> void:",
        '    """Update health bar display."""',
        '    if _menus.has("hud"):',
        '        var health_bar = _menus["hud"].find_child("HealthBar", true, false)',
        "        if health_bar:",
        "            health_bar.value = (current / maximum) * 100.0",
        "",
        "",
        "func update_score(score: int) -> void:",
        '    """Update score display."""',
        '    if _menus.has("hud"):',
        '        var score_label = _menus["hud"].find_child("ScoreLabel", true, false)',
        "        if score_label:",
        '            score_label.text = "Score: %d" % score',
        "",
        "",
        "func show_game_over() -> void:",
        '    """Show game over screen."""',
        "    _is_paused = true",
        "    get_tree().paused = true",
        '    open_menu("game_over")',
        "",
        "",
        "func restart_game() -> void:",
        '    """Restart the game."""',
        "    get_tree().paused = false",
        "    get_tree().reload_current_scene()",
        "",
        "",
        "func quit_to_menu() -> void:",
        '    """Quit to main menu."""',
        "    get_tree().paused = false",
        '    get_tree().change_scene_to_file("res://ui/main_menu.tscn")',
    ]
)


# State Machine Template
TEMPLATE_STATE_MACHINE = _make_template(
    [
        "extends Node",
        'class_name {{ class_name|default("StateMachine") }}',
        "",
        "## Docstring",
        "{% if docstring %}{{ docstring }}{% else %}Generic state machine for game entities.{% endif %}",
        "",
        "## Signals",
        "signal state_changed(old_state: String, new_state: String)",
        "",
        "",
        "## Export Variables",
        '@export var initial_state: String = "{{ initial_state|default("idle") }}"',
        "",
        "",
        "## Onready Variables",
        "@onready var current_state: State = null",
        "@onready var states: Dictionary = {}",
        "",
        "",
        "## Inner Classes",
        "class State extends Node:",
        "    ## Base state class.",
        "    ",
        "    var state_machine: StateMachine",
        "    var entity: Node",
        "    ",
        "    func enter() -> void:",
        '        """Called when entering the state."""',
        "        pass",
        "    ",
        "    func exit() -> void:",
        '        """Called when exiting the state."""',
        "        pass",
        "    ",
        "    func update(delta: float) -> void:",
        '        """Called every frame."""',
        "        pass",
        "    ",
        "    func physics_update(delta: float) -> void:",
        '        """Called every physics frame."""',
        "        pass",
        "    ",
        "    func handle_input(event: InputEvent) -> void:",
        '        """Handle input events."""',
        "        pass",
        "",
        "",
        "## Built-in Virtual Functions",
        "func _ready() -> void:",
        '    """Called when the node enters the scene tree."""',
        "    for child in get_children():",
        "        if child is State:",
        "            states[child.name] = child",
        "            child.state_machine = self",
        "            child.entity = self.get_parent()",
        "    ",
        "    if states.has(initial_state):",
        "        current_state = states[initial_state]",
        "        current_state.enter()",
        "",
        "",
        "func _physics_process(delta: float) -> void:",
        '    """Called every physics frame."""',
        "    if current_state:",
        "        current_state.physics_update(delta)",
        "",
        "",
        "func _unhandled_input(event: InputEvent) -> void:",
        '    """Handle input events."""',
        "    if current_state:",
        "        current_state.handle_input(event)",
        "",
        "",
        "func transition_to(state_name: String) -> void:",
        '    """Transition to a new state."""',
        "    if not states.has(state_name):",
        "        push_warning(\"[StateMachine] State '%s' not found\" % state_name)",
        "        return",
        "    ",
        "    var new_state: State = states[state_name]",
        "    ",
        "    if current_state:",
        "        current_state.exit()",
        "    ",
        '    var old_state_name: String = current_state.name if current_state else ""',
        "    current_state = new_state",
        "    current_state.enter()",
        "    ",
        "    state_changed.emit(old_state_name, state_name)",
    ]
)


# Singleton Template
TEMPLATE_SINGLETON = _make_template(
    [
        "extends Node",
        'class_name {{ class_name|default("GameManager") }}',
        "",
        "## Docstring",
        "{% if docstring %}{{ docstring }}{% else %}Singleton/AutoLoad for global game management.{% endif %}",
        "",
        "## Signals",
        "signal game_paused(is_paused: bool)",
        "signal game_over",
        "signal score_updated(new_score: int)",
        "signal level_started(level_name: String)",
        "signal level_completed(level_name: String)",
        "",
        "",
        "## Singleton Instance (static access)",
        'static var instance: {{ class_name|default("GameManager") }}',
        "",
        "",
        "## Export Variables",
        '@export_group("Game Settings")',
        '@export var start_level: String = "res://levels/level_1.tscn"',
        "@export var persist_between_scenes: bool = true",
        "",
        '@export_group("Debug")',
        "@export var debug_mode: bool = false",
        "",
        "",
        "## Onready Variables",
        "@onready var _score: int = 0",
        '@onready var _current_level: String = ""',
        "@onready var _is_paused: bool = false",
        "@onready var _game_time: float = 0.0",
        "",
        "",
        "func _ready() -> void:",
        '    """Called when the node enters the scene tree."""',
        "    # Singleton pattern - persist across scenes",
        "    if persist_between_scenes:",
        "        if not instance or instance == self:",
        "            instance = self",
        "        else:",
        "            queue_free()",
        "            return",
        "    ",
        "    _initialize_game()",
        "",
        "",
        "func _initialize_game() -> void:",
        '    """Initialize the game."""',
        "    if debug_mode:",
        '        print("[DEBUG] Game initialized")',
        "    _load_settings()",
        "",
        "",
        "func _load_settings() -> void:",
        '    """Load game settings."""',
        "    pass",
        "",
        "",
        "func _process(delta: float) -> void:",
        '    """Called every frame."""',
        "    if not _is_paused:",
        "        _game_time += delta",
        "",
        "",
        "func _input(event: InputEvent) -> void:",
        '    """Handle global input."""',
        '    if event.is_action_pressed("ui_cancel"):',
        "        toggle_pause()",
        "",
        "",
        "## Public Methods (Global Access)",
        "func toggle_pause() -> void:",
        '    """Toggle game pause."""',
        "    _is_paused = not _is_paused",
        "    get_tree().paused = _is_paused",
        "    game_paused.emit(_is_paused)",
        "",
        "",
        "func add_score(points: int) -> void:",
        '    """Add to the score."""',
        "    _score += points",
        "    score_updated.emit(_score)",
        "",
        "",
        "func get_score() -> int:",
        '    """Get current score."""',
        "    return _score",
        "",
        "",
        "func reset_score() -> void:",
        '    """Reset the score."""',
        "    _score = 0",
        "    score_updated.emit(_score)",
        "",
        "",
        "func load_level(level_path: String) -> void:",
        '    """Load a level scene."""',
        "    _current_level = level_path",
        "    level_started.emit(level_path)",
        "    get_tree().change_scene_to_file(level_path)",
        "",
        "",
        "func complete_level() -> void:",
        '    """Mark current level as completed."""',
        "    level_completed.emit(_current_level)",
        "",
        "",
        "func game_over() -> void:",
        '    """Trigger game over."""',
        "    game_over.emit()",
        "",
        "",
        "func restart_game() -> void:",
        '    """Restart from the beginning."""',
        "    _score = 0",
        "    _game_time = 0.0",
        "    _is_paused = false",
        "    get_tree().paused = false",
        "    get_tree().change_scene_to_file(start_level)",
        "",
        "",
        "func quit_game() -> void:",
        '    """Quit the game."""',
        "    get_tree().quit()",
    ]
)


# Template Registry
SCRIPT_TEMPLATES = {
    "base_node": TEMPLATE_NODE,
    "node": TEMPLATE_NODE,
    "node_2d": TEMPLATE_NODE_2D,
    "character_body_2d": TEMPLATE_CHARACTER_BODY_2D,
    "character": TEMPLATE_CHARACTER_BODY_2D,
    "player_controller": TEMPLATE_PLAYER_CONTROLLER,
    "player": TEMPLATE_PLAYER_CONTROLLER,
    "enemy_ai": TEMPLATE_ENEMY_AI,
    "enemy": TEMPLATE_ENEMY_AI,
    "ui_controller": TEMPLATE_UI_CONTROLLER,
    "ui": TEMPLATE_UI_CONTROLLER,
    "state_machine": TEMPLATE_STATE_MACHINE,
    "singleton": TEMPLATE_SINGLETON,
    "autoload": TEMPLATE_SINGLETON,
}


# =============================================================================
# TEMPLATE FUNCTIONS (Public API)
# =============================================================================


def get_script_template(template_name: str) -> str:
    """
    Get the raw template string for a given template name.

    Args:
        template_name: Name of the template (e.g., 'player_controller', 'enemy_ai')

    Returns:
        The raw template string

    Raises:
        KeyError: If template_name is not found

    Example:
        >>> template = get_script_template('player_controller')
        >>> print(template[:50])
        extends CharacterBody2D
    """
    template_name_lower = template_name.lower()

    if template_name_lower not in SCRIPT_TEMPLATES:
        # Try to find by partial match
        for key in SCRIPT_TEMPLATES:
            if template_name_lower in key or key in template_name_lower:
                return SCRIPT_TEMPLATES[key]

        raise KeyError(
            f"Template '{template_name}' not found. "
            f"Available templates: {list(SCRIPT_TEMPLATES.keys())}"
        )

    return SCRIPT_TEMPLATES[template_name_lower]


def render_script(template_name: str, context: dict[str, Any] | None = None) -> str:
    """
    Render a script template with the given context.

    Args:
        template_name: Name of the template to render
        context: Dictionary of variables to pass to the template

    Returns:
        The rendered GDScript code

    Raises:
        KeyError: If template_name is not found
        jinja2.TemplateError: If template has syntax errors

    Example:
        >>> context = {
        ...     'class_name': 'Player',
        ...     'speed': 350.0,
        ...     'jump_velocity': -450.0
        ... }
        >>> script = render_script('player_controller', context)
        >>> print(script[:80])
        extends CharacterBody2D
        class_name Player
    """
    template_str = get_script_template(template_name)

    # Default context
    if context is None:
        context = {}

    # Create Jinja2 environment and render
    env = Environment(loader=BaseLoader(), trim_blocks=True, lstrip_blocks=True)

    try:
        template = env.from_string(template_str)
        rendered = template.render(**context)
    except Exception as e:
        raise RuntimeError(f"Error rendering template '{template_name}': {e}")

    # Clean up extra whitespace
    lines = rendered.split("\n")
    cleaned_lines = []
    prev_empty = False

    for line in lines:
        is_empty = line.strip() == ""
        if is_empty and prev_empty:
            continue
        cleaned_lines.append(line)
        prev_empty = is_empty

    return "\n".join(cleaned_lines).strip() + "\n"


def list_script_templates() -> list[str]:
    """
    List all available script template names.

    Returns:
        List of template names

    Example:
        >>> templates = list_script_templates()
        >>> print(templates[:5])
        ['base_node', 'node', 'node_2d', 'character_body_2d', 'character']
    """
    return list(SCRIPT_TEMPLATES.keys())


# Alias functions for backward compatibility
def get_template(template_name: str) -> str:
    """Alias for get_script_template."""
    return get_script_template(template_name)


def render(template_name: str, context: dict | None = None) -> str:
    """Alias for render_script."""
    return render_script(template_name, context)


if __name__ == "__main__":
    print("Testing templates...")

    # Test listing templates
    templates = list_script_templates()
    print(f"Available templates: {len(templates)}")
    print(f"  {templates[:5]}...")
    print()

    # Test render player controller
    print("=" * 50)
    print("Testing player_controller template:")
    print("=" * 50)

    script = render_script(
        "player_controller",
        {"class_name": "Player", "speed": 350.0, "jump_velocity": -450.0},
    )

    print(script[:500])
    print("...")
    print(f"[Total lines: {len(script.splitlines())}]")
    print()

    # Test render singleton
    print("=" * 50)
    print("Testing singleton template:")
    print("=" * 50)

    script = render_script("singleton", {"class_name": "GameManager"})

    print(script[:300])
    print("...")

    print()
    print("✓ All tests passed!")
