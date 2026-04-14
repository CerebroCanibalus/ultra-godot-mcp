@echo off
REM Godot MCP Server v3.1.0 - Por Lenin y todos los iberófonos 🚩
REM MCP server for Godot Engine with native TSCN parsing

cd /d "%~dp0"

REM Verificar que Python esté instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python no esta instalado o no esta en el PATH
    echo Por favor instala Python 3.10+ desde https://python.org
    exit /b 1
)

REM Instalar el paquete en modo editable si no esta instalado
python -c "import godot_mcp" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Instalando godot-mcp por primera vez...
    pip install -e .
    if errorlevel 1 (
        echo [ERROR] No se pudo instalar godot-mcp
        exit /b 1
    )
)

REM Iniciar el servidor MCP
echo [Godot MCP v3.1.0] Iniciando servidor...
echo [Godot MCP v3.1.0] Parser TSCN nativo - Sin Godot headless
echo [Godot MCP v3.1.0] 38 herramientas disponibles
echo.

python -m godot_mcp.server

if errorlevel 1 (
    echo.
    echo [ERROR] El servidor MCP termino con errores
    pause
    exit /b 1
)
