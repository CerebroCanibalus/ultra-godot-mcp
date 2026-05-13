# Plan de Mejora: Herramientas de Animación

> **Estado:** Draft v1.0  
> **Fecha:** 2026-05-12  
> **Filosofía:** Ultra rápido · Centralizado · Sencillo

---

## 1. Resumen Ejecutivo

Las herramientas de animación actualmente funcionan pero están **fragmentadas, verbosas y faltan de conveniencia**. Este plan propone una consolidación en **3 herramientas maestras** + **4 helpers especializados** que cubran el 95% de los casos de uso con 70% menos llamadas.

**Métrica objetivo:** Reducir de 12 tools dispersas → 7 tools consolidadas. De 5-10 pasos para un setup común → 1-2 pasos.

---

## 2. Diagnóstico Actual

### 2.1 Problemas Críticos

| # | Problema | Impacto | Solución |
|---|----------|---------|----------|
| 1 | **No hay setup integrado AnimationPlayer+Tree** | El usuario debe crear nodos manualmente, luego resources, luego conectar | `setup_animation_system` (1 tool) |
| 2 | **calculate_rest_poses no expuesta** | Función interna útil no disponible para usuarios | Exponer como `calculate_skeleton_poses` |
| 3 | **API verbosa** | `create_blend_space_1d` requiere 7+ parámetros para un caso simple | Defaults inteligentes, auto-naming |
| 4 | **Sin operaciones batch** | Cada track de animación requiere su propio JSON completo | `batch_create_tracks` |
| 5 | **Sin validación** | Puede crear animaciones duplicadas, references rotos | Validación en cada tool |
| 6 | **Skeleton tools separadas** | 6 tools para skeleton 2D/3D con lógica similar | Consolidar en 2 tools con `dimension` param |

### 2.2 Estadísticas

- **Tools registradas:** 12 (animation) + 2 internas sin exponer
- **Pasos para setup común:** 5-8 llamadas
- **Tiempo medio por setup:** ~15 minutos
- **Tasa de error (estimada):** 40% (usuarios se confunden con NodePaths, SubResource IDs)

---

## 3. Filosofía de Rediseño

### 3.1 Principios

```
1. CONVENCIÓN SOBRE CONFIGURACIÓN
   → El 80% de los casos debe funcionar con defaults
   
2. BATCH PRIMERO
   → Una llamada para crear 10 tracks, no 10 llamadas
   
3. VALIDACIÓN DEFENSIVA
   → Fallar rápido con mensajes claros, no dejar TSCN corrupto
   
4. CENTRALIZACIÓN POR DOMINIO
   → Un entry point por sistema (Animation, Skeleton, Sprite)
   
5. 2D/3D UNIFICADO
   → Parámetro `dimension: "2d" | "3d"` en lugar de tools duplicadas
```

### 3.2 Anti-Patrones a Eliminar

```python
# ANTES: 5 llamadas para setup básico
create_animation(scene, name="idle", tracks=[...])          # 1
create_state_machine(scene, name="states", states=[...])     # 2
create_blend_tree(scene, name="tree", nodes=[...])           # 3
add_node(scene, parent=".", type="AnimationPlayer", ...)     # 4
add_node(scene, parent=".", type="AnimationTree", ...)       # 5
set_node_properties(scene, node="AnimationTree", {            # 6
    "tree_root": SubResource("blendtree_tree"),
    "anim_player": "../AnimationPlayer"
})

# DESPUÉS: 1 llamada
setup_animation_system(scene, {
    "player": {
        "animations": [{"name": "idle", "tracks": [...]}]
    },
    "tree": {
        "type": "state_machine",  # o "blend_tree", "blend_space_1d"
        "states": [...],
        "transitions": [...]
    }
})
```

---

## 4. Propuestas de Mejora

### 4.1 NUEVA: `setup_animation_system` 🎯

**Propósito:** Setup completo de AnimationPlayer + AnimationTree en una sola llamada.

**Parámetros:**
```typescript
{
  session_id: string,
  scene_path: string,
  player?: {
    node_name?: string,           // default: "AnimationPlayer"
    autoplay?: string,            // default: ""
    animations: AnimationConfig[]
  },
  tree?: {
    node_name?: string,           // default: "AnimationTree"
    type: "state_machine" | "blend_tree" | "blend_space_1d" | "blend_space_2d",
    config: StateMachineConfig | BlendTreeConfig | BlendSpaceConfig,
    active?: bool                 // default: true
  },
  connect_tree_to_player?: bool   // default: true
}
```

**Caso de uso:** Setup completo de personaje en 1 llamada.

**Ejemplo:**
```python
setup_animation_system(scene, {
    "player": {
        "animations": [
            {
                "name": "idle",
                "length": 1.0,
                "loop": True,
                "tracks": [
                    {"path": "Sprite2D:position", "keyframes": [
                        {"time": 0, "value": [0, 0]},
                        {"time": 0.5, "value": [0, -2]},
                        {"time": 1, "value": [0, 0]}
                    ]}
                ]
            }
        ]
    },
    "tree": {
        "type": "state_machine",
        "config": {
            "states": ["idle", "walk", "run"],
            "transitions": [
                {"from": "idle", "to": "walk"},
                {"from": "walk", "to": "idle"}
            ]
        }
    }
})
```

---

### 4.2 NUEVA: `batch_create_animations` 🎬

**Propósito:** Crear múltiples animaciones con tracks complejos en una sola operación.

**Mejoras sobre `create_animation`:**
- Soporta `keyframes` simplificados (sin necesidad de arrays paralelos de times/values)
- Auto-calcula `length` si no se proporciona
- Soporta easing curves por keyframe
- Valida que los nodos referenciados existan en la escena

**Parámetros:**
```typescript
{
  session_id: string,
  scene_path: string,
  animations: [
    {
      name: string,
      length?: float,            // auto-calculate from keyframes if omitted
      loop?: bool,               // default: false
      tracks: [
        {
          path: string,          // "Sprite2D:position"
          type?: "value" | "position" | "rotation" | "scale" | "method",
          keyframes: [
            {
              time: float,
              value: any,
              easing?: "linear" | "ease_in" | "ease_out" | "ease_in_out" | float
            }
          ]
        }
      ]
    }
  ]
}
```

**Ejemplo:**
```python
batch_create_animations(scene, [
    {
        "name": "jump",
        "loop": False,
        "tracks": [
            {
                "path": "CharacterBody2D:position",
                "keyframes": [
                    {"time": 0.0, "value": [0, 0]},
                    {"time": 0.3, "value": [0, -50], "easing": "ease_out"},
                    {"time": 0.6, "value": [0, 0], "easing": "ease_in"}
                ]
            },
            {
                "path": "Sprite2D:scale",
                "keyframes": [
                    {"time": 0.0, "value": [1, 1]},
                    {"time": 0.3, "value": [0.9, 1.1]},
                    {"time": 0.6, "value": [1, 1]}
                ]
            }
        ]
    }
])
```

---

### 4.3 NUEVA: `setup_skeleton` 🦴

**Propósito:** Consolidar las 6 tools de skeleton en 1-2 tools unificadas.

**Reemplaza:** `create_skeleton2d`, `create_skeleton3d`, `add_bone2d`, `add_bone_attachment3d`

**Parámetros:**
```typescript
{
  session_id: string,
  scene_path: string,
  dimension: "2d" | "3d",
  parent_path?: string,         // default: "."
  node_name?: string,           // default: "Skeleton"
  bones?: [
    {
      name: string,
      parent?: string,          // omit for root
      position?: [x, y] | [x, y, z],
      length?: float,
      angle?: float,
      enabled?: bool
    }
  ],
  attachments?: [               // 3D only
    {
      bone: string,
      node_type: string,
      node_name: string
    }
  ],
  calculate_rest_poses?: bool   // default: true
}
```

**Ejemplo:**
```python
setup_skeleton(scene, dimension="2d", bones=[
    {"name": "Hip", "position": [0, 0]},
    {"name": "Torso", "parent": "Hip", "position": [0, -20], "length": 20},
    {"name": "Head", "parent": "Torso", "position": [0, -15], "length": 10},
    {"name": "ArmL", "parent": "Torso", "position": [-10, -5], "length": 15, "angle": -0.5},
    {"name": "ArmR", "parent": "Torso", "position": [10, -5], "length": 15, "angle": 0.5}
])
```

---

### 4.4 NUEVA: `setup_animated_sprite` 🎞️

**Propósito:** Setup completo de AnimatedSprite2D/3D con SpriteFrames en una llamada.

**Reemplaza:** `add_node` + `create_sprite_frames` + `set_node_properties`

**Parámetros:**
```typescript
{
  session_id: string,
  scene_path: string,
  parent_path?: string,         // default: "."
  node_name?: string,           // default: "AnimatedSprite"
  dimension: "2d" | "3d",       // default: "2d"
  animations: [
    {
      name: string,
      frames: string[],         // paths to textures
      speed?: float,            // default: 5.0
      loop?: bool               // default: true
    }
  ],
  default_animation?: string,   // auto-play this
  atlas?: {                     // optional: use sprite sheet
    texture: string,
    tile_size: [w, h],
    frames: { "animation_name": [[x1,y1], [x2,y2], ...] }
  }
}
```

**Ejemplo:**
```python
setup_animated_sprite(scene, dimension="2d", animations=[
    {
        "name": "idle",
        "frames": [
            "res://sprites/idle_1.png",
            "res://sprites/idle_2.png",
            "res://sprites/idle_3.png"
        ],
        "speed": 4.0
    },
    {
        "name": "run",
        "frames": ["res://sprites/run_1.png", "res://sprites/run_2.png"],
        "speed": 8.0
    }
], default_animation="idle")
```

---

### 4.5 NUEVA: `quick_tween` ⚡

**Propósito:** Crear animaciones simples de una propiedad sin necesidad de AnimationPlayer completo.

**Parámetros:**
```typescript
{
  session_id: string,
  scene_path: string,
  target: string,               // Node path
  property: string,             // "position", "modulate", "rotation", etc.
  to_value: any,                // target value
  duration: float,
  from_value?: any,             // omit to use current
  easing?: "linear" | "ease_in" | "ease_out" | "ease_in_out",
  delay?: float,                // default: 0
  loop?: bool                   // default: false
}
```

**Ejemplo:**
```python
quick_tween(scene, target="Player/Sprite2D", property="modulate", 
            to_value={"r": 1, "g": 0, "b": 0, "a": 1}, 
            duration=0.2, easing="ease_out")
```

---

### 4.6 MEJORA: `create_state_machine` v2 🔄

**Mejoras:**
- Auto-generar transiciones si no se proporcionan (fully connected por defecto)
- Soportar `start_node` explícito
- Soportar `end_node` para state machines anidadas
- Validar que todas las animaciones referenciadas existan

**Antes vs Después:**

```python
# ANTES - Verboso, todo manual
create_state_machine(scene, name="player", states=[
    {"name": "Idle", "node_properties": {"animation": "\"Idle\""}, "position": {"x": 293, "y": 87}},
    {"name": "Walk", "node_properties": {"animation": "\"Walk\""}, "position": {"x": 462, "y": 28}}
], transitions=[
    {"from": "Idle", "to": "Walk", "switch_mode": 0},
    {"from": "Walk", "to": "Idle", "switch_mode": 0}
])

# DESPUÉS - Mínimo, auto-layout
create_state_machine(scene, name="player", states=[
    {"name": "Idle", "animation": "Idle"},
    {"name": "Walk", "animation": "Walk"},
    {"name": "Run", "animation": "Run"}
], transitions="auto", layout="horizontal")  # auto-genera todas las transiciones
```

---

### 4.7 MEJORA: `create_blend_space_1d` v2 / `create_blend_space_2d` v2 📈

**Mejoras:**
- Auto-calcular `min_space`/`max_space` a partir de las posiciones de animaciones
- Defaults de posición en grid uniforme si no se proporcionan
- Auto-naming de puntos basado en animation name

**Antes vs Después:**

```python
# ANTES
Create_blend_space_1d(scene, name="movement", min_space=0.0, max_space=100.0, 
                      blend_position=0.0, animations=[
    {"name": "Idle", "position": 0.0, "animation": '"Idle"'},
    {"name": "Walk", "position": 50.0, "animation": '"Walk"'},
    {"name": "Run", "position": 100.0, "animation": '"Run"'}
])

# DESPUÉS
Create_blend_space_1d(scene, name="movement", animations=[
    {"animation": "Idle"},      # position auto = 0
    {"animation": "Walk"},      # position auto = 50
    {"animation": "Run"}        # position auto = 100
])  # min/max/blend_position auto-calculados
```

---

### 4.8 MEJORA: `create_blend_tree` v2 🌳

**Mejoras:**
- Auto-layout de nodos en grid si no se proporcionan posiciones
- Validación de grafo acíclico
- Auto-conectar output si solo hay un nodo
- Soportar nodos anidados (BlendSpace, StateMachine como nodos del tree)

---

### 4.9 EXPONER: `calculate_skeleton_poses` (antes interna) 🦴

**Propósito:** Exponer la función interna `calculate_rest_poses` como tool MCP.

**Parámetros:**
```typescript
{
  session_id: string,
  scene_path: string,
  skeleton_path: string,
  dimension: "2d" | "3d",
  method?: "automatic" | "from_current" | "from_t_pose"
}
```

---

## 5. Consolidación de Tools

### 5.1 Mapa de Migración

| Tools Actuales (12) | → | Tools Nuevas (7) |
|---------------------|---|------------------|
| `create_animation` | → | `batch_create_animations` |
| `create_state_machine` | → | `create_state_machine` v2 |
| `create_blend_space_1d` | → | `create_blend_space_1d` v2 |
| `create_blend_space_2d` | → | `create_blend_space_2d` v2 |
| `create_blend_tree` | → | `create_blend_tree` v2 |
| `create_sprite_frames` | → | `setup_animated_sprite` |
| `create_skeleton2d` | → | `setup_skeleton` |
| `create_skeleton3d` | → | `setup_skeleton` |
| `add_bone2d` | → | `setup_skeleton` |
| `add_bone_attachment3d` | → | `setup_skeleton` |
| `setup_polygon2d_skinning` | → | `setup_skeleton` |
| `setup_mesh_skinning` | → | `setup_skeleton` |
| `calculate_rest_poses` (interna) | → | `calculate_skeleton_poses` |
| `calculate_bone_weights` (interna) | → | `setup_skeleton` (integrado) |
| **NUEVO** | → | `setup_animation_system` |
| **NUEVO** | → | `quick_tween` |

### 5.2 Tools Obsoletas (mantener para compatibilidad por 1 versión)

- `create_animation` → deprecar, redirigir a `batch_create_animations`
- `create_sprite_frames` → deprecar, redirigir a `setup_animated_sprite`
- `create_skeleton2d/3d` → deprecar, redirigir a `setup_skeleton`
- `add_bone2d` → deprecar
- `add_bone_attachment3d` → deprecar

---

## 6. Mejoras Transversales

### 6.1 Validación Defensiva

Todas las tools deben validar:
- [ ] Que la escena existe
- [ ] Que los nodos referenciados existen
- [ ] Que los recursos referenciados existen
- [ ] Que no hay duplicados (nombres de animación, nodos, etc.)
- [ ] Que los NodePaths son válidos
- [ ] Que las transiciones de state machine son válidas (estados existen)

### 6.2 Auto-Naming y Defaults

| Concepto | Default |
|----------|---------|
| Nombre de AnimationPlayer | `"AnimationPlayer"` |
| Nombre de AnimationTree | `"AnimationTree"` |
| Nombre de Skeleton | `"Skeleton"` + dimensión |
| ID de animación | `"anim_" + name.lower()` |
| ID de state machine | `"sm_" + name.lower()` |
| Loop de animación | `false` (excepto idle que es `true`) |
| Speed de SpriteFrames | `5.0` |
| Easing | `"linear"` |

### 6.3 Batch Operations

Crear helper interno `_batch_subresources` que permita crear múltiples SubResources en una sola pasada de serialización, reduciendo I/O de 5x a 1x.

---

## 7. Ejemplos Completos: Antes vs Después

### 7.1 Setup de Personaje 2D con Animaciones

**ANTES (8 llamadas, ~20 líneas):**
```python
# 1. Crear AnimationPlayer
add_node(scene, parent=".", type="AnimationPlayer", node_name="AnimationPlayer")

# 2. Crear animaciones individuales
create_animation(scene, name="idle", length=1.0, loop_mode=1, tracks=[
    {"type": "value", "path": "Sprite2D:position", "keys": {
        "times": [0.0, 0.5, 1.0],
        "transitions": [1.0, 1.0, 1.0],
        "values": [[0,0], [0,-2], [0,0]]
    }}
])
create_animation(scene, name="walk", length=0.8, loop_mode=1, tracks=[...])

# 3. Crear state machine
create_state_machine(scene, name="player_sm", states=[
    {"name": "Idle", "node_properties": {"animation": '"idle"'}, "position": {"x": 100, "y": 100}},
    {"name": "Walk", "node_properties": {"animation": '"walk"'}, "position": {"x": 300, "y": 100}}
], transitions=[
    {"from": "Idle", "to": "Walk"},
    {"from": "Walk", "to": "Idle"}
])

# 4. Crear AnimationTree
add_node(scene, parent=".", type="AnimationTree", node_name="AnimationTree")

# 5. Conectar AnimationTree
set_node_properties(scene, "AnimationTree", {
    "tree_root": {"type": "SubResource", "ref": "sm_player_sm"},
    "anim_player": "../AnimationPlayer",
    "active": True
})
```

**DESPUÉS (1 llamada, ~12 líneas):**
```python
setup_animation_system(scene,
    player={
        "animations": [
            {
                "name": "idle",
                "loop": True,
                "tracks": [
                    {"path": "Sprite2D:position", "keyframes": [
                        {"time": 0, "value": [0, 0]},
                        {"time": 0.5, "value": [0, -2]},
                        {"time": 1, "value": [0, 0]}
                    ]}
                ]
            },
            {
                "name": "walk",
                "loop": True,
                "tracks": [...]
            }
        ]
    },
    tree={
        "type": "state_machine",
        "config": {
            "states": ["idle", "walk"],
            "transitions": "auto"
        }
    }
)
```

### 7.2 Setup de Skeleton 2D

**ANTES (6 llamadas por hueso):**
```python
create_skeleton2d(scene, parent=".", skeleton_name="Skeleton2D")
add_bone2d(scene, skeleton="Skeleton2D", bone_name="Hip")
add_bone2d(scene, skeleton="Skeleton2D", bone_name="Torso", parent="Hip", rest_transform={...})
add_bone2d(scene, skeleton="Skeleton2D", bone_name="Head", parent="Torso", rest_transform={...})
add_bone2d(scene, skeleton="Skeleton2D", bone_name="ArmL", parent="Torso", rest_transform={...})
add_bone2d(scene, skeleton="Skeleton2D", bone_name="ArmR", parent="Torso", rest_transform={...})
```

**DESPUÉS (1 llamada):**
```python
setup_skeleton(scene, dimension="2d", bones=[
    {"name": "Hip", "position": [0, 0]},
    {"name": "Torso", "parent": "Hip", "position": [0, -20], "length": 20},
    {"name": "Head", "parent": "Torso", "position": [0, -15], "length": 10},
    {"name": "ArmL", "parent": "Torso", "position": [-10, -5], "length": 15, "angle": -0.5},
    {"name": "ArmR", "parent": "Torso", "position": [10, -5], "length": 15, "angle": 0.5}
])
```

### 7.3 AnimatedSprite2D

**ANTES (3 llamadas):**
```python
add_node(scene, parent=".", type="AnimatedSprite2D", node_name="Sprite")
create_sprite_frames(scene, name="player", animations=[
    {"name": "idle", "frames": [{"texture": "res://idle1.png"}, {"texture": "res://idle2.png"}], "speed": 5}
])
set_node_properties(scene, "Sprite", {
    "sprite_frames": {"type": "SubResource", "ref": "sprites_player"},
    "animation": "idle"
})
```

**DESPUÉS (1 llamada):**
```python
setup_animated_sprite(scene, dimension="2d", animations=[
    {"name": "idle", "frames": ["res://idle1.png", "res://idle2.png"], "speed": 5}
], default_animation="idle")
```

---

## 8. Roadmap

### Fase 1: Fundamentos (Semana 1)
- [ ] Implementar `_batch_subresources` helper
- [ ] Implementar validación defensiva base
- [ ] Agregar auto-naming y defaults
- [ ] Tests unitarios para validación

### Fase 2: Tools Nuevas (Semana 2)
- [ ] `setup_animation_system`
- [ ] `batch_create_animations`
- [ ] `setup_skeleton`
- [ ] `setup_animated_sprite`
- [ ] `quick_tween`
- [ ] `calculate_skeleton_poses`

### Fase 3: Mejoras v2 (Semana 3)
- [ ] `create_state_machine` v2 (auto-transitions, auto-layout)
- [ ] `create_blend_space_1d/2d` v2 (auto-ranges, auto-positions)
- [ ] `create_blend_tree` v2 (auto-layout, validación de ciclos)
- [ ] Tests de integración

### Fase 4: Deprecación (Semana 4)
- [ ] Marcar tools antiguas como deprecated
- [ ] Agregar mensajes de migración
- [ ] Actualizar documentación
- [ ] Guía de migración para usuarios

---

## 9. Métricas de Éxito

| Métrica | Actual | Objetivo |
|---------|--------|----------|
| Pasos para setup AnimationPlayer+Tree | 5-8 | 1 |
| Pasos para setup Skeleton 2D (5 huesos) | 6 | 1 |
| Pasos para setup AnimatedSprite | 3 | 1 |
| Líneas de JSON promedio por tool | 15-25 | 8-12 |
| Tiempo de setup animación (estimado) | 15 min | 3 min |
| Tools de animación | 12 | 7 |
| Tasa de error (estimada) | 40% | <10% |

---

## 10. Notas de Implementación

### 10.1 Compatibilidad Hacia Atrás
- Las tools antiguas se mantienen por 1 versión con `@deprecated`
- Se agrega campo `deprecated_redirect` en el registro de tools
- Mensaje claro: "Use `setup_animation_system` instead"

### 10.2 Performance
- Batch operations reducen I/O de disco de N a 1
- Validación se hace en memoria antes de escribir
- Caché de escena invalidada solo al final

### 10.3 Error Handling
- Formato estándar de errores:
  ```json
  {
    "success": false,
    "error": "ANIMATION_DUPLICATE",
    "message": "Animation 'idle' already exists in scene",
    "suggestion": "Use animation_name='idle_v2' or remove existing animation first"
  }
  ```

---

*Plan creado por SATAN - JEFE SUPREMO*  
*Revisión: Pendiente*
