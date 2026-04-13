#!/usr/bin/env python3
"""Test script for LRUCache implementation."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from godot_mcp.core.cache import LRUCache, get_cache, CacheStats


def test_basic_set_get():
    """Test basic set and get operations."""
    print("=== Test 1: Basic set/get ===")
    cache = LRUCache(max_size=3)

    cache.set("/path/to/scene1.tscn", {"nodes": ["Node2D"]}, content_hash="abc123")
    cache.set(
        "/path/to/scene2.tscn", {"nodes": ["CharacterBody2D"]}, content_hash="def456"
    )

    result = cache.get("/path/to/scene1.tscn")
    expected = {"nodes": ["Node2D"]}
    assert result == expected, f"Expected {expected}, got {result}"

    stats = cache.get_stats()
    assert stats["hits"] == 1, f"Expected 1 hit, got {stats['hits']}"
    assert stats["misses"] == 0, f"Expected 0 misses, got {stats['misses']}"
    print(f"[OK] Basic set/get works. Stats: {stats}")


def test_lru_eviction():
    """Test LRU eviction when cache is full."""
    print("\n=== Test 2: LRU Eviction ===")
    cache = LRUCache(max_size=3)

    # Add 3 entries
    cache.set("/scene1.tscn", {"data": 1}, content_hash="a")
    cache.set("/scene2.tscn", {"data": 2}, content_hash="b")
    cache.set("/scene3.tscn", {"data": 3}, content_hash="c")

    # Access scene1 to make it recently used
    cache.get("/scene1.tscn")

    # Add one more - should evict scene2 (least recently used)
    cache.set("/scene4.tscn", {"data": 4}, content_hash="d")

    # scene1 should still be there (was accessed recently)
    assert cache.get("/scene1.tscn") is not None, "scene1 should still be in cache"
    # scene2 should be evicted (LRU)
    assert cache.get("/scene2.tscn") is None, "scene2 should be evicted"

    stats = cache.get_stats()
    assert stats["evictions"] == 1, f"Expected 1 eviction, got {stats['evictions']}"
    print(f"[OK] LRU eviction works. Stats: {stats}")


def test_invalidate():
    """Test manual invalidation."""
    print("\n=== Test 3: Invalidate ===")
    cache = LRUCache(max_size=10)

    cache.set("/scene.tscn", {"data": 1}, content_hash="abc")

    # Invalidate existing key
    result = cache.invalidate("/scene.tscn")
    assert result == True, "Should return True for existing key"
    assert cache.get("/scene.tscn") is None, "Key should be None after invalidate"

    # Invalidate non-existing key
    result = cache.invalidate("/nonexistent.tscn")
    assert result == False, "Should return False for non-existing key"

    stats = cache.get_stats()
    print(f"[OK] Invalidate works. Stats: {stats}")


def test_invalidate_pattern():
    """Test pattern-based invalidation."""
    print("\n=== Test 4: Invalidate Pattern ===")
    cache = LRUCache(max_size=10)

    cache.set("/scenes/player.tscn", {"data": 1}, content_hash="a")
    cache.set("/scenes/enemy.tscn", {"data": 2}, content_hash="b")
    cache.set("/scripts/player.gd", {"data": 3}, content_hash="c")

    # Invalidate all .tscn in /scenes/
    count = cache.invalidate_pattern("/scenes/*.tscn")
    assert count == 2, f"Expected 2 invalidations, got {count}"

    # Verify only .gd remains
    assert cache.get("/scripts/player.gd") is not None
    assert cache.get("/scenes/player.tscn") is None
    assert cache.get("/scenes/enemy.tscn") is None

    stats = cache.get_stats()
    print(f"[OK] Invalidate pattern works. Stats: {stats}")


def test_clear():
    """Test clearing the cache."""
    print("\n=== Test 5: Clear ===")
    cache = LRUCache(max_size=10)

    cache.set("/scene1.tscn", {"data": 1}, content_hash="a")
    cache.set("/scene2.tscn", {"data": 2}, content_hash="b")

    cache.clear()

    assert len(cache) == 0, "Cache should be empty"
    assert cache.get("/scene1.tscn") is None

    stats = cache.get_stats()
    print(f"[OK] Clear works. Stats: {stats}")


def test_stats():
    """Test statistics tracking."""
    print("\n=== Test 6: Stats ===")
    cache = LRUCache(max_size=10)

    # Add some entries
    cache.set("/scene1.tscn", {"data": 1}, content_hash="a")

    # Get existing
    cache.get("/scene1.tscn")
    cache.get("/scene1.tscn")

    # Get non-existing
    cache.get("/nonexistent.tscn")

    stats = cache.get_stats()

    assert stats["hits"] == 2, f"Expected 2 hits, got {stats['hits']}"
    assert stats["misses"] == 1, f"Expected 1 miss, got {stats['misses']}"
    assert stats["hit_rate"] == 0.6666 or abs(stats["hit_rate"] - 0.6667) < 0.001, (
        f"Unexpected hit_rate: {stats['hit_rate']}"
    )

    print(f"[OK] Stats work correctly: {stats}")


def test_singleton():
    """Test singleton global cache."""
    print("\n=== Test 7: Singleton ===")

    cache1 = get_cache(max_size=50)
    cache2 = get_cache(max_size=100)  # Should return same instance

    assert cache1 is cache2, "get_cache should return singleton"
    assert cache1._max_size == 50, "Max size should be from first call"

    print(f"[OK] Singleton works correctly")


def test_contains():
    """Test __contains__ method."""
    print("\n=== Test 8: Contains ===")
    cache = LRUCache(max_size=10)

    cache.set("/scene.tscn", {"data": 1}, content_hash="abc")

    assert "/scene.tscn" in cache
    assert "/nonexistent.tscn" not in cache

    print(f"[OK] Contains works correctly")


if __name__ == "__main__":
    test_basic_set_get()
    test_lru_eviction()
    test_invalidate()
    test_invalidate_pattern()
    test_clear()
    test_stats()
    test_singleton()
    test_contains()

    print("\n=== All tests passed! ===")
