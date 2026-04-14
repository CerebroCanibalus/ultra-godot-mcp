"""Tests para server.py - Verificación de registro de herramientas MCP.

Tests:
1. register_all_tools no lanza excepciones
2. Todas las herramientas esperadas están registradas
3. Cada módulo de herramientas se registra correctamente
4. El objeto MCP tiene el nombre correcto
"""

import sys
import os
import asyncio

import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from fastmcp import FastMCP

from godot_mcp.server import mcp, register_all_tools
from godot_mcp.tools.scene_tools import register_scene_tools
from godot_mcp.tools.node_tools import register_node_tools
from godot_mcp.tools.resource_tools import register_resource_tools
from godot_mcp.tools.session_tools import register_session_tools
from godot_mcp.tools.project_tools import register_project_tools
from godot_mcp.tools.validation_tools import register_validation_tools
from godot_mcp.tools.signal_and_script_tools import register_signal_and_script_tools
from godot_mcp.tools.property_tools import register_property_tools
from godot_mcp.tools.debug_tools import register_debug_tools


# Herramientas esperadas por módulo
EXPECTED_SCENE_TOOLS = {
    "create_scene",
    "get_scene_tree",
    "save_scene",
    "list_scenes",
    "instantiate_scene",
    "modify_scene",
}

EXPECTED_NODE_TOOLS = {
    "add_ext_resource",
    "add_node",
    "remove_node",
    "update_node",
    "get_node_properties",
    "rename_node",
    "move_node",
    "duplicate_node",
    "find_nodes",
}

EXPECTED_RESOURCE_TOOLS = {
    "create_resource",
    "read_resource",
    "update_resource",
    "get_uid",
    "update_project_uids",
    "list_resources",
}

EXPECTED_SESSION_TOOLS = {
    "start_session",
    "end_session",
    "get_active_session",
    "list_sessions",
    "get_session_info",
    "commit_session",
    "discard_changes",
}

EXPECTED_PROJECT_TOOLS = {
    "get_project_info",
    "list_projects",
    "get_project_structure",
    "find_scripts",
    "find_resources",
}

EXPECTED_VALIDATION_TOOLS = {
    "validate_tscn",
    "validate_gdscript",
    "validate_project",
}

EXPECTED_SIGNAL_SCRIPT_TOOLS = {
    "connect_signal",
    "set_script",
    "add_sub_resource",
}

EXPECTED_PROPERTY_TOOLS = {
    "set_node_properties",
}

EXPECTED_DEBUG_TOOLS = {
    "run_debug_scene",
    "check_script_syntax",
}

ALL_EXPECTED_TOOLS = (
    EXPECTED_SCENE_TOOLS
    | EXPECTED_NODE_TOOLS
    | EXPECTED_RESOURCE_TOOLS
    | EXPECTED_SESSION_TOOLS
    | EXPECTED_PROJECT_TOOLS
    | EXPECTED_VALIDATION_TOOLS
    | EXPECTED_SIGNAL_SCRIPT_TOOLS
    | EXPECTED_PROPERTY_TOOLS
    | EXPECTED_DEBUG_TOOLS
)


def _get_registered_tool_names(mcp_instance: FastMCP) -> set:
    """Obtener nombres de herramientas registradas usando list_tools."""
    tools = asyncio.run(mcp_instance.list_tools())
    return {t.name for t in tools}


@pytest.fixture(autouse=True)
def reset_mcp():
    """Resetear herramientas del MCP global antes de cada test."""
    # Eliminar todas las herramientas registradas
    for tool_name in _get_registered_tool_names(mcp):
        mcp.local_provider.remove_tool(tool_name)
    yield


class TestServerRegistration:
    """Tests para register_all_tools."""

    def test_register_all_tools_no_exception(self):
        """register_all_tools no debe lanzar excepciones."""
        # No debería lanzar nada
        register_all_tools()

    def test_all_tools_registered(self):
        """Todas las herramientas esperadas deben estar registradas."""
        register_all_tools()
        registered = _get_registered_tool_names(mcp)

        for tool_name in ALL_EXPECTED_TOOLS:
            assert tool_name in registered, f"Tool '{tool_name}' not registered"

    def test_tool_count(self):
        """Debe registrarse el número correcto de herramientas."""
        register_all_tools()
        registered = _get_registered_tool_names(mcp)
        assert len(registered) == len(ALL_EXPECTED_TOOLS)


class TestServerName:
    """Tests para el nombre del servidor."""

    def test_mcp_name(self):
        """El servidor MCP debe llamarse 'godot-mcp'."""
        assert mcp.name == "godot-mcp"


class TestIndividualModuleRegistration:
    """Tests para registro individual de cada módulo."""

    def test_scene_tools_registration(self):
        """Scene tools deben registrarse correctamente."""
        register_scene_tools(mcp)
        registered = _get_registered_tool_names(mcp)
        assert EXPECTED_SCENE_TOOLS.issubset(registered)

    def test_node_tools_registration(self):
        """Node tools deben registrarse correctamente."""
        register_node_tools(mcp)
        registered = _get_registered_tool_names(mcp)
        assert EXPECTED_NODE_TOOLS.issubset(registered)

    def test_resource_tools_registration(self):
        """Resource tools deben registrarse correctamente."""
        register_resource_tools(mcp)
        registered = _get_registered_tool_names(mcp)
        assert EXPECTED_RESOURCE_TOOLS.issubset(registered)

    def test_session_tools_registration(self):
        """Session tools deben registrarse correctamente."""
        register_session_tools(mcp)
        registered = _get_registered_tool_names(mcp)
        assert EXPECTED_SESSION_TOOLS.issubset(registered)

    def test_project_tools_registration(self):
        """Project tools deben registrarse correctamente."""
        register_project_tools(mcp)
        registered = _get_registered_tool_names(mcp)
        assert EXPECTED_PROJECT_TOOLS.issubset(registered)

    def test_validation_tools_registration(self):
        """Validation tools deben registrarse correctamente."""
        register_validation_tools(mcp)
        registered = _get_registered_tool_names(mcp)
        assert EXPECTED_VALIDATION_TOOLS.issubset(registered)

    def test_signal_script_tools_registration(self):
        """Signal & script tools deben registrarse correctamente."""
        register_signal_and_script_tools(mcp)
        registered = _get_registered_tool_names(mcp)
        assert EXPECTED_SIGNAL_SCRIPT_TOOLS.issubset(registered)

    def test_property_tools_registration(self):
        """Property tools deben registrarse correctamente."""
        register_property_tools(mcp)
        registered = _get_registered_tool_names(mcp)
        assert EXPECTED_PROPERTY_TOOLS.issubset(registered)

    def test_debug_tools_registration(self):
        """Debug tools deben registrarse correctamente."""
        register_debug_tools(mcp)
        registered = _get_registered_tool_names(mcp)
        assert EXPECTED_DEBUG_TOOLS.issubset(registered)


class TestToolSchemas:
    """Tests para verificar que las herramientas tienen schemas válidos."""

    def test_tools_have_descriptions(self):
        """Todas las herramientas deben tener descripción."""
        register_all_tools()
        tools = asyncio.run(mcp.list_tools())

        for tool in tools:
            assert tool.description is not None, (
                f"Tool '{tool.name}' has no description"
            )
            assert len(tool.description) > 0, (
                f"Tool '{tool.name}' has empty description"
            )

    def test_create_scene_has_required_params(self):
        """create_scene debe tener los parámetros requeridos."""
        register_all_tools()
        tools = asyncio.run(mcp.list_tools())
        create_tool = next(t for t in tools if t.name == "create_scene")

        # Verificar que tiene parámetros (formato JSON Schema)
        assert create_tool.parameters is not None
        param_names = list(create_tool.parameters.get("properties", {}).keys())
        assert "session_id" in param_names
        assert "project_path" in param_names
        assert "scene_path" in param_names

    def test_add_node_has_required_params(self):
        """add_node debe tener los parámetros requeridos."""
        register_all_tools()
        tools = asyncio.run(mcp.list_tools())
        add_tool = next(t for t in tools if t.name == "add_node")

        assert add_tool.parameters is not None
        param_names = list(add_tool.parameters.get("properties", {}).keys())
        assert "session_id" in param_names
        assert "scene_path" in param_names
        assert "parent_path" in param_names
        assert "node_type" in param_names
        assert "node_name" in param_names
