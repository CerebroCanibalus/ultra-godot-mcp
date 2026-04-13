"""
Cache LRU para archivos TSCN parseados del proyecto Godot.

Características:
- Cache LRU con límite configurable
- Invalidación automática por hash de contenido
- Thread-safe con threading.Lock
- Métricas de hits, misses, evictions
"""

from __future__ import annotations

import hashlib
import os
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any, Callable, Optional


@dataclass
class CacheEntry:
    """Entrada individual del cache."""

    value: Any  # Objeto Scene parseado
    content_hash: str  # Hash del contenido original
    timestamp: float = field(default_factory=time.time)  # Timestamp de creación
    file_mtime: float = 0.0  # Modification time del archivo


@dataclass
class CacheStats:
    """Estadísticas del cache."""

    hits: int = 0
    misses: int = 0
    evictions: int = 0
    invalidations: int = 0

    @property
    def hit_rate(self) -> float:
        """Calcula el ratio de hits."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0


class LRUCache:
    """
    Cache LRU thread-safe para parsed TSCN files.

    Args:
        max_size: Máximo número de entradas (default: 100)
        hash_function: Función para calcular hash del contenido (default: md5)
    """

    def __init__(
        self,
        max_size: int = 100,
        hash_function: Optional[Callable[[bytes], str]] = None,
    ):
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._max_size = max_size
        self._lock = threading.RLock()
        self._stats = CacheStats()

        # Función de hash configurable
        self._hash_function = hash_function or (
            lambda data: hashlib.md5(data, usedforsecurity=False).hexdigest()
        )

    # ==================== API Principal ====================

    def get(self, key: str) -> Optional[Any]:
        """
        Obtiene un valor del cache.

        Args:
            key: Ruta del archivo TSCN

        Returns:
            El valor cacheado o None si no existe/está inválido
        """
        with self._lock:
            # Verificar si existe la entrada
            if key not in self._cache:
                self._stats.misses += 1
                return None

            entry = self._cache[key]

            # Verificar si el archivo ha cambiado
            if self._is_entry_invalid(entry, key):
                self._remove_entry(key)
                self._stats.misses += 1
                return None

            # Mover al final (LRU)
            self._cache.move_to_end(key)
            self._stats.hits += 1

            return entry.value

    def set(self, key: str, value: Any, content_hash: Optional[str] = None) -> None:
        """
        Guarda un valor en el cache.

        Args:
            key: Ruta del archivo TSCN
            value: Objeto Scene parseado
            content_hash: Hash del contenido (opcional, se calcula si no se provee)
        """
        # Calcular hash si no se provee
        if content_hash is None:
            content_hash = self._calculate_hash_from_file(key)
            if content_hash is None:
                # Si no podemos leer el archivo, usamos un hash genérico
                content_hash = self._hash_function(b"")

        with self._lock:
            # Si ya existe, remover para re-ordenar
            if key in self._cache:
                del self._cache[key]

            # Obtener mtime del archivo
            file_mtime = 0.0
            try:
                file_mtime = os.path.getmtime(key)
            except OSError:
                pass

            # Crear nueva entrada
            entry = CacheEntry(
                value=value,
                content_hash=content_hash,
                timestamp=time.time(),
                file_mtime=file_mtime,
            )

            # Añadir al final (más recientemente usado)
            self._cache[key] = entry

            # Evict oldest if over limit
            while len(self._cache) > self._max_size:
                oldest_key = next(iter(self._cache))
                self._remove_entry(oldest_key)
                self._stats.evictions += 1

    def invalidate(self, key: str) -> bool:
        """
        Invalida una entrada específica.

        Args:
            key: Ruta del archivo a invalidar

        Returns:
            True si la entrada existía y fue removida
        """
        with self._lock:
            if key in self._cache:
                self._remove_entry(key)
                self._stats.invalidations += 1
                return True
            return False

    def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalida todas las entradas que coincidan con un patrón.

        Args:
            pattern: Patrón glob (ej: "res://scenes/*.tscn")

        Returns:
            Número de entradas invalidadas
        """
        import fnmatch

        with self._lock:
            keys_to_remove = [
                key for key in self._cache.keys() if fnmatch.fnmatch(key, pattern)
            ]

            for key in keys_to_remove:
                self._remove_entry(key)
                self._stats.invalidations += 1

            return len(keys_to_remove)

    def clear(self) -> None:
        """Limpia todas las entradas del cache."""
        with self._lock:
            self._cache.clear()

    def get_stats(self) -> dict:
        """
        Obtiene las estadísticas del cache.

        Returns:
            Dict con hits, misses, evictions, invalidations, hit_rate, size, max_size
        """
        with self._lock:
            return {
                "hits": self._stats.hits,
                "misses": self._stats.misses,
                "evictions": self._stats.evictions,
                "invalidations": self._stats.invalidations,
                "hit_rate": round(self._stats.hit_rate, 4),
                "size": len(self._cache),
                "max_size": self._max_size,
            }

    # ==================== Métodos Auxiliares ====================

    def _is_entry_invalid(self, entry: CacheEntry, key: str) -> bool:
        """Verifica si una entrada debe invalidarse por cambio en archivo."""
        # Si la entrada no tiene mtime registrada, no podemos verificar cambios
        if entry.file_mtime == 0.0:
            return False

        try:
            if not os.path.exists(key):
                # Archivo fue eliminado - invalidar
                return True

            # Verificar por mtime
            current_mtime = os.path.getmtime(key)
            if entry.file_mtime != current_mtime:
                return True

            # Verificar por hash de contenido
            current_hash = self._calculate_hash_from_file(key)
            if current_hash and current_hash != entry.content_hash:
                return True

        except OSError:
            # Si no podemos leer el archivo, marcar como inválido
            return True

        return False

    def _calculate_hash_from_file(self, key: str) -> Optional[str]:
        """Calcula el hash del contenido de un archivo."""
        try:
            with open(key, "rb") as f:
                data = f.read()
                return self._hash_function(data)
        except OSError:
            return None

    def _remove_entry(self, key: str) -> None:
        """Remueve una entrada del cache."""
        if key in self._cache:
            del self._cache[key]

    def __contains__(self, key: str) -> bool:
        """Verifica si una clave existe en el cache."""
        with self._lock:
            return key in self._cache

    def __len__(self) -> int:
        """Retorna el número de entradas en el cache."""
        with self._lock:
            return len(self._cache)


# ==================== Instancia Global ====================

# Cache global compartido
_global_cache: Optional[LRUCache] = None
_cache_lock = threading.Lock()


def get_cache(max_size: int = 100) -> LRUCache:
    """
    Obtiene la instancia global del cache (singleton thread-safe).

    Args:
        max_size: Tamaño máximo del cache (solo se usa en la primera llamada)

    Returns:
        Instancia global del cache
    """
    global _global_cache

    with _cache_lock:
        if _global_cache is None:
            _global_cache = LRUCache(max_size=max_size)
        return _global_cache


def reset_cache(max_size: int = 100) -> LRUCache:
    """
    Resetea la instancia global del cache.

    Args:
        max_size: Nuevo tamaño máximo

    Returns:
        Nueva instancia del cache
    """
    global _global_cache

    with _cache_lock:
        _global_cache = LRUCache(max_size=max_size)
        return _global_cache
