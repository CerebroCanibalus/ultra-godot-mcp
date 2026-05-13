"""
Pool de conexiones reutilizables LSP/DAP para Godot.

Evita crear/destruir conexiones TCP en cada llamada a tool,
reduciendo latencia ~500ms por operación.

Usage:
    from godot_mcp.lsp_dap.connection_pool import get_lsp_client, get_dap_client
    
    client = get_lsp_client("localhost", 6005)
    completions = client.get_completions(...)
    # Cliente sigue vivo para la próxima llamada
    
    # Al shutdown del servidor:
    shutdown_all_connections()
"""

from __future__ import annotations

import logging
import threading
from typing import Optional

from .client import GodotLSPClient, GodotDAPClient

logger = logging.getLogger(__name__)

# Clientes singleton por (host, port)
_lsp_clients: dict[tuple[str, int], GodotLSPClient] = {}
_dap_clients: dict[tuple[str, int], GodotDAPClient] = {}
_pool_lock = threading.Lock()


def get_lsp_client(host: str = "localhost", port: int = 6005) -> GodotLSPClient:
    """Obtener cliente LSP reusable. Crea/connect solo si es necesario.
    
    Args:
        host: LSP server host
        port: LSP server port
        
    Returns:
        GodotLSPClient conectado y inicializado
    """
    key = (host, port)
    
    with _pool_lock:
        client = _lsp_clients.get(key)
        
        if client is not None and client.is_connected():
            logger.debug(f"Reusing LSP connection {host}:{port}")
            return client
        
        # Crear nueva conexión
        logger.info(f"Creating new LSP connection {host}:{port}")
        client = GodotLSPClient(host, port)
        
        if not client.connect():
            raise ConnectionError(f"Failed to connect to LSP at {host}:{port}")
        
        _lsp_clients[key] = client
        return client


def get_dap_client(host: str = "localhost", port: int = 6006) -> GodotDAPClient:
    """Obtener cliente DAP reusable. Crea/connect solo si es necesario.
    
    Args:
        host: DAP server host
        port: DAP server port
        
    Returns:
        GodotDAPClient conectado
    """
    key = (host, port)
    
    with _pool_lock:
        client = _dap_clients.get(key)
        
        if client is not None and client.is_connected():
            logger.debug(f"Reusing DAP connection {host}:{port}")
            return client
        
        # Crear nueva conexión
        logger.info(f"Creating new DAP connection {host}:{port}")
        client = GodotDAPClient(host, port)
        
        if not client.connect():
            raise ConnectionError(f"Failed to connect to DAP at {host}:{port}")
        
        _dap_clients[key] = client
        return client


def shutdown_all_connections() -> None:
    """Cerrar todas las conexiones del pool. Llamar al shutdown del servidor."""
    with _pool_lock:
        # Cerrar LSP
        for key, client in list(_lsp_clients.items()):
            try:
                client.disconnect()
                logger.info(f"Shutdown LSP connection {key}")
            except Exception as e:
                logger.warning(f"Error closing LSP connection {key}: {e}")
        _lsp_clients.clear()
        
        # Cerrar DAP
        for key, client in list(_dap_clients.items()):
            try:
                client.disconnect()
                logger.info(f"Shutdown DAP connection {key}")
            except Exception as e:
                logger.warning(f"Error closing DAP connection {key}: {e}")
        _dap_clients.clear()


def reset_pool() -> None:
    """Resetear pool (útil para testing)."""
    shutdown_all_connections()
