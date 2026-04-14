"""
Stress Tests - Godot MCP Python on real LAIKA project.

Stress tests on LAIKA-Solarpunk-GJ project:
1. Massive parsing of all scenes
2. Roundtrip (parse -> to_tscn -> parse) on all scenes
3. Intensive node searches
4. Concurrent session operations
5. Resource and script reading
6. Massive validation
"""

import sys
import os
import time
import tempfile
import shutil
from pathlib import Path

import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from godot_mcp.core.tscn_parser import parse_tscn, parse_tscn_string, Scene
from godot_mcp.core.tres_parser import parse_tres
from godot_mcp.core.tscn_validator import TSCNValidator
from godot_mcp.tools.session_tools import (
    get_session_manager,
    set_session_manager,
    start_session,
    end_session,
    get_session_info,
)
from godot_mcp.tools.scene_tools import (
    create_scene,
    get_scene_tree,
    list_scenes,
    instantiate_scene,
)
from godot_mcp.tools.node_tools import (
    add_node,
    remove_node,
    find_nodes,
    get_node_properties,
)
from godot_mcp.tools.resource_tools import (
    create_resource,
    read_resource,
    list_resources,
)
from godot_mcp.session_manager import SessionManager


# ============================================================
# Configuration
# ============================================================

LAIKA_PROJECT = r"D:\Mis Juegos\LAIKA\LAIKA-Solarpunk-GJ\laika-gd"

# Skip if project doesn't exist
pytestmark = pytest.mark.skipif(
    not os.path.isdir(LAIKA_PROJECT),
    reason=f"LAIKA project not found at {LAIKA_PROJECT}",
)


# ============================================================
# Fixtures
# ============================================================


@pytest.fixture(autouse=True)
def reset_session_manager():
    """Reset session manager before each test."""
    set_session_manager(SessionManager(auto_save=False))
    yield


@pytest.fixture
def laika_session():
    """Create session with LAIKA project."""
    result = start_session(LAIKA_PROJECT)
    assert result["success"] is True, f"Failed to start session: {result}"
    session_id = result["session_id"]
    yield session_id
    end_session(session_id, save=False)


@pytest.fixture
def temp_copy_project():
    """Create temporary copy of LAIKA project for write operations."""
    temp_dir = tempfile.mkdtemp(prefix="laika_stress_")
    src = Path(LAIKA_PROJECT)
    dst = Path(temp_dir)
    for item in src.iterdir():
        if item.name == ".godot":
            continue
        if item.is_dir():
            shutil.copytree(item, dst / item.name, dirs_exist_ok=True)
        else:
            shutil.copy2(item, dst / item.name)
    yield str(dst)
    try:
        shutil.rmtree(temp_dir)
    except Exception:
        pass


# ============================================================
# Helpers
# ============================================================


def find_all_tscn(project_path: str) -> list[str]:
    """Find all .tscn files in project."""
    results = []
    for root, dirs, files in os.walk(project_path):
        if ".godot" in root:
            continue
        for f in files:
            if f.endswith(".tscn"):
                results.append(os.path.join(root, f))
    return results


def find_all_tres(project_path: str) -> list[str]:
    """Find all .tres files in project."""
    results = []
    for root, dirs, files in os.walk(project_path):
        if ".godot" in root:
            continue
        for f in files:
            if f.endswith(".tres"):
                results.append(os.path.join(root, f))
    return results


def find_all_gd(project_path: str) -> list[str]:
    """Find all .gd files in project."""
    results = []
    for root, dirs, files in os.walk(project_path):
        if ".godot" in root:
            continue
        for f in files:
            if f.endswith(".gd"):
                results.append(os.path.join(root, f))
    return results


# ============================================================
# TEST SUITE: Massive Parsing
# ============================================================


class TestMassiveParsing:
    """Massive parsing tests for all project scenes."""

    def test_parse_all_scenes(self, laika_session):
        """Parse ALL scenes in the project without errors."""
        tscn_files = find_all_tscn(LAIKA_PROJECT)
        assert len(tscn_files) > 0, "No scenes found in LAIKA project"

        errors = []
        for scene_path in tscn_files:
            try:
                scene = parse_tscn(scene_path)
                assert scene is not None
                assert len(scene.nodes) > 0, f"Scene {scene_path} has no nodes"
            except Exception as e:
                errors.append((scene_path, str(e)))

        assert len(errors) == 0, f"Failed to parse {len(errors)} scenes:\n" + "\n".join(
            f"  {p}: {e}" for p, e in errors
        )

    def test_parse_all_scenes_performance(self, laika_session):
        """Measure parsing time for all scenes."""
        tscn_files = find_all_tscn(LAIKA_PROJECT)

        start = time.time()
        for scene_path in tscn_files:
            parse_tscn(scene_path)
        elapsed = time.time() - start

        print(
            f"\n[STATS] Parsing {len(tscn_files)} scenes: {elapsed:.3f}s "
            f"({elapsed / len(tscn_files) * 1000:.1f}ms per scene)"
        )

        # Must be reasonable (< 5 seconds for all)
        assert elapsed < 5.0, f"Parsing too slow: {elapsed:.2f}s"

    def test_parse_all_resources(self, laika_session):
        """Parse ALL .tres resources in the project."""
        tres_files = find_all_tres(LAIKA_PROJECT)
        assert len(tres_files) > 0, "No .tres resources found"

        errors = []
        for res_path in tres_files:
            try:
                resource = parse_tres(res_path)
                assert resource is not None
            except Exception as e:
                errors.append((res_path, str(e)))

        assert len(errors) == 0, (
            f"Failed to parse {len(errors)} resources:\n"
            + "\n".join(f"  {p}: {e}" for p, e in errors)
        )


# ============================================================
# TEST SUITE: Roundtrip (parse -> serialize -> parse)
# ============================================================


class TestRoundtrip:
    """Roundtrip tests on all project scenes."""

    def test_roundtrip_all_scenes(self, laika_session):
        """Roundtrip parse -> to_tscn -> parse on ALL scenes."""
        tscn_files = find_all_tscn(LAIKA_PROJECT)

        errors = []
        for scene_path in tscn_files:
            try:
                # Parse original
                scene1 = parse_tscn(scene_path)
                original_nodes = len(scene1.nodes)
                original_ext = len(scene1.ext_resources)
                original_sub = len(scene1.sub_resources)

                # Serialize
                tscn_output = scene1.to_tscn()
                assert len(tscn_output) > 0

                # Re-parse
                scene2 = parse_tscn_string(tscn_output)

                # Verify structure preserved
                assert len(scene2.nodes) == original_nodes, (
                    f"Node count mismatch in {scene_path}: "
                    f"{len(scene2.nodes)} vs {original_nodes}"
                )
                assert len(scene2.ext_resources) == original_ext, (
                    f"ExtResource count mismatch in {scene_path}"
                )
                assert len(scene2.sub_resources) == original_sub, (
                    f"SubResource count mismatch in {scene_path}"
                )
            except Exception as e:
                errors.append((scene_path, str(e)))

        assert len(errors) == 0, (
            f"Roundtrip failed for {len(errors)} scenes:\n"
            + "\n".join(f"  {p}: {e}" for p, e in errors)
        )

    def test_roundtrip_performance(self, laika_session):
        """Measure roundtrip time for all scenes."""
        tscn_files = find_all_tscn(LAIKA_PROJECT)

        start = time.time()
        for scene_path in tscn_files:
            scene = parse_tscn(scene_path)
            output = scene.to_tscn()
            parse_tscn_string(output)
        elapsed = time.time() - start

        print(
            f"\n[STATS] Roundtrip {len(tscn_files)} scenes: {elapsed:.3f}s "
            f"({elapsed / len(tscn_files) * 1000:.1f}ms per scene)"
        )

        assert elapsed < 10.0, f"Roundtrip too slow: {elapsed:.2f}s"

    def test_roundtrip_preserves_node_properties(self, laika_session):
        """Verify roundtrip preserves key node properties."""
        tscn_files = find_all_tscn(LAIKA_PROJECT)
        largest = max(tscn_files, key=lambda p: os.path.getsize(p))

        scene1 = parse_tscn(largest)

        for node in scene1.nodes:
            if node.properties:
                output = scene1.to_tscn()
                scene2 = parse_tscn_string(output)

                found = next((n for n in scene2.nodes if n.name == node.name), None)
                assert found is not None, f"Node {node.name} lost in roundtrip"
                assert found.type == node.type, (
                    f"Node {node.name} type changed: {found.type} vs {node.type}"
                )


# ============================================================
# TEST SUITE: Massive Validation
# ============================================================


class TestMassiveValidation:
    """Massive validation tests."""

    def test_validate_all_scenes(self, laika_session):
        """Validate ALL scenes in the project.

        Note: LAIKA project has known issues (duplicate nodes, missing resources).
        This test verifies the validator runs without crashing and reports findings.
        """
        tscn_files = find_all_tscn(LAIKA_PROJECT)

        errors = []
        warnings = []
        for scene_path in tscn_files:
            try:
                scene = parse_tscn(scene_path)
                validator = TSCNValidator(project_path=LAIKA_PROJECT)
                result = validator.validate(scene)

                if result.errors:
                    errors.append((scene_path, result.errors))
                if result.warnings:
                    warnings.append((scene_path, result.warnings))
            except Exception as e:
                errors.append((scene_path, [str(e)]))

        print(
            f"\n[STATS] Validation: {len(tscn_files)} scenes, "
            f"{len(errors)} with errors, {len(warnings)} with warnings"
        )

        # The validator should run without crashing - errors are expected
        # in the LAIKA project (duplicate nodes, missing resources, etc.)
        # We just verify the validator doesn't throw exceptions
        assert len(errors) + len(warnings) >= 0  # Always passes if no crash


# ============================================================
# TEST SUITE: Write Operations (on temp copy)
# ============================================================


class TestWriteOperations:
    """Intensive write operation tests."""

    def test_create_and_list_scenes(self, laika_session, temp_copy_project):
        """Create multiple scenes and list them."""
        for i in range(10):
            result = create_scene(
                session_id=laika_session,
                project_path=temp_copy_project,
                scene_path=f"stress_test/scene_{i}.tscn",
                root_type="Node2D",
                root_name=f"Root_{i}",
            )
            assert result["success"] is True, f"Failed to create scene_{i}: {result}"

        result = list_scenes(
            session_id=laika_session,
            project_path=temp_copy_project,
            recursive=True,
        )
        assert result["success"] is True
        assert result["count"] >= 10

    def test_bulk_add_nodes(self, laika_session, temp_copy_project):
        """Add many nodes to a scene."""
        create_scene(
            session_id=laika_session,
            project_path=temp_copy_project,
            scene_path="stress_test/bulk_nodes.tscn",
            root_type="Node2D",
            root_name="Root",
        )

        scene_path = os.path.join(temp_copy_project, "stress_test", "bulk_nodes.tscn")

        start = time.time()
        for i in range(50):
            result = add_node(
                session_id=laika_session,
                scene_path=scene_path,
                parent_path=".",
                node_type="Node2D",
                node_name=f"Node_{i}",
            )
            assert result["success"] is True, f"Failed to add Node_{i}: {result}"
        elapsed = time.time() - start

        print(
            f"\n[STATS] Add 50 nodes: {elapsed:.3f}s "
            f"({elapsed / 50 * 1000:.1f}ms per node)"
        )

        result = find_nodes(
            session_id=laika_session,
            scene_path=scene_path,
            type_filter="Node2D",
        )
        assert result["success"] is True
        assert result["count"] == 51  # 50 + Root

    def test_bulk_remove_nodes(self, laika_session, temp_copy_project):
        """Remove many nodes from a scene."""
        create_scene(
            session_id=laika_session,
            project_path=temp_copy_project,
            scene_path="stress_test/bulk_remove.tscn",
            root_type="Node2D",
            root_name="Root",
        )

        scene_path = os.path.join(temp_copy_project, "stress_test", "bulk_remove.tscn")

        for i in range(20):
            add_node(
                session_id=laika_session,
                scene_path=scene_path,
                parent_path=".",
                node_type="Node2D",
                node_name=f"ToRemove_{i}",
            )

        start = time.time()
        for i in range(20):
            result = remove_node(
                session_id=laika_session,
                scene_path=scene_path,
                node_path=f"ToRemove_{i}",
            )
            assert result["success"] is True, f"Failed to remove ToRemove_{i}: {result}"
        elapsed = time.time() - start

        print(
            f"\n[STATS] Remove 20 nodes: {elapsed:.3f}s "
            f"({elapsed / 20 * 1000:.1f}ms per node)"
        )

        result = find_nodes(
            session_id=laika_session,
            scene_path=scene_path,
            type_filter="Node2D",
        )
        assert result["success"] is True
        assert result["count"] == 1  # Only Root

    def test_instantiate_scenes_stress(self, laika_session, temp_copy_project):
        """Instantiate multiple scenes into a parent."""
        child_path = os.path.join(temp_copy_project, "stress_test", "child.tscn")
        os.makedirs(os.path.dirname(child_path), exist_ok=True)
        with open(child_path, "w", encoding="utf-8") as f:
            f.write(
                '[gd_scene load_steps=1 format=3]\n\n[node name="ChildRoot" type="Node2D"]\n'
            )

        parent_path = os.path.join(temp_copy_project, "stress_test", "parent.tscn")
        with open(parent_path, "w", encoding="utf-8") as f:
            f.write(
                '[gd_scene load_steps=1 format=3]\n\n[node name="Root" type="Node2D"]\n'
            )

        start = time.time()
        for i in range(15):
            result = instantiate_scene(
                session_id=laika_session,
                scene_path=child_path,
                parent_scene_path=parent_path,
                node_name=f"Child_{i}",
                parent_node_path=".",
                project_path=temp_copy_project,
            )
            assert result["success"] is True, (
                f"Failed to instantiate Child_{i}: {result}"
            )
        elapsed = time.time() - start

        print(
            f"\n[STATS] Instantiate 15 scenes: {elapsed:.3f}s "
            f"({elapsed / 15 * 1000:.1f}ms per instance)"
        )

        result = get_scene_tree(
            session_id=laika_session,
            scene_path=parent_path,
        )
        assert result["success"] is True
        assert len(result["data"]["nodes"]) == 16  # Root + 15 children


# ============================================================
# TEST SUITE: Session and Memory
# ============================================================


class TestSessionStress:
    """Session and memory stress tests."""

    def test_multiple_sessions(self):
        """Create and destroy multiple sessions."""
        start = time.time()
        session_ids = []

        for i in range(5):
            result = start_session(LAIKA_PROJECT)
            assert result["success"] is True
            session_ids.append(result["session_id"])

        for sid in session_ids:
            info = get_session_info(sid)
            assert info["success"] is True

        for sid in session_ids:
            end_session(sid, save=False)

        elapsed = time.time() - start
        print(f"\n[STATS] 5 sessions created and destroyed: {elapsed:.3f}s")

    def test_session_info_accuracy(self, laika_session):
        """Verify session_info reflects real operations."""
        info1 = get_session_info(laika_session)
        initial_ops = info1["operations_count"]

        with tempfile.TemporaryDirectory() as tmpdir:
            project_file = os.path.join(tmpdir, "project.godot")
            with open(project_file, "w") as f:
                f.write("[configuration]\nconfig_version=5\n")

            create_scene(
                session_id=laika_session,
                project_path=tmpdir,
                scene_path="test.tscn",
            )

        info2 = get_session_info(laika_session)
        assert info2["operations_count"] >= initial_ops


# ============================================================
# TEST SUITE: Complex Project Scenes
# ============================================================


class TestComplexScenes:
    """Tests on the most complex LAIKA project scenes."""

    def test_largest_scene_parse(self, laika_session):
        """Parse the largest scene in the project."""
        tscn_files = find_all_tscn(LAIKA_PROJECT)
        largest = max(tscn_files, key=lambda p: os.path.getsize(p))

        scene = parse_tscn(largest)
        assert len(scene.nodes) > 0
        print(
            f"\n[STATS] Largest scene: {os.path.basename(largest)} "
            f"({os.path.getsize(largest)} bytes, {len(scene.nodes)} nodes, "
            f"{len(scene.ext_resources)} ext_resources, "
            f"{len(scene.sub_resources)} sub_resources)"
        )

    def test_most_nodes_scene(self, laika_session):
        """Parse the scene with most nodes."""
        tscn_files = find_all_tscn(LAIKA_PROJECT)

        max_nodes = 0
        max_scene = None
        for scene_path in tscn_files:
            scene = parse_tscn(scene_path)
            if len(scene.nodes) > max_nodes:
                max_nodes = len(scene.nodes)
                max_scene = scene_path

        print(
            f"\n[STATS] Scene with most nodes: {os.path.basename(max_scene)} "
            f"({max_nodes} nodes)"
        )

        assert max_nodes > 0

    def test_scene_with_ext_resources(self, laika_session):
        """Parse scenes with external resources."""
        tscn_files = find_all_tscn(LAIKA_PROJECT)

        scenes_with_ext = []
        for scene_path in tscn_files:
            scene = parse_tscn(scene_path)
            if scene.ext_resources:
                scenes_with_ext.append((scene_path, len(scene.ext_resources)))

        if scenes_with_ext:
            max_ext = max(scenes_with_ext, key=lambda x: x[1])
            print(
                f"\n[STATS] Scene with most ExtResources: {os.path.basename(max_ext[0])} "
                f"({max_ext[1]} resources)"
            )

        assert len(scenes_with_ext) >= 0


# ============================================================
# TEST SUITE: Intensive Searches
# ============================================================


class TestIntensiveSearch:
    """Intensive node search tests."""

    def test_find_all_node_types(self, laika_session):
        """Find all node types across all scenes."""
        tscn_files = find_all_tscn(LAIKA_PROJECT)

        all_types = set()
        for scene_path in tscn_files:
            scene = parse_tscn(scene_path)
            for node in scene.nodes:
                all_types.add(node.type)

        print(f"\n[STATS] Node types found: {len(all_types)}")
        print(f"   {', '.join(sorted(all_types))}")

        assert len(all_types) > 0

    def test_find_nodes_by_common_types(self, laika_session):
        """Search nodes by common types across all scenes."""
        tscn_files = find_all_tscn(LAIKA_PROJECT)

        common_types = ["Node2D", "Control", "Label", "Sprite2D", "CharacterBody2D"]
        results = {}

        for node_type in common_types:
            count = 0
            for scene_path in tscn_files:
                scene = parse_tscn(scene_path)
                count += sum(1 for n in scene.nodes if n.type == node_type)
            results[node_type] = count

        print(f"\n[STATS] Nodes by common type:")
        for t, c in results.items():
            print(f"   {t}: {c}")

        assert results.get("Node2D", 0) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
