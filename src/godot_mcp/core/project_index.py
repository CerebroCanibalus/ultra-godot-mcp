"""
Project Index - Índice en memoria de todo el proyecto Godot

Este módulo proporciona un índice searchable O(1) de:
- Escenas (.tscn) → tipos de nodos, scripts usados
- Scripts (.gd) → class_name, extends, funciones
- Recursos (.tres) → tipo, usado por
- Relaciones entre archivos (qué escena usa qué script/recurso)

 Incluye:
- Actualización incremental (solo re-indexar lo cambiado)
- Watchdog para detectar cambios en archivos
- API de búsqueda
"""

from __future__ import annotations

import os
import re
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

# =============================================================================
# Tipos de datos para el índice
# =============================================================================


@dataclass
class ScriptInfo:
    """Información de un script GDScript."""

    path: str  # Ruta absoluta
    relative_path: str  # Ruta relativa al proyecto (res://...)
    class_name: Optional[str] = None  # class_name definido
    extends: Optional[str] = None  # Clase base (extends)
    functions: list[str] = field(default_factory=list)  # Lista de funciones
    variables: list[str] = field(default_factory=list)  # Variables de clase
    signals: list[str] = field(default_factory=list)  # Señales definidas
    mtime: float = 0.0  # Modified time para cache


@dataclass
class SceneInfo:
    """Información de una escena .tscn."""

    path: str  # Ruta absoluta
    relative_path: str  # Ruta relativa (res://...)
    root_type: str = ""  # Tipo del nodo raíz
    node_types: list[str] = field(default_factory=list)  # Todos los tipos de nodos
    node_names: dict[str, str] = field(default_factory=dict)  # nombre -> tipo
    scripts: list[str] = field(default_factory=list)  # Rutas de scripts usados
    resources: list[str] = field(default_factory=list)  # Rutas de recursos externos
    mtime: float = 0.0


@dataclass
class ResourceInfo:
    """Información de un recurso .tres."""

    path: str
    relative_path: str
    resource_type: str = ""
    script_class: Optional[str] = None
    used_by_scenes: list[str] = field(default_factory=list)
    used_by_scripts: list[str] = field(default_factory=list)
    mtime: float = 0.0


@dataclass
class ProjectIndex:
    """
    Índice completo del proyecto.

    Todos los diccionarios usan rutas relativas (res://...) como clave
    para búsquedas O(1).
    """

    project_path: str = ""
    scenes: dict[str, SceneInfo] = field(default_factory=dict)
    scripts: dict[str, ScriptInfo] = field(default_factory=dict)
    resources: dict[str, ResourceInfo] = field(default_factory=dict)

    # Índices inversos para búsquedas rápidas
    # scripts_by_extends["CharacterBody2D"] -> ["res://Player.gd", "res://Enemy.gd"]
    scripts_by_extends: dict[str, list[str]] = field(default_factory=dict)
    # scenes_by_node_type["CharacterBody2D"] -> ["res://Player.tscn", "res://Enemy.tscn"]
    scenes_by_node_type: dict[str, list[str]] = field(default_factory=dict)
    # scenes_using_script["res://Player.gd"] -> ["res://Player.tscn"]
    scenes_using_script: dict[str, list[str]] = field(default_factory=dict)
    # scenes_using_resource["res://texture.png"] -> ["res://Level.tscn"]
    scenes_using_resource: dict[str, list[str]] = field(default_factory=dict)


# =============================================================================
# Parser de scripts GDScript
# =============================================================================


def parse_gd_script(file_path: str, project_path: str = "") -> ScriptInfo:
    """
    Parsea un archivo .gd y extrae información de metadatos.

    Args:
        file_path: Ruta absoluta al archivo .gd
        project_path: Ruta del proyecto (para convertir a res://)

    Returns:
        ScriptInfo con la información extraída
    """
    path = Path(file_path)
    relative_path = _to_res_path(file_path, project_path)

    info = ScriptInfo(
        path=file_path,
        relative_path=relative_path,
        mtime=path.stat().st_mtime if path.exists() else 0.0,
    )

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Buscar class_name
        class_match = re.search(r"class_name\s+(\w+)", content)
        if class_match:
            info.class_name = class_match.group(1)

        # Buscar extends
        extends_match = re.search(r"extends\s+([\w.]+)", content)
        if extends_match:
            info.extends = extends_match.group(1)

        # Buscar funciones (func name(...))
        func_pattern = re.compile(r"func\s+(\w+)\s*\(")
        info.functions = func_pattern.findall(content)

        # Buscar variables de clase (var name: type = value)
        var_pattern = re.compile(r"^\s*var\s+(\w+)", re.MULTILINE)
        info.variables = var_pattern.findall(content)

        # Buscar señales (signal name(...))
        signal_pattern = re.compile(r"signal\s+(\w+)")
        info.signals = signal_pattern.findall(content)

    except Exception as e:
        # Silenciar errores de parsing - el archivo podría estar incompleto
        pass

    return info


def _to_res_path(absolute_path: str, project_path: str = "") -> str:
    """
    Convierte una ruta absoluta a ruta res://.

    Args:
        absolute_path: Ruta absoluta
        project_path: Ruta del proyecto (para remover el prefijo)

    Returns:
        Ruta en formato res://
    """
    # Normalizar separadores
    path = absolute_path.replace("\\", "/")

    # Normalizar el path del proyecto si se provee
    if project_path:
        project_normalized = project_path.replace("\\", "/").rstrip("/")
        # Remover el prefijo del proyecto (manejar con y sin slash final)
        if path.startswith(project_normalized + "/"):
            path = path[len(project_normalized) + 1 :]
        elif path.startswith(project_normalized):
            # Mismo directorio (edge case)
            path = path[len(project_normalized) :]

    # Remover cualquier residuo de drive (D:, C:, etc.) al inicio
    if len(path) > 1 and path[1] == ":":
        path = path[2:]

    # Asegurar que no tenga slashes múltiples y comience correctamente
    path = path.lstrip("/")

    # Agregar res:// al inicio
    return "res://" + path


# =============================================================================
# Indexador principal
# =============================================================================


class ProjectIndexer:
    """Indexador de proyectos Godot con actualización incremental."""

    def __init__(self, project_path: str):
        self.project_path = project_path
        self._lock = threading.RLock()
        self._index: Optional[ProjectIndex] = None
        self._watchdog: Optional[Observer] = None
        self._watchdog_handler: Optional[FileSystemEventHandler] = None

    def build_index(self, force: bool = False) -> ProjectIndex:
        """
        Construye el índice del proyecto.

        Args:
            force: Si True, fuerza reindexación completa

        Returns:
            ProjectIndex con toda la información del proyecto
        """
        with self._lock:
            if self._index and not force:
                return self._index

            index = ProjectIndex(project_path=self.project_path)

            # 1. Indexar todos los scripts .gd
            self._index_scripts(index)

            # 2. Indexar todas las escenas .tscn
            self._index_scenes(index)

            # 3. Indexar todos los recursos .tres
            self._index_resources(index)

            # 4. Construir índices inversos
            self._build_inverse_indices(index)

            self._index = index
            return index

    def _index_scripts(self, index: ProjectIndex) -> None:
        """Indexa todos los scripts .gd del proyecto."""
        for root, _, files in os.walk(self.project_path):
            for file in files:
                if file.endswith(".gd"):
                    full_path = os.path.join(root, file)
                    try:
                        info = parse_gd_script(full_path, self.project_path)
                        index.scripts[info.relative_path] = info
                    except Exception:
                        pass

    def _index_scenes(self, index: ProjectIndex) -> None:
        """Indexa todas las escenas .tscn del proyecto."""
        from godot_mcp.core.tscn_parser import parse_tscn

        for root, _, files in os.walk(self.project_path):
            for file in files:
                if file.endswith(".tscn"):
                    full_path = os.path.join(root, file)
                    try:
                        scene = parse_tscn(full_path)

                        relative_path = _to_res_path(full_path, self.project_path)

                        # Extraer información
                        node_types = []
                        node_names = {}
                        scripts = []
                        resources = []

                        root_type = ""
                        if scene.nodes:
                            root_type = scene.nodes[0].type

                        for node in scene.nodes:
                            node_types.append(node.type)
                            node_names[node.name] = node.type

                            # Buscar script en propiedades
                            if "script" in node.properties:
                                script_ref = node.properties["script"]
                                if (
                                    isinstance(script_ref, dict)
                                    and script_ref.get("type") == "ExtResource"
                                ):
                                    # Buscar el recurso externo
                                    ref_id = script_ref.get("ref", "")
                                    for ext in scene.ext_resources:
                                        if ext.id == ref_id:
                                            scripts.append(ext.path)
                                            break

                        # Recursos externos
                        for ext in scene.ext_resources:
                            if ext.path:
                                resources.append(ext.path)

                        path_obj = Path(full_path)
                        mtime = path_obj.stat().st_mtime if path_obj.exists() else 0.0

                        index.scenes[relative_path] = SceneInfo(
                            path=full_path,
                            relative_path=relative_path,
                            root_type=root_type,
                            node_types=node_types,
                            node_names=node_names,
                            scripts=scripts,
                            resources=resources,
                            mtime=mtime,
                        )
                    except Exception:
                        pass

    def _index_resources(self, index: ProjectIndex) -> None:
        """Indexa todos los recursos .tres del proyecto."""
        from godot_mcp.core.tres_parser import parse_tres

        for root, _, files in os.walk(self.project_path):
            for file in files:
                if file.endswith(".tres"):
                    full_path = os.path.join(root, file)
                    try:
                        resource = parse_tres(full_path)

                        relative_path = _to_res_path(full_path, self.project_path)
                        path_obj = Path(full_path)
                        mtime = path_obj.stat().st_mtime if path_obj.exists() else 0.0

                        index.resources[relative_path] = ResourceInfo(
                            path=full_path,
                            relative_path=relative_path,
                            resource_type=resource.header.type,
                            script_class=resource.header.script_class,
                            mtime=mtime,
                        )
                    except Exception:
                        pass

    def _build_inverse_indices(self, index: ProjectIndex) -> None:
        """Construye índices inversos para búsquedas rápidas."""

        # scripts_by_extends: scripts que extienden una clase
        for path, script in index.scripts.items():
            if script.extends:
                if script.extends not in index.scripts_by_extends:
                    index.scripts_by_extends[script.extends] = []
                index.scripts_by_extends[script.extends].append(path)

        # scenes_by_node_type: escenas que contienen un tipo de nodo
        for path, scene in index.scenes.items():
            for node_type in scene.node_types:
                if node_type not in index.scenes_by_node_type:
                    index.scenes_by_node_type[node_type] = []
                if path not in index.scenes_by_node_type[node_type]:
                    index.scenes_by_node_type[node_type].append(path)

        # scenes_using_script: escenas que usan un script
        for path, scene in index.scenes.items():
            for script_path in scene.scripts:
                if script_path not in index.scenes_using_script:
                    index.scenes_using_script[script_path] = []
                if path not in index.scenes_using_script[script_path]:
                    index.scenes_using_script[script_path].append(path)

        # scenes_using_resource: escenas que usan un recurso
        for path, scene in index.scenes.items():
            for res_path in scene.resources:
                if res_path not in index.scenes_using_resource:
                    index.scenes_using_resource[res_path] = []
                if path not in index.scenes_using_resource[res_path]:
                    index.scenes_using_resource[res_path].append(path)

    def invalidate_file(self, file_path: str) -> None:
        """
        Invalida un archivo específico y lo re-indexa si es necesario.

        Args:
            file_path: Ruta absoluta del archivo que cambió
        """
        with self._lock:
            if not self._index:
                return

            relative_path = _to_res_path(file_path, self.project_path)
            path_obj = Path(file_path)

            # Determinar el tipo de archivo y actualizar
            if file_path.endswith(".gd"):
                if relative_path in self._index.scripts:
                    if path_obj.exists():
                        # Re-parsear el script
                        self._index.scripts[relative_path] = parse_gd_script(
                            file_path, self.project_path
                        )
                    else:
                        # El archivo fue eliminado
                        del self._index.scripts[relative_path]

            elif file_path.endswith(".tscn"):
                if relative_path in self._index.scenes:
                    if path_obj.exists():
                        # Re-parsear la escena
                        self._reindex_scene(relative_path, file_path, self._index)
                    else:
                        del self._index.scenes[relative_path]

            elif file_path.endswith(".tres"):
                if relative_path in self._index.resources:
                    if path_obj.exists():
                        self._reindex_resource(relative_path, file_path, self._index)
                    else:
                        del self._index.resources[relative_path]

            # Reconstruir índices inversos
            self._build_inverse_indices(self._index)

    def _reindex_scene(
        self, relative_path: str, full_path: str, index: ProjectIndex
    ) -> None:
        """Re-indexa una escena específica."""
        from godot_mcp.core.tscn_parser import parse_tscn

        try:
            scene = parse_tscn(full_path)

            node_types = []
            node_names = {}
            scripts = []
            resources = []

            root_type = ""
            if scene.nodes:
                root_type = scene.nodes[0].type

            for node in scene.nodes:
                node_types.append(node.type)
                node_names[node.name] = node.type

                if "script" in node.properties:
                    script_ref = node.properties["script"]
                    if (
                        isinstance(script_ref, dict)
                        and script_ref.get("type") == "ExtResource"
                    ):
                        ref_id = script_ref.get("ref", "")
                        for ext in scene.ext_resources:
                            if ext.id == ref_id:
                                scripts.append(ext.path)
                                break

            for ext in scene.ext_resources:
                if ext.path:
                    resources.append(ext.path)

            path_obj = Path(full_path)
            mtime = path_obj.stat().st_mtime if path_obj.exists() else 0.0

            index.scenes[relative_path] = SceneInfo(
                path=full_path,
                relative_path=relative_path,
                root_type=root_type,
                node_types=node_types,
                node_names=node_names,
                scripts=scripts,
                resources=resources,
                mtime=mtime,
            )
        except Exception:
            pass

    def _reindex_resource(
        self, relative_path: str, full_path: str, index: ProjectIndex
    ) -> None:
        """Re-indexa un recurso específico."""
        from godot_mcp.core.tres_parser import parse_tres

        try:
            resource = parse_tres(full_path)
            path_obj = Path(full_path)
            mtime = path_obj.stat().st_mtime if path_obj.exists() else 0.0

            index.resources[relative_path] = ResourceInfo(
                path=full_path,
                relative_path=relative_path,
                resource_type=resource.header.type,
                script_class=resource.header.script_class,
                mtime=mtime,
            )
        except Exception:
            pass


# =============================================================================
# Gestor global de índices (cacheado)
# =============================================================================


# Instancias por proyecto
_indexers: dict[str, ProjectIndexer] = {}
_index_lock = threading.Lock()


def _get_indexer(project_path: str) -> ProjectIndexer:
    """Obtiene o crea un indexador para el proyecto."""
    with _index_lock:
        normalized = os.path.normpath(project_path)
        if normalized not in _indexers:
            _indexers[normalized] = ProjectIndexer(normalized)
        return _indexers[normalized]


def build_index(project_path: str, force: bool = False) -> ProjectIndex:
    """
    Construye el índice de un proyecto.

    Args:
        project_path: Ruta al directorio del proyecto (donde está project.godot)
        force: Si True, fuerza re-indexación completa

    Returns:
        ProjectIndex con toda la información indexada
    """
    indexer = _get_indexer(project_path)
    return indexer.build_index(force=force)


def get_index(project_path: str) -> ProjectIndex:
    """
    Obtiene el índice de un proyecto (usando cache si existe).

    Args:
        project_path: Ruta al directorio del proyecto

    Returns:
        ProjectIndex cacheado o construye uno nuevo
    """
    return build_index(project_path, force=False)


def find_scenes_using_resource(resource_path: str) -> list[str]:
    """
    Encuentra todas las escenas que usan un recurso específico.

    Args:
        resource_path: Ruta del recurso (res://...) o ruta absoluta

    Returns:
        Lista de rutas de escenas (res://...) que usan el recurso
    """
    # Normalizar la ruta
    if not resource_path.startswith("res://"):
        resource_path = _to_res_path(resource_path)

    # Obtener índice
    # Asumimos que hay un proyecto activo - necesitamos mejorarlo
    with _index_lock:
        for indexer in _indexers.values():
            index = indexer.build_index()
            if resource_path in index.scenes_using_resource:
                return index.scenes_using_resource[resource_path]
            # También buscar en recursos directamente
            if resource_path in index.resources:
                return index.resources[resource_path].used_by_scenes

    return []


def find_scripts_extending(base_class: str) -> list[str]:
    """
    Encuentra todos los scripts que extienden una clase específica.

    Args:
        base_class: Nombre de la clase base (ej: "CharacterBody2D", "Node")

    Returns:
        Lista de rutas de scripts (res://...) que extienden la clase
    """
    with _index_lock:
        for indexer in _indexers.values():
            index = indexer.build_index()
            return index.scripts_by_extends.get(base_class, [])

    return []


def search_by_type(node_type: str) -> list[str]:
    """
    Busca todas las escenas que contienen un tipo de nodo específico.

    Args:
        node_type: Tipo de nodo (ej: "CharacterBody2D", "Area2D", "Sprite2D")

    Returns:
        Lista de rutas de escenas (res://...) con ese tipo de nodo
    """
    with _index_lock:
        for indexer in _indexers.values():
            index = indexer.build_index()
            return index.scenes_by_node_type.get(node_type, [])

    return []


def invalidate_file(file_path: str) -> None:
    """
    Invalida un archivo específico en el índice.

    Args:
        file_path: Ruta absoluta del archivo que cambió
    """
    # Encontrar qué proyecto pertenece el archivo
    with _index_lock:
        for indexer in _indexers.values():
            project_path = indexer.project_path
            if file_path.startswith(project_path):
                indexer.invalidate_file(file_path)
                break


def get_unused_resources(project_path: str) -> list[str]:
    """
    Encuentra recursos que no son usados por ninguna escena.

    Args:
        project_path: Ruta al directorio del proyecto

    Returns:
        Lista de rutas de recursos (res://...) no usados
    """
    index = get_index(project_path)
    unused = []

    for res_path, resource in index.resources.items():
        # Verificar si está en scenes_using_resource
        if res_path not in index.scenes_using_resource:
            # Verificar si algún script lo usa
            used = False
            for script_path, scenes in index.scenes_using_script.items():
                if res_path in scenes:
                    used = True
                    break

            if not used:
                unused.append(res_path)

    return unused


# =============================================================================
# Watchdog - Detector de cambios en archivos
# =============================================================================


class ProjectFileHandler(FileSystemEventHandler):
    """Manejador de eventos de archivo para el watchdog."""

    def __init__(self, indexer: ProjectIndexer):
        self.indexer = indexer
        # Debounce para evitar múltiples eventos rápidos
        self._pending: dict[str, float] = {}
        self._debounce_seconds = 0.5

    def _schedule_invalidation(self, file_path: str) -> None:
        """Programa invalidación con debounce."""
        self._pending[file_path] = time.time() + self._debounce_seconds

    def _process_pending(self) -> None:
        """Procesa invalidaciones pendientes."""
        now = time.time()
        to_process = []

        for file_path, scheduled_time in list(self._pending.items()):
            if now >= scheduled_time:
                to_process.append(file_path)
                del self._pending[file_path]

        for file_path in to_process:
            self.indexer.invalidate_file(file_path)

    def on_modified(self, event: FileSystemEvent) -> None:
        """Called when a file is modified."""
        if event.is_directory:
            return

        if event.src_path.endswith((".gd", ".tscn", ".tres")):
            self._schedule_invalidation(event.src_path)

    def on_created(self, event: FileSystemEvent) -> None:
        """Called when a file is created."""
        if event.is_directory:
            return

        if event.src_path.endswith((".gd", ".tscn", ".tres")):
            # Forzar re-index completo cuando se crea un archivo nuevo
            self.indexer.build_index(force=True)

    def on_deleted(self, event: FileSystemEvent) -> None:
        """Called when a file is deleted."""
        if event.is_directory:
            return

        if event.src_path.endswith((".gd", ".tscn", ".tres")):
            self.indexer.invalidate_file(event.src_path)


def start_watchdog(project_path: str) -> Observer:
    """
    Inicia el watchdog para un proyecto.

    Args:
        project_path: Ruta al directorio del proyecto

    Returns:
        Observador activo (para poder detenerlo después)
    """
    indexer = _get_indexer(project_path)

    handler = ProjectFileHandler(indexer)
    observer = Observer()
    observer.schedule(handler, project_path, recursive=True)
    observer.start()

    return observer


def stop_watchdog(observer: Observer) -> None:
    """
    Detiene un observador de watchdog.

    Args:
        observer: Observador a detener
    """
    observer.stop()
    observer.join()


# =============================================================================
# Utilidades adicionales
# =============================================================================


def find_nodes_by_name_pattern(project_path: str, pattern: str) -> list[dict]:
    """
    Busca nodos en todas las escenas que coinciden con un patrón de nombre.

    Args:
        project_path: Ruta al proyecto
        pattern: Patrón con wildcards (ej: "Enemy*", "*Bullet")

    Returns:
        Lista de diccionarios con {scene_path, node_name, node_type}
    """
    import re

    index = get_index(project_path)

    # Convertir patrón glob a regex
    regex_pattern = "^" + pattern.replace("*", ".*").replace("?", ".") + "$"
    regex = re.compile(regex_pattern, re.IGNORECASE)

    results = []

    from godot_mcp.core.tscn_parser import parse_tscn

    for scene_path, scene_info in index.scenes.items():
        try:
            scene = parse_tscn(scene_info.path)
            for node in scene.nodes:
                if regex.match(node.name):
                    results.append(
                        {
                            "scene_path": scene_path,
                            "node_name": node.name,
                            "node_type": node.type,
                        }
                    )
        except Exception:
            pass

    return results


def get_project_stats(project_path: str) -> dict:
    """
    Obtiene estadísticas del proyecto.

    Args:
        project_path: Ruta al proyecto

    Returns:
        Diccionario con estadísticas
    """
    index = get_index(project_path)

    # Contar tipos de nodos
    node_type_counts: dict[str, int] = {}
    for scene in index.scenes.values():
        for node_type in scene.node_types:
            node_type_counts[node_type] = node_type_counts.get(node_type, 0) + 1

    return {
        "total_scenes": len(index.scenes),
        "total_scripts": len(index.scripts),
        "total_resources": len(index.resources),
        "node_type_counts": node_type_counts,
        "scripts_by_extends_count": {
            k: len(v) for k, v in index.scripts_by_extends.items()
        },
    }
