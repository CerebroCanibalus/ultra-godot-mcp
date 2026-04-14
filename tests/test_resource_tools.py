"""
Tests for resource_tools module.

Tests:
1. create_resource - success, duplicate, with properties
2. read_resource - success, cache hit/miss, not found, invalid extension
3. update_resource - success, not found, invalid extension
4. get_uid - success, not found, generate if missing
5. update_project_uids - success, invalid project
6. list_resources - recursive, filter by type, empty project
"""

import sys
import os
import tempfile

import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from godot_mcp.tools.resource_tools import (
    create_resource,
    read_resource,
    update_resource,
    get_uid,
    update_project_uids,
    list_resources,
)
from godot_mcp.tools.session_tools import (
    get_session_manager,
    set_session_manager,
    start_session,
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


@pytest.fixture
def session_id(temp_project):
    """Create a real session for testing."""
    result = start_session(temp_project)
    assert result["success"] is True
    return result["session_id"]


@pytest.fixture
def existing_resource(temp_project):
    """Create an existing .tres resource file."""
    resource_path = os.path.join(temp_project, "test_resource.tres")
    with open(resource_path, "w", encoding="utf-8") as f:
        f.write("""[gd_resource type="Resource" load_steps=1 format=3 uid="uid://test123"]

resource_name = "TestResource"
value = 42
""")
    return resource_path


# ============ TEST SUITE: CREATE_RESOURCE ============


class TestCreateResource:
    """Tests for create_resource function."""

    def test_create_resource_success(self, session_id, temp_project):
        """Test creating a new resource successfully."""
        resource_path = os.path.join(temp_project, "new_resource.tres")
        result = create_resource(
            session_id=session_id,
            resource_path=resource_path,
            resource_type="Resource",
        )
        assert result["success"] is True
        assert result["resource_path"] == resource_path
        assert result["resource_type"] == "Resource"
        assert "uid" in result

        # Verify file was created
        assert os.path.exists(resource_path)

    def test_create_resource_with_properties(self, session_id, temp_project):
        """Test creating resource with properties."""
        resource_path = os.path.join(temp_project, "prop_resource.tres")
        result = create_resource(
            session_id=session_id,
            resource_path=resource_path,
            resource_type="Resource",
            properties={"resource_name": "MyResource", "value": 100},
        )
        assert result["success"] is True
        assert result["properties"]["resource_name"] == "MyResource"

        # Verify properties in file
        with open(resource_path, "r", encoding="utf-8") as f:
            content = f.read()
        assert "resource_name" in content
        assert "MyResource" in content

    def test_create_resource_duplicate_fails(self, session_id, existing_resource):
        """Test that creating duplicate resource fails."""
        result = create_resource(
            session_id=session_id,
            resource_path=existing_resource,
            resource_type="Resource",
        )
        assert result["success"] is False
        assert "already exists" in result["error"]

    def test_create_resource_empty_path(self, session_id, temp_project):
        """Test creating resource with empty path fails."""
        result = create_resource(
            session_id=session_id,
            resource_path="",
            resource_type="Resource",
        )
        assert result["success"] is False
        assert "cannot be empty" in result["error"]

    def test_create_resource_adds_tres_extension(self, session_id, temp_project):
        """Test that .tres extension is added if missing."""
        resource_path = os.path.join(temp_project, "no_extension")
        result = create_resource(
            session_id=session_id,
            resource_path=resource_path,
            resource_type="Resource",
        )
        assert result["success"] is True
        assert result["resource_path"].endswith(".tres")
        assert os.path.exists(resource_path + ".tres")

    def test_create_resource_creates_directories(self, session_id, temp_project):
        """Test that parent directories are created if needed."""
        resource_path = os.path.join(temp_project, "sub", "dir", "resource.tres")
        result = create_resource(
            session_id=session_id,
            resource_path=resource_path,
            resource_type="Resource",
        )
        assert result["success"] is True
        assert os.path.exists(resource_path)


# ============ TEST SUITE: READ_RESOURCE ============


class TestReadResource:
    """Tests for read_resource function."""

    def test_read_resource_success(self, session_id, existing_resource):
        """Test reading a resource successfully."""
        result = read_resource(
            session_id=session_id,
            resource_path=existing_resource,
        )
        assert result["success"] is True
        assert result["data"]["header"]["type"] == "Resource"
        assert result["data"]["properties"]["resource_name"] == "TestResource"
        assert result["data"]["properties"]["value"] == 42

    def test_read_resource_not_found(self, session_id, temp_project):
        """Test reading non-existent resource fails."""
        result = read_resource(
            session_id=session_id,
            resource_path=os.path.join(temp_project, "nonexistent.tres"),
        )
        assert result["success"] is False
        assert "not found" in result["error"]

    def test_read_resource_invalid_extension(self, session_id, temp_project):
        """Test reading file with invalid extension fails."""
        # Create a non-.tres file
        file_path = os.path.join(temp_project, "test.txt")
        with open(file_path, "w") as f:
            f.write("not a resource")

        result = read_resource(
            session_id=session_id,
            resource_path=file_path,
        )
        assert result["success"] is False
        assert ".tres" in result["error"].lower()

    def test_read_resource_cache_hit(self, session_id, existing_resource):
        """Test that second read returns cached result."""
        # First read - cache miss
        result1 = read_resource(
            session_id=session_id,
            resource_path=existing_resource,
        )
        assert result1["success"] is True
        assert result1["from_cache"] is False

        # Second read - cache hit
        result2 = read_resource(
            session_id=session_id,
            resource_path=existing_resource,
        )
        assert result2["success"] is True
        assert result2["from_cache"] is True


# ============ TEST SUITE: UPDATE_RESOURCE ============


class TestUpdateResource:
    """Tests for update_resource function."""

    def test_update_resource_success(self, session_id, existing_resource):
        """Test updating a resource successfully."""
        result = update_resource(
            session_id=session_id,
            resource_path=existing_resource,
            properties={"value": 999, "new_prop": "hello"},
        )
        assert result["success"] is True
        assert "value" in result["updated_properties"]
        assert "new_prop" in result["updated_properties"]

        # Verify changes persisted
        read_result = read_resource(
            session_id=session_id,
            resource_path=existing_resource,
        )
        assert read_result["data"]["properties"]["value"] == 999
        assert read_result["data"]["properties"]["new_prop"] == "hello"

    def test_update_resource_not_found(self, session_id, temp_project):
        """Test updating non-existent resource fails."""
        result = update_resource(
            session_id=session_id,
            resource_path=os.path.join(temp_project, "nonexistent.tres"),
            properties={"value": 1},
        )
        assert result["success"] is False

    def test_update_resource_invalid_extension(self, session_id, temp_project):
        """Test updating file with invalid extension fails."""
        file_path = os.path.join(temp_project, "test.txt")
        with open(file_path, "w") as f:
            f.write("not a resource")

        result = update_resource(
            session_id=session_id,
            resource_path=file_path,
            properties={"value": 1},
        )
        assert result["success"] is False
        assert ".tres" in result["error"].lower()


# ============ TEST SUITE: GET_UID ============


class TestGetUid:
    """Tests for get_uid function."""

    def test_get_uid_success(self, session_id, existing_resource):
        """Test getting UID from resource with UID."""
        result = get_uid(
            session_id=session_id,
            resource_path=existing_resource,
        )
        assert result["success"] is True
        assert result["uid"] == "uid://test123"

    def test_get_uid_not_found(self, session_id, temp_project):
        """Test getting UID from non-existent resource fails."""
        result = get_uid(
            session_id=session_id,
            resource_path=os.path.join(temp_project, "nonexistent.tres"),
        )
        assert result["success"] is False

    def test_get_uid_generate_if_missing(self, session_id, temp_project):
        """Test that UID is generated if resource has none."""
        # Create resource without UID
        resource_path = os.path.join(temp_project, "no_uid.tres")
        with open(resource_path, "w", encoding="utf-8") as f:
            f.write(
                '[gd_resource type="Resource" format=3]\n\nresource_name = "Test"\n'
            )

        result = get_uid(
            session_id=session_id,
            resource_path=resource_path,
        )
        assert result["success"] is True
        assert result["generated"] is True
        assert result["uid"].startswith("uid://")


# ============ TEST SUITE: UPDATE_PROJECT_UIDS ============


class TestUpdateProjectUids:
    """Tests for update_project_uids function."""

    def test_update_project_uids_success(self, session_id, temp_project):
        """Test updating UIDs for a project."""
        # Create a resource without UID
        resource_path = os.path.join(temp_project, "no_uid.tres")
        with open(resource_path, "w", encoding="utf-8") as f:
            f.write(
                '[gd_resource type="Resource" format=3]\n\nresource_name = "Test"\n'
            )

        result = update_project_uids(
            session_id=session_id,
            project_path=temp_project,
        )
        assert result["success"] is True
        assert result["total_tres_files"] >= 1
        assert result["uids_updated"] >= 1

    def test_update_project_uids_invalid_project(self, session_id):
        """Test updating UIDs for invalid project fails."""
        result = update_project_uids(
            session_id=session_id,
            project_path="/nonexistent/path",
        )
        assert result["success"] is False

    def test_update_project_uids_no_project_godot(self, session_id, tmp_path):
        """Test updating UIDs for directory without project.godot fails."""
        result = update_project_uids(
            session_id=session_id,
            project_path=str(tmp_path),
        )
        assert result["success"] is False
        assert "no project.godot" in result["error"]


# ============ TEST SUITE: LIST_RESOURCES ============


class TestListResources:
    """Tests for list_resources function."""

    def test_list_resources_recursive(self, session_id, temp_project):
        """Test listing resources recursively."""
        # Create resources in different directories
        os.makedirs(os.path.join(temp_project, "resources"))
        for name in ["a.tres", "b.tres", "resources/c.tres"]:
            full_path = os.path.join(temp_project, name)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write('[gd_resource type="Resource" format=3]\n\n')

        result = list_resources(
            session_id=session_id,
            project_path=temp_project,
            recursive=True,
        )
        assert result["success"] is True
        assert result["count"] == 3

    def test_list_resources_non_recursive(self, session_id, temp_project):
        """Test listing resources only in root."""
        # Create resource in root
        with open(os.path.join(temp_project, "root.tres"), "w", encoding="utf-8") as f:
            f.write('[gd_resource type="Resource" format=3]\n\n')

        # Create resource in subdirectory
        os.makedirs(os.path.join(temp_project, "sub"))
        with open(
            os.path.join(temp_project, "sub", "nested.tres"), "w", encoding="utf-8"
        ) as f:
            f.write('[gd_resource type="Resource" format=3]\n\n')

        result = list_resources(
            session_id=session_id,
            project_path=temp_project,
            recursive=False,
        )
        assert result["success"] is True
        assert result["count"] == 1  # Only root.tres

    def test_list_resources_filter_by_type(self, session_id, temp_project):
        """Test listing resources filtered by type."""
        # Create resources with different types
        with open(
            os.path.join(temp_project, "resource.tres"), "w", encoding="utf-8"
        ) as f:
            f.write('[gd_resource type="Resource" format=3]\n\n')
        with open(
            os.path.join(temp_project, "physics.tres"), "w", encoding="utf-8"
        ) as f:
            f.write('[gd_resource type="PhysicsMaterial" format=3]\n\n')

        result = list_resources(
            session_id=session_id,
            project_path=temp_project,
            resource_type="PhysicsMaterial",
        )
        assert result["success"] is True
        assert result["count"] == 1

    def test_list_resources_empty_project(self, session_id, temp_project):
        """Test listing resources in empty project."""
        result = list_resources(
            session_id=session_id,
            project_path=temp_project,
        )
        assert result["success"] is True
        assert result["count"] == 0

    def test_list_resources_invalid_project(self, session_id):
        """Test listing resources in invalid project."""
        result = list_resources(
            session_id=session_id,
            project_path="/nonexistent/path",
        )
        assert result["success"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
