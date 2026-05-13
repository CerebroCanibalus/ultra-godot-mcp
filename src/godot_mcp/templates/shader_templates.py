"""
Shader Templates - Plantillas Jinja2 para generación de shaders Godot.

Provee templates reutilizables para efectos comunes de shaders,
parametrizables vía variables Jinja2.

Templates disponibles:
- post_process_base: Efectos de post-procesado con hint_screen_texture
- volumetric_fog: Niebla volumétrica basada en profundidad
- water: Agua con ondas, normal map y reflejo
- dissolve: Efecto de disolución con ruido
- outline: Silueta/outline por post-procesado
- canvas_item_glow: Glow/bloom para sprites 2D
- sdf_raymarch: Raymarching con primitivas SDF
- particle_trail: Trails de partículas GPU
- toon_shading: Cel-shading básico
- pixelate: Pixelación con control de resolución
- chromatic_aberration: Aberración cromática
- noise_generator: Funciones de ruido reutilizables (FBM, Voronoi)
"""

import logging
from typing import Any

from jinja2 import BaseLoader, Environment, TemplateNotFound

logger = logging.getLogger(__name__)


# ============ TEMPLATES DE SHADERS ============

SHADER_TEMPLATES = {
    "post_process_base": """shader_type canvas_item;

uniform float u_intensity : hint_range(0.0, 1.0) = {{ intensity | default(0.5) }};
uniform sampler2D screen_texture : hint_screen_texture, repeat_disable, filter_nearest;

void fragment() {
    vec4 color = texture(screen_texture, SCREEN_UV);
    
    // Efecto base de post-procesado
    // Personalizar aquí el efecto deseado
    vec3 final_color = color.rgb * (1.0 + u_intensity * 0.2);
    
    COLOR = vec4(final_color, color.a);
}
""",

    "volumetric_fog": """shader_type spatial;
render_mode blend_add, unshaded, cull_disabled, depth_draw_never;

uniform vec4 u_fog_color : source_color = {{ fog_color | default('vec4(0.5, 0.6, 0.7, 1.0)') }};
uniform float u_fog_density : hint_range(0.0, 1.0) = {{ density | default(0.1) }};
uniform float u_fog_start : hint_range(0.0, 100.0) = {{ fog_start | default(10.0) }};
uniform float u_fog_end : hint_range(0.0, 200.0) = {{ fog_end | default(50.0) }};

void fragment() {
    float depth = textureLod(DEPTH_TEXTURE, SCREEN_UV, 0.0).r;
    vec4 world_pos = INV_PROJECTION_MATRIX * vec4(SCREEN_UV * 2.0 - 1.0, depth, 1.0);
    world_pos.xyz /= world_pos.w;
    
    float dist = length(world_pos.xyz - CAMERA_POSITION_WORLD);
    float fog_factor = clamp((dist - u_fog_start) / (u_fog_end - u_fog_start), 0.0, 1.0);
    fog_factor = 1.0 - exp(-fog_factor * fog_factor * u_fog_density * 3.0);
    
    ALBEDO = u_fog_color.rgb;
    ALPHA = fog_factor * u_fog_color.a;
}
""",

    "water": """shader_type spatial;
render_mode cull_disabled;

uniform vec4 u_water_color : source_color = {{ water_color | default('vec4(0.0, 0.3, 0.5, 0.8)') }};
uniform float u_wave_speed : hint_range(0.0, 5.0) = {{ wave_speed | default(1.0) }};
uniform float u_wave_scale : hint_range(0.0, 2.0) = {{ wave_scale | default(0.3) }};
uniform float u_wave_height : hint_range(0.0, 1.0) = {{ wave_height | default(0.1) }};
uniform sampler2D u_normal_map : hint_normal;

varying vec3 v_world_pos;

float get_wave_height(vec2 pos, float time) {
    float h = 0.0;
    h += sin(pos.x * 2.0 + time * u_wave_speed) * u_wave_height;
    h += sin(pos.y * 1.5 + time * u_wave_speed * 0.8) * u_wave_height * 0.5;
    h += sin((pos.x + pos.y) * 1.0 + time * u_wave_speed * 1.2) * u_wave_height * 0.3;
    return h;
}

void vertex() {
    vec3 world_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
    v_world_pos = world_pos;
    
    float time = TIME;
    float height = get_wave_height(world_pos.xz, time);
    VERTEX.y += height;
    
    // Calcular normal aproximada
    float dx = get_wave_height(world_pos.xz + vec2(0.1, 0.0), time) - height;
    float dz = get_wave_height(world_pos.xz + vec2(0.0, 0.1), time) - height;
    NORMAL = normalize(vec3(-dx * 10.0, 1.0, -dz * 10.0));
}

void fragment() {
    vec3 normal = NORMAL;
    
    // Normal map si está disponible
    {% if use_normal_map | default(false) %}
    vec3 normal_map = texture(u_normal_map, UV * u_wave_scale + TIME * 0.1).rgb;
    normal = normalize(normal * 2.0 - 1.0);
    {% endif %}
    
    // Fresnel
    vec3 view_dir = normalize(CAMERA_POSITION_WORLD - v_world_pos);
    float fresnel = pow(1.0 - max(dot(view_dir, normal), 0.0), 3.0);
    
    ALBEDO = mix(u_water_color.rgb, vec3(0.8, 0.9, 1.0), fresnel * 0.5);
    METALLIC = 0.3;
    ROUGHNESS = 0.1 + fresnel * 0.2;
    ALPHA = u_water_color.a;
}
""",

    "dissolve": """shader_type {% if is_3d | default(true) %}spatial{% else %}canvas_item{% endif %};

uniform float u_dissolve_amount : hint_range(0.0, 1.0) = {{ dissolve_amount | default(0.0) }};
uniform vec4 u_dissolve_color : source_color = {{ dissolve_color | default('vec4(1.0, 0.5, 0.0, 1.0)') }};
uniform float u_edge_width : hint_range(0.0, 0.5) = {{ edge_width | default(0.05) }};
uniform sampler2D u_noise_texture : hint_default_black;

void fragment() {
    {% if is_3d | default(true) %}
    float noise = texture(u_noise_texture, UV).r;
    vec4 albedo = texture(TEXTURE, UV);
    {% else %}
    float noise = texture(u_noise_texture, UV).r;
    vec4 albedo = texture(TEXTURE, UV);
    {% endif %}
    
    float edge = smoothstep(u_dissolve_amount, u_dissolve_amount + u_edge_width, noise);
    float glow = smoothstep(u_dissolve_amount - u_edge_width, u_dissolve_amount, noise);
    
    vec3 final_color = mix(u_dissolve_color.rgb, albedo.rgb, edge);
    float final_alpha = albedo.a * step(u_dissolve_amount, noise);
    
    {% if is_3d | default(true) %}
    ALBEDO = final_color;
    ALPHA = final_alpha;
    EMISSION = u_dissolve_color.rgb * glow * 2.0;
    {% else %}
    COLOR = vec4(final_color, final_alpha);
    {% endif %}
}
""",

    "outline": """shader_type canvas_item;

uniform vec4 u_outline_color : source_color = {{ outline_color | default('vec4(1.0, 1.0, 1.0, 1.0)') }};
uniform float u_outline_width : hint_range(0.0, 10.0) = {{ outline_width | default(2.0) }};
uniform sampler2D screen_texture : hint_screen_texture, repeat_disable, filter_nearest;

void fragment() {
    vec4 color = texture(TEXTURE, UV);
    vec2 pixel_size = TEXTURE_PIXEL_SIZE * u_outline_width;
    
    float alpha = 0.0;
    alpha += texture(TEXTURE, UV + vec2(pixel_size.x, 0.0)).a;
    alpha += texture(TEXTURE, UV - vec2(pixel_size.x, 0.0)).a;
    alpha += texture(TEXTURE, UV + vec2(0.0, pixel_size.y)).a;
    alpha += texture(TEXTURE, UV - vec2(0.0, pixel_size.y)).a;
    alpha += texture(TEXTURE, UV + vec2(pixel_size.x, pixel_size.y)).a;
    alpha += texture(TEXTURE, UV - vec2(pixel_size.x, pixel_size.y)).a;
    alpha += texture(TEXTURE, UV + vec2(pixel_size.x, -pixel_size.y)).a;
    alpha += texture(TEXTURE, UV - vec2(pixel_size.x, -pixel_size.y)).a;
    
    alpha = clamp(alpha, 0.0, 1.0);
    
    vec4 outline = u_outline_color;
    outline.a *= alpha;
    
    COLOR = mix(outline, color, color.a);
}
""",

    "canvas_item_glow": """shader_type canvas_item;

uniform float u_glow_intensity : hint_range(0.0, 4.0) = {{ glow_intensity | default(1.5) }};
uniform float u_glow_radius : hint_range(0.0, 0.1) = {{ glow_radius | default(0.02) }};
uniform vec4 u_glow_color : source_color = {{ glow_color | default('vec4(1.0, 1.0, 1.0, 1.0)') }};

void fragment() {
    vec4 color = texture(TEXTURE, UV);
    
    // Samplear alrededor para crear blur/glow
    float glow = 0.0;
    vec2 pixel = u_glow_radius * vec2(1.0, 1.0);
    
    glow += texture(TEXTURE, UV + vec2(pixel.x, 0.0)).a;
    glow += texture(TEXTURE, UV - vec2(pixel.x, 0.0)).a;
    glow += texture(TEXTURE, UV + vec2(0.0, pixel.y)).a;
    glow += texture(TEXTURE, UV - vec2(0.0, pixel.y)).a;
    glow += texture(TEXTURE, UV + pixel).a;
    glow += texture(TEXTURE, UV - pixel).a;
    glow += texture(TEXTURE, UV + vec2(pixel.x, -pixel.y)).a;
    glow += texture(TEXTURE, UV + vec2(-pixel.x, pixel.y)).a;
    
    glow = glow / 8.0 * u_glow_intensity;
    
    vec3 glow_rgb = u_glow_color.rgb * glow;
    vec3 final_rgb = color.rgb + glow_rgb * (1.0 - color.a);
    
    COLOR = vec4(final_rgb, max(color.a, glow * u_glow_color.a));
}
""",

    "pixelate": """shader_type canvas_item;

uniform float u_pixel_size : hint_range(1.0, 128.0) = {{ pixel_size | default(8.0) }};
uniform sampler2D screen_texture : hint_screen_texture, repeat_disable, filter_nearest;

void fragment() {
    vec2 pixelated_uv = floor(UV * u_pixel_size) / u_pixel_size;
    COLOR = texture(TEXTURE, pixelated_uv);
}
""",

    "chromatic_aberration": """shader_type canvas_item;

uniform float u_offset : hint_range(0.0, 10.0) = {{ offset | default(3.0) }};
uniform sampler2D screen_texture : hint_screen_texture, repeat_disable, filter_nearest;

void fragment() {
    vec2 pixel = TEXTURE_PIXEL_SIZE * u_offset;
    
    float r = texture(screen_texture, SCREEN_UV + vec2(pixel.x, 0.0)).r;
    float g = texture(screen_texture, SCREEN_UV).g;
    float b = texture(screen_texture, SCREEN_UV - vec2(pixel.x, 0.0)).b;
    
    COLOR = vec4(r, g, b, 1.0);
}
""",

    "sdf_raymarch": """shader_type spatial;
render_mode unshaded, cull_disabled;

uniform vec4 u_shape_color : source_color = {{ shape_color | default('vec4(0.2, 0.6, 1.0, 1.0)') }};
uniform float u_max_steps : hint_range(16, 256) = {{ max_steps | default(64) }};
uniform float u_max_dist : hint_range(1.0, 100.0) = {{ max_dist | default(50.0) }};
uniform float u_epsilon : hint_range(0.0001, 0.01) = {{ epsilon | default(0.001) }};

// SDF Primitives
float sdSphere(vec3 p, float r) {
    return length(p) - r;
}

float sdBox(vec3 p, vec3 b) {
    vec3 q = abs(p) - b;
    return length(max(q, 0.0)) + min(max(q.x, max(q.y, q.z)), 0.0);
}

float sdPlane(vec3 p, vec3 n, float h) {
    return dot(p, n) + h;
}

// SDF Operations
float opUnion(float d1, float d2) {
    return min(d1, d2);
}

float opSubtraction(float d1, float d2) {
    return max(-d1, d2);
}

float opIntersection(float d1, float d2) {
    return max(d1, d2);
}

float opSmoothUnion(float d1, float d2, float k) {
    float h = clamp(0.5 + 0.5 * (d2 - d1) / k, 0.0, 1.0);
    return mix(d2, d1, h) - k * h * (1.0 - h);
}

// Scene definition
float map(vec3 p) {
    float sphere = sdSphere(p - vec3(0.0, 0.0, 0.0), 1.0);
    float box = sdBox(p - vec3(1.5, 0.0, 0.0), vec3(0.8));
    float plane = sdPlane(p, vec3(0.0, 1.0, 0.0), 1.0);
    
    float scene = opSmoothUnion(sphere, box, 0.5);
    scene = opUnion(scene, plane);
    
    return scene;
}

vec3 calcNormal(vec3 p) {
    vec2 e = vec2(u_epsilon, 0.0);
    return normalize(vec3(
        map(p + e.xyy) - map(p - e.xyy),
        map(p + e.yxy) - map(p - e.yxy),
        map(p + e.yyx) - map(p - e.yyx)
    ));
}

void fragment() {
    vec3 ro = CAMERA_POSITION_WORLD;
    vec3 rd = normalize((INV_VIEW_MATRIX * vec4(NORMAL, 0.0)).xyz);
    
    float t = 0.0;
    bool hit = false;
    
    for (int i = 0; i < int(u_max_steps); i++) {
        vec3 p = ro + rd * t;
        float d = map(p);
        
        if (d < u_epsilon) {
            hit = true;
            break;
        }
        
        t += d;
        if (t > u_max_dist) break;
    }
    
    if (hit) {
        vec3 p = ro + rd * t;
        vec3 n = calcNormal(p);
        
        vec3 light_dir = normalize(vec3(1.0, 1.0, -1.0));
        float diff = max(dot(n, light_dir), 0.0);
        
        ALBEDO = u_shape_color.rgb * (0.3 + diff * 0.7);
        ALPHA = u_shape_color.a;
    } else {
        discard;
    }
}
""",

    "toon_shading": """shader_type spatial;
render_mode diffuse_lambert_wrap;

uniform vec4 u_base_color : source_color = {{ base_color | default('vec4(0.8, 0.2, 0.2, 1.0)') }};
uniform float u_shades : hint_range(1.0, 8.0) = {{ shades | default(3.0) }};
uniform float u_rim_power : hint_range(0.0, 8.0) = {{ rim_power | default(3.0) }};
uniform vec4 u_rim_color : source_color = {{ rim_color | default('vec4(1.0, 1.0, 1.0, 1.0)') }};

void fragment() {
    // Normalizada
    vec3 normal = normalize(NORMAL);
    vec3 view_dir = normalize(VIEW);
    
    // Difuso cuantizado (toon)
    float NdotL = max(dot(normal, normalize(vec3(1.0, 1.0, 0.0))), 0.0);
    float diffuse = floor(NdotL * u_shades) / u_shades;
    
    // Rim light
    float rim = 1.0 - max(dot(view_dir, normal), 0.0);
    rim = pow(rim, u_rim_power);
    
    vec3 final_color = u_base_color.rgb * diffuse;
    final_color = mix(final_color, u_rim_color.rgb, rim * u_rim_color.a);
    
    ALBEDO = final_color;
    {% if use_specular | default(false) %}
    SPECULAR = 0.5;
    {% endif %}
}
""",

    "particle_trail": """shader_type particles;

uniform float u_trail_length : hint_range(0.0, 1.0) = {{ trail_length | default(0.5) }};
uniform vec4 u_trail_color : source_color = {{ trail_color | default('vec4(1.0, 0.5, 0.0, 1.0)') }};

void start() {
    // Inicialización de partícula
    VELOCITY = vec3(0.0, 1.0, 0.0);
}

void process() {
    // Trail effect basado en la vida de la partícula
    float life_ratio = 1.0 - (LIFETIME / MAX_LIFETIME);
    
    // Escalar basado en vida
    TRANSFORM[0][0] = 1.0 - life_ratio * u_trail_length;
    TRANSFORM[1][1] = 1.0 - life_ratio * u_trail_length;
    TRANSFORM[2][2] = 1.0 - life_ratio * u_trail_length;
    
    // Color basado en vida
    COLOR = mix(u_trail_color, vec4(0.0), life_ratio);
}
""",

    "noise_functions": """// Funciones de ruido reutilizables para incluir en shaders
// Uso: #include "res://shaders/noise_functions.gdshaderinc"

// Hash 2D
float hash(vec2 p) {
    return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

// Hash 3D  
float hash3(vec3 p) {
    return fract(sin(dot(p, vec3(127.1, 311.7, 74.7))) * 43758.5453);
}

// Value Noise 2D
float value_noise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    f = f * f * (3.0 - 2.0 * f);
    
    float a = hash(i);
    float b = hash(i + vec2(1.0, 0.0));
    float c = hash(i + vec2(0.0, 1.0));
    float d = hash(i + vec2(1.0, 1.0));
    
    return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
}

// FBM (Fractal Brownian Motion)
float fbm(vec2 p, int octaves) {
    float value = 0.0;
    float amplitude = 0.5;
    float frequency = 1.0;
    
    for (int i = 0; i < octaves; i++) {
        value += amplitude * value_noise(p * frequency);
        amplitude *= 0.5;
        frequency *= 2.0;
    }
    
    return value;
}

// Voronoi 2D
vec2 voronoi(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    
    float min_dist = 1.0;
    vec2 nearest = vec2(0.0);
    
    for (int y = -1; y <= 1; y++) {
        for (int x = -1; x <= 1; x++) {
            vec2 neighbor = vec2(float(x), float(y));
            vec2 point = neighbor + hash(i + neighbor);
            float dist = length(point - f);
            
            if (dist < min_dist) {
                min_dist = dist;
                nearest = point;
            }
        }
    }
    
    return vec2(min_dist, hash(i + floor(nearest)));
}
""",

    "grayscale": """shader_type canvas_item;

uniform float u_intensity : hint_range(0.0, 1.0) = {{ intensity | default(1.0) }};

void fragment() {
    vec4 color = texture(TEXTURE, UV);
    float gray = dot(color.rgb, vec3(0.299, 0.587, 0.114));
    vec3 final = mix(color.rgb, vec3(gray), u_intensity);
    COLOR = vec4(final, color.a);
}
""",

    "vignette": """shader_type canvas_item;

uniform float u_intensity : hint_range(0.0, 1.0) = {{ intensity | default(0.5) }};
uniform float u_roundness : hint_range(0.0, 1.0) = {{ roundness | default(0.5) }};
uniform vec4 u_color : source_color = {{ color | default('vec4(0.0, 0.0, 0.0, 1.0)') }};
uniform sampler2D screen_texture : hint_screen_texture, repeat_disable, filter_nearest;

void fragment() {
    vec4 color = texture(screen_texture, SCREEN_UV);
    
    vec2 center = UV - 0.5;
    float vignette = 1.0 - dot(center, center) * 2.0;
    vignette = pow(vignette, mix(1.0, 5.0, u_roundness));
    vignette = clamp(vignette, 0.0, 1.0);
    
    vec3 final = mix(u_color.rgb, color.rgb, vignette);
    COLOR = vec4(final, color.a);
}
""",

    "grain": """shader_type canvas_item;

uniform float u_amount : hint_range(0.0, 1.0) = {{ amount | default(0.1) }};
uniform float u_size : hint_range(0.5, 2.0) = {{ size | default(1.0) }};
uniform sampler2D screen_texture : hint_screen_texture, repeat_disable, filter_nearest;

float rand(vec2 co) {
    return fract(sin(dot(co, vec2(12.9898, 78.233))) * 43758.5453);
}

void fragment() {
    vec4 color = texture(screen_texture, SCREEN_UV);
    float noise = rand(UV * u_size * 1000.0 + TIME) * u_amount;
    COLOR = vec4(color.rgb + noise - u_amount * 0.5, color.a);
}
""",
}


# ============ MOTOR DE TEMPLATES ============

class ShaderTemplateEngine:
    """
    Motor de templates para shaders Godot.
    
    Renderiza templates Jinja2 con variables personalizables.
    """
    
    def __init__(self):
        self.loader = BaseLoader()
        self.env = Environment(loader=self.loader)
        self._templates = {}
        self._load_templates()
    
    def _load_templates(self):
        """Cargar todos los templates en el environment."""
        for name, source in SHADER_TEMPLATES.items():
            self.env.loader = self._create_dict_loader({name: source})
            self._templates[name] = self.env.get_template(name)
    
    def _create_dict_loader(self, templates_dict: dict):
        """Crear un loader que lee de un diccionario."""
        class DictLoader(BaseLoader):
            def get_source(self, environment, template):
                if template in templates_dict:
                    source = templates_dict[template]
                    return source, None, lambda: source == templates_dict[template]
                raise TemplateNotFound(template)
        return DictLoader()
    
    def render(self, template_name: str, **kwargs) -> str:
        """
        Renderizar un template con variables.
        
        Args:
            template_name: Nombre del template (e.g., "water", "dissolve")
            **kwargs: Variables para el template
            
        Returns:
            Código del shader renderizado
            
        Raises:
            ValueError: Si el template no existe
        """
        if template_name not in self._templates:
            available = ", ".join(sorted(self._templates.keys()))
            raise ValueError(
                f"Template '{template_name}' no encontrado. "
                f"Disponibles: {available}"
            )
        
        return self._templates[template_name].render(**kwargs)
    
    def list_templates(self) -> list[str]:
        """Listar todos los templates disponibles."""
        return sorted(self._templates.keys())
    
    def get_template_info(self, template_name: str) -> dict:
        """
        Obtener información sobre un template.
        
        Returns:
            Dict con nombre, descripción breve, parámetros esperados
        """
        descriptions = {
            "post_process_base": "Shader base para post-procesado con hint_screen_texture",
            "volumetric_fog": "Niebla volumétrica basada en profundidad de escena",
            "water": "Agua con ondas procedurales, normal map y fresnel",
            "dissolve": "Efecto de disolución con borde glow y ruido",
            "outline": "Outline/silueta alrededor de sprites",
            "canvas_item_glow": "Glow/bloom para sprites 2D",
            "sdf_raymarch": "Raymarching con primitivas SDF (esferas, cajas)",
            "toon_shading": "Cel-shading con rim light",
            "particle_trail": "Trails de partículas GPU",
            "noise_functions": "Funciones de ruido reutilizables (FBM, Voronoi)",
            "grayscale": "Conversión a escala de grises",
            "pixelate": "Pixelación con control de tamaño",
            "chromatic_aberration": "Aberración cromática RGB",
            "vignette": "Viñeta oscura en los bordes",
            "grain": "Ruido de película/grano",
        }
        
        if template_name not in self._templates:
            return {"error": f"Template '{template_name}' no encontrado"}
        
        return {
            "name": template_name,
            "description": descriptions.get(template_name, "Sin descripción"),
            "available": True,
        }
    
    def create_custom_template(self, name: str, code: str):
        """
        Registrar un template personalizado en runtime.
        
        Args:
            name: Nombre para el nuevo template
            code: Código fuente del shader (con sintaxis Jinja2 opcional)
        """
        self.env.loader = self._create_dict_loader({name: code})
        self._templates[name] = self.env.get_template(name)
        logger.info(f"Template personalizado registrado: {name}")


# Instancia global del motor de templates
shader_template_engine = ShaderTemplateEngine()


def render_shader_template(template_name: str, **kwargs) -> str:
    """
    Función de conveniencia para renderizar un template.
    
    Args:
        template_name: Nombre del template
        **kwargs: Variables del template
        
    Returns:
        Código del shader
    """
    return shader_template_engine.render(template_name, **kwargs)


def list_available_templates() -> list[str]:
    """Listar todos los templates disponibles."""
    return shader_template_engine.list_templates()
