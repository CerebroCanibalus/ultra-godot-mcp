@echo off
REM Ultra Godot MCP v3.1.0 - Por los trabajadores y los iberófonos del mundo 🏴
REM Plus Ultra: ir más allá - MCP server con parser TSCN nativo

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
echo [Ultra Godot MCP v3.1.0] Plus Ultra: Iniciando servidor...
echo [Ultra Godot MCP v3.1.0] Parser TSCN nativo - Sin Godot (38 tools), Debug (2 tools)
echo [Ultra Godot MCP v3.1.0] 40 herramientas disponibles
echo.

python -m godot_mcp.server

if errorlevel 1 (
    echo.
    echo [ERROR] El servidor MCP termino con errores
    pause
    exit /b 1
)
