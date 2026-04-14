"""Tests para templates de nodos y scripts.

Tests:
1. Node templates: listar, obtener, renderizar, validar contexto
2. Script templates: listar, obtener, renderizar
3. Verificar que los templates generan contenido válido
"""

import sys
import os

import pytest
from jinja2 import TemplateNotFound

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from godot_mcp.templates.node_templates import (
    get_template,
    list_templates,
    render_template,
    get_node_snippet,
    get_template_names_by_category,
    validate_context,
    NodeTemplateEngine,
)
from godot_mcp.templates.script_templates import (
    get_script_template,
    render_script,
    list_script_templates,
)


# =============================================================================
# NODE TEMPLATES
# =============================================================================


class TestNodeTemplateList:
    """Tests para list_templates y get_template_names_by_category."""

    def test_list_templates_not_empty(self):
        """Debe haber al menos un template disponible."""
        templates = list_templates()
        assert len(templates) > 0

    def test_list_templates_sorted(self):
        """Los templates deben estar ordenados alfabéticamente."""
        templates = list_templates()
        assert templates == sorted(templates)

    def test_expected_templates_exist(self):
        """Deben existir los templates esperados."""
        templates = list_templates()
        expected = [
            "node2d_basic",
            "node2d_sprite",
            "node2d_collision",
            "character_body_2d",
            "area2d_trigger",
            "control_button",
            "node3d_basic",
            "camera2d",
            "timer",
        ]
        for name in expected:
            assert name in templates, f"Template '{name}' not found"

    def test_categories_not_empty(self):
        """Debe haber categorías con templates."""
        categories = get_template_names_by_category()
        assert len(categories) > 0
        for category, names in categories.items():
            assert len(names) > 0, f"Category '{category}' is empty"

    def test_all_categorized_templates_exist(self):
        """Todos los templates en categorías deben existir."""
        categories = get_template_names_by_category()
        all_templates = set(list_templates())
        for category, names in categories.items():
            for name in names:
                assert name in all_templates, (
                    f"Template '{name}' in category '{category}' not found"
                )


class TestNodeTemplateGet:
    """Tests para get_template."""

    def test_get_existing_template(self):
        """Debe obtener un template existente."""
        template = get_template("node2d_basic")
        assert isinstance(template, str)
        assert len(template) > 0

    def test_get_nonexistent_template_raises(self):
        """Debe lanzar TemplateNotFound para templates inexistentes."""
        with pytest.raises(TemplateNotFound):
            get_template("nonexistent_template_xyz")

    def test_template_contains_gd_scene(self):
        """Los templates de nodos deben contener [gd_scene o [node."""
        template = get_template("node2d_basic")
        assert "[gd_scene" in template or "[node" in template


class TestNodeTemplateRender:
    """Tests para render_template."""

    def test_render_without_context(self):
        """Debe renderizar sin contexto (usando defaults)."""
        rendered = render_template("node2d_basic")
        assert isinstance(rendered, str)
        assert len(rendered) > 0

    def test_render_with_custom_context(self):
        """Debe renderizar con contexto personalizado."""
        rendered = render_template("node2d_basic", {"name": "MyCustomNode"})
        assert "MyCustomNode" in rendered

    def test_render_nonexistent_template_raises(self):
        """Debe lanzar TemplateNotFound para templates inexistentes."""
        with pytest.raises(TemplateNotFound):
            render_template("nonexistent_xyz")

    def test_render_character_body_2d(self):
        """CharacterBody2D debe generar estructura válida."""
        rendered = render_template("character_body_2d", {"name": "Player"})
        assert "Player" in rendered
        assert "CharacterBody2D" in rendered

    def test_render_area2d_trigger(self):
        """Area2D trigger debe generar estructura válida."""
        rendered = render_template("area2d_trigger", {"name": "DamageZone"})
        assert "DamageZone" in rendered
        assert "Area2D" in rendered

    def test_render_control_button(self):
        """Control button debe generar estructura válida."""
        rendered = render_template("control_button", {"text": "Click Me"})
        assert "Click Me" in rendered
        assert "Button" in rendered


class TestNodeTemplateValidateContext:
    """Tests para validate_context."""

    def test_valid_context(self):
        """Contexto válido debe retornar lista vacía."""
        # Obtener las claves requeridas del contexto default
        from godot_mcp.templates.node_templates import DEFAULT_CONTEXTS

        required = DEFAULT_CONTEXTS.get("node2d_basic", {})
        full_context = {k: "test" for k in required}
        missing = validate_context("node2d_basic", full_context)
        assert missing == []

    def test_missing_keys(self):
        """Contexto incompleto debe retornar claves faltantes."""
        # node2d_basic requiere al menos "name"
        missing = validate_context("node2d_basic", {})
        assert "name" in missing

    def test_nonexistent_template(self):
        """Template inexistente debe retornar error."""
        missing = validate_context("nonexistent_xyz", {})
        assert "template not found" in missing


class TestNodeSnippet:
    """Tests para get_node_snippet."""

    def test_get_sprite_snippet(self):
        """Debe obtener snippet de Sprite2D."""
        snippet = get_node_snippet("Sprite2D")
        assert isinstance(snippet, str)
        assert len(snippet) > 0

    def test_get_collision_snippet(self):
        """Debe obtener snippet de CollisionShape2D."""
        snippet = get_node_snippet("CollisionShape2D")
        assert isinstance(snippet, str)
        assert len(snippet) > 0

    def test_get_nonexistent_snippet(self):
        """Snippet inexistente debe retornar string vacío o comentario."""
        snippet = get_node_snippet("NonExistentNode")
        # Puede retornar empty o un comentario
        assert isinstance(snippet, str)


class TestNodeTemplateEngine:
    """Tests para la clase NodeTemplateEngine."""

    def test_engine_render(self):
        """NodeTemplateEngine debe poder renderizar templates."""
        engine = NodeTemplateEngine()
        rendered = engine.render("node2d_basic", {"name": "EngineTest"})
        assert "EngineTest" in rendered

    def test_engine_render_multiple(self):
        """NodeTemplateEngine debe poder renderizar múltiples templates."""
        engine = NodeTemplateEngine()
        for template_name in ["node2d_basic", "character_body_2d"]:
            rendered = engine.render(template_name, {"name": "Test"})
            assert "Test" in rendered


# =============================================================================
# SCRIPT TEMPLATES
# =============================================================================


class TestScriptTemplateList:
    """Tests para list_script_templates."""

    def test_list_not_empty(self):
        """Debe haber al menos un script template."""
        templates = list_script_templates()
        assert len(templates) > 0

    def test_expected_templates_exist(self):
        """Deben existir los templates esperados."""
        templates = list_script_templates()
        expected = [
            "base_node",
            "node_2d",
            "character_body_2d",
            "player_controller",
            "enemy_ai",
            "ui_controller",
            "state_machine",
            "singleton",
        ]
        for name in expected:
            assert name in templates, f"Script template '{name}' not found"


class TestScriptTemplateGet:
    """Tests para get_script_template."""

    def test_get_existing_template(self):
        """Debe obtener un template existente."""
        template = get_script_template("base_node")
        assert isinstance(template, str)
        assert len(template) > 0

    def test_get_nonexistent_template_raises(self):
        """Debe lanzar KeyError para templates inexistentes."""
        with pytest.raises(KeyError):
            get_script_template("nonexistent_script_xyz")

    def test_template_contains_extends(self):
        """Los scripts deben contener 'extends'."""
        template = get_script_template("base_node")
        assert "extends" in template


class TestScriptTemplateRender:
    """Tests para render_script."""

    def test_render_base_node(self):
        """Debe renderizar base_node correctamente."""
        rendered = render_script("base_node", {"class_name": "MyNode"})
        assert "MyNode" in rendered

    def test_render_character_body_2d(self):
        """Debe renderizar character_body_2d correctamente."""
        rendered = render_script("character_body_2d", {"class_name": "Player"})
        assert "Player" in rendered
        assert "CharacterBody2D" in rendered

    def test_render_player_controller(self):
        """Debe renderizar player_controller correctamente."""
        rendered = render_script("player_controller", {"class_name": "Hero"})
        assert "Hero" in rendered
        assert "CharacterBody2D" in rendered

    def test_render_enemy_ai(self):
        """Debe renderizar enemy_ai correctamente."""
        rendered = render_script("enemy_ai", {"class_name": "Goblin"})
        assert "Goblin" in rendered

    def test_render_state_machine(self):
        """Debe renderizar state_machine correctamente."""
        rendered = render_script("state_machine", {"class_name": "EnemyFSM"})
        assert "EnemyFSM" in rendered

    def test_render_singleton(self):
        """Debe renderizar singleton correctamente."""
        rendered = render_script("singleton", {"class_name": "GameManager"})
        assert "GameManager" in rendered

    def test_render_nonexistent_raises(self):
        """Debe lanzar KeyError para templates inexistentes."""
        with pytest.raises(KeyError):
            render_script("nonexistent_xyz")

    def test_rendered_script_valid_syntax(self):
        """El script renderizado debe tener sintaxis GDScript básica válida."""
        rendered = render_script("base_node", {"class_name": "TestNode"})
        # Verificaciones básicas de sintaxis GDScript
        assert "extends" in rendered
        # No debe tener Jinja2 sin resolver
        assert "{{" not in rendered
        assert "}}" not in rendered
        assert "{%" not in rendered
        assert "%}" not in rendered
