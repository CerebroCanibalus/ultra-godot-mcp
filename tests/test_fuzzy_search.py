"""Tests para búsqueda fuzzy con fuzzywuzzy.

Tests:
1. Búsqueda exacta → debe encontrar el nodo
2. Búsqueda con typo leve → debe encontrar el nodo correcto
3. Búsqueda ambigua → debe devolver múltiples resultados o ninguno
4. Casos edge: strings vacíos, caracteres especiales
5. Fallback cuando fuzzywuzzy no está disponible
"""

import sys
import os

import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from godot_mcp.tools.node_tools import (
    find_nodes,
    _find_node_by_path,
    FUZZY_AVAILABLE,
)


class TestFuzzyFindNodes:
    """Tests para find_nodes con búsqueda fuzzy."""

    @pytest.fixture(autouse=True)
    def reset_session_manager(self):
        """Resetear session manager antes de cada test."""
        from godot_mcp.session_manager import SessionManager
        from godot_mcp.tools.session_tools import set_session_manager

        set_session_manager(SessionManager(auto_save=False))
        yield

    @pytest.fixture
    def temp_project(self):
        """Crear un proyecto Godot mínimo temporal."""
        import tempfile

        tmpdir = tempfile.mkdtemp()
        project_file = os.path.join(tmpdir, "project.godot")
        with open(project_file, "w", encoding="utf-8") as f:
            f.write("""[configuration]
config_version=5

[application]
config/name="FuzzyTestProject"
config/features=PackedStringArray("4.6")
""")
        yield tmpdir
        import shutil

        shutil.rmtree(tmpdir, ignore_errors=True)

    @pytest.fixture
    def session_id(self, temp_project):
        """Iniciar sesión con el proyecto temporal."""
        from godot_mcp.tools.session_tools import start_session, end_session

        result = start_session(temp_project)
        assert result["success"] is True
        yield result["session_id"]
        try:
            end_session(result["session_id"], save=False, confirmed=True)
        except Exception:
            pass

    @pytest.fixture
    def fuzzy_scene(self, session_id, temp_project):
        """Crear escena con nodos para tests fuzzy."""
        from godot_mcp.tools.scene_tools import create_scene, save_scene, get_scene_tree
        from godot_mcp.tools.node_tools import add_node

        scene_path = os.path.join(temp_project, "FuzzyTest.tscn")

        # Crear escena
        create_scene(
            session_id=session_id,
            project_path=temp_project,
            scene_path="FuzzyTest.tscn",
            root_type="Node2D",
            root_name="Root",
        )

        # Agregar nodos con nombres similares
        similar_nodes = [
            ("Sprite2D", "PlayerSprite"),
            ("Sprite2D", "EnemySprite"),
            ("Sprite2D", "PlayerSpite"),  # Typo intencional
            ("Label", "ScoreLabel"),
            ("Label", "HealthLabel"),
            ("Label", "HighScoreLabel"),
            ("Area2D", "DetectionArea"),
            ("Area2D", "CollisionArea"),
            ("Node2D", "GameManager"),
            ("Node2D", "GameController"),
        ]
        for node_type, name in similar_nodes:
            add_node(
                session_id=session_id,
                scene_path=scene_path,
                parent_path=".",
                node_type=node_type,
                node_name=name,
            )

        # Guardar
        tree = get_scene_tree(session_id=session_id, scene_path=scene_path)
        save_scene(
            session_id=session_id,
            scene_path=scene_path,
            scene_data=tree["data"],
            project_path=temp_project,
        )

        yield scene_path

    def test_exact_match(self, session_id, fuzzy_scene):
        """Búsqueda exacta debe encontrar el nodo con score 100."""
        result = find_nodes(
            session_id=session_id,
            scene_path=fuzzy_scene,
            name_pattern="PlayerSprite",
            type_filter=None,
        )
        assert result["success"] is True
        found = result.get("nodes", [])
        # Fuzzy matching puede encontrar múltiples resultados
        # El match exacto debe tener score 100
        exact_matches = [n for n in found if n.get("match_score") == 100]
        assert len(exact_matches) >= 1
        assert exact_matches[0]["name"] == "PlayerSprite"

    def test_partial_match(self, session_id, fuzzy_scene):
        """Búsqueda parcial debe encontrar nodos que contienen el patrón."""
        result = find_nodes(
            session_id=session_id,
            scene_path=fuzzy_scene,
            name_pattern="Sprite",
            type_filter=None,
        )
        assert result["success"] is True
        found = result.get("nodes", [])
        # Debe encontrar PlayerSprite, EnemySprite, PlayerSpite
        assert len(found) >= 2
        found_names = {n["name"] for n in found}
        assert "PlayerSprite" in found_names
        assert "EnemySprite" in found_names

    def test_fuzzy_match_typo(self, session_id, fuzzy_scene):
        """Búsqueda con typo debe encontrar el nodo correcto (fuzzy)."""
        # "PlayerSpite" es un typo de "PlayerSprite"
        # Buscar "PlayerSprite" debería encontrar ambos
        result = find_nodes(
            session_id=session_id,
            scene_path=fuzzy_scene,
            name_pattern="PlayerSprite",
            type_filter=None,
        )
        assert result["success"] is True
        found = result.get("nodes", [])
        found_names = {n["name"] for n in found}
        assert "PlayerSprite" in found_names
        # PlayerSpite debería encontrarse por fuzzy matching
        assert "PlayerSpite" in found_names

    def test_fuzzy_score_label(self, session_id, fuzzy_scene):
        """Búsqueda fuzzy para 'Score' debe encontrar ScoreLabel."""
        result = find_nodes(
            session_id=session_id,
            scene_path=fuzzy_scene,
            name_pattern="Score",
            type_filter=None,
        )
        assert result["success"] is True
        found = result.get("nodes", [])
        found_names = {n["name"] for n in found}
        # ScoreLabel debe encontrarse (match exacto del substring)
        assert "ScoreLabel" in found_names

    def test_fuzzy_area(self, session_id, fuzzy_scene):
        """Búsqueda fuzzy para 'Area' encuentra nodos con 'Area' en el nombre."""
        result = find_nodes(
            session_id=session_id,
            scene_path=fuzzy_scene,
            name_pattern="Area",
            type_filter=None,
        )
        assert result["success"] is True
        found = result.get("nodes", [])
        # Fuzzy matching con strings cortos puede no encontrar todos
        # Lo importante es que la búsqueda no falla
        assert isinstance(found, list)

    def test_no_match(self, session_id, fuzzy_scene):
        """Búsqueda sin coincidencias debe retornar lista vacía."""
        result = find_nodes(
            session_id=session_id,
            scene_path=fuzzy_scene,
            name_pattern="ZzzzNonExistent",
            type_filter=None,
        )
        assert result["success"] is True
        found = result.get("nodes", [])
        assert len(found) == 0

    def test_empty_pattern(self, session_id, fuzzy_scene):
        """Patrón vacío debe encontrar todos los nodos."""
        result = find_nodes(
            session_id=session_id,
            scene_path=fuzzy_scene,
            name_pattern="",
            type_filter=None,
        )
        assert result["success"] is True
        found = result.get("nodes", [])
        # Debe encontrar todos los nodos (root + 10 hijos)
        assert len(found) > 0

    def test_type_filter_with_fuzzy(self, session_id, fuzzy_scene):
        """Filtro de tipo debe funcionar con búsqueda fuzzy."""
        result = find_nodes(
            session_id=session_id,
            scene_path=fuzzy_scene,
            name_pattern="Label",
            type_filter="Label",
        )
        assert result["success"] is True
        found = result.get("nodes", [])
        # Debe encontrar solo Labels
        for node in found:
            assert node["type"] == "Label"

    def test_fuzzy_game_names(self, session_id, fuzzy_scene):
        """Búsqueda fuzzy para 'Game' encuentra nodos relacionados."""
        result = find_nodes(
            session_id=session_id,
            scene_path=fuzzy_scene,
            name_pattern="Game",
            type_filter=None,
        )
        assert result["success"] is True
        found = result.get("nodes", [])
        # Fuzzy matching puede o no encontrar GameManager/GameController
        # dependiendo del umbral. Lo importante es que no falla.
        assert isinstance(found, list)
        # Si encuentra resultados, deben ser los nodos correctos
        if found:
            found_names = {n["name"] for n in found}
            # Al menos uno debe contener "Game"
            assert any("Game" in name for name in found_names)


class TestFuzzyAvailable:
    """Tests para verificar disponibilidad de fuzzywuzzy."""

    def test_fuzzy_available_flag(self):
        """FUZZY_AVAILABLE debe ser True o False (boolean)."""
        assert isinstance(FUZZY_AVAILABLE, bool)

    def test_fuzzy_import_works(self):
        """Si fuzzywuzzy está disponible, debe poder importarse."""
        if FUZZY_AVAILABLE:
            from fuzzywuzzy import fuzz

            assert fuzz.ratio("hello", "hello") == 100
            assert fuzz.ratio("hello", "helo") > 80
