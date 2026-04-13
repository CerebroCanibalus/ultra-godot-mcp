# -*- coding: utf-8 -*-
import sys

sys.path.insert(0, "src")

from godot_mcp.core.models import (
    Scene,
    Node,
    ExtResource,
    SubResource,
    PropertyValue,
    GodotVector2,
    GodotVector3,
    GodotColor,
    GodotRect2,
    GodotNodePath,
    GodotStringName,
    GodotArray,
    GodotDictionary,
    create_scene,
    create_node,
)

# Test 1: Crear una escena
scene = create_scene("Node2D", "Main")
print("[OK] Scene creada")

# Test 2: Anadir nodos
player = create_node("CharacterBody2D", "Player", position=GodotVector2(100, 200))
sprite = create_node("Sprite2D", "Sprite")
player.add_child(sprite)
scene.root.add_child(player)
print("[OK] Nodos anadidos")

# Test 3: get_node_by_path
found = scene.get_node_by_path("Main/Player")
print("[OK] get_node_by_path: {}".format(found.name if found else "None"))

# Test 4: get_children_of
children = scene.get_children_of("Main/Player")
print("[OK] get_children_of: {} hijos".format(len(children)))

# Test 5: find_nodes_by_type
nodes = scene.find_nodes_by_type("Sprite2D")
print("[OK] find_nodes_by_type: {} Sprite2D".format(len(nodes)))

# Test 6: find_nodes_by_name
nodes = scene.find_nodes_by_name("*Player")
print("[OK] find_nodes_by_name: {} nodos que coinciden".format(len(nodes)))

# Test 7: to_dict serializacion
d = scene.to_dict()
print("[OK] to_dict: serializacion exitosa, root type = {}".format(d["root"]["type"]))

# Test 8: PropertyValue
prop = PropertyValue(value=GodotVector2(10, 20), type="Vector2")
print("[OK] PropertyValue: {}, {}".format(prop.value.x, prop.value.y))

# Test 9: ExtResource y SubResource
ext = ExtResource(id="1", type="PackedScene", path="res://scenes/Player.tscn")
sub = SubResource(id="1", type="CircleShape2D")
scene.add_ext_resource(ext)
scene.add_sub_resource(sub)
print("[OK] ExtResource y SubResource anadidos")

print("")
print("Todos los tests pasaron!")
