"""Tests E2E de flujo completo para Godot MCP.

Estos tests simulan flujos reales de usuario usando las herramientas MCP
contra proyectos Godot temporales. Cada test ejecuta un flujo completo
de múltiples operaciones.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from godot_mcp.tools.scene_tools import (
    create_scene,
    get_scene_tree,
    save_scene,
    list_scenes,
)
from godot_mcp.tools.node_tools import (
    add_node,
    add_ext_resource,
    remove_node,
    rename_node,
    move_node,
    duplicate_node,
    find_nodes,
)
from godot_mcp.tools.signal_and_script_tools import connect_signal, add_sub_resource
from godot_mcp.tools.property_tools import set_node_properties
from godot_mcp.tools.validation_tools import validate_tscn


class TestE2EBasicWorkflow:
    """Flujo básico: crear escena → agregar nodos → guardar → validar."""

    def test_create_player_scene(self, session_id, temp_project):
        """Crear una escena de jugador completa con colisiones."""
        # 1. Crear escena
        result = create_scene(
            session_id=session_id,
            project_path=temp_project,
            scene_path="scenes/Player.tscn",
            root_type="CharacterBody2D",
            root_name="Player",
        )
        assert result["success"] is True

        scene_path = os.path.join(temp_project, "scenes", "Player.tscn")

        # 2. Agregar Sprite2D
        result = add_node(
            session_id=session_id,
            scene_path=scene_path,
            parent_path=".",
            node_type="Sprite2D",
            node_name="Sprite",
        )
        assert result["success"] is True

        # 3. Agregar CollisionShape2D
        result = add_node(
            session_id=session_id,
            scene_path=scene_path,
            parent_path=".",
            node_type="CollisionShape2D",
            node_name="CollisionShape",
        )
        assert result["success"] is True

        # 4. Agregar SubResource para la forma
        result = add_sub_resource(
            session_id=session_id,
            scene_path=scene_path,
            resource_type="RectangleShape2D",
            properties={"size": {"type": "Vector2", "x": 32, "y": 32}},
        )
        assert result["success"] is True
        shape_id = result["resource_id"]

        # 5. Asignar forma al CollisionShape2D
        result = set_node_properties(
            session_id=session_id,
            scene_path=scene_path,
            node_path="CollisionShape",
            properties={"shape": {"type": "SubResource", "ref": shape_id}},
        )
        assert result["success"] is True

        # 6. Obtener datos y guardar escena
        tree = get_scene_tree(session_id=session_id, scene_path=scene_path)
        assert tree["success"] is True
        scene_data = tree["data"]

        result = save_scene(
            session_id=session_id,
            scene_path=scene_path,
            scene_data=scene_data,
            project_path=temp_project,
        )
        assert result["success"] is True

        # 7. Validar escena
        result = validate_tscn(
            scene_path=scene_path, project_path=temp_project, strict=False
        )
        assert result["success"] is True

        # 8. Verificar estructura
        tree = get_scene_tree(session_id=session_id, scene_path=scene_path)
        assert tree["success"] is True
        nodes = tree["data"].get("nodes", [])
        node_names = [n.get("name") for n in nodes]
        assert "Player" in node_names
        assert "Sprite" in node_names
        assert "CollisionShape" in node_names


class TestE2ESignalWorkflow:
    """Flujo con señales: crear nodos → conectar señales → guardar."""

    def test_connect_area_signal(self, session_id, temp_project):
        """Crear un Area2D con señal body_entered conectada."""
        # 1. Crear escena
        result = create_scene(
            session_id=session_id,
            project_path=temp_project,
            scene_path="scenes/Hazard.tscn",
            root_type="Area2D",
            root_name="Hazard",
        )
        assert result["success"] is True

        scene_path = os.path.join(temp_project, "scenes", "Hazard.tscn")

        # 2. Agregar CollisionShape2D
        result = add_node(
            session_id=session_id,
            scene_path=scene_path,
            parent_path=".",
            node_type="CollisionShape2D",
            node_name="Shape",
        )
        assert result["success"] is True

        # 3. Agregar forma
        result = add_sub_resource(
            session_id=session_id,
            scene_path=scene_path,
            resource_type="CircleShape2D",
            properties={"radius": 16.0},
        )
        assert result["success"] is True
        shape_id = result["resource_id"]

        result = set_node_properties(
            session_id=session_id,
            scene_path=scene_path,
            node_path="Shape",
            properties={"shape": {"type": "SubResource", "ref": shape_id}},
        )
        assert result["success"] is True

        # 4. Conectar señal
        result = connect_signal(
            session_id=session_id,
            scene_path=scene_path,
            from_node="Hazard",
            signal="body_entered",
            to_node="Hazard",
            method="_on_body_entered",
        )
        assert result["success"] is True

        # 5. Guardar y validar
        tree = get_scene_tree(session_id=session_id, scene_path=scene_path)
        assert tree["success"] is True
        scene_data = tree["data"]

        result = save_scene(
            session_id=session_id,
            scene_path=scene_path,
            scene_data=scene_data,
            project_path=temp_project,
        )
        assert result["success"] is True

        result = validate_tscn(
            scene_path=scene_path, project_path=temp_project, strict=False
        )
        assert result["success"] is True

        # 6. Verificar conexiones
        tree = get_scene_tree(session_id=session_id, scene_path=scene_path)
        assert tree["success"] is True
        connections = tree["data"].get("connections", [])
        assert len(connections) == 1
        assert connections[0]["signal"] == "body_entered"


class TestE2ENodeOperations:
    """Flujo de operaciones de nodos: renombrar, mover, duplicar."""

    def test_rename_move_duplicate(self, session_id, temp_project):
        """Probar operaciones de nodos en cadena."""
        # 1. Crear escena
        result = create_scene(
            session_id=session_id,
            project_path=temp_project,
            scene_path="scenes/Operations.tscn",
            root_type="Node2D",
            root_name="Root",
        )
        assert result["success"] is True

        scene_path = os.path.join(temp_project, "scenes", "Operations.tscn")

        # 2. Agregar nodos hijos
        for name in ["Enemy1", "Enemy2"]:
            result = add_node(
                session_id=session_id,
                scene_path=scene_path,
                parent_path=".",
                node_type="Node2D",
                node_name=name,
            )
            assert result["success"] is True

        # 3. Agregar nieto a Enemy1
        result = add_node(
            session_id=session_id,
            scene_path=scene_path,
            parent_path="Enemy1",
            node_type="Sprite2D",
            node_name="Sprite",
        )
        assert result["success"] is True

        # 4. Renombrar nodo
        result = rename_node(
            session_id=session_id,
            scene_path=scene_path,
            node_path="Enemy1",
            new_name="Boss",
        )
        assert result["success"] is True

        # 5. Duplicar nodo (debe incluir hijos)
        result = duplicate_node(
            session_id=session_id,
            scene_path=scene_path,
            node_path="Boss",
            new_name="Boss_2",
        )
        assert result["success"] is True

        # 6. Verificar estructura
        tree = get_scene_tree(session_id=session_id, scene_path=scene_path)
        assert tree["success"] is True
        nodes = tree["data"].get("nodes", [])
        node_names = [n.get("name") for n in nodes]
        assert "Boss" in node_names
        assert "Boss_2" in node_names
        assert "Enemy2" in node_names

        # 7. Guardar y validar
        scene_data = tree["data"]
        result = save_scene(
            session_id=session_id,
            scene_path=scene_path,
            scene_data=scene_data,
            project_path=temp_project,
        )
        assert result["success"] is True

        result = validate_tscn(
            scene_path=scene_path, project_path=temp_project, strict=False
        )
        assert result["success"] is True


class TestE2EFindNodes:
    """Flujo de búsqueda de nodos."""

    def test_find_nodes_by_type_and_name(self, session_id, temp_project):
        """Buscar nodos por tipo y nombre."""
        # 1. Crear escena con múltiples nodos
        result = create_scene(
            session_id=session_id,
            project_path=temp_project,
            scene_path="scenes/Search.tscn",
            root_type="Node2D",
            root_name="Root",
        )
        assert result["success"] is True

        scene_path = os.path.join(temp_project, "scenes", "Search.tscn")

        # 2. Agregar varios tipos de nodos
        nodes_to_add = [
            (".", "Sprite2D", "PlayerSprite"),
            (".", "Sprite2D", "EnemySprite"),
            (".", "Label", "ScoreLabel"),
            (".", "Label", "HealthLabel"),
            (".", "Area2D", "DetectionArea"),
        ]
        for parent, ntype, name in nodes_to_add:
            result = add_node(
                session_id=session_id,
                scene_path=scene_path,
                parent_path=parent,
                node_type=ntype,
                node_name=name,
            )
            assert result["success"] is True

        # 3. Guardar
        tree = get_scene_tree(session_id=session_id, scene_path=scene_path)
        scene_data = tree["data"]
        result = save_scene(
            session_id=session_id,
            scene_path=scene_path,
            scene_data=scene_data,
            project_path=temp_project,
        )
        assert result["success"] is True

        # 4. Buscar por tipo
        result = find_nodes(
            session_id=session_id,
            scene_path=scene_path,
            name_pattern=None,
            type_filter="Sprite2D",
        )
        assert result["success"] is True
        found = result.get("nodes", [])
        assert len(found) == 2
        found_names = {n.get("name") for n in found}
        assert "PlayerSprite" in found_names
        assert "EnemySprite" in found_names

        # 5. Buscar por nombre (fuzzy)
        result = find_nodes(
            session_id=session_id,
            scene_path=scene_path,
            name_pattern="Score",
            type_filter=None,
        )
        assert result["success"] is True
        found = result.get("nodes", [])
        assert len(found) == 1
        assert found[0].get("name") == "ScoreLabel"

        # 6. Buscar por nombre parcial
        result = find_nodes(
            session_id=session_id,
            scene_path=scene_path,
            name_pattern="Label",
            type_filter=None,
        )
        assert result["success"] is True
        found = result.get("nodes", [])
        assert len(found) == 2


class TestE2EExtResource:
    """Flujo con recursos externos."""

    def test_add_script_resource(self, session_id, temp_project):
        """Agregar un script como recurso externo y asignarlo a un nodo."""
        scene_rel = "scenes/Scripted.tscn"
        script_rel = "scripts/player.gd"

        script_path = os.path.join(temp_project, script_rel)
        os.makedirs(os.path.dirname(script_path), exist_ok=True)

        # Crear script GDScript mínimo
        with open(script_path, "w", encoding="utf-8") as f:
            f.write("extends CharacterBody2D\n\nfunc _process(delta):\n\tpass\n")

        # 1. Crear escena
        result = create_scene(
            session_id=session_id,
            project_path=temp_project,
            scene_path=scene_rel,
            root_type="CharacterBody2D",
            root_name="Player",
        )
        assert result["success"] is True

        scene_path = os.path.join(temp_project, scene_rel)

        # 2. Agregar script como ExtResource
        rel_script = "res://" + script_rel
        result = add_ext_resource(
            session_id=session_id,
            scene_path=scene_path,
            resource_type="Script",
            resource_path=rel_script,
        )
        assert result["success"] is True
        script_id = result["resource_id"]

        # 3. Asignar script al nodo root
        result = set_node_properties(
            session_id=session_id,
            scene_path=scene_path,
            node_path="Player",
            properties={"script": {"type": "ExtResource", "ref": script_id}},
        )
        assert result["success"] is True

        # 4. Guardar y validar
        tree = get_scene_tree(session_id=session_id, scene_path=scene_path)
        scene_data = tree["data"]
        result = save_scene(
            session_id=session_id,
            scene_path=scene_path,
            scene_data=scene_data,
            project_path=temp_project,
        )
        assert result["success"] is True

        result = validate_tscn(
            scene_path=scene_path, project_path=temp_project, strict=False
        )
        assert result["success"] is True

        # 5. Verificar que el script está asignado
        tree = get_scene_tree(session_id=session_id, scene_path=scene_path)
        nodes = tree["data"].get("nodes", [])
        root = nodes[0]
        assert root.get("name") == "Player"
        props = root.get("properties", {})
        assert "script" in props


class TestE2EListScenes:
    """Flujo de listado de escenas."""

    def test_list_scenes_after_creation(self, session_id, temp_project):
        """Crear múltiples escenas y verificar que list_scenes las encuentra."""
        # Crear varias escenas
        scene_names = ["Level1", "Level2", "MainMenu"]
        for name in scene_names:
            result = create_scene(
                session_id=session_id,
                project_path=temp_project,
                scene_path=f"scenes/{name}.tscn",
                root_type="Node2D",
                root_name=name,
            )
            assert result["success"] is True

        # Listar escenas
        result = list_scenes(
            session_id=session_id, project_path=temp_project, recursive=True
        )
        assert result["success"] is True
        scenes = result.get("scenes", [])
        scene_paths = {s["path"] for s in scenes}

        for name in scene_names:
            assert f"scenes/{name}.tscn" in scene_paths
