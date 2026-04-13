"""
Session Manager for Godot MCP
Lightweight session management without WebSocket/Bridge
"""

import json
import os
import threading
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Operation:
    """Represents a single operation for undo/redo history"""

    id: str
    timestamp: datetime
    operation_type: str  # "create", "edit", "delete", "save", "open", etc.
    target: str  # Scene path, node path, etc.
    description: str
    data: Dict[str, Any]  # Additional data for the operation
    result: str  # "success", "failed", "cancelled"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "operation_type": self.operation_type,
            "target": self.target,
            "description": self.description,
            "data": self.data,
            "result": self.result,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Operation":
        return cls(
            id=data["id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            operation_type=data["operation_type"],
            target=data["target"],
            description=data["description"],
            data=data.get("data", {}),
            result=data["result"],
        )


@dataclass
class Session:
    """Represents a Godot project session"""

    id: str
    project_path: str
    created_at: datetime
    modified_at: datetime
    open_scenes: List[str] = field(default_factory=list)
    operation_history: List[Operation] = field(default_factory=list)
    cache: Dict[str, Any] = field(default_factory=dict)  # Shared cache
    active_scene: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    # Nuevos campos para workspace en memoria
    loaded_scenes: Dict[str, "Scene"] = field(
        default_factory=dict
    )  # Scene parseadas en memoria
    dirty_scenes: set = field(
        default_factory=set
    )  # Escenas modificadas pendientes de guardar

    def to_dict(self) -> Dict[str, Any]:
        # Nota: loaded_scenes no se serializa (contiene objetos Scene en memoria)
        return {
            "id": self.id,
            "project_path": self.project_path,
            "created_at": self.created_at.isoformat(),
            "modified_at": self.modified_at.isoformat(),
            "open_scenes": self.open_scenes,
            "operation_history": [op.to_dict() for op in self.operation_history],
            "cache": self.cache,
            "active_scene": self.active_scene,
            "metadata": self.metadata,
            "dirty_scenes": list(self.dirty_scenes),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Session":
        return cls(
            id=data["id"],
            project_path=data["project_path"],
            created_at=datetime.fromisoformat(data["created_at"]),
            modified_at=datetime.fromisoformat(data["modified_at"]),
            open_scenes=data.get("open_scenes", []),
            operation_history=[
                Operation.from_dict(op) for op in data.get("operation_history", [])
            ],
            cache=data.get("cache", {}),
            active_scene=data.get("active_scene"),
            metadata=data.get("metadata", {}),
            loaded_scenes={},  # No restaurar objetos en memoria
            dirty_scenes=set(data.get("dirty_scenes", [])),
        )

    def mark_modified(self):
        """Update the modified_at timestamp"""
        self.modified_at = datetime.now()

    def add_open_scene(self, scene_path: str):
        """Add a scene to the list of open scenes"""
        if scene_path not in self.open_scenes:
            self.open_scenes.append(scene_path)
            self.active_scene = scene_path
            self.mark_modified()

    def remove_open_scene(self, scene_path: str):
        """Remove a scene from the list of open scenes"""
        if scene_path in self.open_scenes:
            self.open_scenes.remove(scene_path)
            if self.active_scene == scene_path:
                self.active_scene = self.open_scenes[-1] if self.open_scenes else None
            self.mark_modified()

    def set_active_scene(self, scene_path: str):
        """Set the active scene"""
        if scene_path in self.open_scenes or scene_path is None:
            self.active_scene = scene_path
            self.mark_modified()


class SessionManager:
    """
    Lightweight session manager for Godot MCP projects.
    Thread-safe and optionally persists to disk.

    NEW: Soporta workspace en memoria con lazy loading y dirty tracking.
    """

    def __init__(self, persistence_path: Optional[str] = None, auto_save: bool = True):
        """
        Initialize the session manager.

        Args:
            persistence_path: Optional path to save/load session data as JSON
            auto_save: Whether to automatically persist changes to disk
        """
        self._sessions: Dict[str, Session] = {}
        self._active_project: Optional[str] = None
        self._lock = threading.RLock()
        self._persistence_path = persistence_path
        self._auto_save = auto_save

        # File locks para concurrencia por archivo
        self._file_locks: Dict[str, threading.Lock] = {}
        self._file_locks_lock = threading.Lock()

        # Load existing sessions if persistence is configured
        if persistence_path and os.path.exists(persistence_path):
            self._load_from_disk()

    def _get_file_lock(self, file_path: str) -> threading.Lock:
        """Obtiene un lock para un archivo específico."""
        with self._file_locks_lock:
            if file_path not in self._file_locks:
                self._file_locks[file_path] = threading.Lock()
            return self._file_locks[file_path]

    def _load_from_disk(self):
        """Load sessions from disk"""
        try:
            with open(self._persistence_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self._active_project = data.get("active_project")
                for session_data in data.get("sessions", []):
                    session = Session.from_dict(session_data)
                    self._sessions[session.id] = session
            logger.info(
                f"Loaded {len(self._sessions)} sessions from {self._persistence_path}"
            )
        except Exception as e:
            logger.error(f"Failed to load sessions from disk: {e}")

    def _save_to_disk(self):
        """Save sessions to disk"""
        if not self._persistence_path:
            return

        try:
            data = {
                "active_project": self._active_project,
                "sessions": [session.to_dict() for session in self._sessions.values()],
            }
            # Ensure directory exists
            Path(self._persistence_path).parent.mkdir(parents=True, exist_ok=True)
            with open(self._persistence_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            logger.info(
                f"Saved {len(self._sessions)} sessions to {self._persistence_path}"
            )
        except Exception as e:
            logger.error(f"Failed to save sessions to disk: {e}")

    def _generate_session_id(self) -> str:
        """Generate a unique session ID"""
        return f"session_{uuid.uuid4().hex[:12]}"

    # ==================== Public API ====================

    def create_session(self, project_path: str) -> str:
        """
        Create a new session for a project.

        Args:
            project_path: Path to the Godot project

        Returns:
            session_id: The ID of the created session
        """
        with self._lock:
            # Check if a session for this project already exists
            existing_session = self._find_session_by_project(project_path)
            if existing_session:
                logger.info(f"Session already exists for project: {project_path}")
                return existing_session.id

            # Create new session
            session_id = self._generate_session_id()
            now = datetime.now()

            session = Session(
                id=session_id,
                project_path=project_path,
                created_at=now,
                modified_at=now,
                open_scenes=[],
                operation_history=[],
                cache={},
            )

            self._sessions[session_id] = session

            # Set as active project if none exists
            if self._active_project is None:
                self._active_project = project_path

            # Persist if enabled
            if self._auto_save and self._persistence_path:
                self._save_to_disk()

            logger.info(f"Created session {session_id} for project: {project_path}")
            return session_id

    def get_session(self, session_id: str) -> Optional[Session]:
        """
        Get a session by ID.

        Args:
            session_id: The session ID

        Returns:
            Session object or None if not found
        """
        with self._lock:
            return self._sessions.get(session_id)

    def get_session_by_project(self, project_path: str) -> Optional[Session]:
        """
        Get a session by project path.

        Args:
            project_path: Path to the Godot project

        Returns:
            Session object or None if not found
        """
        with self._lock:
            return self._find_session_by_project(project_path)

    def _find_session_by_project(self, project_path: str) -> Optional[Session]:
        """Internal method to find session by project path"""
        for session in self._sessions.values():
            if session.project_path == project_path:
                return session
        return None

    def close_session(self, session_id: str, save: bool = True) -> bool:
        """
        Close a session.

        Args:
            session_id: The session ID to close
            save: Whether to save the session state to disk

        Returns:
            True if session was closed, False if not found
        """
        with self._lock:
            if session_id not in self._sessions:
                logger.warning(f"Session {session_id} not found")
                return False

            session = self._sessions[session_id]
            project_path = session.project_path

            # Remove the session
            del self._sessions[session_id]

            # Update active project if needed
            if self._active_project == project_path:
                # Find another session for this project or clear
                remaining = [
                    s for s in self._sessions.values() if s.project_path == project_path
                ]
                self._active_project = remaining[0].project_path if remaining else None

            # Persist if enabled
            if save and self._auto_save and self._persistence_path:
                self._save_to_disk()

            logger.info(f"Closed session {session_id}")
            return True

    def get_active_project(self) -> Optional[str]:
        """
        Get the currently active project path.

        Returns:
            Project path or None if no active project
        """
        with self._lock:
            return self._active_project

    def set_active_project(self, project_path: str) -> bool:
        """
        Set the active project.

        Args:
            project_path: Path to the Godot project

        Returns:
            True if successful, False if project not in any session
        """
        with self._lock:
            # Verify the project exists in any session
            session = self._find_session_by_project(project_path)
            if session is None:
                logger.warning(f"Project {project_path} not in any session")
                return False

            self._active_project = project_path

            # Persist if enabled
            if self._auto_save and self._persistence_path:
                self._save_to_disk()

            logger.info(f"Set active project to: {project_path}")
            return True

    def get_active_session(self) -> Optional[Session]:
        """
        Get the session for the active project.

        Returns:
            Session object or None if no active project
        """
        with self._lock:
            if self._active_project is None:
                return None
            return self._find_session_by_project(self._active_project)

    def record_operation(
        self,
        session_id: str,
        operation_type: str,
        target: str,
        description: str = "",
        data: Optional[Dict[str, Any]] = None,
        result: str = "success",
    ) -> Optional[Operation]:
        """
        Record an operation in the session's history.

        Args:
            session_id: The session ID
            operation_type: Type of operation (create, edit, delete, etc.)
            target: The target of the operation (scene path, node path, etc.)
            description: Human-readable description
            data: Additional data for the operation
            result: Result status (success, failed, cancelled)

        Returns:
            The created Operation or None if session not found
        """
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                logger.warning(f"Session {session_id} not found")
                return None

            operation = Operation(
                id=uuid.uuid4().hex[:8],
                timestamp=datetime.now(),
                operation_type=operation_type,
                target=target,
                description=description,
                data=data or {},
                result=result,
            )

            session.operation_history.append(operation)
            session.mark_modified()

            # Persist if enabled
            if self._auto_save and self._persistence_path:
                self._save_to_disk()

            logger.debug(
                f"Recorded operation {operation.id}: {operation_type} on {target}"
            )
            return operation

    def get_recent_operations(self, session_id: str, n: int = 10) -> List[Operation]:
        """
        Get the n most recent operations for a session.

        Args:
            session_id: The session ID
            n: Number of operations to retrieve (default: 10)

        Returns:
            List of recent operations, most recent first
        """
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                logger.warning(f"Session {session_id} not found")
                return []

            # Return most recent operations first
            return session.operation_history[-n:][::-1]

    def get_operations_by_type(
        self, session_id: str, operation_type: str
    ) -> List[Operation]:
        """
        Get all operations of a specific type for a session.

        Args:
            session_id: The session ID
            operation_type: Type of operation to filter

        Returns:
            List of matching operations, most recent first
        """
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return []

            filtered = [
                op
                for op in session.operation_history
                if op.operation_type == operation_type
            ]
            return filtered[::-1]  # Most recent first

    # ==================== Scene Management ====================

    def add_open_scene(self, session_id: str, scene_path: str) -> bool:
        """Add a scene to the open scenes list"""
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return False

            session.add_open_scene(scene_path)

            if self._auto_save and self._persistence_path:
                self._save_to_disk()
            return True

    def remove_open_scene(self, session_id: str, scene_path: str) -> bool:
        """Remove a scene from the open scenes list"""
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return False

            session.remove_open_scene(scene_path)

            if self._auto_save and self._persistence_path:
                self._save_to_disk()
            return True

    def get_open_scenes(self, session_id: str) -> List[str]:
        """Get the list of open scenes for a session"""
        with self._lock:
            session = self._sessions.get(session_id)
            return session.open_scenes.copy() if session else []

    # ==================== Workspace (In-Memory Scene Cache) ====================

    def load_scene_into_session(
        self, session_id: str, scene_path: str, parser_func=None
    ) -> Optional["Scene"]:
        """
        Carga una escena en el workspace de la sesión.

        Args:
            session_id: ID de la sesión
            scene_path: Ruta absoluta al archivo .tscn
            parser_func: Función opcional para parsear (default usa parse_tscn)

        Returns:
            Scene parseada o None si falla
        """
        from godot_mcp.core.tscn_parser import parse_tscn as default_parse

        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                logger.warning(f"Session {session_id} not found")
                return None

            # Si ya está cargada, retornarla
            if scene_path in session.loaded_scenes:
                return session.loaded_scenes[scene_path]

            # Parsear la escena
            parse = parser_func or default_parse
            try:
                scene = parse(scene_path)
                session.loaded_scenes[scene_path] = scene
                # Agregar a open_scenes
                if scene_path not in session.open_scenes:
                    session.open_scenes.append(scene_path)
                logger.debug(f"Loaded scene into session: {scene_path}")
                return scene
            except Exception as e:
                logger.error(f"Failed to load scene {scene_path}: {e}")
                return None

    def get_loaded_scene(self, session_id: str, scene_path: str) -> Optional["Scene"]:
        """
        Obtiene una escena ya cargada en el workspace.

        Args:
            session_id: ID de la sesión
            scene_path: Ruta absoluta al archivo .tscn

        Returns:
            Scene o None si no está cargada
        """
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return None
            return session.loaded_scenes.get(scene_path)

    def mark_scene_dirty(self, session_id: str, scene_path: str) -> bool:
        """Marca una escena como modificada (dirty)."""
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return False
            session.dirty_scenes.add(scene_path)
            return True

    def is_scene_dirty(self, session_id: str, scene_path: str) -> bool:
        """Verifica si una escena tiene cambios sin guardar."""
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return False
            return scene_path in session.dirty_scenes

    def get_dirty_scenes(self, session_id: str) -> List[str]:
        """Obtiene lista de escenas modificadas."""
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return []
            return list(session.dirty_scenes)

    def commit_scene(self, session_id: str, scene_path: str, writer_func=None) -> bool:
        """
        Guarda una escena dirty a disco y limpia el flag.

        Args:
            session_id: ID de la sesión
            scene_path: Ruta absoluta al archivo .tscn
            writer_func: Función opcional para escribir

        Returns:
            True si se guardó correctamente
        """
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                logger.warning(f"Session {session_id} not found")
                return False

            scene = session.loaded_scenes.get(scene_path)
            if scene is None:
                logger.warning(f"Scene not loaded: {scene_path}")
                return False

            if scene_path not in session.dirty_scenes:
                logger.debug(f"Scene not dirty, skipping: {scene_path}")
                return True

            # Escribir a disco
            try:
                # Usar la función writer si se provee, si no usar el método to_tscn
                if writer_func:
                    writer_func(scene_path, scene)
                else:
                    with open(scene_path, "w", encoding="utf-8") as f:
                        f.write(scene.to_tscn())

                # Limpiar dirty flag
                session.dirty_scenes.discard(scene_path)
                session.mark_modified()

                logger.info(f"Committed scene: {scene_path}")
                return True
            except Exception as e:
                logger.error(f"Failed to commit scene {scene_path}: {e}")
                return False

    def unload_scene(self, session_id: str, scene_path: str) -> bool:
        """Descarga una escena del workspace."""
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return False

            if scene_path in session.loaded_scenes:
                del session.loaded_scenes[scene_path]
                session.dirty_scenes.discard(scene_path)
                return True
            return False

    def unload_all_scenes(self, session_id: str) -> bool:
        """Descarga todas las escenas del workspace."""
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return False

            session.loaded_scenes.clear()
            session.dirty_scenes.clear()
            return True

    # ==================== Cache Management ====================

    def set_cache(self, session_id: str, key: str, value: Any) -> bool:
        """Set a value in the session's cache"""
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return False

            session.cache[key] = value
            session.mark_modified()

            if self._auto_save and self._persistence_path:
                self._save_to_disk()
            return True

    def get_cache(self, session_id: str, key: str, default: Any = None) -> Any:
        """Get a value from the session's cache"""
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return default
            return session.cache.get(key, default)

    def clear_cache(self, session_id: str) -> bool:
        """Clear the session's cache"""
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return False

            session.cache.clear()
            session.mark_modified()

            if self._auto_save and self._persistence_path:
                self._save_to_disk()
            return True

    # ==================== Metadata ====================

    def set_metadata(self, session_id: str, key: str, value: Any) -> bool:
        """Set metadata for a session"""
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return False

            session.metadata[key] = value
            session.mark_modified()
            return True

    def get_metadata(self, session_id: str, key: str, default: Any = None) -> Any:
        """Get metadata from a session"""
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return default
            return session.metadata.get(key, default)

    # ==================== Utility Methods ====================

    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all sessions with their basic info"""
        with self._lock:
            return [
                {
                    "id": s.id,
                    "project_path": s.project_path,
                    "created_at": s.created_at.isoformat(),
                    "modified_at": s.modified_at.isoformat(),
                    "open_scenes_count": len(s.open_scenes),
                    "operations_count": len(s.operation_history),
                    "is_active": s.project_path == self._active_project,
                }
                for s in self._sessions.values()
            ]

    def get_session_count(self) -> int:
        """Get the number of active sessions"""
        with self._lock:
            return len(self._sessions)

    def clear_all_sessions(self) -> int:
        """Clear all sessions (for testing or reset)"""
        with self._lock:
            count = len(self._sessions)
            self._sessions.clear()
            self._active_project = None

            if self._persistence_path and os.path.exists(self._persistence_path):
                os.remove(self._persistence_path)

            logger.info(f"Cleared {count} sessions")
            return count

    def export_session(self, session_id: str, output_path: str) -> bool:
        """Export a session to a JSON file"""
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return False

            try:
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(session.to_dict(), f, indent=2)
                logger.info(f"Exported session {session_id} to {output_path}")
                return True
            except Exception as e:
                logger.error(f"Failed to export session: {e}")
                return False

    def import_session(self, input_path: str) -> Optional[str]:
        """Import a session from a JSON file"""
        try:
            with open(input_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            session = Session.from_dict(data)

            # Generate new ID to avoid conflicts
            session.id = self._generate_session_id()

            with self._lock:
                self._sessions[session.id] = session

                if self._auto_save and self._persistence_path:
                    self._save_to_disk()

            logger.info(f"Imported session from {input_path}")
            return session.id
        except Exception as e:
            logger.error(f"Failed to import session: {e}")
            return None


# ==================== Convenience Functions ====================


def create_manager(
    persistence_path: Optional[str] = None, auto_save: bool = True
) -> SessionManager:
    """Create a new SessionManager instance"""
    return SessionManager(persistence_path=persistence_path, auto_save=auto_save)


if __name__ == "__main__":
    # Demo usage
    manager = SessionManager(persistence_path="./sessions.json", auto_save=True)

    # Create a session
    session_id = manager.create_session("D:/Games/MyGodotProject")
    print(f"Created session: {session_id}")

    # Add open scenes
    manager.add_open_scene(session_id, "res://scenes/Main.tscn")
    manager.add_open_scene(session_id, "res://scenes/Player.tscn")

    # Record operations
    manager.record_operation(
        session_id,
        "create",
        "res://scenes/Main.tscn",
        "Created new scene",
        {"root_node": "Node2D"},
    )
    manager.record_operation(
        session_id,
        "edit",
        "res://scenes/Main.tscn",
        "Added Sprite2D node",
        {"node_name": "Sprite2D"},
    )
    manager.record_operation(
        session_id, "save", "res://scenes/Main.tscn", "Saved scene to disk"
    )

    # Get recent operations
    operations = manager.get_recent_operations(session_id, n=5)
    print("\nRecent operations:")
    for op in operations:
        print(f"  - [{op.operation_type}] {op.description}")

    # Get session info
    session = manager.get_session(session_id)
    if session:
        print(f"\nSession info:")
        print(f"  Project: {session.project_path}")
        print(f"  Open scenes: {session.open_scenes}")
        print(f"  Active scene: {session.active_scene}")
        print(f"  Operations: {len(session.operation_history)}")

    # Set cache
    manager.set_cache(session_id, "last_node_id", 42)
    print(f"\nCache value: {manager.get_cache(session_id, 'last_node_id')}")

    # List all sessions
    print("\nAll sessions:")
    for s in manager.list_sessions():
        print(f"  - {s['id']}: {s['project_path']} (active: {s['is_active']})")

    # Close session
    manager.close_session(session_id)
    print("\nSession closed")
