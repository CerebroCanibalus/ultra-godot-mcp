@echo off
REM Script de verificación post-auditoría
REM Valida que las correcciones críticas no rompan el sistema

cd /d "%~dp0"

echo ==========================================
echo  AUDITORIA MCP - VERIFICACION DE CORRECCIONES
echo ==========================================
echo.

REM 1. Verificar que Python puede importar los módulos corregidos
echo [1/6] Verificando imports...
python -c "from godot_mcp.core.tscn_parser import parse_tscn, parse_tscn_string; print('  TSCNParser: OK')" 
if errorlevel 1 (
    echo [FAIL] TSCNParser no importa
    exit /b 1
)

python -c "from godot_mcp.tools.decorators import require_session; print('  Decorators: OK')"
if errorlevel 1 (
    echo [FAIL] Decorators no importa
    exit /b 1
)

python -c "from godot_mcp.tools.session_tools import get_session_manager; print('  SessionTools: OK')"
if errorlevel 1 (
    echo [FAIL] SessionTools no importa
    exit /b 1
)

python -c "from godot_mcp.core.cache import get_cache; print('  Cache: OK')"
if errorlevel 1 (
    echo [FAIL] Cache no importa
    exit /b 1
)

echo.
echo [2/6] Verificando Vector4 parsing...
python -c "
from godot_mcp.core.tscn_parser import _parse_value
result = _parse_value('Vector4(1.0, 2.0, 3.0, 4.0)')
assert result['type'] == 'Vector4', 'Type mismatch'
assert result['x'] == 1.0, 'X mismatch'
assert result['y'] == 2.0, 'Y mismatch'
assert result['z'] == 3.0, 'Z mismatch'
assert result['w'] == 4.0, 'W mismatch'
print('  Vector4 parsing: OK')
"
if errorlevel 1 (
    echo [FAIL] Vector4 parsing incorrecto
    exit /b 1
)

echo.
echo [3/6] Verificando cache invalidation...
python -c "
from godot_mcp.core.cache import get_cache
from godot_mcp.tools.node_tools import _mark_scene_dirty
cache = get_cache()
cache.set('test_scene.tscn', {'data': 'test'})
assert cache.get('test_scene.tscn') is not None, 'Cache should have value'
_mark_scene_dirty('test_scene.tscn')
assert cache.get('test_scene.tscn') is None, 'Cache should be invalidated'
print('  Cache invalidation: OK')
"
if errorlevel 1 (
    echo [FAIL] Cache invalidation no funciona
    exit /b 1
)

echo.
echo [4/6] Verificando SessionManager...
python -c "
from godot_mcp.session_manager import SessionManager
sm = SessionManager()
session = sm.create_session('D:\\test', 'test_session')
assert session is not None, 'Session should be created'
print('  SessionManager: OK')
"
if errorlevel 1 (
    echo [FAIL] SessionManager no funciona
    exit /b 1
)

echo.
echo [5/6] Verificando GodotCLIWrapper (imports)...
python -c "
from godot_mcp.godot_cli.base import GodotCLIWrapper
print('  GodotCLIWrapper: OK')
"
if errorlevel 1 (
    echo [FAIL] GodotCLIWrapper no importa
    exit /b 1
)

echo.
echo [6/6] Verificando LSP/DAP clients...
python -c "
from godot_mcp.lsp_dap.client import GodotLSPClient
print('  LSP Client: OK')
"
if errorlevel 1 (
    echo [FAIL] LSP Client no importa
    exit /b 1
)

echo.
echo ==========================================
echo  TODAS LAS VERIFICACIONES PASARON
echo ==========================================
echo.
echo Correcciones aplicadas:
echo   - Codigo duplicado eliminado (tscn_parser.py)
echo   - Import circular roto (decorators.py)
echo   - Vector4 parsing corregido
echo   - Cache invalidation agregada
echo   - Timeouts y manejo de procesos mejorado
echo   - Except Exception especificados
echo.

pause
