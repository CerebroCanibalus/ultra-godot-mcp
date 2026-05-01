#!/usr/bin/env python3
"""
BENCHMARK MCP GODOT - Diagnóstico de Rendimiento v1.0

Mide operaciones críticas del MCP para identificar cuellos de botella reales.
No asume nada - solo mide y reporta.
"""

import cProfile
import io
import json
import os
import pstats
import sys
import tempfile
import time
import tracemalloc
from pathlib import Path

# Agregar src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from godot_mcp.core.tscn_parser import parse_tscn_string, Scene, SceneNode
from godot_mcp.core.project_index import ProjectIndexer, parse_gd_script
from godot_mcp.core.cache import LRUCache
from godot_mcp.session_manager import SessionManager


# =============================================================================
# Generadores de Datos de Prueba
# =============================================================================

def generate_tscn_small():
    """Escena pequeña: 5 nodos, 2 ext_resources"""
    return """[gd_scene load_steps=3 format=3 uid="uid://abc123"]

[ext_resource type="Script" path="res://player.gd" id="1_abc"]
[ext_resource type="PackedScene" path="res://sprite.tscn" id="2_def"]

[node name="Player" type="CharacterBody2D"]
position = Vector2(100, 200)
script = ExtResource("1_abc")

[node name="Sprite2D" type="Sprite2D" parent="."]
texture = ExtResource("2_def")

[node name="CollisionShape2D" type="CollisionShape2D" parent="."]

[node name="Area2D" type="Area2D" parent="."]

[node name="Camera2D" type="Camera2D" parent="."]
"""

def generate_tscn_medium():
    """Escena mediana: 50 nodos, 10 ext_resources"""
    lines = ['[gd_scene load_steps=11 format=3 uid="uid://bench123"]\n']
    for i in range(10):
        lines.append(f'[ext_resource type="Script" path="res://script_{i}.gd" id="{i}_res"]\n')
    
    # Root node
    lines.append('[node name="Root" type="Node2D"]\n')
    
    # 49 child nodes con propiedades
    for i in range(49):
        res_id = i % 10
        lines.append(f'[node name="Node{i}" type="Sprite2D" parent="."]')
        lines.append(f'position = Vector2({i*10}, {i*5})')
        lines.append(f'texture = ExtResource("{res_id}_res")')
        lines.append('')
    
    return '\n'.join(lines)

def generate_tscn_large():
    """Escena grande: 200 nodos, 50 ext_resources (simula nivel complejo)"""
    lines = ['[gd_scene load_steps=51 format=3 uid="uid://bench_large"]\n']
    for i in range(50):
        lines.append(f'[ext_resource type="Texture2D" path="res://assets/tex_{i}.png" id="tex_{i}"]\n')
    
    lines.append('[node name="Level" type="Node2D"]\n')
    
    for i in range(199):
        res_id = i % 50
        node_type = ["Sprite2D", "StaticBody2D", "Area2D", "Marker2D", "CollisionShape2D"][i % 5]
        lines.append(f'[node name="Entity{i}" type="{node_type}" parent="."]')
        lines.append(f'position = Vector2({i*16}, {i*8})')
        if node_type == "Sprite2D":
            lines.append(f'texture = ExtResource("tex_{res_id}")')
            lines.append(f'modulate = Color(1, 0.5, 0.5, 1)')
        elif node_type == "CollisionShape2D":
            lines.append(f'shape = SubResource("shape_{i}")')
        lines.append('')
    
    # Sub-resources
    for i in range(50):
        lines.append(f'[sub_resource type="RectangleShape2D" id="shape_{i}"]')
        lines.append(f'size = Vector2(16, 16)')
        lines.append('')
    
    return '\n'.join(lines)

def generate_gdscript():
    """GDScript típico con funciones, variables, señales"""
    return '''extends CharacterBody2D

class_name Player

signal health_changed(new_health)
signal died

@export var speed: float = 200.0
@export var jump_force: float = 400.0
@export var max_health: int = 100

var velocity: Vector2 = Vector2.ZERO
var health: int = max_health
var is_jumping: bool = false

func _ready():
    health = max_health
    emit_signal("health_changed", health)

func _physics_process(delta):
    handle_input()
    apply_gravity(delta)
    move_and_slide()

func handle_input():
    var direction = Input.get_axis("ui_left", "ui_right")
    velocity.x = direction * speed

func apply_gravity(delta):
    if not is_on_floor():
        velocity.y += 980 * delta

func take_damage(amount: int):
    health -= amount
    emit_signal("health_changed", health)
    if health <= 0:
        die()

func die():
    emit_signal("died")
    queue_free()

func heal(amount: int):
    health = min(health + amount, max_health)
    emit_signal("health_changed", health)
'''

# =============================================================================
# Benchmark Functions
# =============================================================================

def benchmark_parse_tscn():
    """Benchmark: Parsing de TSCN (operación más frecuente)"""
    print("\n" + "="*70)
    print("BENCHMARK 1: TSCN PARSING")
    print("="*70)
    
    test_cases = [
        ("Small (5 nodes)", generate_tscn_small()),
        ("Medium (50 nodes)", generate_tscn_medium()),
        ("Large (200 nodes)", generate_tscn_large()),
    ]
    
    for name, content in test_cases:
        # Warmup
        for _ in range(3):
            parse_tscn_string(content)
        
        # Medir
        times = []
        for _ in range(20):
            start = time.perf_counter()
            scene = parse_tscn_string(content)
            elapsed = time.perf_counter() - start
            times.append(elapsed)
        
        avg = sum(times) / len(times)
        min_t = min(times)
        max_t = max(times)
        
        print(f"  {name:20s} | avg: {avg*1000:7.3f}ms | min: {min_t*1000:7.3f}ms | max: {max_t*1000:7.3f}ms | nodes: {len(scene.nodes)}")

def benchmark_tscn_serialization():
    """Benchmark: Serialización Scene -> TSCN string"""
    print("\n" + "="*70)
    print("BENCHMARK 2: TSCN SERIALIZATION")
    print("="*70)
    
    test_cases = [
        ("Small", parse_tscn_string(generate_tscn_small())),
        ("Medium", parse_tscn_string(generate_tscn_medium())),
        ("Large", parse_tscn_string(generate_tscn_large())),
    ]
    
    for name, scene in test_cases:
        times = []
        for _ in range(20):
            start = time.perf_counter()
            result = scene.to_tscn()
            elapsed = time.perf_counter() - start
            times.append(elapsed)
        
        avg = sum(times) / len(times)
        print(f"  {name:20s} | avg: {avg*1000:7.3f}ms | output: {len(result):,} chars")

def benchmark_cache():
    """Benchmark: Operaciones de cache"""
    print("\n" + "="*70)
    print("BENCHMARK 3: CACHE OPERATIONS")
    print("="*70)
    
    cache = LRUCache(max_size=100)
    scene = parse_tscn_string(generate_tscn_medium())
    
    # Set
    times = []
    for i in range(100):
        start = time.perf_counter()
        cache.set(f"key_{i}", scene)
        times.append(time.perf_counter() - start)
    print(f"  cache.set() x100     | avg: {sum(times)/len(times)*1000:7.3f}ms")
    
    # Get (hits)
    times = []
    for i in range(100):
        start = time.perf_counter()
        cache.get(f"key_{i}")
        times.append(time.perf_counter() - start)
    print(f"  cache.get() (hit) x100| avg: {sum(times)/len(times)*1000:7.3f}ms")
    
    # Get (miss)
    times = []
    for i in range(100):
        start = time.perf_counter()
        cache.get(f"nonexistent_{i}")
        times.append(time.perf_counter() - start)
    print(f"  cache.get() (miss) x100| avg: {sum(times)/len(times)*1000:7.3f}ms")
    
    stats = cache.get_stats()
    print(f"  Cache stats: hits={stats['hits']}, misses={stats['misses']}, hit_rate={stats['hit_rate']:.1%}")

def benchmark_session_manager():
    """Benchmark: Session Manager operaciones"""
    print("\n" + "="*70)
    print("BENCHMARK 4: SESSION MANAGER")
    print("="*70)
    
    # Crear manager sin persistencia para medir solo memoria
    mgr = SessionManager(persistence_path=None, auto_save=False)
    
    # Crear sesiones
    times = []
    for i in range(50):
        start = time.perf_counter()
        sid = mgr.create_session(f"D:/TestProject{i}")
        times.append(time.perf_counter() - start)
    print(f"  create_session() x50  | avg: {sum(times)/len(times)*1000:7.3f}ms")
    
    # Record operations
    sid = list(mgr._sessions.keys())[0]
    times = []
    for i in range(100):
        start = time.perf_counter()
        mgr.record_operation(sid, "edit", f"node_{i}", f"Modified node {i}")
        times.append(time.perf_counter() - start)
    print(f"  record_operation() x100| avg: {sum(times)/len(times)*1000:7.3f}ms")
    
    # Get operations
    times = []
    for _ in range(100):
        start = time.perf_counter()
        mgr.get_recent_operations(sid, n=10)
        times.append(time.perf_counter() - start)
    print(f"  get_recent_ops() x100 | avg: {sum(times)/len(times)*1000:7.3f}ms")
    
    print(f"  Active sessions: {mgr.get_session_count()}")

def benchmark_gdscript_parsing():
    """Benchmark: Parseo de GDScript"""
    print("\n" + "="*70)
    print("BENCHMARK 5: GDSCRIPT PARSING")
    print("="*70)
    
    # Crear archivo temporal
    with tempfile.NamedTemporaryFile(mode='w', suffix='.gd', delete=False) as f:
        f.write(generate_gdscript())
        temp_path = f.name
    
    try:
        times = []
        for _ in range(100):
            start = time.perf_counter()
            info = parse_gd_script(temp_path, "D:/FakeProject")
            elapsed = time.perf_counter() - start
            times.append(elapsed)
        
        avg = sum(times) / len(times)
        info = parse_gd_script(temp_path, "D:/FakeProject")
        print(f"  parse_gd_script() x100 | avg: {avg*1000:7.3f}ms")
        print(f"  Parsed: {len(info.functions)} functions, {len(info.variables)} vars, {len(info.signals)} signals")
    finally:
        os.unlink(temp_path)

def benchmark_memory_usage():
    """Benchmark: Uso de memoria"""
    print("\n" + "="*70)
    print("BENCHMARK 6: MEMORY USAGE")
    print("="*70)
    
    tracemalloc.start()
    
    # Medir memoria base
    baseline = tracemalloc.get_traced_memory()[0]
    
    # Parsear escena grande
    scene = parse_tscn_string(generate_tscn_large())
    after_parse = tracemalloc.get_traced_memory()[0]
    
    # Serializar
    tscn = scene.to_tscn()
    after_serialize = tracemalloc.get_traced_memory()[0]
    
    tracemalloc.stop()
    
    print(f"  Baseline memory:     {baseline/1024:8.1f} KB")
    print(f"  After parse (large): {(after_parse-baseline)/1024:8.1f} KB")
    print(f"  After serialize:     {(after_serialize-after_parse)/1024:8.1f} KB")
    print(f"  Total delta:         {(after_serialize-baseline)/1024:8.1f} KB")

def benchmark_profiling_detailed():
    """cProfile detallado de la operación más crítica: parse_tscn"""
    print("\n" + "="*70)
    print("BENCHMARK 7: DETAILED PROFILING (parse_tscn large scene x50)")
    print("="*70)
    
    large_content = generate_tscn_large()
    
    profiler = cProfile.Profile()
    profiler.enable()
    
    for _ in range(50):
        parse_tscn_string(large_content)
    
    profiler.disable()
    
    # Stats
    s = io.StringIO()
    ps = pstats.Stats(profiler, stream=s)
    ps.sort_stats('cumulative')
    ps.print_stats(20)
    
    print(s.getvalue())

def benchmark_project_index_mock():
    """Benchmark: Indexación de proyecto simulado"""
    print("\n" + "="*70)
    print("BENCHMARK 8: PROJECT INDEX (Simulated)")
    print("="*70)
    
    # Crear estructura de proyecto temporal
    with tempfile.TemporaryDirectory() as tmpdir:
        # Crear 20 escenas, 20 scripts, 10 recursos
        for i in range(20):
            with open(os.path.join(tmpdir, f"scene_{i}.tscn"), 'w') as f:
                f.write(generate_tscn_small())
            with open(os.path.join(tmpdir, f"script_{i}.gd"), 'w') as f:
                f.write(generate_gdscript())
        
        # Crear indexador
        indexer = ProjectIndexer(tmpdir)
        
        start = time.perf_counter()
        index = indexer.build_index()
        elapsed = time.perf_counter() - start
        
        print(f"  Index time (50 files): {elapsed*1000:7.1f}ms")
        print(f"  Scenes indexed: {len(index.scenes)}")
        print(f"  Scripts indexed: {len(index.scripts)}")
        
        # Segunda llamada (cache)
        start = time.perf_counter()
        index2 = indexer.build_index()
        elapsed2 = time.perf_counter() - start
        print(f"  Index time (cached):   {elapsed2*1000:7.1f}ms")

# =============================================================================
# Main
# =============================================================================

def run_all_benchmarks():
    print("\n" + "#"*70)
    print("# MCP GODOT - DIAGNÓSTICO DE RENDIMIENTO")
    print("#"*70)
    print(f"# Python: {sys.version}")
    print(f"# Platform: {sys.platform}")
    print(f"# CWD: {os.getcwd()}")
    print("#"*70)
    
    benchmark_parse_tscn()
    benchmark_tscn_serialization()
    benchmark_cache()
    benchmark_session_manager()
    benchmark_gdscript_parsing()
    benchmark_memory_usage()
    benchmark_project_index_mock()
    benchmark_profiling_detailed()
    
    print("\n" + "#"*70)
    print("# BENCHMARK COMPLETADO")
    print("#"*70)

if __name__ == "__main__":
    run_all_benchmarks()
