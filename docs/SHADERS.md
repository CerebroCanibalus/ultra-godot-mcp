# Shader Tools - Documentación

## Overview

Las Shader Tools son 4 herramientas centralizadas que cubren el ciclo de vida completo de shaders en Godot 4.x. Diseñadas bajo la filosofía de **"4 herramientas que hacen el trabajo de 20"**.

## Tools Disponibles

### 1. `manage_shader`

**Herramienta MADRE** para gestión completa de archivos `.gdshader`.

**Modos:**
- `create` - Crear shader desde template o código raw
- `edit` - Editar secciones específicas (vertex/fragment/globals/full)
- `read` - Leer metadata y código fuente
- `validate` - Validación sintáctica + compilación con Godot CLI
- `delete` - Eliminar archivo
- `list_templates` - Listar templates disponibles

**Ejemplos:**
```python
# Crear shader desde template
manage_shader(
    mode="create",
    shader_path="res://shaders/water.gdshader",
    template="water",
    uniforms={"wave_speed": 2.0, "wave_height": 0.2}
)

# Validar shader existente
manage_shader(
    mode="validate",
    shader_path="res://shaders/effect.gdshader"
)
# → Retorna: valid, syntax_valid, godot_valid, errors[], warnings[]

# Editar función fragment
manage_shader(
    mode="edit",
    shader_path="res://shaders/effect.gdshader",
    replace_section="fragment",
    code="""
void fragment() {
    COLOR = vec4(1.0, 0.0, 0.0, 1.0);
}
"""
)
```

**Templates disponibles:**
| Template | Descripción |
|----------|-------------|
| `post_process_base` | Efectos de pantalla con hint_screen_texture |
| `volumetric_fog` | Niebla volumétrica depth-based |
| `water` | Agua con ondas procedurales y fresnel |
| `dissolve` | Disolución con borde glow y ruido |
| `outline` | Outline/silueta para sprites |
| `canvas_item_glow` | Glow/bloom para UI/sprites 2D |
| `sdf_raymarch` | Raymarching con primitivas SDF |
| `toon_shading` | Cel-shading con rim light |
| `particle_trail` | Trails de partículas GPU |
| `grayscale` | Escala de grises |
| `pixelate` | Pixelación |
| `chromatic_aberration` | Aberración cromática RGB |
| `vignette` | Viñeta oscura en bordes |
| `grain` | Ruido de película |
| `noise_functions` | Include con funciones FBM/Voronoi |

---

### 2. `manage_shader_material`

Puente entre shaders y nodos. Gestiona ShaderMaterial con **workarounds de bugs integrados**.

**Modos:**
- `create` - Crear ShaderMaterial y asignar a nodo
- `set_params` - Setear parámetros (con double-set workaround)
- `read_params` - Leer parámetros actuales y uniforms disponibles
- `clear_params` - Limpiar todos los parámetros

**Ejemplos:**
```python
# Crear material y asignar shader
manage_shader_material(
    mode="create",
    target_node="Player/Sprite2D",
    scene_path="res://scenes/Player.tscn",
    shader_path="res://shaders/dissolve.gdshader",
    use_override=True
)

# Setear parámetros (bugfix automático)
manage_shader_material(
    mode="set_params",
    target_node="Player/Sprite2D",
    scene_path="res://scenes/Player.tscn",
    params={
        "u_dissolve_amount": 0.7,
        "u_edge_color": "#FF6600"
    }
)
```

**Bugs mitigados automáticamente:**
- **Shader parameter binding bug**: Double-set integrado
- **Type coercion**: Color ↔ vec3, float ↔ int
- **Validación**: Verifica que el uniform existe antes de setear

---

### 3. `create_render_pipeline`

Crea cadenas de efectos de post-procesado con SubViewports.

**Ejemplo:**
```python
create_render_pipeline(
    pipeline_name="res://pipelines/damage_postfx.tscn",
    effects=[
        {
            "shader": "res://shaders/chromatic_aberration.gdshader",
            "params": {"u_offset": 3.0}
        },
        {
            "shader": "res://shaders/vignette.gdshader",
            "params": {"u_intensity": 0.6, "u_color": "#330000"}
        },
        {
            "shader": "res://shaders/grain.gdshader",
            "params": {"u_amount": 0.15}
        }
    ],
    resolution={"x": 1920, "y": 1080}
)
```

**Output:** Escena `.tscn` con CanvasLayer + ColorRects encadenados, lista para instanciar.

---

### 4. `analyze_shader`

Inteligencia y diagnóstico profundo de shaders.

**Modos:**
- `inspect` - Análisis estructural completo (uniforms, funciones, complejidad)
- `optimize` - Recomendaciones de optimización por plataforma
- `compare` - Comparar dos shaders
- `profile` - Estimación de costo de performance

**Ejemplo - Optimización:**
```python
analyze_shader(
    shader_path="res://shaders/water.gdshader",
    mode="optimize",
    target_platform="mobile"
)
# → Retorna recomendaciones como:
#   "Reducir texture samples a máximo 2"
#   "Reemplazar if/else con step() y mix()"
#   "Especificar mediump/highp explícitamente"
```

**Ejemplo - Inspección:**
```python
analyze_shader(
    shader_path="res://shaders/effect.gdshader",
    mode="inspect"
)
# → Retorna:
#   shader_type, render_modes[], uniforms[], functions[],
#   complexity: {texture_samples, branch_count, loop_count, instruction_estimate},
#   warnings[]
```

---

## Parser Features

El `GDShaderParser` extrae:
- ✅ Shader type (spatial, canvas_item, particles, sky, fog)
- ✅ Render modes
- ✅ Uniforms con tipo, default, hint y línea
- ✅ Varyings
- ✅ Functions (built-in y custom)
- ✅ Constants
- ✅ Includes (.gdshaderinc) con resolución de rutas
- ✅ Métricas de complejidad (branches, loops, texture samples)
- ✅ Warnings automáticos (loops no-constantes, división con varyings, etc.)

---

## Estructura de Archivos

```
src/godot_mcp/
├── core/
│   └── shader_parser.py          # Parser de GDShader
├── templates/
│   └── shader_templates.py       # 15 templates Jinja2
├── tools/
│   └── shader_tools.py           # 4 tools FastMCP
└── server.py                     # Registro de tools

tests/
└── test_shader_tools.py          # 16 tests
```

---

## Workarounds Integrados

| Problema | Mitigación |
|----------|-----------|
| Shader parameter binding bug (Godot 4.x) | Double-set automático en `manage_shader_material` |
| Loops con variables no-constantes | Warning en `analyze_shader` + sugerencia de unroll |
| highp no explícito en mobile | Sugerencia en `analyze_shader` modo optimize |
| Múltiples texture() calls | Warning si >4, sugerencia de atlas |
| Uniforms duplicados | Detección en validación sintáctica |

---

## Tips de Uso

### Workflow Recomendado

1. **Crear shader**: `manage_shader(mode="create", template="...")`
2. **Validar**: `manage_shader(mode="validate", ...)`
3. **Asignar a nodo**: `manage_shader_material(mode="create", ...)`
4. **Configurar params**: `manage_shader_material(mode="set_params", ...)`
5. **Optimizar**: `analyze_shader(mode="optimize", target_platform="mobile")`

### Post-Procesado Completo

```python
# 1. Crear shaders individuales
manage_shader(mode="create", template="chromatic_aberration", shader_path="res://shaders/chromatic.gdshader")
manage_shader(mode="create", template="vignette", shader_path="res://shaders/vignette.gdshader")

# 2. Crear pipeline
pipeline = create_render_pipeline(
    pipeline_name="res://pipelines/damage_effect.tscn",
    effects=[
        {"shader": "res://shaders/chromatic.gdshader", "params": {"u_offset": 2.0}},
        {"shader": "res://shaders/vignette.gdshader", "params": {"u_intensity": 0.5}},
    ]
)

# 3. Instanciar pipeline en la escena principal
```

---

## Changelog

**v4.6.0** - Shader Tools Release
- 4 tools centralizadas para gestión completa de shaders
- Parser de GDShader con extracción de uniforms, funciones, complejidad
- 15 templates Jinja2 listos para usar
- Validación sintáctica + compilación con Godot CLI
- Workarounds de bugs conocidos integrados
- Soporte para render pipelines con SubViewports
- Análisis de optimización por plataforma (desktop/mobile/web)
