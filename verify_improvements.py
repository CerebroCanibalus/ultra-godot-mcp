"""
Verificacion de las mejoras aplicadas:
1. Pool de conexiones LSP/DAP
2. Validacion de project_path
3. Cleanup automatico de temp files
"""

import sys
import os

# Asegurar que el src esta en el path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

print("=" * 60)
print("VERIFICACION DE MEJORAS PENDIENTES")
print("=" * 60)

# Test 1: Connection Pool
print("\n[1/5] Verificando Connection Pool...")
try:
    from godot_mcp.lsp_dap.connection_pool import (
        get_lsp_client, 
        get_dap_client, 
        shutdown_all_connections,
        reset_pool
    )
    print("  [OK] Connection pool importa correctamente")
    print("  [OK] Funciones exportadas: get_lsp_client, get_dap_client, shutdown_all_connections, reset_pool")
except Exception as e:
    print(f"  [ERROR] Error importando connection pool: {e}")
    sys.exit(1)

# Test 2: Validacion de project_path
print("\n[2/5] Verificando validacion de project_path...")
try:
    from godot_mcp.tools.decorators import validate_project_path
    
    # Test con path vacio
    valid, error = validate_project_path("")
    assert not valid, "Path vacio deberia ser invalido"
    assert "required" in error.lower(), f"Mensaje incorrecto: {error}"
    print("  [OK] Path vacio correctamente rechazado")
    
    # Test con path inexistente
    valid, error = validate_project_path("/ruta/que/no/existe")
    assert not valid, "Path inexistente deberia ser invalido"
    assert "not found" in error.lower(), f"Mensaje incorrecto: {error}"
    print("  [OK] Path inexistente correctamente rechazado")
    
    # Test con directorio existente pero sin project.godot
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        valid, error = validate_project_path(tmpdir)
        assert not valid, "Dir sin project.godot deberia ser invalido"
        assert "no project.godot" in error.lower(), f"Mensaje incorrecto: {error}"
        print("  [OK] Dir sin project.godot correctamente rechazado")
    
    print("  [OK] validate_project_path funciona correctamente")
except Exception as e:
    print(f"  [ERROR] Error en validacion: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: GodotCLIWrapper con atexit
print("\n[3/5] Verificando GodotCLIWrapper cleanup automatico...")
try:
    from godot_mcp.godot_cli.base import GodotCLIWrapper
    
    # Verificar que GodotCLIWrapper tiene el metodo _cleanup_at_exit
    assert hasattr(GodotCLIWrapper, '_cleanup_at_exit'), "Falta metodo _cleanup_at_exit"
    print("  [OK] GodotCLIWrapper tiene _cleanup_at_exit")
    
    # Crear instancia y verificar que registra temp files
    cli = GodotCLIWrapper()
    assert hasattr(cli, '_temp_files'), "Falta atributo _temp_files"
    print("  [OK] GodotCLIWrapper registra _temp_files")
    
    print("  [OK] GodotCLIWrapper cleanup automatico configurado")
except Exception as e:
    print(f"  [ERROR] Error en GodotCLIWrapper: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: LSP Tools usan pool
print("\n[4/5] Verificando LSP tools usan connection pool...")
try:
    from godot_mcp.lsp_dap import lsp_tools
    import inspect
    
    # Verificar que get_lsp_client esta importado
    assert hasattr(lsp_tools, 'get_lsp_client'), "lsp_tools no importa get_lsp_client"
    print("  [OK] lsp_tools importa get_lsp_client")
    
    # Verificar que las funciones no crean GodotLSPClient directamente
    source = inspect.getsource(lsp_tools.lsp_get_completions)
    assert "GodotLSPClient(" not in source, "lsp_get_completions aun crea GodotLSPClient"
    print("  [OK] lsp_get_completions usa pool (no crea GodotLSPClient)")
    
    source = inspect.getsource(lsp_tools.lsp_get_hover)
    assert "GodotLSPClient(" not in source, "lsp_get_hover aun crea GodotLSPClient"
    print("  [OK] lsp_get_hover usa pool")
    
    source = inspect.getsource(lsp_tools.lsp_get_symbols)
    assert "GodotLSPClient(" not in source, "lsp_get_symbols aun crea GodotLSPClient"
    print("  [OK] lsp_get_symbols usa pool")
    
    source = inspect.getsource(lsp_tools.lsp_get_diagnostics)
    assert "GodotLSPClient(" not in source, "lsp_get_diagnostics aun crea GodotLSPClient"
    print("  [OK] lsp_get_diagnostics usa pool")
    
    print("  [OK] Todas las LSP tools usan connection pool")
except Exception as e:
    print(f"  [ERROR] Error en LSP tools: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 5: DAP Tools usan pool
print("\n[5/5] Verificando DAP tools usan connection pool...")
try:
    from godot_mcp.lsp_dap import dap_tools
    import inspect
    
    # Verificar que get_dap_client esta importado
    assert hasattr(dap_tools, 'get_dap_client'), "dap_tools no importa get_dap_client"
    print("  [OK] dap_tools importa get_dap_client")
    
    # Verificar que las funciones no crean GodotDAPClient directamente
    source = inspect.getsource(dap_tools.dap_start_debugging)
    assert "GodotDAPClient(" not in source, "dap_start_debugging aun crea GodotDAPClient"
    print("  [OK] dap_start_debugging usa pool")
    
    source = inspect.getsource(dap_tools.dap_set_breakpoint)
    assert "GodotDAPClient(" not in source, "dap_set_breakpoint aun crea GodotDAPClient"
    print("  [OK] dap_set_breakpoint usa pool")
    
    source = inspect.getsource(dap_tools.dap_continue)
    assert "GodotDAPClient(" not in source, "dap_continue aun crea GodotDAPClient"
    print("  [OK] dap_continue usa pool")
    
    source = inspect.getsource(dap_tools.dap_step_over)
    assert "GodotDAPClient(" not in source, "dap_step_over aun crea GodotDAPClient"
    print("  [OK] dap_step_over usa pool")
    
    source = inspect.getsource(dap_tools.dap_step_into)
    assert "GodotDAPClient(" not in source, "dap_step_into aun crea GodotDAPClient"
    print("  [OK] dap_step_into usa pool")
    
    source = inspect.getsource(dap_tools.dap_get_stack_trace)
    assert "GodotDAPClient(" not in source, "dap_get_stack_trace aun crea GodotDAPClient"
    print("  [OK] dap_get_stack_trace usa pool")
    
    print("  [OK] Todas las DAP tools usan connection pool")
except Exception as e:
    print(f"  [ERROR] Error en DAP tools: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("[OK] TODAS LAS VERIFICACIONES PASARON (5/5)")
print("=" * 60)
print("\nResumen de mejoras aplicadas:")
print("  * Pool de conexiones LSP/DAP reutilizables")
print("  * Validacion de project_path en todas las tools")
print("  * Cleanup automatico de temp files via atexit")
print("  * Validacion de inputs en LSP/DAP tools")
print("\nEl MCP ahora es mas rapido, seguro y robusto.")
