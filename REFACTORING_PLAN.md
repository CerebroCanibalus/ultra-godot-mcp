# 📋 Plan de Refactorización Media - Godot MCP Python

## Resumen Ejecutivo

Basado en el test exhaustivo realizado en el proyecto LAIKA, se han identificado 4 áreas críticas que requieren refactorización.

---

## 🔴 Problemas Críticos Identificados

### 1. Arquitectura de Sesiones - PRIORIDAD ALTA

**Problema:** Las tools NO requieren `session_id` como parámetro obligatorio
- Cada operación abre/cierra archivos individualmente
- No hay persistencia de estado entre operaciones
- No se aprovecha el SessionCache implementado

**Solución:** TODAS las tools deben requerir `session_id: str` como primer parámetro obligatorio

**Tasks:**
- [ ] Modificar session_tools.py para exponer gestión de sesiones
- [ ] Agregar session_id obligatorio a todas las tools
- [ ] Implementar middleware de validación de sesiones
- [ ] Crear sistema de locks por archivo

---

### 2. Sistema de Sub-resources y Ext-resources - PRIORIDAD ALTA

**Problema:** Formato TSCN inválido para Godot 4
- Shapes guardados como diccionarios inline: `shape = {"'type'": "'CapsuleShape2D'"...}`
- Texturas como strings simples en lugar de ext_resource
- No se crean sub-resources ni ext-resources

**Formato Actual (INVÁLIDO):**
```tscn
shape = {"'type'": "'CapsuleShape2D'", "'radius'": 12}
texture = "res://sprite.png"
```

**Formato Correcto:**
```tscn
[ext_resource type="Texture2D" path="res://sprite.png" id="1_xkfk2"]
[sub_resource type="CapsuleShape2D" id="CapsuleShape2D_7p5xm"]
radius = 12.0

[node name="Body" type="CollisionShape2D"]
shape = SubResource("CapsuleShape2D_7p5xm")
texture = ExtResource("1_xkfk2")
```

**Nuevas Tools Requeridas:**
- `create_sub_resource()` - Crea sub-resources con ID único
- `create_ext_resource()` - Crea referencias a archivos externos
- Modificar `add_node` y `update_node` para manejar recursos

---

### 3. Tools para Tareas Especializadas - PRIORIDAD MEDIA

**Faltan tools para:**
- Esqueletos 2D/3D (Skeleton2D, Bone2D)
- AnimationPlayer complejo (tracks, keyframes, blend trees)
- TileMap avanzado (atlas, terrains)

**Nuevos módulos necesarios:**
- `skeleton_tools.py`
- `animation_tools.py`
- `tilemap_tools.py`

---

### 4. Sistema de Scripts GDScript - PRIORIDAD MEDIA

**Problema:** No hay tool dedicada para crear scripts con buen formato

**Nuevas Tools:**
- `create_gdscript()` - Con templates y validación
- `validate_gdscript()` - Validación de sintaxis
- `add_script_method()` - Agregar métodos a scripts existentes

**Templates necesarios:**
- character_controller
- state_machine
- singleton
- component

---

## 📊 Prioridad de Implementación

1. **ALTA:** Sistema de Sesiones (requerido para todo lo demás)
2. **ALTA:** Sub-resources y Ext-resources (bloqueante para Godot 4)
3. **MEDIA:** Scripts GDScript (mejora DX significativa)
4. **MEDIA:** Tools especializadas (features avanzadas)

---

## ✅ Estado Actual del Test

**Tools que funcionan:**
- create_scene
- add_node (básico)
- update_node (propiedades simples)
- get_scene_tree

**Tools con problemas:**
- update_node (no crea recursos correctamente)
- add_node (sin soporte de sub-resources)

**El servidor MCP inicia correctamente** después de las correcciones de encoding Unicode.
