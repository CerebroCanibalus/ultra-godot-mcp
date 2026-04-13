"""
Resource Parser - Native Python parser for Godot 4.x .tres files

Parses .tres files (resource format). Similar to TSCN but for resources only.
"""

from __future__ import annotations

import hashlib
import os
import re
from dataclasses import dataclass, field
from typing import Any, Optional

from godot_mcp.core.tscn_parser import _format_gdscript_value, _parse_gdscript_value


@dataclass
class ResourceHeader:
    """Header section [gd_resource]"""

    type: str = ""
    load_steps: int = 1
    format: int = 3
    uid: str = ""
    script_class: str = ""

    def to_dict(self) -> dict:
        result = {
            "type": self.type,
            "load_steps": self.load_steps,
            "format": self.format,
        }
        if self.uid:
            result["uid"] = self.uid
        if self.script_class:
            result["script_class"] = self.script_class
        return result

    def to_tres(self) -> str:
        parts = [
            f'type="{self.type}"',
            f"load_steps={self.load_steps}",
            f"format={self.format}",
        ]
        if self.uid:
            parts.append(f'uid="{self.uid}"')
        if self.script_class:
            parts.append(f'script_class="{self.script_class}"')
        return f"[gd_resource {' '.join(parts)}]"


@dataclass
class Resource:
    """Complete parsed .tres resource file"""

    header: ResourceHeader = field(default_factory=ResourceHeader)
    properties: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "header": self.header.to_dict(),
            "properties": self.properties,
        }

    def to_tres(self) -> str:
        lines = []

        # Header
        lines.append(self.header.to_tres())
        lines.append("")

        # Properties
        for key, value in self.properties.items():
            formatted_value = _format_gdscript_value(value)
            lines.append(f"{key} = {formatted_value}")

        return "\n".join(lines)


# ============ PARSING FUNCTIONS ============


def _parse_resource_header(line: str) -> dict:
    """Parse [gd_resource] header line"""
    result = {
        "load_steps": 1,
        "format": 3,
    }

    content = line.strip().strip("[]")
    parts = content.split()

    # First part is "gd_resource", skip it
    for part in parts[1:]:
        if "=" in part:
            key, value = part.split("=", 1)
            value = value.strip('"')

            if key == "load_steps" or key == "format":
                result[key] = int(value)
            else:
                result[key] = value

    return result


def parse_tres_string(content: str) -> Resource:
    """Parse .tres content from string"""
    lines = content.split("\n")

    resource = Resource()
    in_header = True

    for line in lines:
        line = line.strip()

        if not line or line.startswith(";"):
            continue

        # Check for header
        if line.startswith("[gd_resource"):
            in_header = True
            data = _parse_resource_header(line)
            resource.header = ResourceHeader(
                type=data.get("type", ""),
                load_steps=data.get("load_steps", 1),
                format=data.get("format", 3),
                uid=data.get("uid", ""),
                script_class=data.get("script_class", ""),
            )

        # Property line
        elif " = " in line:
            key, value = line.split(" = ", 1)
            key = key.strip()
            value = value.strip()
            parsed_value = _parse_gdscript_value(value)
            resource.properties[key] = parsed_value

    return resource


def parse_tres(file_path: str) -> Resource:
    """Parse .tres file from path"""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    return parse_tres_string(content)


# ============ UID GENERATION ============


def generate_uid_from_path(file_path: str) -> str:
    """Generate a UID based on the file path (Godot 4.4+ style)"""
    # Normalize path separators
    normalized = file_path.replace("\\", "/")

    # Hash the path to create a unique ID
    path_hash = hashlib.md5(normalized.encode()).hexdigest()[:12]

    return f"uid://{path_hash}"


def extract_uid_from_tres(file_path: str) -> Optional[str]:
    """Extract UID from existing .tres file"""
    try:
        resource = parse_tres(file_path)
        return resource.header.uid if resource.header.uid else None
    except Exception:
        return None


# ============ TEST ============


def main():
    """Test parser with example .tres content"""
    example = """[gd_resource type="Resource" format=3 uid="uid://abc123"]

resource_name = "TestResource"
value = 42
enabled = true
position = Vector2(10, 20)
tags = ["tag1", "tag2"]
metadata = {"key": "value"}
"""

    print("=" * 60)
    print("Parsing example .tres...")
    print("=" * 60)

    resource = parse_tres_string(example)

    print(f"\nHeader: {resource.header}")
    print(f"  type: {resource.header.type}")
    print(f"  load_steps: {resource.header.load_steps}")
    print(f"  format: {resource.header.format}")
    print(f"  uid: {resource.header.uid}")

    print(f"\nProperties: {len(resource.properties)}")
    for key, value in resource.properties.items():
        print(f"  {key} = {value}")

    print("\n" + "=" * 60)
    print("Converting back to .tres...")
    print("=" * 60)

    output = resource.to_tres()
    print(output)


if __name__ == "__main__":
    main()
