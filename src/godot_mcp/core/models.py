"""
Godot MCP - Modelos de estructuras de datos Godot

Este módulo contiene las dataclasses para representar estructuras Godot como:
- Scene: escena completa
- ExtResource: recursos externos
- SubResource: recursos embebidos
- Node: nodo con propiedades e hijos
- PropertyValue: valor de propiedad con tipo
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Optional, Union


# =============================================================================
# Tipos Godot
# =============================================================================


@dataclass
class GodotVector2:
    """Representa un Vector2 de Godot."""

    x: float = 0.0
    y: float = 0.0

    def to_dict(self) -> dict:
        return {"x": self.x, "y": self.y}

    @classmethod
    def from_dict(cls, data: dict) -> GodotVector2:
        return cls(x=data.get("x", 0.0), y=data.get("y", 0.0))


@dataclass
class GodotVector3:
    """Representa un Vector3 de Godot."""

    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def to_dict(self) -> dict:
        return {"x": self.x, "y": self.y, "z": self.z}

    @classmethod
    def from_dict(cls, data: dict) -> GodotVector3:
        return cls(x=data.get("x", 0.0), y=data.get("y", 0.0), z=data.get("z", 0.0))


@dataclass
class GodotColor:
    """Representa un Color de Godot."""

    r: float = 1.0
    g: float = 1.0
    b: float = 1.0
    a: float = 1.0

    def to_dict(self) -> dict:
        return {"r": self.r, "g": self.g, "b": self.b, "a": self.a}

    @classmethod
    def from_dict(cls, data: dict) -> GodotColor:
        return cls(
            r=data.get("r", 1.0),
            g=data.get("g", 1.0),
            b=data.get("b", 1.0),
            a=data.get("a", 1.0),
        )


@dataclass
class GodotRect2:
    """Representa un Rect2 de Godot."""

    position: GodotVector2 = field(default_factory=GodotVector2)
    size: GodotVector2 = field(default_factory=GodotVector2)

    def to_dict(self) -> dict:
        return {"position": self.position.to_dict(), "size": self.size.to_dict()}

    @classmethod
    def from_dict(cls, data: dict) -> GodotRect2:
        return cls(
            position=GodotVector2.from_dict(data.get("position", {})),
            size=GodotVector2.from_dict(data.get("size", {})),
        )


@dataclass
class GodotNodePath:
    """Representa un NodePath de Godot."""

    path: str = ""

    def to_dict(self) -> dict:
        return {"path": self.path}

    @classmethod
    def from_dict(cls, data: dict) -> GodotNodePath:
        return cls(path=data.get("path", ""))


@dataclass
class GodotStringName:
    """Representa un StringName de Godot."""

    name: str = ""

    def to_dict(self) -> dict:
        return {"name": self.name}

    @classmethod
    def from_dict(cls, data: dict) -> GodotStringName:
        return cls(name=data.get("name", ""))


@dataclass
class GodotArray:
    """Representa un Array de Godot."""

    items: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"items": self.items}

    @classmethod
    def from_dict(cls, data: dict) -> GodotArray:
        return cls(items=data.get("items", []))


@dataclass
class GodotDictionary:
    """Representa un Dictionary de Godot."""

    data: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {"data": self.data}

    @classmethod
    def from_dict(cls, data: dict) -> GodotDictionary:
        return cls(data=data.get("data", {}))


# =============================================================================
# PropertyValue
# =============================================================================


@dataclass
class PropertyValue:
    """
    Representa un valor de propiedad con su tipo en Godot.

    Attributes:
        value: El valor de la propiedad
        type: El tipo de Godot (string, int, float, Vector2, etc.)
    """

    value: Any = None
    type: str = "null"

    def to_dict(self) -> dict:
        return {"value": self._serialize_value(self.value), "type": self.type}

    def _serialize_value(self, val: Any) -> Any:
        """Serializa el valor según su tipo."""
        if isinstance(
            val,
            (
                GodotVector2,
                GodotVector3,
                GodotColor,
                GodotRect2,
                GodotNodePath,
                GodotStringName,
                GodotArray,
                GodotDictionary,
            ),
        ):
            return val.to_dict()
        elif isinstance(val, PropertyValue):
            return val.to_dict()
        elif isinstance(val, list):
            return [self._serialize_value(item) for item in val]
        elif isinstance(val, dict):
            return {k: self._serialize_value(v) for k, v in val.items()}
        return val

    @classmethod
    def from_dict(cls, data: dict) -> PropertyValue:
        """Crea un PropertyValue desde un diccionario."""
        value = data.get("value")
        type_name = data.get("type", "null")

        # Convertir valores según el tipo
        if value is not None:
            value = cls._deserialize_value(value, type_name)

        return cls(value=value, type=type_name)

    @staticmethod
    def _deserialize_value(value: Any, type_name: str) -> Any:
        """Deserializa un valor según su tipo."""
        if type_name == "Vector2":
            return GodotVector2.from_dict(value) if isinstance(value, dict) else value
        elif type_name == "Vector3":
            return GodotVector3.from_dict(value) if isinstance(value, dict) else value
        elif type_name == "Color":
            return GodotColor.from_dict(value) if isinstance(value, dict) else value
        elif type_name == "Rect2":
            return GodotRect2.from_dict(value) if isinstance(value, dict) else value
        elif type_name == "NodePath":
            return GodotNodePath.from_dict(value) if isinstance(value, dict) else value
        elif type_name == "StringName":
            return (
                GodotStringName.from_dict(value) if isinstance(value, dict) else value
            )
        elif type_name == "Array":
            return GodotArray.from_dict(value) if isinstance(value, dict) else value
        elif type_name == "Dictionary":
            return (
                GodotDictionary.from_dict(value) if isinstance(value, dict) else value
            )
        return value


# =============================================================================
# Resource Types
# =============================================================================


@dataclass
class ExtResource:
    """
    Representa un recurso externo en Godot.

    Attributes:
        id: Identificador único del recurso
        type: Tipo de recurso (ej: "PackedScene", "Script")
        path: Ruta del recurso (ej: "res://scenes/Player.tscn")
    """

    id: str = ""
    type: str = ""
    path: str = ""

    def to_dict(self) -> dict:
        return {"id": self.id, "type": self.type, "path": self.path}

    @classmethod
    def from_dict(cls, data: dict) -> ExtResource:
        return cls(
            id=data.get("id", ""), type=data.get("type", ""), path=data.get("path", "")
        )


@dataclass
class SubResource:
    """
    Representa un recurso embebido en Godot.

    Attributes:
        id: Identificador único del recurso
        type: Tipo de recurso
        values: Propiedades del recurso
    """

    id: str = ""
    type: str = ""
    values: dict[str, PropertyValue] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type,
            "values": {k: v.to_dict() for k, v in self.values.items()},
        }

    @classmethod
    def from_dict(cls, data: dict) -> SubResource:
        values = {}
        for k, v in data.get("values", {}).items():
            values[k] = PropertyValue.from_dict(v) if isinstance(v, dict) else v
        return cls(id=data.get("id", ""), type=data.get("type", ""), values=values)


# =============================================================================
# Node
# =============================================================================


@dataclass
class Node:
    """
    Representa un nodo en una escena de Godot.

    Attributes:
        name: Nombre del nodo
        type: Tipo de nodo (ej: "Node2D", "CharacterBody2D")
        properties: Propiedades del nodo
        children: Hijos del nodo
        parent_path: Ruta del nodo padre
    """

    name: str = ""
    type: str = ""
    properties: dict[str, PropertyValue] = field(default_factory=dict)
    children: list[Node] = field(default_factory=list)
    parent_path: str = ""

    def to_dict(self) -> dict:
        """Convierte el nodo a diccionario."""
        return {
            "name": self.name,
            "type": self.type,
            "properties": {k: v.to_dict() for k, v in self.properties.items()},
            "children": [child.to_dict() for child in self.children],
            "parent_path": self.parent_path,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Node:
        """Crea un nodo desde un diccionario."""
        properties = {}
        for k, v in data.get("properties", {}).items():
            if isinstance(v, dict):
                properties[k] = PropertyValue.from_dict(v)
            else:
                properties[k] = PropertyValue(value=v, type=typeof(v))

        children = [Node.from_dict(child) for child in data.get("children", [])]

        return cls(
            name=data.get("name", ""),
            type=data.get("type", ""),
            properties=properties,
            children=children,
            parent_path=data.get("parent_path", ""),
        )

    def get_property(self, key: str, default: Any = None) -> Any:
        """Obtiene el valor de una propiedad."""
        prop = self.properties.get(key)
        return prop.value if prop else default

    def set_property(self, key: str, value: Any, type_name: str = "null") -> None:
        """Establece una propiedad."""
        self.properties[key] = PropertyValue(value=value, type=type_name)

    def add_child(self, child: Node) -> None:
        """Añade un hijo al nodo."""
        child.parent_path = f"{self.get_path()}/{child.name}"
        self.children.append(child)

    def get_path(self) -> str:
        """Obtiene la ruta completa del nodo."""
        return self.parent_path + "/" + self.name if self.parent_path else self.name


def typeof(value: Any) -> str:
    """Determina el tipo de Godot para un valor."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "float"
    if isinstance(value, str):
        return "String"
    if isinstance(value, GodotVector2):
        return "Vector2"
    if isinstance(value, GodotVector3):
        return "Vector3"
    if isinstance(value, GodotColor):
        return "Color"
    if isinstance(value, GodotRect2):
        return "Rect2"
    if isinstance(value, GodotNodePath):
        return "NodePath"
    if isinstance(value, GodotStringName):
        return "StringName"
    if isinstance(value, (list, GodotArray)):
        return "Array"
    if isinstance(value, (dict, GodotDictionary)):
        return "Dictionary"
    return "null"


# =============================================================================
# Scene
# =============================================================================


@dataclass
class Scene:
    """
    Representa una escena completa de Godot.

    Attributes:
        gd_scene: Versión del formato de escena
        ext_resources: Lista de recursos externos
        sub_resources: Lista de recursos embebidos
        root: Nodo raíz de la escena
    """

    gd_scene: str = "4.0"
    ext_resources: list[ExtResource] = field(default_factory=list)
    sub_resources: list[SubResource] = field(default_factory=list)
    root: Optional[Node] = None

    def to_dict(self) -> dict:
        """Convierte la escena a diccionario."""
        return {
            "gd_scene": self.gd_scene,
            "ext_resources": [r.to_dict() for r in self.ext_resources],
            "sub_resources": [r.to_dict() for r in self.sub_resources],
            "root": self.root.to_dict() if self.root else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Scene:
        """Crea una escena desde un diccionario."""
        ext_resources = [
            ExtResource.from_dict(r) for r in data.get("ext_resources", [])
        ]
        sub_resources = [
            SubResource.from_dict(r) for r in data.get("sub_resources", [])
        ]
        root = Node.from_dict(data["root"]) if data.get("root") else None

        return cls(
            gd_scene=data.get("gd_scene", "4.0"),
            ext_resources=ext_resources,
            sub_resources=sub_resources,
            root=root,
        )

    def add_ext_resource(self, resource: ExtResource) -> None:
        """Añade un recurso externo."""
        self.ext_resources.append(resource)

    def add_sub_resource(self, resource: SubResource) -> None:
        """Añade un recurso embebido."""
        self.sub_resources.append(resource)

    def get_node_by_path(self, path: str) -> Optional[Node]:
        """
        Obtiene un nodo por su ruta.

        Args:
            path: Ruta del nodo (ej: "root/child/grandchild")

        Returns:
            El nodo encontrado o None si no existe
        """
        if not self.root:
            return None

        # Manejar ruta absoluta desde la raíz
        path = path.strip("/")
        parts = path.split("/")

        if not parts or parts[0] == "":
            return None

        current = self.root

        # Si el primer elemento no es el nombre del root, empezar desde root
        if parts[0] != current.name:
            # Buscar desde la raíz
            return self._find_node_recursive(self.root, parts[0], parts[1:])

        # Navegar a través de la ruta
        for part in parts[1:]:
            found = self._find_child_by_name(current, part)
            if not found:
                return None
            current = found

        return current

    def _find_child_by_name(self, node: Node, name: str) -> Optional[Node]:
        """Encuentra un hijo directo por nombre."""
        for child in node.children:
            if child.name == name:
                return child
        return None

    def _find_node_recursive(
        self, node: Node, name: str, remaining_path: list[str]
    ) -> Optional[Node]:
        """Busca recursivamente un nodo."""
        # Buscar en hijos directos
        for child in node.children:
            if child.name == name:
                if not remaining_path:
                    return child
                return self._find_node_recursive(
                    child, remaining_path[0], remaining_path[1:]
                )
        return None

    def get_children_of(self, node_path: str) -> list[Node]:
        """
        Obtiene los hijos de un nodo.

        Args:
            path: Ruta del nodo padre

        Returns:
            Lista de nodos hijos
        """
        node = self.get_node_by_path(node_path)
        return node.children if node else []

    def find_nodes_by_type(self, type_name: str) -> list[Node]:
        """
        Busca todos los nodos de un tipo específico.

        Args:
            type_name: Tipo de nodo (ej: "Area2D", "Sprite2D")

        Returns:
            Lista de nodos encontrados
        """
        if not self.root:
            return []

        results = []
        self._find_by_type_recursive(self.root, type_name, results)
        return results

    def _find_by_type_recursive(
        self, node: Node, type_name: str, results: list[Node]
    ) -> None:
        """Búsqueda recursiva por tipo."""
        if node.type == type_name:
            results.append(node)
        for child in node.children:
            self._find_by_type_recursive(child, type_name, results)

    def find_nodes_by_name(self, pattern: str) -> list[Node]:
        """
        Busca nodos por patrón de nombre (soporta wildcards).

        Args:
            pattern: Patrón con wildcards (ej: "Enemy*", "*Bullet")

        Returns:
            Lista de nodos encontrados
        """
        if not self.root:
            return []

        # Convertir patrón glob a regex
        regex_pattern = "^" + pattern.replace("*", ".*").replace("?", ".") + "$"
        regex = re.compile(regex_pattern, re.IGNORECASE)

        results = []
        self._find_by_name_recursive(self.root, regex, results)
        return results

    def _find_by_name_recursive(
        self, node: Node, pattern: re.Pattern, results: list[Node]
    ) -> None:
        """Búsqueda recursiva por nombre."""
        if pattern.match(node.name):
            results.append(node)
        for child in node.children:
            self._find_by_name_recursive(child, pattern, results)

    def get_all_nodes(self) -> list[Node]:
        """Obtiene todos los nodos de la escena."""
        if not self.root:
            return []

        results = []
        self._collect_all_nodes(self.root, results)
        return results

    def _collect_all_nodes(self, node: Node, results: list[Node]) -> None:
        """Recolecta todos los nodos recursivamente."""
        results.append(node)
        for child in node.children:
            self._collect_all_nodes(child, results)


# =============================================================================
# Funciones de utilidad
# =============================================================================


def create_scene(root_type: str = "Node", root_name: str = "root") -> Scene:
    """Crea una nueva escena vacía."""
    root = Node(name=root_name, type=root_type)
    return Scene(root=root)


def create_node(node_type: str, node_name: str, **properties) -> Node:
    """Crea un nuevo nodo con propiedades."""
    node = Node(name=node_name, type=node_type)
    for key, value in properties.items():
        node.set_property(key, value, typeof(value))
    return node
