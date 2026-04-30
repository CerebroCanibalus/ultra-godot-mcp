"""
Godot MCP Server v4.0.0 - Ultra-fast MCP server for Godot Engine.

Entry point del servidor MCP usando FastMCP.
Registro dinámico de módulos v4.0.0.
"""

import importlib
import logging
import sys
from typing import Optional, List, Tuple

from fastmcp import FastMCP

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# Lista de módulos a registrar (fácil de extender)
# Formato: (module_path, register_function_name)
REGISTERED_MODULES: List[Tuple[str, str]] = [
    # Capa 1: Core (v3.x)
    ("tools.scene_tools", "register_scene_tools"),
    ("tools.node_tools", "register_node_tools"),
    ("tools.resource_tools", "register_resource_tools"),
    ("tools.session_tools", "register_session_tools"),
    ("tools.project_tools", "register_project_tools"),
    ("tools.validation_tools", "register_validation_tools"),
    ("tools.signal_and_script_tools", "register_signal_and_script_tools"),
    ("tools.property_tools", "register_property_tools"),
    ("tools.debug_tools", "register_debug_tools"),
    # Capa 2: Godot CLI Bridge (v4.0.0)
    ("godot_cli.export_tools", "register_export_tools"),
    ("godot_cli.runtime_tools", "register_runtime_tools"),
    ("godot_cli.import_tools", "register_import_tools"),
    ("godot_cli.screenshot_tools", "register_screenshot_tools"),
    ("godot_cli.movie_tools", "register_movie_tools"),
    # Capa 3: LSP/DAP Native (v4.0.0)
    ("lsp_dap.lsp_tools", "register_lsp_tools"),
    ("lsp_dap.dap_tools", "register_dap_tools"),
    # Capa 4: Project Intelligence (v4.0.0)
    ("intelligence.dependency_tools", "register_dependency_tools"),
    ("intelligence.signal_graph_tools", "register_signal_graph_tools"),
    ("intelligence.code_analysis_tools", "register_code_analysis_tools"),
    # Capa 5: Skeleton Tools (v4.1.0)
    ("tools.skeleton_tools", "register_skeleton_tools"),
    # Capa 6: Array Operations (v4.2.0)
    ("tools.array_tools", "register_array_tools"),
    # Capa 7: Resource Builder (v4.3.0)
    ("tools.resource_builder_tools", "register_resource_builder_tools"),
    # Capa 8: TileMap Inspector & Editor (v4.4.0)
    ("tools.tilemap_tools", "register_tilemap_tools"),
]


def register_all_tools(mcp: Optional[FastMCP] = None) -> Tuple[int, int]:
    """
    Registrar todas las herramientas disponibles en el servidor MCP.
    
    Usa import dinámico para soportar módulos opcionales.
    Los módulos que no existen se saltan sin error fatal.
    
    Args:
        mcp: Instancia de FastMCP. Si es None, usa la instancia global.
    
    Returns:
        (registered_count, skipped_count)
    """
    # Usar instancia global si no se provee
    if mcp is None:
        mcp = globals()["mcp"]
    """
    Registrar todas las herramientas disponibles en el servidor MCP.
    
    Usa import dinámico para soportar módulos opcionales.
    Los módulos que no existen se saltan sin error fatal.
    
    Args:
        mcp: Instancia de FastMCP
    
    Returns:
        (registered_count, skipped_count)
    """
    logger.info("Registrando herramientas del servidor MCP v4.0.0...")
    
    registered = 0
    skipped = 0
    
    for module_path, register_func in REGISTERED_MODULES:
        try:
            # Import dinámico
            full_module = f"godot_mcp.{module_path}"
            module = importlib.import_module(full_module)
            register_fn = getattr(module, register_func)
            register_fn(mcp)
            
            logger.info(f"[OK] {module_path} registrado")
            registered += 1
            
        except ImportError as e:
            # Módulo no existe - saltar silenciosamente
            logger.debug(f"[SKIP] {module_path} no disponible: {e}")
            skipped += 1
            
        except AttributeError as e:
            # Función de registro no existe
            logger.warning(f"[SKIP] {module_path}.{register_func} no encontrado: {e}")
            skipped += 1
            
        except Exception as e:
            logger.error(f"[FAIL] {module_path}: {e}")
            raise
    
    logger.info(f"Registrados {registered}/{len(REGISTERED_MODULES)} módulos "
                f"({skipped} saltados)")
    
    return registered, skipped


# Instancia global del servidor MCP (para backward compatibility y tests)
mcp = FastMCP("godot-mcp-v4")


def main(transport: Optional[str] = None) -> None:
    """
    Punto de entrada principal del servidor MCP.

    Args:
        transport: Tipo de transporte a usar (stdio, sse, etc.).
                  Si es None, usa el valor por defecto de FastMCP.
    """
    try:
        logger.info("Iniciando Ultra Godot MCP v4.0.0 - Plus Ultra...")
        logger.info("Zero addon. Zero WebSocket. Maximum performance.")

        # Registrar todas las herramientas en la instancia global
        registered, skipped = register_all_tools(mcp)
        
        logger.info(f"Servidor MCP listo con {registered} módulos activos")

        # Ejecutar el servidor
        mcp.run(transport=transport)

    except KeyboardInterrupt:
        logger.info("Servidor detenido por el usuario")
        sys.exit(0)
    except Exception as e:
        logger.exception(f"Error fatal al iniciar el servidor: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
