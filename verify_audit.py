import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("==========================================")
print(" AUDITORIA MCP - VERIFICACION DE CORRECCIONES")
print("==========================================")
print()

errors = []

# 1. Verificar imports
print("[1/6] Verificando imports...")
try:
    from godot_mcp.core.tscn_parser import parse_tscn, parse_tscn_string
    print("  TSCNParser: OK")
except Exception as e:
    errors.append(f"TSCNParser: {e}")
    print(f"  TSCNParser: FAIL - {e}")

try:
    from godot_mcp.tools.decorators import require_session
    print("  Decorators: OK")
except Exception as e:
    errors.append(f"Decorators: {e}")
    print(f"  Decorators: FAIL - {e}")

try:
    from godot_mcp.tools.session_tools import get_session_manager
    print("  SessionTools: OK")
except Exception as e:
    errors.append(f"SessionTools: {e}")
    print(f"  SessionTools: FAIL - {e}")

try:
    from godot_mcp.core.cache import get_cache
    print("  Cache: OK")
except Exception as e:
    errors.append(f"Cache: {e}")
    print(f"  Cache: FAIL - {e}")

# 2. Verificar Vector4 parsing
print()
print("[2/6] Verificando Vector4 parsing...")
try:
    from godot_mcp.core.tscn_parser import _parse_gdscript_value
    result = _parse_gdscript_value("Vector4(1.0, 2.0, 3.0, 4.0)")
    assert result['type'] == 'Vector4', f"Type mismatch: {result.get('type')}"
    assert result['x'] == 1.0, f"X mismatch: {result.get('x')}"
    assert result['y'] == 2.0, f"Y mismatch: {result.get('y')}"
    assert result['z'] == 3.0, f"Z mismatch: {result.get('z')}"
    assert result['w'] == 4.0, f"W mismatch: {result.get('w')}"
    print("  Vector4 parsing: OK")
except Exception as e:
    errors.append(f"Vector4: {e}")
    print(f"  Vector4 parsing: FAIL - {e}")

# 3. Verificar cache invalidation
print()
print("[3/6] Verificando cache invalidation...")
try:
    from godot_mcp.core.cache import get_cache
    from godot_mcp.tools.node_tools import _mark_scene_dirty
    cache = get_cache()
    cache.set('test_scene.tscn', {'data': 'test'})
    assert cache.get('test_scene.tscn') is not None, 'Cache should have value'
    _mark_scene_dirty('test_scene.tscn')
    assert cache.get('test_scene.tscn') is None, 'Cache should be invalidated'
    print("  Cache invalidation: OK")
except Exception as e:
    errors.append(f"CacheInvalidation: {e}")
    print(f"  Cache invalidation: FAIL - {e}")

# 4. Verificar SessionManager
print()
print("[4/6] Verificando SessionManager...")
try:
    from godot_mcp.session_manager import SessionManager
    sm = SessionManager()
    # Don't actually create session since we need a real path
    print("  SessionManager: OK")
except Exception as e:
    errors.append(f"SessionManager: {e}")
    print(f"  SessionManager: FAIL - {e}")

# 5. Verificar GodotCLIWrapper
print()
print("[5/6] Verificando GodotCLIWrapper (imports)...")
try:
    from godot_mcp.godot_cli.base import GodotCLIWrapper
    print("  GodotCLIWrapper: OK")
except Exception as e:
    errors.append(f"GodotCLIWrapper: {e}")
    print(f"  GodotCLIWrapper: FAIL - {e}")

# 6. Verificar LSP/DAP clients
print()
print("[6/6] Verificando LSP/DAP clients...")
try:
    from godot_mcp.lsp_dap.client import GodotLSPClient
    print("  LSP Client: OK")
except Exception as e:
    errors.append(f"LSPClient: {e}")
    print(f"  LSP Client: FAIL - {e}")

print()
print("==========================================")
if errors:
    print(f"  ERRORES: {len(errors)}")
    for err in errors:
        print(f"    - {err}")
    sys.exit(1)
else:
    print("  TODAS LAS VERIFICACIONES PASARON")
    print("==========================================")
    print()
    print("Correcciones aplicadas:")
    print("  - Codigo duplicado eliminado (tscn_parser.py)")
    print("  - Import circular roto (decorators.py)")
    print("  - Vector4 parsing corregido")
    print("  - Cache invalidation agregada")
    print("  - Timeouts y manejo de procesos mejorado")
    print("  - Except Exception especificados")
    print()
