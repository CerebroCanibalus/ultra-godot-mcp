#!/usr/bin/env python3
"""
Godot LSP Bridge for OpenCode - MCP Integrated Edition

Bridges stdio (OpenCode) to TCP (Godot LSP server).

NOTA: El lanzamiento de Godot es responsabilidad del SessionManager del MCP.
Este bridge asume que Godot ya está corriendo con LSP habilitado.

Usage:
    python godot_lsp_bridge.py [--port PORT] [--host HOST]

Environment Variables:
    GODOT_LSP_PORT - Puerto del LSP (default: 6005)
    GODOT_LSP_HOST - Host del LSP (default: 127.0.0.1)

Configuración en opencode.jsonc:
    "lsp": {
        "gdscript": {
            "command": [
                "python",
                "D:/Mis Juegos/GodotMCP/godot-mcp-python/scripts/godot_lsp_bridge.py"
            ],
            "extensions": [".gd", ".gdshader"]
        }
    }
"""

from __future__ import annotations

import argparse
import logging
import os
import re
import socket
import sys
import threading

# Logging a stderr (stdout es canal LSP)
logging.basicConfig(
    level=logging.INFO,
    format="[%(name)s] %(levelname)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("godot-lsp-bridge")


class LSPInterceptor:
    """
    Intercepta mensajes LSP y reescribe languageId.
    
    OpenCode envía "languageId":"plaintext" para archivos .gd
    Godot espera "languageId":"gdscript"
    """
    
    def __init__(self):
        self.buffer = b""
    
    def process(self, data: bytes) -> bytes:
        """Procesa datos recibidos, reescribiendo languageId si es necesario."""
        self.buffer += data
        output = bytearray()
        
        while True:
            buffer_str = self.buffer.decode("utf-8", errors="replace")
            
            # Buscar Content-Length
            match = re.search(r"Content-Length: (\d+)\r\n", buffer_str)
            if not match:
                break
            
            header_end = buffer_str.find("\r\n\r\n")
            if header_end == -1:
                break
            
            content_length = int(match.group(1))
            body_start = header_end + 4
            total_length = body_start + content_length
            
            if len(self.buffer) < total_length:
                break
            
            # Extraer body
            body = self.buffer[body_start:total_length]
            body_str = body.decode("utf-8", errors="replace")
            
            # Reescribir languageId
            if '"languageId":"plaintext"' in body_str:
                body_str = body_str.replace('"languageId":"plaintext"', '"languageId":"gdscript"')
                new_body = body_str.encode("utf-8")
                
                # Reconstruir headers con nuevo Content-Length
                old_header = buffer_str[:header_end]
                new_header = re.sub(
                    r"Content-Length: \d+",
                    f"Content-Length: {len(new_body)}",
                    old_header,
                )
                
                output.extend(new_header.encode("utf-8"))
                output.extend(b"\r\n\r\n")
                output.extend(new_body)
            else:
                output.extend(self.buffer[:total_length])
            
            # Avanzar buffer
            self.buffer = self.buffer[total_length:]
        
        return bytes(output)


class GodotLSPBridge:
    """Bridge stdio ↔ TCP entre OpenCode y Godot LSP."""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 6005):
        self.host = host
        self.port = port
        self.socket: socket.socket | None = None
        self.interceptor = LSPInterceptor()
        self.running = False
    
    def connect(self) -> bool:
        """Conecta al servidor LSP de Godot."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            logger.info(f"✓ Conectado a Godot LSP en {self.host}:{self.port}")
            return True
        except ConnectionRefusedError:
            logger.error(f"No se pudo conectar a {self.host}:{self.port}")
            logger.error("Asegúrate de que Godot Editor esté abierto con LSP habilitado")
            logger.error("O usa el SessionManager del MCP para lanzar Godot")
            return False
        except Exception as e:
            logger.error(f"Error conectando: {e}")
            return False
    
    def run(self) -> None:
        """Ejecuta el bridge: retransmite mensajes entre stdio y TCP."""
        if not self.socket:
            logger.error("Socket no inicializado")
            return
        
        self.running = True
        
        # Thread para leer de TCP y escribir a stdout
        def tcp_to_stdout():
            sock = self.socket
            if sock is None:
                self.running = False
                return
            try:
                while self.running:
                    data = sock.recv(8192)
                    if not data:
                        break
                    sys.stdout.buffer.write(data)
                    sys.stdout.buffer.flush()
            except Exception:
                pass
            finally:
                self.running = False
        
        tcp_thread = threading.Thread(target=tcp_to_stdout, daemon=True)
        tcp_thread.start()
        
        # Leer de stdin y enviar a TCP (con interceptor)
        try:
            while self.running:
                data = sys.stdin.buffer.read(4096)
                if not data:
                    break
                
                processed = self.interceptor.process(data)
                if processed:
                    self.socket.sendall(processed)
        
        except KeyboardInterrupt:
            logger.info("Interrumpido por usuario")
        except Exception as e:
            logger.error(f"Error en bridge: {e}")
        finally:
            self.shutdown()
    
    def shutdown(self) -> None:
        """Cierra el bridge limpiamente."""
        self.running = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        logger.info("Bridge cerrado")


def main():
    parser = argparse.ArgumentParser(
        description="Bridge LSP para OpenCode ↔ Godot Editor",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("GODOT_LSP_PORT", 6005)),
        help="Puerto del servidor LSP (default: 6005)",
    )
    parser.add_argument(
        "--host",
        default=os.environ.get("GODOT_LSP_HOST", "127.0.0.1"),
        help="Host del servidor LSP (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Modo verbose",
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    bridge = GodotLSPBridge(host=args.host, port=args.port)
    
    if not bridge.connect():
        sys.exit(1)
    
    try:
        bridge.run()
    except Exception as e:
        logger.error(f"Error fatal: {e}")
        sys.exit(1)
    finally:
        bridge.shutdown()


if __name__ == "__main__":
    main()
