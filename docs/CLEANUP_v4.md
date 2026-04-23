# 🧹 Análisis de Limpieza e Integración con Sesiones v4.0.0

## Resumen Ejecutivo

El sistema de sesiones actual es **sólido** y no requiere refactor mayor. La integración con Godot CLI headless es una **extensión natural** que aprovecha el campo `metadata` de Session para cachear el proceso de Godot.

**Hallazgo clave:** El código actual está bien diseñado - solo necesitamos:
1. **Añadir** Godot CLI wrapper a Session
2. **Limpiar** duplicación en debug_tools.py
3. **Refactor** server.py para registro dinámico de módulos

---

## 1. Integración con Sistema de Sesiones

### 1.1 Extensión de Session (Sin Breaking Changes)

```python
@dataclass
class Session:
    # ... campos existentes ...
    
    # NUEVO v4.0.0: Godot CLI Headless Process
    godot_process: Optional[subprocess.Popen] = field(default=None, repr=False)
    godot_process_pid: Optional[int] = field(default=None)
    godot_cli_ready: bool = field(default=False)
    godot_cli_port: Optional[int] = field(default=None)  # Para LSP/DAP
    
    # NUEVO v4.0.0: Cache de resultados CLI
    cli_cache: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        # ... existing ...
        # NO serializar godot_process (no es serializable)
        return {
            # ... existing fields ...
            "godot_cli_ready": self.godot_cli_ready,
            "godot_cli_port": self.godot_cli_port,
            "cli_cache": self.cli_cache,
        }
```

### 1.2 Nuevos Métodos en SessionManager

```python
class SessionManager:
    # ... existing methods ...
    
    # ==================== Godot CLI Lifecycle ====================
    
    def start_godot_headless(self, session_id: str, 
                            godot_path: Optional[str] = None) -> dict:
        """
        Inicia Godot en modo headless para la sesión.
        
        El proceso queda corriendo en background para operaciones rápidas.
        Se mata automáticamente al cerrar la sesión.
        """
        session = self._sessions.get(session_id)
        if not session:
            return {"success": False, "error": "Session not found"}
        
        # Si ya hay un proceso corriendo, reusarlo
        if session.godot_process and session.godot_process.poll() is None:
            return {"success": True, "pid": session.godot_process.pid, 
                    "reused": True}
        
        # Buscar ejecutable
        godot_exe = godot_path or _find_godot_executable()
        if not godot_exe:
            return {"success": False, "error": "Godot executable not found"}
        
        # Iniciar Godot headless con --script que mantiene vivo el proceso
        # Usamos un script GDScript que hereda de MainLoop y espera comandos
        cmd = [
            godot_exe,
            "--headless",
            "--path", session.project_path,
            "--script", "res://.godot_mcp/headless_bridge.gd"
        ]
        
        try:
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8"
            )
            
            session.godot_process = process
            session.godot_process_pid = process.pid
            session.godot_cli_ready = True
            
            logger.info(f"Started Godot headless for session {session_id} "
                       f"(PID: {process.pid})")
            
            return {
                "success": True,
                "pid": process.pid,
                "reused": False
            }
            
        except Exception as e:
            return {"success": False, "error": f"Failed to start Godot: {e}"}
    
    def stop_godot_headless(self, session_id: str) -> bool:
        """Detiene el proceso Godot headless de la sesión."""
        session = self._sessions.get(session_id)
        if not session or not session.godot_process:
            return False
        
        try:
            session.godot_process.terminate()
            session.godot_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            session.godot_process.kill()
        except Exception as e:
            logger.error(f"Error stopping Godot: {e}")
            return False
        finally:
            session.godot_process = None
            session.godot_process_pid = None
            session.godot_cli_ready = False
        
        return True
    
    def execute_gdscript_quick(self, session_id: str, 
                               script_content: str,
                               timeout: int = 10) -> dict:
        """
        Ejecuta GDScript usando el proceso headless existente.
        
        MUCHO más rápido que iniciar Godot cada vez.
        """
        session = self._sessions.get(session_id)
        if not session:
            return {"success": False, "error": "Session not found"}
        
        # Asegurar que Godot headless esté corriendo
        if not session.godot_cli_ready or not session.godot_process:
            result = self.start_godot_headless(session_id)
            if not result["success"]:
                return result
        
        # Enviar script al proceso vía stdin y leer stdout
        # (requiere que el script bridge.gd soporte este protocolo)
        try:
            process = session.godot_process
            
            # Enviar comando
            process.stdin.write(script_content + "\n__END__\n")
            process.stdin.flush()
            
            # Leer respuesta hasta __RESULT__
            output_lines = []
            while True:
                line = process.stdout.readline()
                if line.strip() == "__RESULT__":
                    break
                output_lines.append(line)
            
            return {
                "success": True,
                "output": "".join(output_lines),
                "pid": session.godot_process_pid
            }
            
        except Exception as e:
            return {"success": False, "error": f"Execution failed: {e}"}
    
    def get_godot_status(self, session_id: str) -> dict:
        """Obtiene estado del proceso Godot headless."""
        session = self._sessions.get(session_id)
        if not session:
            return {"running": False, "error": "Session not found"}
        
        process = session.godot_process
        if not process:
            return {"running": False, "ready": False}
        
        poll = process.poll()
        is_running = poll is None
        
        return {
            "running": is_running,
            "ready": session.godot_cli_ready and is_running,
            "pid": session.godot_process_pid,
            "exit_code": poll if not is_running else None,
            "project_path": session.project_path
        }
```

### 1.3 Modificación de close_session

```python
def close_session(self, session_id: str, save: bool = True) -> bool:
    """
    Close a session.
    
    NEW v4.0.0: Automatically stops Godot headless process.
    """
    with self._lock:
        if session_id not in self._sessions:
            return False
        
        session = self._sessions[session_id]
        
        # NEW: Stop Godot headless if running
        if session.godot_process:
            logger.info(f"Stopping Godot headless for session {session_id}")
            self.stop_godot_headless(session_id)
        
        # ... rest of existing close logic ...
```

---

## 2. Código a Limpiar

### 2.1 Duplicación en debug_tools.py

**Problema:** `_find_godot_executable()` está duplicado entre `debug_tools.py` y el nuevo `godot_cli/base.py`.

**Solución:** Mover a módulo compartido.

```python
# src/godot_mcp/godot_cli/base.py (NUEVO)
"""Base utilities for Godot CLI operations."""

import os
import shutil
import subprocess
import tempfile
import logging
from typing import Optional, List

logger = logging.getLogger(__name__)

# Rutas de búsqueda (movidas desde debug_tools.py)
GODOT_SEARCH_PATHS = [
    r"D:\Mis Juegos\Godot",
    r"C:\Program Files\Godot",
    r"C:\Program Files (x86)\Godot",
    "/usr/local/bin",
    "/usr/bin",
    "/Applications",
]

GODOT_EXECUTABLE_NAMES = [
    "Godot_v4.6.1-stable_win64_console.exe",
    "Godot_v4.6.1-stable_win64.exe",
    "Godot_v4.5.1-stable_win64_console.exe",
    "Godot_v4.5.1-stable_win64.exe",
    "Godot_v4.5-stable_win64_console.exe",
    "Godot_v4.5-stable_win64.exe",
    "godot",
    "Godot",
]

def find_godot_executable() -> Optional[str]:
    """Find Godot executable in common locations."""
    godot_in_path = shutil.which("godot") or shutil.which("Godot")
    if godot_in_path:
        return godot_in_path
    
    for search_path in GODOT_SEARCH_PATHS:
        if not os.path.exists(search_path):
            continue
        for exe_name in GODOT_EXECUTABLE_NAMES:
            candidate = os.path.join(search_path, exe_name)
            if os.path.isfile(candidate):
                return candidate
    
    return None


def parse_godot_log(log_content: str) -> dict:
    """Parse Godot log output into categorized messages."""
    # ... moved from _parse_log_output in debug_tools.py ...


class GodotCLIWrapper:
    """
    Wrapper for Godot CLI operations.
    
    Provides a unified interface for running Godot commands
    with proper error handling and logging.
    """
    
    def __init__(self, godot_path: Optional[str] = None):
        self.godot_path = godot_path or find_godot_executable()
        self._temp_files: List[str] = []
    
    def run_command(self, args: List[str], 
                   project_path: Optional[str] = None,
                   timeout: int = 30) -> dict:
        """Run a Godot CLI command with proper setup."""
        if not self.godot_path:
            return {"success": False, "error": "Godot not found"}
        
        cmd = [self.godot_path] + args
        
        if project_path:
            cmd.extend(["--path", project_path])
        
        # Create log file
        log_file = os.path.join(tempfile.gettempdir(), 
                               f"godot_cli_{os.getpid()}.log")
        self._temp_files.append(log_file)
        cmd.extend(["--log-file", log_file])
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding="utf-8",
                errors="replace"
            )
            
            # Read log
            log_content = ""
            if os.path.exists(log_file):
                with open(log_file, "r", encoding="utf-8", errors="replace") as f:
                    log_content = f.read()
            
            parsed = parse_godot_log(log_content + result.stdout + result.stderr)
            
            return {
                "success": result.returncode == 0,
                "exit_code": result.returncode,
                "errors": parsed["errors"],
                "warnings": parsed["warnings"],
                "prints": parsed["prints"],
                "info": parsed["info"],
                "stack_traces": parsed["stack_traces"],
            }
            
        except subprocess.TimeoutExpired:
            return {"success": False, "error": f"Timeout after {timeout}s"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def cleanup(self):
        """Remove temporary files."""
        for f in self._temp_files:
            try:
                if os.path.exists(f):
                    os.remove(f)
            except Exception:
                pass
        self._temp_files.clear()
```

### 2.2 Refactor de debug_tools.py

```python
# debug_tools.py - REFACTORADO
"""
Debug Tools - Wrapper sobre GodotCLIWrapper.

Ahora usa GodotCLIWrapper de godot_cli.base para evitar duplicación.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from ..godot_cli.base import GodotCLIWrapper, find_godot_executable

logger = logging.getLogger(__name__)


def run_debug_scene(
    project_path: str,
    scene_path: Optional[str] = None,
    godot_path: Optional[str] = None,
    timeout: int = 30,
    debug_collisions: bool = False,
    debug_paths: bool = False,
    debug_navigation: bool = False,
) -> dict[str, Any]:
    """
    Run a Godot scene in headless mode and capture debug output.
    
    REFACTOR v4.0.0: Usa GodotCLIWrapper internamente.
    """
    # Validación
    import os
    project_path = os.path.abspath(project_path)
    if not os.path.isdir(project_path):
        return {"success": False, "error": f"Project not found: {project_path}"}
    
    if not os.path.isfile(os.path.join(project_path, "project.godot")):
        return {"success": False, "error": "No project.godot found"}
    
    # Usar wrapper
    cli = GodotCLIWrapper(godot_path)
    if not cli.godot_path:
        return {"success": False, "error": "Godot not found"}
    
    # Build args
    args = ["--headless", "--quit-after", "1"]
    
    if scene_path:
        args.append(scene_path)
    if debug_collisions:
        args.append("--debug-collisions")
    if debug_paths:
        args.append("--debug-paths")
    if debug_navigation:
        args.append("--debug-navigation")
    
    result = cli.run_command(args, project_path=project_path, timeout=timeout)
    result["godot_path"] = cli.godot_path
    result["scene_path"] = scene_path
    result["project_path"] = project_path
    
    cli.cleanup()
    return result


def check_script_syntax(
    project_path: str,
    script_path: str,
    godot_path: Optional[str] = None,
    timeout: int = 30,
) -> dict[str, Any]:
    """
    Check GDScript syntax using Godot's --check-only.
    
    REFACTOR v4.0.0: Usa GodotCLIWrapper.
    """
    import os
    project_path = os.path.abspath(project_path)
    if not os.path.isdir(project_path):
        return {"success": False, "error": f"Project not found: {project_path}"}
    
    cli = GodotCLIWrapper(godot_path)
    if not cli.godot_path:
        return {"success": False, "error": "Godot not found"}
    
    args = ["--headless", "--check-only", "--script", script_path]
    result = cli.run_command(args, project_path=project_path, timeout=timeout)
    result["script_path"] = script_path
    result["godot_path"] = cli.godot_path
    
    cli.cleanup()
    return result
```

### 2.3 Registro Dinámico en server.py

```python
# server.py - REFACTORADO v4.0.0
"""
Godot MCP Server v4.0.0 - Plus Ultra

Entry point con registro dinámico de módulos.
"""

import logging
import sys
from typing import Optional, List, Callable

from fastmcp import FastMCP

logger = logging.getLogger(__name__)

# Lista de módulos a registrar (fácil de extender)
REGISTERED_MODULES = [
    ("scene_tools", "register_scene_tools"),
    ("node_tools", "register_node_tools"),
    ("resource_tools", "register_resource_tools"),
    ("session_tools", "register_session_tools"),
    ("project_tools", "register_project_tools"),
    ("validation_tools", "register_validation_tools"),
    ("signal_and_script_tools", "register_signal_and_script_tools"),
    ("property_tools", "register_property_tools"),
    ("debug_tools", "register_debug_tools"),
    # NUEVO v4.0.0
    ("godot_cli.export_tools", "register_export_tools"),
    ("godot_cli.runtime_tools", "register_runtime_tools"),
    ("godot_cli.import_tools", "register_import_tools"),
    ("godot_cli.screenshot_tools", "register_screenshot_tools"),
    ("godot_cli.movie_tools", "register_movie_tools"),
    ("lsp_dap.lsp_tools", "register_lsp_tools"),
    ("lsp_dap.dap_tools", "register_dap_tools"),
    ("intelligence.dependency_tools", "register_dependency_tools"),
    ("intelligence.signal_graph_tools", "register_signal_graph_tools"),
    ("intelligence.code_analysis_tools", "register_code_analysis_tools"),
]


def register_all_tools(mcp: FastMCP) -> None:
    """Registrar todas las herramientas disponibles."""
    logger.info("Registrando herramientas del servidor MCP v4.0.0...")
    
    registered = 0
    failed = []
    
    for module_path, register_func in REGISTERED_MODULES:
        try:
            # Import dinámico
            module = __import__(
                f"godot_mcp.tools.{module_path}",
                fromlist=[register_func]
            )
            register_fn = getattr(module, register_func)
            register_fn(mcp)
            
            logger.info(f"[OK] {module_path} registrado")
            registered += 1
            
        except ImportError as e:
            # Módulo no existe aún (en desarrollo) - no es error fatal
            logger.warning(f"[SKIP] {module_path} no disponible: {e}")
            failed.append((module_path, str(e)))
            
        except Exception as e:
            logger.error(f"[FAIL] {module_path}: {e}")
            failed.append((module_path, str(e)))
            raise
    
    logger.info(f"Registrados {registered}/{len(REGISTERED_MODULES)} módulos")
    if failed:
        logger.warning(f"Módulos saltados: {len(failed)}")


def main(transport: Optional[str] = None) -> None:
    """Punto de entrada principal."""
    mcp = FastMCP("godot-mcp-v4")
    
    try:
        logger.info("Iniciando Ultra Godot MCP v4.0.0 - Plus Ultra...")
        register_all_tools(mcp)
        logger.info("Servidor MCP listo")
        mcp.run(transport=transport)
    except KeyboardInterrupt:
        logger.info("Servidor detenido")
        sys.exit(0)
    except Exception as e:
        logger.exception(f"Error fatal: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
```

---

## 3. Archivos a Crear/Modificar/Eliminar

### 3.1 Nuevos Archivos

```
src/godot_mcp/
├── godot_cli/
│   ├── __init__.py              # Exports
│   ├── base.py                  # GodotCLIWrapper, find_godot_executable
│   ├── export_tools.py          # 4 tools
│   ├── runtime_tools.py         # 6 tools
│   ├── import_tools.py          # 2 tools
│   ├── screenshot_tools.py      # 2 tools
│   └── movie_tools.py           # 2 tools
├── lsp_dap/
│   ├── __init__.py
│   ├── client.py                # JSON-RPC client
│   ├── lsp_tools.py             # 3 tools
│   └── dap_tools.py             # 6 tools
└── intelligence/
    ├── __init__.py
    ├── dependency_tools.py      # 2 tools
    ├── signal_graph_tools.py    # 2 tools
    └── code_analysis_tools.py   # 3 tools
```

### 3.2 Archivos a Modificar

| Archivo | Cambios |
|---------|---------|
| `session_manager.py` | Añadir campos `godot_process`, `godot_cli_ready`, métodos `start_godot_headless()`, `stop_godot_headless()`, `execute_gdscript_quick()` |
| `debug_tools.py` | Refactor para usar `GodotCLIWrapper` desde `godot_cli.base` |
| `server.py` | Registro dinámico de módulos, lista `REGISTERED_MODULES` |
| `pyproject.toml` | Añadir `godot_cli`, `lsp_dap`, `intelligence` a packages |

### 3.3 Archivos a Eliminar

**Ninguno.** Todo el código v3.x es reutilizable.

---

## 4. Flujo de Trabajo con Sesiones + Godot Headless

```
1. start_session(project_path)
   └─→ session_id
   └─→ [OPCIONAL] start_godot_headless(session_id)
       └─→ Godot headless corriendo en background (PID: X)

2. create_scene(session_id, "Player.tscn") 
   └─→ Escena creada (filesystem - rápido)

3. add_node(session_id, "Player.tscn", ...)
   └─→ Nodo añadido (filesystem - rápido)

4. get_scene_info_runtime(session_id, "Player.tscn")
   └─→ Usa Godot headless existente
   └─→ MUCHO más rápido que iniciar Godot cada vez

5. test_scene_load(session_id, "Player.tscn")
   └─→ Usa Godot headless existente
   └─→ Resultado en <1s vs 5-10s iniciando de cero

6. end_session(session_id, save=True)
   └─→ Guarda cambios
   └─→ [AUTOMÁTICO] stop_godot_headless(session_id)
       └─→ Mata proceso Godot
```

### Ventajas de Godot Headless por Sesión

| Métrica | Sin Headless (v3.x) | Con Headless (v4.0.0) |
|---------|---------------------|----------------------|
| **Primera ejecución** | 5-10s | 5-10s (inicialización) |
| **Ejecuciones subsecuentes** | 5-10s | **<1s** |
| **Memoria** | 0 MB (proceso muere) | **~100-200 MB** (proceso vivo) |
| **Uso CPU idle** | 0% | **~0-1%** |

**Trade-off:** Memoria constante vs velocidad. Para desarrollo iterativo (editar→probar→editar), el headless es **10x más rápido**.

---

## 5. Checklist de Implementación

### Fase 1: Base (1 día)
- [ ] Crear `godot_cli/base.py` con `GodotCLIWrapper`
- [ ] Refactor `debug_tools.py` para usar `GodotCLIWrapper`
- [ ] Añadir campos Godot a `Session`
- [ ] Añadir métodos headless a `SessionManager`
- [ ] Modificar `close_session` para matar Godot

### Fase 2: CLI Bridge (3 días)
- [ ] `export_tools.py`
- [ ] `runtime_tools.py`
- [ ] `import_tools.py`
- [ ] `screenshot_tools.py`
- [ ] `movie_tools.py`

### Fase 3: LSP/DAP (2 días)
- [ ] `lsp_dap/client.py` (JSON-RPC)
- [ ] `lsp_tools.py`
- [ ] `dap_tools.py`

### Fase 4: Intelligence (2 días)
- [ ] `dependency_tools.py`
- [ ] `signal_graph_tools.py`
- [ ] `code_analysis_tools.py`

### Fase 5: Integración (1 día)
- [ ] Refactor `server.py` con registro dinámico
- [ ] Actualizar `pyproject.toml`
- [ ] Tests
- [ ] Documentación

**Total: 9 días**

---

*Análisis de limpieza v4.0.0*
*Fecha: 2026-04-21*
*Conclusión: Extensión limpia, sin breaking changes, máximo reuso de código existente*
