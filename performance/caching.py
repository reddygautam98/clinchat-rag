#!/usr/bin/env python3
"""
Database Optimization and Caching System
Advanced database performance optimization with intelligent caching strategies
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime, timedelta
import hashlib
import json
import redis
import asyncpg
from dataclasses import dataclass
from functools import wraps
import threading
from collections import OrderedDict

logger = logging.getLogger(__name__)

@dataclass
class CacheConfig:
    """Cache configuration settings"""
    redis_url: str = "redis://localhost:6379"
    default_ttl: int = 3600  # 1 hour
    max_memory_cache_size: int = 1000
    enable_query_cache: bool = True
    enable_result_cache: bool = True
    cache_prefix: str = "clinchat_rag"

@dataclass
class QueryOptimization:
    """Query optimization recommendations"""
    query_hash: str
    original_query: str
    optimized_query: Optional[str]
    execution_time_before: float
    execution_time_after: Optional[float]
    improvement_percent: Optional[float]
    recommendations: List[str]
    indexes_suggested: List[str]
    timestamp: datetime

class MemoryCache:
    """In-memory LRU cache implementation"""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.cache: OrderedDict = OrderedDict()
        self.lock = threading.RLock()
        self.hits = 0
        self.misses = 0
    
    def get(self, key: str) -> Any:
        """Get value from cache"""
        with self.lock:
            if key in self.cache:
                # Move to end (most recently used)
                value = self.cache.pop(key)
                self.cache[key] = value
                self.hits += 1
                return value
            else:
                self.misses += 1
                return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache"""
        with self.lock:
            # Remove oldest item if at capacity
            if len(self.cache) >= self.max_size and key not in self.cache:
                self.cache.popitem(last=False)
            
            # Add TTL information if provided
            if ttl:
                value = {
                    "data": value,
                    "expires_at": datetime.now() + timedelta(seconds=ttl)
                }
            
            self.cache[key] = value
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                return True
            return False
    
    def clear(self) -> None:
        """Clear all cache entries"""
        with self.lock:
            self.cache.clear()
            self.hits = 0
            self.misses = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self.lock:
            total_requests = self.hits + self.misses
            hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
            
            return {
                "size": len(self.cache),
                "max_size": self.max_size,
                "hits": self.hits,
                "misses": self.misses,
                "hit_rate": hit_rate,
                "memory_usage_percent": (len(self.cache) / self.max_size) * 100
            }

class RedisCache:
    """Redis-based distributed cache"""
    
    def __init__(self, config: CacheConfig):
        self.config = config
        self.redis_client: Optional[redis.Redis] = None
        self._connect()
    
    def _connect(self):
        """Connect to Redis"""
        try:
            self.redis_client = redis.from_url(
                self.config.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            # Test connection
            self.redis_client.ping()
            logger.info("Connected to Redis successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis_client = None
    
    def _get_key(self, key: str) -> str:
        """Get prefixed cache key"""
        return f"{self.config.cache_prefix}:{key}"
    
    async def get(self, key: str) -> Any:
        """Get value from Redis cache"""
        if not self.redis_client:
            return None
        
        try:
            prefixed_key = self._get_key(key)
            value = self.redis_client.get(prefixed_key)
            
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in Redis cache"""
        if not self.redis_client:
            return False
        
        try:
            prefixed_key = self._get_key(key)
            serialized_value = json.dumps(value, default=str)
            
            if ttl:
                self.redis_client.setex(prefixed_key, ttl, serialized_value)
            else:
                self.redis_client.setex(prefixed_key, self.config.default_ttl, serialized_value)
            
            return True
        except Exception as e:
            logger.error(f"Redis set error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from Redis cache"""
        if not self.redis_client:
            return False
        
        try:
            prefixed_key = self._get_key(key)
            result = self.redis_client.delete(prefixed_key)
            return result > 0
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern"""
        if not self.redis_client:
            return 0
        
        try:
            prefixed_pattern = self._get_key(pattern)
            keys = self.redis_client.keys(prefixed_pattern)
            
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Redis clear pattern error: {e}")
            return 0
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get Redis cache statistics"""
        if not self.redis_client:
            return {"status": "disconnected"}
        
        try:
            info = self.redis_client.info()
            
            return {
                "status": "connected",
                "memory_used": info.get("used_memory_human", "0"),
                "memory_peak": info.get("used_memory_peak_human", "0"),
                "connected_clients": info.get("connected_clients", 0),
                "total_commands": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": self._calculate_hit_rate(info),
                "uptime_seconds": info.get("uptime_in_seconds", 0)
            }
        except Exception as e:
            logger.error(f"Redis stats error: {e}")
            return {"status": "error", "error": str(e)}
    
    def _calculate_hit_rate(self, info: Dict[str, Any]) -> float:
        """Calculate cache hit rate"""
        hits = info.get("keyspace_hits", 0)
        misses = info.get("keyspace_misses", 0)
        total = hits + misses
        
        return (hits / total * 100) if total > 0 else 0.0

class CacheManager:
    """Multi-level cache management system"""
    
    def __init__(self, config: CacheConfig):
        self.config = config
        self.memory_cache = MemoryCache(config.max_memory_cache_size)
        self.redis_cache = RedisCache(config)
    
    async def get(self, key: str) -> Any:
        """Get value from multi-level cache (memory first, then Redis)"""
        # Try memory cache first
        value = self.memory_cache.get(key)
        if value is not None:
            # Check TTL if applicable
            if isinstance(value, dict) and "expires_at" in value:
                if datetime.now() > value["expires_at"]:
                    self.memory_cache.delete(key)
                    value = None
                else:
                    return value["data"]
            else:
                return value
        
        # Try Redis cache
        value = await self.redis_cache.get(key)
        if value is not None:
            # Store in memory cache for faster access
            self.memory_cache.set(key, value)
            return value
        
        return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None, 
                 memory_only: bool = False) -> bool:
        """Set value in cache"""
        # Store in memory cache
        self.memory_cache.set(key, value, ttl)
        
        # Store in Redis cache unless memory_only is True
        if not memory_only:
            return await self.redis_cache.set(key, value, ttl)
        
        return True
    
    async def delete(self, key: str) -> bool:
        """Delete from all cache levels"""
        memory_result = self.memory_cache.delete(key)
        redis_result = await self.redis_cache.delete(key)
        
        return memory_result or redis_result
    
    async def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern"""
        # Clear memory cache (simple approach - clear all)
        self.memory_cache.clear()
        
        # Clear Redis cache with pattern
        return await self.redis_cache.clear_pattern(pattern)
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        memory_stats = self.memory_cache.get_stats()
        redis_stats = await self.redis_cache.get_stats()
        
        return {
            "memory_cache": memory_stats,
            "redis_cache": redis_stats,
            "config": {
                "default_ttl": self.config.default_ttl,
                "max_memory_cache_size": self.config.max_memory_cache_size,
                "cache_prefix": self.config.cache_prefix
            }
        }

class DatabaseOptimizer:
    """Database query optimization and performance analysis"""
    
    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
        self.query_stats: Dict[str, Dict[str, Any]] = {}
        self.optimizations: List[QueryOptimization] = []
    
    def get_query_hash(self, query: str) -> str:
        """Generate hash for query"""
        normalized_query = " ".join(query.split()).lower()
        return hashlib.md5(normalized_query.encode()).hexdigest()
    
    async def analyze_query(self, query: str) -> Dict[str, Any]:
        """Analyze query performance and suggest optimizations"""
        query_hash = self.get_query_hash(query)
        
        async with self.db_pool.acquire() as conn:
            try:
                # Get execution plan
                explain_query = f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {query}"
                result = await conn.fetchval(explain_query)
                
                plan = result[0] if result else {}
                execution_time = plan.get("Execution Time", 0)
                
                # Analyze for optimization opportunities
                recommendations = []
                indexes_suggested = []
                
                # Check for missing indexes
                if "Seq Scan" in str(plan):
                    recommendations.append("Consider adding indexes for sequential scans")
                
                # Check for expensive sorts
                if plan.get("Total Cost", 0) > 1000:
                    recommendations.append("High cost query detected - review WHERE clauses and JOINs")
                
                # Check for large buffer usage
                buffers_info = plan.get("Buffers", {})
                if buffers_info.get("Shared Hit Blocks", 0) > 10000:
                    recommendations.append("High buffer usage - consider query optimization")
                
                analysis = {
                    "query_hash": query_hash,
                    "execution_time": execution_time,
                    "total_cost": plan.get("Total Cost", 0),
                    "rows": plan.get("Actual Rows", 0),
                    "buffers": buffers_info,
                    "recommendations": recommendations,
                    "indexes_suggested": indexes_suggested,
                    "plan": plan
                }
                
                # Store query stats
                self.query_stats[query_hash] = analysis
                
                return analysis
                
            except Exception as e:
                logger.error(f"Query analysis error: {e}")
                return {"error": str(e)}
    
    async def suggest_indexes(self) -> List[str]:
        """Suggest database indexes based on query patterns"""
        suggestions = []
        
        async with self.db_pool.acquire() as conn:
            try:
                # Analyze missing indexes
                missing_indexes_query = """
                SELECT 
                    schemaname,
                    tablename,
                    attname,
                    n_distinct,
                    correlation
                FROM pg_stats 
                WHERE schemaname = 'public'
                AND n_distinct > 100
                ORDER BY n_distinct DESC
                LIMIT 20
                """
                
                results = await conn.fetch(missing_indexes_query)
                
                for row in results:
                    table = row['tablename']
                    column = row['attname']
                    suggestions.append(f"CREATE INDEX idx_{table}_{column} ON {table}({column});")
                
                # Analyze slow queries for index suggestions
                slow_queries_query = """
                SELECT query, mean_time, calls 
                FROM pg_stat_statements 
                WHERE mean_time > 100 
                ORDER BY mean_time DESC 
                LIMIT 10
                """
                
                try:
                    slow_queries = await conn.fetch(slow_queries_query)
                    for query_row in slow_queries:
                        # Simple heuristic for index suggestions
                        query_text = query_row['query'].lower()
                        if 'where' in query_text and 'order by' in query_text:
                            suggestions.append(f"-- Consider composite index for: {query_text[:100]}...")
                except Exception:
                    # pg_stat_statements might not be enabled
                    pass
                
                return suggestions
                
            except Exception as e:
                logger.error(f"Index suggestion error: {e}")
                return []
    
    async def get_database_stats(self) -> Dict[str, Any]:
        """Get comprehensive database performance statistics"""
        async with self.db_pool.acquire() as conn:
            try:
                # Database size
                db_size_query = "SELECT pg_size_pretty(pg_database_size(current_database()))"
                db_size = await conn.fetchval(db_size_query)
                
                # Table statistics
                table_stats_query = """
                SELECT 
                    schemaname,
                    tablename,
                    n_tup_ins,
                    n_tup_upd,
                    n_tup_del,
                    n_live_tup,
                    n_dead_tup,
                    last_vacuum,
                    last_autovacuum,
                    last_analyze,
                    last_autoanalyze
                FROM pg_stat_user_tables
                ORDER BY n_live_tup DESC
                LIMIT 20
                """
                
                table_stats = await conn.fetch(table_stats_query)
                
                # Index usage
                index_usage_query = """
                SELECT 
                    schemaname,
                    tablename,
                    indexname,
                    idx_tup_read,
                    idx_tup_fetch
                FROM pg_stat_user_indexes
                WHERE idx_tup_read > 0
                ORDER BY idx_tup_read DESC
                LIMIT 20
                """
                
                index_usage = await conn.fetch(index_usage_query)
                
                # Connection stats
                connection_stats_query = """
                SELECT 
                    COUNT(*) as total_connections,
                    COUNT(*) FILTER (WHERE state = 'active') as active_connections,
                    COUNT(*) FILTER (WHERE state = 'idle') as idle_connections
                FROM pg_stat_activity
                WHERE pid != pg_backend_pid()
                """
                
                connection_stats = await conn.fetchrow(connection_stats_query)
                
                return {
                    "database_size": db_size,
                    "connections": dict(connection_stats),
                    "table_stats": [dict(row) for row in table_stats],
                    "index_usage": [dict(row) for row in index_usage],
                    "query_stats_count": len(self.query_stats),
                    "optimizations_count": len(self.optimizations)
                }
                
            except Exception as e:
                logger.error(f"Database stats error: {e}")
                return {"error": str(e)}

def cached_query(cache_manager: CacheManager, ttl: int = 3600, 
                key_prefix: str = "query"):
    """Decorator for caching database query results"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            key_parts = [key_prefix, func.__name__]
            
            # Add args to key (except first arg which is usually 'self')
            if len(args) > 1:
                key_parts.extend([str(arg) for arg in args[1:]])
            
            # Add kwargs to key
            if kwargs:
                key_parts.extend([f"{k}={v}" for k, v in sorted(kwargs.items())])
            
            cache_key = ":".join(key_parts)
            
            # Try to get from cache
            cached_result = await cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute query and cache result
            result = await func(*args, **kwargs)
            await cache_manager.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator

# Example usage
async def example_usage():
    """Example usage of caching and optimization systems"""
    
    # Initialize cache
    cache_config = CacheConfig()
    cache_manager = CacheManager(cache_config)
    
    # Example cached function
    @cached_query(cache_manager, ttl=1800)
    async def get_patient_data(patient_id: str):
        # Simulate database query
        await asyncio.sleep(0.5)  # Simulate query time
        return {"patient_id": patient_id, "name": "John Doe", "age": 45}
    
    # Test caching
    print("🔍 Testing cache performance...")
    
    start_time = time.time()
    result1 = await get_patient_data("12345")
    first_call_time = time.time() - start_time
    
    start_time = time.time()
    result2 = await get_patient_data("12345")  # Should be cached
    second_call_time = time.time() - start_time
    
    print(f"First call: {first_call_time:.3f}s")
    print(f"Second call (cached): {second_call_time:.3f}s")
    print(f"Cache speedup: {first_call_time/second_call_time:.1f}x faster")
    
    # Get cache statistics
    stats = await cache_manager.get_stats()
    print(f"Memory cache hit rate: {stats['memory_cache']['hit_rate']:.1f}%")

if __name__ == "__main__":
    asyncio.run(example_usage())