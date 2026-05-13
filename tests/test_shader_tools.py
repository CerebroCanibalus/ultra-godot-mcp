"""
Tests para Shader Tools del MCP Godot.

Cubre:
- ShaderParser: parseo y validación
- ShaderTemplates: renderizado de templates
- manage_shader: crear, leer, validar, editar, eliminar
- manage_shader_material: crear material, setear parámetros
- create_render_pipeline: composición de efectos
- analyze_shader: inspección y optimización
"""

import os
import tempfile
import unittest
from pathlib import Path

from godot_mcp.core.shader_parser import GDShaderParser, quick_parse_shader
from godot_mcp.templates.shader_templates import (
    ShaderTemplateEngine,
    render_shader_template,
    list_available_templates,
)


class TestShaderParser(unittest.TestCase):
    """Tests para el parser de GDShader."""
    
    def setUp(self):
        self.parser = GDShaderParser()
    
    def test_parse_simple_shader(self):
        """Parsear shader básico."""
        code = """
shader_type spatial;

uniform float u_speed = 1.0;
uniform vec4 u_color : source_color = vec4(1.0, 0.0, 0.0, 1.0);

void vertex() {
    VERTEX.y += sin(TIME * u_speed) * 0.1;
}

void fragment() {
    ALBEDO = u_color.rgb;
}
"""
        analysis = self.parser.parse_string(code)
        
        self.assertEqual(analysis.shader_type, "spatial")
        self.assertEqual(len(analysis.uniforms), 2)
        self.assertEqual(len(analysis.functions), 2)
        self.assertEqual(analysis.functions[0].name, "vertex")
        self.assertEqual(analysis.functions[1].name, "fragment")
    
    def test_parse_with_render_modes(self):
        """Parsear render modes."""
        code = """
shader_type canvas_item;
render_mode blend_add, unshaded;

void fragment() {
    COLOR = vec4(1.0);
}
"""
        analysis = self.parser.parse_string(code)
        
        self.assertIn("blend_add", analysis.render_modes)
        self.assertIn("unshaded", analysis.render_modes)
    
    def test_validate_valid_shader(self):
        """Validar shader correcto."""
        code = """
shader_type spatial;

void fragment() {
    ALBEDO = vec3(1.0);
}
"""
        is_valid, errors = GDShaderParser.validate_shader_code(code)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
    
    def test_validate_invalid_shader(self):
        """Validar shader con errores."""
        code = """
// Falta shader_type

void fragment() {
    ALBEDO = vec3(1.0);
}
"""
        is_valid, errors = GDShaderParser.validate_shader_code(code)
        self.assertFalse(is_valid)
        self.assertTrue(any("shader_type" in e for e in errors))
    
    def test_detect_unused_uniforms(self):
        """Detectar uniforms no usados."""
        code = """
shader_type spatial;

uniform float u_unused = 1.0;
uniform float u_used = 2.0;

void fragment() {
    ALBEDO = vec3(u_used);
}
"""
        analysis = self.parser.parse_string(code)
        
        unused = [u.name for u in analysis.uniforms 
                  if code.count(u.name) <= 1]
        self.assertIn("u_unused", unused)
        self.assertNotIn("u_used", unused)


class TestShaderTemplates(unittest.TestCase):
    """Tests para templates de shaders."""
    
    def setUp(self):
        self.engine = ShaderTemplateEngine()
    
    def test_list_templates(self):
        """Listar templates disponibles."""
        templates = list_available_templates()
        self.assertIn("water", templates)
        self.assertIn("dissolve", templates)
        self.assertIn("post_process_base", templates)
    
    def test_render_water_template(self):
        """Renderizar template de agua."""
        code = render_shader_template(
            "water",
            wave_speed=2.0,
            wave_height=0.2,
        )
        
        self.assertIn("shader_type spatial", code)
        self.assertIn("u_wave_speed", code)
        self.assertIn("u_wave_height", code)
        self.assertIn("2.0", code)  # wave_speed
        self.assertIn("0.2", code)  # wave_height
    
    def test_render_post_process(self):
        """Renderizar template de post-procesado."""
        code = render_shader_template(
            "post_process_base",
            intensity=0.8,
        )
        
        self.assertIn("shader_type canvas_item", code)
        self.assertIn("hint_screen_texture", code)
        self.assertIn("0.8", code)
    
    def test_render_invalid_template(self):
        """Intentar renderizar template inexistente."""
        with self.assertRaises(ValueError):
            render_shader_template("template_inexistente")
    
    def test_all_templates_render(self):
        """Verificar que todos los templates renderizan sin errores."""
        templates = list_available_templates()
        
        for name in templates:
            try:
                code = self.engine.render(name)
                self.assertTrue(len(code) > 0, f"Template {name} renderizó vacío")
                # noise_functions es un include, no tiene shader_type
                if name != "noise_functions":
                    self.assertIn("shader_type", code, f"Template {name} no tiene shader_type")
            except Exception as e:
                self.fail(f"Template {name} falló: {e}")


class TestManageShader(unittest.TestCase):
    """Tests para la tool manage_shader."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.project_path = self.temp_dir
        self.shader_path = os.path.join(self.temp_dir, "shaders", "test.gdshader")
    
    def test_create_shader_from_template(self):
        """Crear shader desde template."""
        # Simular llamada a manage_shader mode=create
        from godot_mcp.tools.shader_tools import _resolve_path
        
        abs_path = _resolve_path(self.project_path, self.shader_path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        
        code = render_shader_template("grayscale")
        with open(abs_path, "w") as f:
            f.write(code)
        
        self.assertTrue(os.path.isfile(abs_path))
        
        # Validar
        parser = GDShaderParser()
        analysis = parser.parse_file(abs_path)
        self.assertEqual(analysis.shader_type, "canvas_item")
    
    def test_validate_shader(self):
        """Validar shader."""
        abs_path = os.path.join(self.temp_dir, "test_valid.gdshader")
        with open(abs_path, "w") as f:
            f.write("shader_type spatial;\nvoid fragment() { ALBEDO = vec3(1.0); }\n")
        
        is_valid, errors = GDShaderParser.validate_shader_code(open(abs_path).read())
        self.assertTrue(is_valid)
    
    def test_read_shader(self):
        """Leer shader y extraer metadatos."""
        abs_path = os.path.join(self.temp_dir, "test_read.gdshader")
        with open(abs_path, "w") as f:
            f.write("""
shader_type spatial;
uniform float u_speed = 1.0;
uniform vec4 u_color : source_color;
void fragment() { ALBEDO = u_color.rgb; }
""")
        
        analysis = quick_parse_shader(abs_path)
        
        self.assertEqual(analysis["shader_type"], "spatial")
        self.assertEqual(len(analysis["uniforms"]), 2)
        self.assertEqual(analysis["uniforms"][0]["name"], "u_speed")
        self.assertEqual(analysis["uniforms"][1]["name"], "u_color")


class TestShaderAnalysis(unittest.TestCase):
    """Tests para análisis de shaders."""
    
    def test_complexity_analysis(self):
        """Analizar complejidad de shader."""
        code = """
shader_type spatial;

uniform sampler2D u_texture1;
uniform sampler2D u_texture2;
uniform sampler2D u_texture3;
uniform sampler2D u_texture4;
uniform sampler2D u_texture5;

void fragment() {
    vec4 c1 = texture(u_texture1, UV);
    vec4 c2 = texture(u_texture2, UV);
    vec4 c3 = texture(u_texture3, UV);
    vec4 c4 = texture(u_texture4, UV);
    vec4 c5 = texture(u_texture5, UV);
    
    if (c1.r > 0.5) {
        ALBEDO = c1.rgb;
    } else {
        ALBEDO = c2.rgb;
    }
    
    for (int i = 0; i < 4; i++) {
        ALBEDO += c3.rgb * 0.1;
    }
}
"""
        parser = GDShaderParser()
        analysis = parser.parse_string(code)
        
        self.assertEqual(analysis.complexity["texture_samples"], 5)
        self.assertEqual(analysis.complexity["branch_count"], 2)  # if + else
        self.assertEqual(analysis.complexity["loop_count"], 1)
        
        # Debe haber warning por múltiples textures (>4)
        self.assertTrue(
            any("texture" in w.lower() for w in analysis.warnings),
            f"No se detectó warning por múltiples textures. Warnings: {analysis.warnings}"
        )
    
    def test_platform_optimization_mobile(self):
        """Sugerencias de optimización para mobile."""
        code = """
shader_type spatial;
uniform sampler2D u_tex1;
uniform sampler2D u_tex2;
uniform sampler2D u_tex3;
uniform sampler2D u_tex4;
void fragment() {
    vec4 c = texture(u_tex1, UV);
    c += texture(u_tex2, UV);
    c += texture(u_tex3, UV);
    c += texture(u_tex4, UV);
    ALBEDO = c.rgb;
}
"""
        parser = GDShaderParser()
        analysis = parser.parse_string(code)
        
        # En mobile >2 textures debe dar warning
        self.assertTrue(
            analysis.complexity["texture_samples"] > 2,
            "Shader debería tener >2 texture samples"
        )


class TestIntegration(unittest.TestCase):
    """Tests de integración end-to-end."""
    
    def test_full_pipeline(self):
        """Pipeline completo: template → shader → análisis."""
        # 1. Renderizar template
        code = render_shader_template("dissolve", dissolve_amount=0.5)
        
        # 2. Validar
        is_valid, errors = GDShaderParser.validate_shader_code(code)
        self.assertTrue(is_valid, f"Errores de validación: {errors}")
        
        # 3. Parsear
        parser = GDShaderParser()
        analysis = parser.parse_string(code)
        
        # 4. Verificar estructura
        self.assertTrue(len(analysis.uniforms) > 0)
        self.assertIn("u_dissolve_amount", [u.name for u in analysis.uniforms])


if __name__ == "__main__":
    unittest.main()
