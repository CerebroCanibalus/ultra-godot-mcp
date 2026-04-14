"""
Session Tools - Herramientas para gestión de sesiones Godot.

Provee herramientas FastMCP para:
- Crear/cerrar sesiones de proyecto
- Gestionar workspace en memoria
- Rastrear operaciones
- Commit/rollback de cambios

Usa el SessionManager extendido con workspace.
"""

from __future__ import annotations

import functools
import logging
import os
from typing import Any, Callable, Optional, TypeVar

from fastmcp import FastMCP

from godot_mcp.session_manager import SessionManager

logger = logging.getLogger(__name__)


# ==================== INSTANCIA GLOBAL ====================

# Instancia global del SessionManager (compartida entre todas las tools)
_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """Obtiene la instancia global del SessionManager."""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager(auto_save=False)
    return _session_manager


def set_session_manager(manager: SessionManager) -> None:
    """Configura la instancia global del SessionManager."""
    global _session_manager
    _session_manager = manager


# ==================== DECORADOR @require_session ====================

T = TypeVar("T")


def require_session(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorador que valida que session_id existe y obtiene la sesión.

    Uso:
        @require_session
        def create_scene(session_id: str, scene_path: str, ...) -> dict:
            session = get_current_session()  # Obtiene la sesión validada
            ...

    El decorador:
    1. Valida que session_id no esté vacío
    2. Verifica que la sesión existe en el manager
    3. Pasa la sesión como segundo argumento (opcional)
    4. Maneja errores elegantemente
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> dict:
        # Extraer session_id de kwargs o args
        session_id = kwargs.get("session_id")

        if not session_id:
            # Buscar en positional args (asumiendo que es el primer parámetro)
            if args:
                session_id = args[0]

        if not session_id:
            return {
                "success": False,
                "error": "session_id es requerido como primer parámetro",
            }

        # Validar que la sesión existe
        manager = get_session_manager()
        session = manager.get_session(session_id)

        if session is None:
            return {
                "success": False,
                "error": f"Session no encontrada: {session_id}. "
                f"Usa start_session() para crear una nueva.",
            }

        # Llamar la función original
        return func(*args, **kwargs)

    return wrapper


# ==================== CONTEXTO DE SESIÓN ====================


class SessionContext:
    """
    Contexto de sesión para acceso rápido al workspace.

    Uso:
        with SessionContext(session_id) as ctx:
            scene = ctx.load_scene("res://Player.tscn")
            # modificar scene...
            ctx.commit_scene("res://Player.tscn")
    """

    def __init__(self, session_id: str):
        self.session_id = session_id
        self._manager = get_session_manager()
        self._session = self._manager.get_session(session_id)

    def __enter__(self) -> "SessionContext":
        if self._session is None:
            raise ValueError(f"Session no encontrada: {self.session_id}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        # No hacer auto-commit en exit para permitir controle manual
        return False

    @property
    def project_path(self) -> str:
        """Ruta del proyecto."""
        return self._session.project_path

    @property
    def loaded_scenes(self) -> dict:
        """Escenas cargadas en memoria."""
        return self._session.loaded_scenes

    @property
    def dirty_scenes(self) -> set:
        """Escenas modificadas pendientes."""
        return self._session.dirty_scenes

    def load_scene(self, scene_path: str):
        """Carga una escena en el workspace."""
        return self._manager.load_scene_into_session(self.session_id, scene_path)

    def get_scene(self, scene_path: str):
        """Obtiene una escena ya cargada."""
        return self._manager.get_loaded_scene(self.session_id, scene_path)

    def mark_dirty(self, scene_path: str):
        """Marca una escena como modificada."""
        self._manager.mark_scene_dirty(self.session_id, scene_path)

    def commit_scene(self, scene_path: str) -> bool:
        """Guarda una escena a disco."""
        return self._manager.commit_scene(self.session_id, scene_path)

    def commit_all(self) -> int:
        """Guarda todas las escenas dirty."""
        dirty = self._manager.get_dirty_scenes(self.session_id)
        count = 0
        for scene_path in dirty:
            if self.commit_scene(scene_path):
                count += 1
        return count

    def unload_scene(self, scene_path: str):
        """Descarga una escena del workspace."""
        self._manager.unload_scene(self.session_id, scene_path)


# ==================== TOOLS DE SESIÓN ====================


def start_session(project_path: str) -> dict:
    """
    Inicia una nueva sesión para un proyecto Godot.

    Crea una sesión que mantiene un workspace en memoria
    para todas las operaciones subsecuentes.

    Args:
        project_path: Ruta absoluta al directorio del proyecto.

    Returns:
        Dict con session_id y metadata.

    Ejemplo:
        session_id = start_session("D:/Mis Juegos/MyProject")
    """
    manager = get_session_manager()

    # Validar que el proyecto existe
    if not os.path.isdir(project_path):
        return {
            "success": False,
            "error": f"Directorio de proyecto no encontrado: {project_path}",
        }

    project_file = os.path.join(project_path, "project.godot")
    if not os.path.isfile(project_file):
        return {
            "success": False,
            "error": f"No es un proyecto Godot válido (no tiene project.godot)",
        }

    # Crear sesión
    session_id = manager.create_session(project_path)

    return {
        "success": True,
        "session_id": session_id,
        "project_path": project_path,
        "message": "Sesión iniciada. Usa este session_id en todas las operaciones.",
    }


def end_session(session_id: str, save: bool = True) -> dict:
    """
    Cierra una sesión, opcionalmente guardando cambios.

    Args:
        session_id: ID de la sesión a cerrar.
        save: Si True, guarda todas las escenas dirty antes de cerrar.

    Returns:
        Dict con resultado de la operación.

    Ejemplo:
        end_session("session_abc123", save=True)
    """
    manager = get_session_manager()

    # Validar sesión existe
    session = manager.get_session(session_id)
    if session is None:
        return {"success": False, "error": f"Session no encontrada: {session_id}"}

    # Guardar cambios si se solicita
    if save:
        dirty = manager.get_dirty_scenes(session_id)
        saved_count = 0
        for scene_path in dirty:
            if manager.commit_scene(session_id, scene_path):
                saved_count += 1

        logger.info(f"Guardados {saved_count} scenes antes de cerrar sesión")

    # Descargar todas las escenas
    manager.unload_all_scenes(session_id)

    # Cerrar sesión
    result = manager.close_session(session_id, save=save)

    return {
        "success": result,
        "session_id": session_id,
        "saved": save,
        "message": "Sesión cerrada" if result else "Error al cerrar sesión",
    }


def get_active_session() -> dict:
    """
    Obtiene la sesión activa actual.

    Returns:
        Dict con info de la sesión activa o None.
    """
    manager = get_session_manager()
    session = manager.get_active_session()

    if session is None:
        return {
            "success": True,
            "active_session": None,
            "message": "No hay sesión activa",
        }

    return {
        "success": True,
        "session_id": session.id,
        "project_path": session.project_path,
        "open_scenes": session.open_scenes,
        "dirty_count": len(session.dirty_scenes),
    }


def list_sessions() -> dict:
    """
    Lista todas las sesiones activas.

    Returns:
        Lista de sesiones con su información.
    """
    manager = get_session_manager()
    sessions = manager.list_sessions()

    return {
        "success": True,
        "count": len(sessions),
        "sessions": sessions,
    }


def get_session_info(session_id: str) -> dict:
    """
    Obtiene información detallada de una sesión.

    Args:
        session_id: ID de la sesión.

    Returns:
        Dict con información de la sesión.
    """
    manager = get_session_manager()
    session = manager.get_session(session_id)

    if session is None:
        return {"success": False, "error": f"Session no encontrada: {session_id}"}

    return {
        "success": True,
        "session_id": session.id,
        "project_path": session.project_path,
        "created_at": session.created_at.isoformat(),
        "modified_at": session.modified_at.isoformat(),
        "open_scenes": session.open_scenes,
        "loaded_scenes_count": len(session.loaded_scenes),
        "dirty_scenes": list(session.dirty_scenes),
        "operations_count": len(session.operation_history),
        "active_scene": session.active_scene,
    }


def commit_session(session_id: str, scene_path: Optional[str] = None) -> dict:
    """
    Guarda escena(s) a disco.

    Args:
        session_id: ID de la sesión.
        scene_path: Ruta específica a guardar (opcional, None = todas).

    Returns:
        Dict con resultado.
    """
    manager = get_session_manager()
    session = manager.get_session(session_id)

    if session is None:
        return {"success": False, "error": f"Session no encontrada: {session_id}"}

    if scene_path:
        # Guardar una escena específica
        result = manager.commit_scene(session_id, scene_path)
        return {
            "success": result,
            "scene_path": scene_path,
        }
    else:
        # Guardar todas las dirty
        dirty = manager.get_dirty_scenes(session_id)
        saved = []
        failed = []

        for sp in dirty:
            if manager.commit_scene(session_id, sp):
                saved.append(sp)
            else:
                failed.append(sp)

        return {
            "success": len(failed) == 0,
            "saved_count": len(saved),
            "saved": saved,
            "failed": failed,
        }


def discard_changes(session_id: str, scene_path: Optional[str] = None) -> dict:
    """
    Descarta cambios sin guardar.

    Args:
        session_id: ID de la sesión.
        scene_path: Ruta específica (opcional, None = todas).

    Returns:
        Dict con resultado.
    """
    manager = get_session_manager()
    session = manager.get_session(session_id)

    if session is None:
        return {"success": False, "error": f"Session no encontrada: {session_id}"}

    if scene_path:
        # Descartar una escena específica
        manager.unload_scene(session_id, scene_path)
        return {
            "success": True,
            "scene_path": scene_path,
            "message": "Cambios descartados",
        }
    else:
        # Descartar todas
        count = len(session.dirty_scenes)
        manager.unload_all_scenes(session_id)

        return {
            "success": True,
            "discarded_count": count,
            "message": "Todos los cambios descartados",
        }


# ==================== REGISTRO DE HERRAMIENTAS ====================


def register_session_tools(mcp: FastMCP) -> None:
    """
    Registra todas las herramientas de sesión con FastMCP.

    Args:
        mcp: Instancia de FastMCP.
    """
    logger.info("Registrando session_tools...")

    # Herramientas de sesión
    mcp.add_tool(start_session)
    mcp.add_tool(end_session)
    mcp.add_tool(get_active_session)
    mcp.add_tool(list_sessions)
    mcp.add_tool(get_session_info)
    mcp.add_tool(commit_session)
    mcp.add_tool(discard_changes)

    logger.info("[OK] 7 session_tools registradas")
