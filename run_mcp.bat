@echo off
REM Godot MCP Server v2.0.0 - Por Lenin y todos los iberófonos 🚩
REM Ultra-fast MCP server for Godot Engine with native TSCN parsing

cd /d "D:\Mis Juegos\GodotMCP\godot-mcp-python"

REM Verificar que Python esté instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python no está instalado o no está en el PATH
    echo Por favor instala Python 3.10+ desde https://python.org
    exit /b 1
)

REM Instalar el paquete en modo editable si no está instalado
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
echo [Godot MCP v2.0.0] Iniciando servidor...
echo [Godot MCP v2.0.0] Parser TSCN nativo - Sin Godot headless
echo [Godot MCP v2.0.0] 24 herramientas disponibles
echo.

python -m godot_mcp.server

if errorlevel 1 (
    echo.
    echo [ERROR] El servidor MCP terminó con errores
    pause
    exit /b 1
)
