"""
Tests for session_tools module.

Tests:
1. start_session - success, invalid directory, not godot project
2. end_session - success, save changes, not found
3. get_active_session - with active, without active
4. list_sessions - multiple sessions, empty
5. get_session_info - success, not found
6. commit_session - commit one, commit all
7. discard_changes - discard one, discard all
8. SessionContext - load, commit, unload
9. require_session decorator - valid, invalid, empty
"""

import sys
import os
import tempfile
from unittest.mock import patch

import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from godot_mcp.tools.session_tools import (
    get_session_manager,
    set_session_manager,
    start_session,
    end_session,
    get_active_session,
    list_sessions,
    get_session_info,
    commit_session,
    discard_changes,
    SessionContext,
    require_session,
)
from godot_mcp.session_manager import SessionManager


# ============ FIXTURES ============


@pytest.fixture(autouse=True)
def reset_session_manager():
    """Reset session manager before each test."""
    set_session_manager(SessionManager(auto_save=False))
    yield


@pytest.fixture
def temp_project():
    """Create a temporary Godot project directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_file = os.path.join(tmpdir, "project.godot")
        with open(project_file, "w", encoding="utf-8") as f:
            f.write("""[configuration]
config_version=5

[application]
config/name="TestProject"
config/features=PackedStringArray("4.6")
""")
        yield tmpdir


# ============ TEST SUITE: START_SESSION ============


class TestStartSession:
    """Tests for start_session function."""

    def test_start_session_success(self, temp_project):
        """Test starting a session successfully."""
        result = start_session(temp_project)
        assert result["success"] is True
        assert "session_id" in result
        assert result["project_path"] == temp_project

    def test_start_session_invalid_directory(self):
        """Test starting session with invalid directory fails."""
        result = start_session("/nonexistent/path")
        assert result["success"] is False
        assert "no encontrado" in result["error"]

    def test_start_session_not_godot_project(self, tmp_path):
        """Test starting session in non-Godot project fails."""
        result = start_session(str(tmp_path))
        assert result["success"] is False
        assert "project.godot" in result["error"]

    def test_start_session_reuses_existing(self, temp_project):
        """Test that starting session for same project returns same ID."""
        result1 = start_session(temp_project)
        result2 = start_session(temp_project)
        assert result1["session_id"] == result2["session_id"]


# ============ TEST SUITE: END_SESSION ============


class TestEndSession:
    """Tests for end_session function."""

    def test_end_session_success(self, temp_project):
        """Test ending a session successfully."""
        start_result = start_session(temp_project)
        session_id = start_result["session_id"]

        result = end_session(session_id, save=False)
        assert result["success"] is True
        assert result["session_id"] == session_id

    def test_end_session_not_found(self):
        """Test ending non-existent session fails."""
        result = end_session("nonexistent_session", save=False)
        assert result["success"] is False
        assert "no encontrada" in result["error"]

    def test_end_session_with_save(self, temp_project):
        """Test ending session with save=True."""
        start_result = start_session(temp_project)
        session_id = start_result["session_id"]

        result = end_session(session_id, save=True)
        assert result["success"] is True
        assert result["saved"] is True


# ============ TEST SUITE: GET_ACTIVE_SESSION ============


class TestGetActiveSession:
    """Tests for get_active_session function."""

    def test_get_active_session_with_session(self, temp_project):
        """Test getting active session when one exists."""
        start_session(temp_project)

        result = get_active_session()
        assert result["success"] is True
        # When there IS an active session, the response has session_id key
        # (not active_session which is only used when there's NO session)
        assert "session_id" in result
        assert result["session_id"] is not None

    def test_get_active_session_no_session(self):
        """Test getting active session when none exists."""
        result = get_active_session()
        assert result["success"] is True
        assert result["active_session"] is None


# ============ TEST SUITE: LIST_SESSIONS ============


class TestListSessions:
    """Tests for list_sessions function."""

    def test_list_sessions_empty(self):
        """Test listing sessions when none exist."""
        result = list_sessions()
        assert result["success"] is True
        assert result["count"] == 0
        assert result["sessions"] == []

    def test_list_sessions_multiple(self, temp_project):
        """Test listing multiple sessions."""
        # Create sessions for different projects
        with tempfile.TemporaryDirectory() as project2:
            project_file = os.path.join(project2, "project.godot")
            with open(project_file, "w", encoding="utf-8") as f:
                f.write("[configuration]\nconfig_version=5\n")

            start_session(temp_project)
            start_session(project2)

            result = list_sessions()
            assert result["success"] is True
            assert result["count"] == 2


# ============ TEST SUITE: GET_SESSION_INFO ============


class TestGetSessionInfo:
    """Tests for get_session_info function."""

    def test_get_session_info_success(self, temp_project):
        """Test getting session info successfully."""
        start_result = start_session(temp_project)
        session_id = start_result["session_id"]

        result = get_session_info(session_id)
        assert result["success"] is True
        assert result["session_id"] == session_id
        assert result["project_path"] == temp_project
        assert "created_at" in result
        assert "modified_at" in result

    def test_get_session_info_not_found(self):
        """Test getting info for non-existent session fails."""
        result = get_session_info("nonexistent_session")
        assert result["success"] is False
        assert "no encontrada" in result["error"]


# ============ TEST SUITE: COMMIT_SESSION ============


class TestCommitSession:
    """Tests for commit_session function."""

    def test_commit_session_not_found(self):
        """Test committing non-existent session fails."""
        result = commit_session("nonexistent_session")
        assert result["success"] is False

    def test_commit_session_all_no_dirty(self, temp_project):
        """Test committing session with no dirty scenes."""
        start_result = start_session(temp_project)
        session_id = start_result["session_id"]

        result = commit_session(session_id)
        assert result["success"] is True
        assert result["saved_count"] == 0

    def test_commit_session_specific_scene(self, temp_project):
        """Test committing a specific scene."""
        start_result = start_session(temp_project)
        session_id = start_result["session_id"]

        # Create a scene file and mark it dirty
        scene_path = os.path.join(temp_project, "test.tscn")
        with open(scene_path, "w", encoding="utf-8") as f:
            f.write(
                '[gd_scene load_steps=1 format=3]\n\n[node name="Root" type="Node2D"]\n'
            )

        manager = get_session_manager()
        manager.mark_scene_dirty(session_id, scene_path)

        # Commit specific scene
        result = commit_session(session_id, scene_path=scene_path)
        assert result["success"] is True
        assert result["scene_path"] == scene_path

        # Verify scene is no longer dirty
        info = get_session_info(session_id)
        assert scene_path not in info["dirty_scenes"]


# ============ TEST SUITE: DISCARD_CHANGES ============


class TestDiscardChanges:
    """Tests for discard_changes function."""

    def test_discard_changes_not_found(self):
        """Test discarding changes for non-existent session fails."""
        result = discard_changes("nonexistent_session")
        assert result["success"] is False

    def test_discard_changes_all(self, temp_project):
        """Test discarding all changes."""
        start_result = start_session(temp_project)
        session_id = start_result["session_id"]

        # Create scene files and mark them dirty
        for name in ["scene1.tscn", "scene2.tscn"]:
            scene_path = os.path.join(temp_project, name)
            with open(scene_path, "w", encoding="utf-8") as f:
                f.write("[gd_scene load_steps=1 format=3]\n")
            manager = get_session_manager()
            manager.mark_scene_dirty(session_id, scene_path)

        # Discard all
        result = discard_changes(session_id)
        assert result["success"] is True
        assert result["discarded_count"] == 2

    def test_discard_changes_specific(self, temp_project):
        """Test discarding changes for a specific scene."""
        start_result = start_session(temp_project)
        session_id = start_result["session_id"]

        scene_path = os.path.join(temp_project, "test.tscn")
        with open(scene_path, "w", encoding="utf-8") as f:
            f.write("[gd_scene load_steps=1 format=3]\n")

        manager = get_session_manager()
        manager.mark_scene_dirty(session_id, scene_path)

        # Discard specific scene
        result = discard_changes(session_id, scene_path=scene_path)
        assert result["success"] is True
        assert result["scene_path"] == scene_path


# ============ TEST SUITE: SESSION_CONTEXT ============


class TestSessionContext:
    """Tests for SessionContext class."""

    def test_session_context_enter_exit(self, temp_project):
        """Test SessionContext enter and exit."""
        start_result = start_session(temp_project)
        session_id = start_result["session_id"]

        with SessionContext(session_id) as ctx:
            assert ctx.session_id == session_id
            assert ctx.project_path == temp_project

    def test_session_context_invalid_session(self):
        """Test SessionContext with invalid session raises error."""
        with pytest.raises(ValueError):
            with SessionContext("nonexistent_session"):
                pass

    def test_session_context_properties(self, temp_project):
        """Test SessionContext property access."""
        start_result = start_session(temp_project)
        session_id = start_result["session_id"]

        with SessionContext(session_id) as ctx:
            assert isinstance(ctx.loaded_scenes, dict)
            assert isinstance(ctx.dirty_scenes, set)


# ============ TEST SUITE: REQUIRE_SESSION DECORATOR ============


class TestRequireSessionDecorator:
    """Tests for @require_session decorator."""

    def test_require_session_valid(self, temp_project):
        """Test decorator with valid session."""
        start_result = start_session(temp_project)
        session_id = start_result["session_id"]

        @require_session
        def dummy_tool(session_id: str) -> dict:
            return {"success": True}

        result = dummy_tool(session_id)
        assert result["success"] is True

    def test_require_session_empty(self):
        """Test decorator with empty session_id."""

        @require_session
        def dummy_tool(session_id: str) -> dict:
            return {"success": True}

        result = dummy_tool("")
        assert result["success"] is False
        assert "requerido" in result["error"]

    def test_require_session_not_found(self):
        """Test decorator with non-existent session."""

        @require_session
        def dummy_tool(session_id: str) -> dict:
            return {"success": True}

        result = dummy_tool("nonexistent_session")
        assert result["success"] is False
        assert "no encontrada" in result["error"]

    def test_require_session_with_kwargs(self, temp_project):
        """Test decorator with session_id in kwargs."""
        start_result = start_session(temp_project)
        session_id = start_result["session_id"]

        @require_session
        def dummy_tool(session_id: str, other_param: str = "default") -> dict:
            return {"success": True, "other": other_param}

        result = dummy_tool(session_id=session_id, other_param="test")
        assert result["success"] is True
        assert result["other"] == "test"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
