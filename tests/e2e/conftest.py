"""Fixtures compartidos para tests E2E."""

import os
import sys
import tempfile
import shutil
import pytest

# Agregar src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from godot_mcp.session_manager import SessionManager
from godot_mcp.tools.session_tools import (
    start_session,
    end_session,
    set_session_manager,
)


@pytest.fixture(autouse=True)
def reset_session_manager():
    """Resetear session manager antes de cada test."""
    set_session_manager(SessionManager(auto_save=False))
    yield


@pytest.fixture
def temp_project():
    """Crear un proyecto Godot mínimo temporal."""
    tmpdir = tempfile.mkdtemp()
    project_file = os.path.join(tmpdir, "project.godot")
    with open(project_file, "w", encoding="utf-8") as f:
        f.write("""[configuration]
config_version=5

[application]
config/name="E2ETestProject"
config/features=PackedStringArray("4.6")
""")
    yield tmpdir
    # Cleanup: end_session si existe
    try:
        from godot_mcp.tools.session_tools import get_active_session

        active = get_active_session()
        if active and active.get("success"):
            end_session(active["session_id"], save=False, confirmed=True)
    except Exception:
        pass
    shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.fixture
def session_id(temp_project):
    """Iniciar sesión con el proyecto temporal."""
    result = start_session(temp_project)
    assert result["success"] is True, f"Failed to start session: {result}"
    yield result["session_id"]
    # Cleanup
    try:
        end_session(result["session_id"], save=False, confirmed=True)
    except Exception:
        pass
