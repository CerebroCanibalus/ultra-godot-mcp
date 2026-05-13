"""
GDShader Parser - Analizador de sintaxis para archivos .gdshader

Extrae metadatos estructurados de shaders Godot:
- Uniforms (nombre, tipo, default, hint)
- Render modes
- Funciones (vertex, fragment, light, custom)
- Includes (.gdshaderinc)
- Métricas de complejidad (branches, loops, texture samples)
- Varyings
- Constants
- Sampler uniforms y sus texturas asociadas
"""

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class ShaderUniform:
    """Representa un uniform en un shader."""
    name: str
    type: str
    default_value: Optional[str] = None
    hint: Optional[str] = None  # e.g., "hint_range(0.0, 1.0)"
    line_number: int = 0
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "type": self.type,
            "default": self.default_value,
            "hint": self.hint,
            "line": self.line_number,
        }


@dataclass
class ShaderFunction:
    """Representa una función en un shader."""
    name: str
    return_type: str = "void"
    line_number: int = 0
    is_builtin: bool = False  # vertex, fragment, light
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "return_type": self.return_type,
            "line": self.line_number,
            "builtin": self.is_builtin,
        }


@dataclass
class ShaderVarying:
    """Representa un varying en un shader."""
    name: str
    type: str
    line_number: int = 0
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "type": self.type,
            "line": self.line_number,
        }


@dataclass
class ShaderInclude:
    """Representa un include de shader."""
    path: str
    line_number: int = 0
    resolved: bool = False
    
    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "line": self.line_number,
            "resolved": self.resolved,
        }


@dataclass
class ShaderAnalysis:
    """Resultado completo del análisis de un shader."""
    shader_type: str = ""  # spatial, canvas_item, particles, sky, fog
    render_modes: list[str] = field(default_factory=list)
    uniforms: list[ShaderUniform] = field(default_factory=list)
    varyings: list[ShaderVarying] = field(default_factory=list)
    functions: list[ShaderFunction] = field(default_factory=list)
    includes: list[ShaderInclude] = field(default_factory=list)
    constants: list[dict] = field(default_factory=list)
    
    # Métricas de complejidad
    complexity: dict = field(default_factory=lambda: {
        "branch_count": 0,
        "loop_count": 0,
        "texture_samples": 0,
        "instruction_estimate": 0,
        "function_count": 0,
        "uniform_count": 0,
    })
    
    # Advertencias detectadas
    warnings: list[str] = field(default_factory=list)
    
    # Metadata
    line_count: int = 0
    file_path: str = ""
    
    def to_dict(self) -> dict:
        return {
            "shader_type": self.shader_type,
            "render_modes": self.render_modes,
            "uniforms": [u.to_dict() for u in self.uniforms],
            "varyings": [v.to_dict() for v in self.varyings],
            "functions": [f.to_dict() for f in self.functions],
            "includes": [i.to_dict() for i in self.includes],
            "constants": self.constants,
            "complexity": self.complexity,
            "warnings": self.warnings,
            "line_count": self.line_count,
            "file_path": self.file_path,
        }


class GDShaderParser:
    """
    Parser de archivos .gdshader de Godot 4.x.
    
    Extrae información estructurada sin necesidad de compilar,
    usando análisis léxico basado en regex.
    """
    
    # Patrones regex para análisis
    SHADER_TYPE_PATTERN = re.compile(r'^\s*shader_type\s+(\w+)\s*;')
    RENDER_MODE_PATTERN = re.compile(r'^\s*render_mode\s+([^;]+);')
    UNIFORM_PATTERN = re.compile(
        r'^\s*uniform\s+(\w+)\s+(\w+)\s*(?::\s*([^;]+))?\s*(?:=\s*([^;]+))?\s*;'
    )
    VARYING_PATTERN = re.compile(r'^\s*varying\s+(\w+)\s+(\w+)\s*;')
    CONST_PATTERN = re.compile(
        r'^\s*const\s+(\w+)\s+(\w+)\s*=\s*([^;]+)\s*;'
    )
    FUNCTION_PATTERN = re.compile(
        r'^\s*(\w+)\s+(\w+)\s*\([^)]*\)\s*\{'
    )
    INCLUDE_PATTERN = re.compile(r'^\s*#include\s+["\']([^"\']+)["\']')
    
    # Patrones de análisis de complejidad
    BRANCH_PATTERN = re.compile(r'\b(if|else|switch)\b')
    LOOP_PATTERN = re.compile(r'\b(for|while|do)\b')
    TEXTURE_PATTERN = re.compile(r'\btexture\s*\(')
    DISCARD_PATTERN = re.compile(r'\bdiscard\s*;')
    
    # Tipos de shader válidos en Godot 4.x
    VALID_SHADER_TYPES = {
        "spatial", "canvas_item", "particles", "sky", "fog"
    }
    
    # Funciones built-in
    BUILTIN_FUNCTIONS = {"vertex", "fragment", "light"}
    
    def __init__(self):
        self.analysis = ShaderAnalysis()
    
    def parse_file(self, file_path: str) -> ShaderAnalysis:
        """
        Parsear un archivo .gdshader completo.
        
        Args:
            file_path: Ruta al archivo .gdshader
            
        Returns:
            ShaderAnalysis con todos los metadatos extraídos
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Shader file not found: {file_path}")
        
        content = path.read_text(encoding="utf-8")
        self.analysis = ShaderAnalysis(file_path=file_path)
        
        lines = content.splitlines()
        self.analysis.line_count = len(lines)
        
        in_function = False
        function_depth = 0
        current_function = None
        
        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # Ignorar líneas vacías y comentarios
            if not stripped or stripped.startswith("//"):
                continue
            
            # Shader type
            match = self.SHADER_TYPE_PATTERN.match(stripped)
            if match:
                self.analysis.shader_type = match.group(1)
                if self.analysis.shader_type not in self.VALID_SHADER_TYPES:
                    self.analysis.warnings.append(
                        f"Tipo de shader desconocido: {self.analysis.shader_type}"
                    )
                continue
            
            # Render modes
            match = self.RENDER_MODE_PATTERN.match(stripped)
            if match:
                modes = [m.strip() for m in match.group(1).split(",")]
                self.analysis.render_modes.extend(modes)
                continue
            
            # Includes
            match = self.INCLUDE_PATTERN.match(stripped)
            if match:
                include_path = match.group(1)
                resolved = (path.parent / include_path).exists()
                self.analysis.includes.append(
                    ShaderInclude(
                        path=include_path,
                        line_number=line_num,
                        resolved=resolved,
                    )
                )
                continue
            
            # Uniforms
            match = self.UNIFORM_PATTERN.match(stripped)
            if match:
                uniform_type = match.group(1)
                uniform_name = match.group(2)
                hint = match.group(3)
                default = match.group(4)
                
                self.analysis.uniforms.append(
                    ShaderUniform(
                        name=uniform_name,
                        type=uniform_type,
                        default_value=default.strip() if default else None,
                        hint=hint.strip() if hint else None,
                        line_number=line_num,
                    )
                )
                continue
            
            # Varyings
            match = self.VARYING_PATTERN.match(stripped)
            if match:
                self.analysis.varyings.append(
                    ShaderVarying(
                        type=match.group(1),
                        name=match.group(2),
                        line_number=line_num,
                    )
                )
                continue
            
            # Constants
            match = self.CONST_PATTERN.match(stripped)
            if match:
                self.analysis.constants.append({
                    "type": match.group(1),
                    "name": match.group(2),
                    "value": match.group(3).strip(),
                    "line": line_num,
                })
                continue
            
            # Functions (detección del inicio)
            match = self.FUNCTION_PATTERN.match(stripped)
            if match and not in_function:
                return_type = match.group(1)
                func_name = match.group(2)
                
                # Skip built-in types usados como variables
                if return_type in {"vec2", "vec3", "vec4", "mat2", "mat3", "mat4", 
                                   "int", "float", "bool", "uint", "void"}:
                    current_function = ShaderFunction(
                        name=func_name,
                        return_type=return_type,
                        line_number=line_num,
                        is_builtin=func_name in self.BUILTIN_FUNCTIONS,
                    )
                    self.analysis.functions.append(current_function)
                    in_function = True
                    function_depth = 1
                continue
            
            # Tracking de profundidad de función para análisis interno
            if in_function:
                function_depth += stripped.count("{")
                function_depth -= stripped.count("}")
                
                if function_depth <= 0:
                    in_function = False
                    current_function = None
                    continue
                
                # Análisis de complejidad dentro de funciones
                self._analyze_complexity(stripped, line_num)
        
        # Calcular métricas finales
        self._compute_metrics()
        
        return self.analysis
    
    def parse_string(self, code: str, file_path: str = "<string>") -> ShaderAnalysis:
        """Parsear código de shader desde string."""
        self.analysis = ShaderAnalysis(file_path=file_path)
        
        lines = code.splitlines()
        self.analysis.line_count = len(lines)
        
        # Reusar lógica de parse_file pero desde string
        # (Implementación similar, omitida por brevedad)
        # En su lugar, escribimos a archivo temporal y parseamos
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.gdshader', delete=False, encoding='utf-8'
        ) as f:
            f.write(code)
            temp_path = f.name
        
        try:
            return self.parse_file(temp_path)
        finally:
            os.unlink(temp_path)
    
    def _analyze_complexity(self, line: str, line_num: int):
        """Analizar complejidad de una línea de código."""
        # Branches
        branches = len(self.BRANCH_PATTERN.findall(line))
        self.analysis.complexity["branch_count"] += branches
        
        # Loops
        loops = len(self.LOOP_PATTERN.findall(line))
        self.analysis.complexity["loop_count"] += loops
        
        # Texture samples
        textures = len(self.TEXTURE_PATTERN.findall(line))
        self.analysis.complexity["texture_samples"] += textures
        
        # Detectar loops con variables no-constantes (warning)
        if "for" in line.lower():
            if not re.search(r'for\s*\(\s*(?:int|uint)\s+\w+\s*=\s*\d+', line):
                # Loop potencialmente no-constante
                self.analysis.warnings.append(
                    f"Loop en línea {line_num} puede usar variable no-constante "
                    f"(lento en mobile/WebGL)"
                )
        
        # Detectar discard temprano sin justificación
        if self.DISCARD_PATTERN.search(line):
            # Solo warning si no hay condición previa visible
            pass  # Se analiza mejor en el contexto completo
        
        # Detectar división por varyings en fragment (precisión)
        if "/" in line and any(v.name in line for v in self.analysis.varyings):
            if "highp" not in line:
                self.analysis.warnings.append(
                    f"División con varying en línea {line_num} - "
                    f"considerar highp en mobile para evitar artifacts"
                )
    
    def _compute_metrics(self):
        """Calcular métricas finales."""
        self.analysis.complexity["function_count"] = len(self.analysis.functions)
        self.analysis.complexity["uniform_count"] = len(self.analysis.uniforms)
        
        # Estimación rough de instrucciones
        # texture samples son ~10 instrucciones cada uno
        # branches son ~2 instrucciones
        # loops multiplican su cuerpo
        est = (
            self.analysis.complexity["texture_samples"] * 10 +
            self.analysis.complexity["branch_count"] * 2 +
            self.analysis.line_count  # rough estimate
        )
        self.analysis.complexity["instruction_estimate"] = est
        
        # Warnings adicionales
        if self.analysis.complexity["texture_samples"] > 4:
            self.analysis.warnings.append(
                f"{self.analysis.complexity['texture_samples']} texture() calls - "
                f"considerar batching en atlas para mejor performance"
            )
        
        if not self.analysis.shader_type:
            self.analysis.warnings.append(
                "No se encontró declaración 'shader_type' - shader no será válido"
            )
    
    def get_uniform_names(self) -> list[str]:
        """Obtener lista de nombres de uniforms."""
        return [u.name for u in self.analysis.uniforms]
    
    def get_uniform_by_name(self, name: str) -> Optional[ShaderUniform]:
        """Buscar uniform por nombre."""
        for u in self.analysis.uniforms:
            if u.name == name:
                return u
        return None
    
    def get_builtin_functions(self) -> list[ShaderFunction]:
        """Obtener solo funciones built-in (vertex/fragment/light)."""
        return [f for f in self.analysis.functions if f.is_builtin]
    
    def has_render_mode(self, mode: str) -> bool:
        """Verificar si tiene un render mode específico."""
        return mode in self.analysis.render_modes
    
    @staticmethod
    def validate_shader_code(code: str) -> tuple[bool, list[str]]:
        """
        Validación rápida de sintaxis sin compilar.
        
        Returns:
            (is_valid, list_of_errors)
        """
        errors = []
        lines = code.splitlines()
        
        has_shader_type = False
        has_main_function = False
        brace_count = 0
        
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if not stripped or stripped.startswith("//"):
                continue
            
            # Verificar shader_type
            if GDShaderParser.SHADER_TYPE_PATTERN.match(stripped):
                has_shader_type = True
            
            # Verificar funciones principales
            if re.search(r'\b(vertex|fragment|light)\s*\(', stripped):
                has_main_function = True
            
            # Balance de llaves
            brace_count += stripped.count("{")
            brace_count -= stripped.count("}")
            
            if brace_count < 0:
                errors.append(f"Línea {i}: Llave de cierre excede aperturas")
        
        if brace_count != 0:
            errors.append(f"Desbalance de llaves: {brace_count} sin cerrar")
        
        if not has_shader_type:
            errors.append("Falta declaración 'shader_type'")
        
        if not has_main_function:
            errors.append("No se encontró función vertex(), fragment() o light()")
        
        # Verificar uniforms duplicados
        uniform_names = []
        for line in lines:
            match = GDShaderParser.UNIFORM_PATTERN.match(line.strip())
            if match:
                name = match.group(2)
                if name in uniform_names:
                    errors.append(f"Uniform duplicado: {name}")
                uniform_names.append(name)
        
        return len(errors) == 0, errors


def quick_parse_shader(file_path: str) -> dict:
    """
    Función de conveniencia para parseo rápido.
    
    Args:
        file_path: Ruta al .gdshader
        
    Returns:
        Dict con análisis completo
    """
    parser = GDShaderParser()
    analysis = parser.parse_file(file_path)
    return analysis.to_dict()
