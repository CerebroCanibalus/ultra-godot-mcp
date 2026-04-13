"""
Test Script para Godot MCP Server
Verifica importaciones, inicio del servidor y herramientas
"""

import sys
import traceback
import importlib
from pathlib import Path


def print_section(title):
    sep = "=" * 60
    print(sep)
    print(title)
    print(sep)


def test_dependencies():
    """Verificar que las dependencias esten instaladas."""
    print_section("DEPENDENCIAS INSTALADAS")

    deps = {
        "fastmcp": "FastMCP",
        "fuzzywuzzy": "fuzzywuzzy",
        "watchdog": "watchdog",
    }

    all_ok = True
    for dep, name in deps.items():
        try:
            __import__(dep)
            version = getattr(sys.modules[dep], "__version__", "unknown")
            print("  [OK] " + name + " version: " + version)
        except ImportError:
            print("  [FAIL] " + name + " - NO INSTALADO")
            all_ok = False

    return all_ok


def test_core_modules():
    """Test de importacion de modulos core."""
    print_section("MODULOS CORE")

    modules = [
        "godot_mcp",
        "godot_mcp.core",
        "godot_mcp.core.cache",
        "godot_mcp.core.models",
        "godot_mcp.core.tscn_parser",
        "godot_mcp.core.tres_parser",
        "godot_mcp.core.project_index",
    ]

    all_ok = True
    src_path = Path("D:/Mis Juegos/GodotMCP/godot-mcp-python/src")
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

    for mod in modules:
        try:
            importlib.import_module(mod)
            print("  [OK] " + mod)
        except Exception as e:
            print("  [FAIL] " + mod + ": " + str(e))
            all_ok = False

    return all_ok


def test_tool_modules():
    """Test de importacion de modulos de herramientas."""
    print_section("MODULOS DE HERRAMIENTAS")

    modules = [
        "godot_mcp.tools.scene_tools",
        "godot_mcp.tools.node_tools",
        "godot_mcp.tools.resource_tools",
        "godot_mcp.tools.session_tools",
        "godot_mcp.tools.project_tools",
    ]

    all_ok = True
    src_path = Path("D:/Mis Juegos/GodotMCP/godot-mcp-python/src")
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

    for mod in modules:
        try:
            importlib.import_module(mod)
            print("  [OK] " + mod)
        except Exception as e:
            print("  [FAIL] " + mod + ": " + str(e))
            all_ok = False

    return all_ok


def test_fastmcp_api():
    """Verificar API de FastMCP usada."""
    print_section("VERIFICACION API FASTMCP")

    src_path = Path("D:/Mis Juegos/GodotMCP/godot-mcp-python/src")
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

    try:
        from fastmcp import FastMCP
        import inspect

        mcp = FastMCP("test-api")

        # Verificar metodos disponibles
        has_add_tool = hasattr(mcp, "add_tool")
        status = "DISPONIBLE" if has_add_tool else "NO DISPONIBLE"
        print("  add_tool: " + status)

        has_tool = callable(getattr(mcp, "tool", None))
        status = "DISPONIBLE" if has_tool else "NO DISPONIBLE"
        print("  .tool() decorator: " + status)

        # Probar registro de funcion
        def test_function(x):
            return x

        try:
            mcp.add_tool(test_function)
            print("  [OK] mcp.add_tool() funciona")
        except Exception as e:
            print("  [FAIL] mcp.add_tool(): " + str(e))
            return False

        return True

    except Exception as e:
        print("  [FAIL] Error verificando API: " + str(e))
        traceback.print_exc()
        return False


def test_server_start():
    """Test de inicio del servidor."""
    print_section("INICIO DEL SERVIDOR MCP")

    src_path = Path("D:/Mis Juegos/GodotMCP/godot-mcp-python/src")
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

    try:
        from godot_mcp import server

        print("  [OK] server.py importado")

        from fastmcp import FastMCP

        mcp = FastMCP("test-godot-mcp")

        # Importar registradores
        from godot_mcp.tools.scene_tools import register_scene_tools
        from godot_mcp.tools.node_tools import register_node_tools
        from godot_mcp.tools.resource_tools import register_resource_tools
        from godot_mcp.tools.session_tools import register_session_tools
        from godot_mcp.tools.project_tools import register_project_tools

        print("  [OK] Todos los registradores importados")

        # Intentar registrar cada grupo
        test_groups = [
            ("scene_tools", register_scene_tools),
            ("node_tools", register_node_tools),
            ("session_tools", register_session_tools),
            ("project_tools", register_project_tools),
            ("resource_tools", register_resource_tools),
        ]

        for name, register_func in test_groups:
            try:
                mcp_test = FastMCP("test-" + name)
                register_func(mcp_test)
                print("  [OK] " + name + " registrado")
            except Exception as e:
                print("  [FAIL] " + name + ": " + str(e))
                traceback.print_exc()

        return True

    except Exception as e:
        print("  [FAIL] Error al iniciar servidor: " + str(e))
        traceback.print_exc()
        return False


def main():
    """Ejecutar todos los tests."""
    sep = "=" * 60
    print(sep)
    print("GODOT MCP SERVER - TEST DE INTEGRACION")
    print(sep)

    results = {}

    # Test 1: Dependencias
    results["dependencias"] = test_dependencies()

    # Test 2: Modulos core
    results["core"] = test_core_modules()

    # Test 3: Modulos de herramientas
    results["tools"] = test_tool_modules()

    # Test 4: API FastMCP
    results["api"] = test_fastmcp_api()

    # Test 5: Inicio del servidor
    results["server"] = test_server_start()

    # Resumen
    print_section("RESUMEN DE RESULTADOS")

    all_passed = True
    for test_name, passed in results.items():
        if passed:
            status = "PASO"
        else:
            status = "FALLO"
            all_passed = False
        print("  " + test_name + ": " + status)

    if all_passed:
        print("\nTODOS LOS TESTS PASARON")
        sys.exit(0)
    else:
        print("\nALGUNOS TESTS FALLARON")
        sys.exit(1)


if __name__ == "__main__":
    main()
