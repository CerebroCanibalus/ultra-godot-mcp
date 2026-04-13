"""
Decoradores para herramientas MCP Godot.

Provee decorators reutilizables para validación automática de sesiones
y otras validaciones comunes.
"""

from __future__ import annotations

import functools
import logging
from typing import Any, Callable, Optional, TypeVar

# Importar desde session_tools para compartir la misma instancia
from godot_mcp.tools.session_tools import get_session_manager

logger = logging.getLogger(__name__)


# ==================== DECORADOR @require_session ====================

T = TypeVar("T")


def require_session(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorador que valida automáticamente el session_id en todas las herramientas.

    El decorador:
    1. Extrae session_id de kwargs o primer argumento posicional
    2. Valida que session_id no esté vacío
    3. Verifica que la sesión existe en el SessionManager
    4. Ejecuta la función original si la sesión es válida
    5. Retorna error estructurado si la validación falla

    Uso:
        @require_session
        def create_scene(session_id: str, project_path: str, scene_path: str) -> dict:
            # La validación de sesión ya se hizo automáticamente
            # Aquí va solo la lógica de negocio
            ...

    Returns:
        Función wrapper que valida sesión antes de ejecutar.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> dict:
        # Extraer session_id de kwargs o args
        session_id = kwargs.get("session_id")

        if not session_id:
            # Buscar en positional args (asumiendo que es el primer parámetro)
            if args:
                session_id = args[0]

        # Validar que session_id fue proporcionado
        if not session_id:
            return {
                "success": False,
                "error": "session_id es requerido como primer parámetro",
            }

        # Validar que la sesión existe en el manager
        try:
            manager = get_session_manager()
            session = manager.get_session(session_id)

            if session is None:
                return {
                    "success": False,
                    "error": f"Session no encontrada: {session_id}. "
                    f"Usa start_session() para crear una nueva.",
                }
        except Exception as e:
            logger.error(f"Error validando sesión: {e}")
            return {
                "success": False,
                "error": f"Error validando sesión: {str(e)}",
            }

        # Sesión válida - ejecutar función original
        return func(*args, **kwargs)

    return wrapper


# ==================== DECORADOR @require_session_with_project ====================


def require_session_with_project(func: Callable[..., T]) -> Callable[..., T]:
    """
     Decorador que valida sesión Y verifica que project_path existe.

     Además de validar la sesión, verifica que el proyecto
    还存在 y es válido (contiene project.godot).

     Uso:
         @require_session_with_project
         def list_scenes(session_id: str, project_path: str, recursive: bool) -> dict:
             # Validación de sesión y proyecto hecha automáticamente
             ...
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> dict:
        import os

        # Primero ejecutar validación de sesión
        session_id = kwargs.get("session_id") or (args[0] if args else None)

        if not session_id:
            return {
                "success": False,
                "error": "session_id es requerido como primer parámetro",
            }

        # Validar sesión
        manager = get_session_manager()
        session = manager.get_session(session_id)

        if session is None:
            return {
                "success": False,
                "error": f"Session no encontrada: {session_id}. "
                f"Usa start_session() para crear una nueva.",
            }

        # Validar project_path
        project_path = kwargs.get("project_path") or (
            args[1] if len(args) > 1 else None
        )

        if project_path:
            if not os.path.isdir(project_path):
                return {
                    "success": False,
                    "error": f"Directorio de proyecto no encontrado: {project_path}",
                }

            project_file = os.path.join(project_path, "project.godot")
            if not os.path.isfile(project_file):
                return {
                    "success": False,
                    "error": f"No es un proyecto Godot válido (no tiene project.godot): {project_path}",
                }

        # Ejecutar función original
        return func(*args, **kwargs)

    return wrapper
