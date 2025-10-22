#!/usr/bin/env python3
"""
Performance Monitoring and Optimization System
Real-time performance tracking, bottleneck detection, and optimization recommendations
"""

import asyncio
import time
import logging
import psutil
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import threading
from pathlib import Path
import sqlite3
from contextlib import asynccontextmanager
import aiohttp
import asyncpg
from functools import wraps

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetric:
    """Individual performance metric"""
    name: str
    value: float
    unit: str
    timestamp: datetime
    category: str
    severity: str = "info"  # info, warning, error, critical
    tags: Dict[str, Any] = None

@dataclass
class SystemMetrics:
    """System-level performance metrics"""
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    network_io: Dict[str, int]
    process_count: int
    load_average: List[float]
    timestamp: datetime

@dataclass
class DatabaseMetrics:
    """Database performance metrics"""
    active_connections: int
    query_duration_avg: float
    query_duration_p95: float
    query_count: int
    slow_queries: int
    deadlocks: int
    cache_hit_ratio: float
    index_usage: Dict[str, float]
    timestamp: datetime

@dataclass
class APIMetrics:
    """API performance metrics"""
    endpoint: str
    method: str
    status_code: int
    response_time: float
    request_size: int
    response_size: int
    user_id: Optional[str]
    timestamp: datetime

class PerformanceCollector:
    """Real-time performance data collector"""
    
    def __init__(self, db_path: str = "performance/performance_metrics.db"):
        """Initialize performance collector"""
        self.db_path = db_path
        self.metrics_buffer: deque = deque(maxlen=10000)
        self.system_metrics_history: deque = deque(maxlen=1000)
        self.api_metrics_history: deque = deque(maxlen=5000)
        self.db_metrics_history: deque = deque(maxlen=1000)
        
        self.running = False
        self.collection_interval = 10  # seconds
        self.alert_thresholds = {
            "cpu_percent": 80.0,
            "memory_percent": 85.0,
            "disk_percent": 90.0,
            "response_time": 2.0,  # seconds
            "error_rate": 5.0,  # percentage
        }
        
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database for metrics storage"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS system_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    cpu_percent REAL NOT NULL,
                    memory_percent REAL NOT NULL,
                    disk_percent REAL NOT NULL,
                    network_io_sent INTEGER NOT NULL,
                    network_io_recv INTEGER NOT NULL,
                    process_count INTEGER NOT NULL,
                    load_avg_1 REAL,
                    load_avg_5 REAL,
                    load_avg_15 REAL
                );
                
                CREATE TABLE IF NOT EXISTS api_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    endpoint TEXT NOT NULL,
                    method TEXT NOT NULL,
                    status_code INTEGER NOT NULL,
                    response_time REAL NOT NULL,
                    request_size INTEGER NOT NULL,
                    response_size INTEGER NOT NULL,
                    user_id TEXT
                );
                
                CREATE TABLE IF NOT EXISTS db_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    active_connections INTEGER NOT NULL,
                    query_duration_avg REAL NOT NULL,
                    query_duration_p95 REAL NOT NULL,
                    query_count INTEGER NOT NULL,
                    slow_queries INTEGER NOT NULL,
                    deadlocks INTEGER NOT NULL,
                    cache_hit_ratio REAL NOT NULL
                );
                
                CREATE TABLE IF NOT EXISTS performance_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    threshold REAL NOT NULL,
                    severity TEXT NOT NULL,
                    message TEXT NOT NULL,
                    resolved INTEGER DEFAULT 0
                );
                
                CREATE INDEX IF NOT EXISTS idx_system_metrics_timestamp ON system_metrics(timestamp);
                CREATE INDEX IF NOT EXISTS idx_api_metrics_timestamp ON api_metrics(timestamp);
                CREATE INDEX IF NOT EXISTS idx_api_metrics_endpoint ON api_metrics(endpoint);
                CREATE INDEX IF NOT EXISTS idx_db_metrics_timestamp ON db_metrics(timestamp);
                CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON performance_alerts(timestamp);
            """)
    
    async def start_collection(self):
        """Start performance data collection"""
        if self.running:
            return
        
        self.running = True
        logger.info("Starting performance data collection")
        
        # Start collection tasks
        tasks = [
            asyncio.create_task(self._collect_system_metrics()),
            asyncio.create_task(self._process_metrics_buffer()),
        ]
        
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"Error in performance collection: {e}")
        finally:
            self.running = False
    
    async def stop_collection(self):
        """Stop performance data collection"""
        self.running = False
        logger.info("Stopping performance data collection")
    
    async def _collect_system_metrics(self):
        """Collect system-level performance metrics"""
        while self.running:
            try:
                # CPU metrics
                cpu_percent = psutil.cpu_percent(interval=1)
                
                # Memory metrics
                memory = psutil.virtual_memory()
                memory_percent = memory.percent
                
                # Disk metrics
                disk = psutil.disk_usage('/')
                disk_percent = disk.percent
                
                # Network metrics
                network = psutil.net_io_counters()
                network_io = {
                    "sent": network.bytes_sent,
                    "recv": network.bytes_recv
                }
                
                # Process metrics
                process_count = len(psutil.pids())
                
                # Load average (Unix-like systems)
                try:
                    load_average = list(psutil.getloadavg())
                except (AttributeError, OSError):
                    load_average = [0.0, 0.0, 0.0]
                
                metrics = SystemMetrics(
                    cpu_percent=cpu_percent,
                    memory_percent=memory_percent,
                    disk_percent=disk_percent,
                    network_io=network_io,
                    process_count=process_count,
                    load_average=load_average,
                    timestamp=datetime.now()
                )
                
                self.system_metrics_history.append(metrics)
                
                # Check for alerts
                await self._check_system_alerts(metrics)
                
                # Store in database
                await self._store_system_metrics(metrics)
                
                await asyncio.sleep(self.collection_interval)
                
            except Exception as e:
                logger.error(f"Error collecting system metrics: {e}")
                await asyncio.sleep(5)
    
    async def _process_metrics_buffer(self):
        """Process buffered metrics and store in database"""
        while self.running:
            try:
                if self.metrics_buffer:
                    # Process batch of metrics
                    batch = []
                    for _ in range(min(100, len(self.metrics_buffer))):
                        batch.append(self.metrics_buffer.popleft())
                    
                    if batch:
                        await self._store_metrics_batch(batch)
                
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error processing metrics buffer: {e}")
                await asyncio.sleep(5)
    
    async def _check_system_alerts(self, metrics: SystemMetrics):
        """Check system metrics against alert thresholds"""
        alerts = []
        
        # CPU alert
        if metrics.cpu_percent > self.alert_thresholds["cpu_percent"]:
            alerts.append({
                "metric_name": "cpu_percent",
                "metric_value": metrics.cpu_percent,
                "threshold": self.alert_thresholds["cpu_percent"],
                "severity": "warning" if metrics.cpu_percent < 95 else "critical",
                "message": f"High CPU usage: {metrics.cpu_percent:.1f}%"
            })
        
        # Memory alert
        if metrics.memory_percent > self.alert_thresholds["memory_percent"]:
            alerts.append({
                "metric_name": "memory_percent",
                "metric_value": metrics.memory_percent,
                "threshold": self.alert_thresholds["memory_percent"],
                "severity": "warning" if metrics.memory_percent < 95 else "critical",
                "message": f"High memory usage: {metrics.memory_percent:.1f}%"
            })
        
        # Disk alert
        if metrics.disk_percent > self.alert_thresholds["disk_percent"]:
            alerts.append({
                "metric_name": "disk_percent",
                "metric_value": metrics.disk_percent,
                "threshold": self.alert_thresholds["disk_percent"],
                "severity": "warning" if metrics.disk_percent < 98 else "critical",
                "message": f"High disk usage: {metrics.disk_percent:.1f}%"
            })
        
        # Store alerts
        if alerts:
            await self._store_alerts(alerts)
    
    async def _store_system_metrics(self, metrics: SystemMetrics):
        """Store system metrics in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO system_metrics (
                        timestamp, cpu_percent, memory_percent, disk_percent,
                        network_io_sent, network_io_recv, process_count,
                        load_avg_1, load_avg_5, load_avg_15
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    metrics.timestamp.isoformat(),
                    metrics.cpu_percent,
                    metrics.memory_percent,
                    metrics.disk_percent,
                    metrics.network_io["sent"],
                    metrics.network_io["recv"],
                    metrics.process_count,
                    metrics.load_average[0] if len(metrics.load_average) > 0 else 0.0,
                    metrics.load_average[1] if len(metrics.load_average) > 1 else 0.0,
                    metrics.load_average[2] if len(metrics.load_average) > 2 else 0.0,
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"Error storing system metrics: {e}")
    
    async def _store_metrics_batch(self, batch: List[PerformanceMetric]):
        """Store batch of performance metrics"""
        # Implementation for storing general metrics
        pass
    
    async def _store_alerts(self, alerts: List[Dict[str, Any]]):
        """Store performance alerts in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                for alert in alerts:
                    conn.execute("""
                        INSERT INTO performance_alerts (
                            timestamp, metric_name, metric_value, threshold,
                            severity, message
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        datetime.now().isoformat(),
                        alert["metric_name"],
                        alert["metric_value"],
                        alert["threshold"],
                        alert["severity"],
                        alert["message"]
                    ))
                conn.commit()
        except Exception as e:
            logger.error(f"Error storing alerts: {e}")
    
    def record_api_request(self, endpoint: str, method: str, status_code: int,
                          response_time: float, request_size: int = 0,
                          response_size: int = 0, user_id: Optional[str] = None):
        """Record API request metrics"""
        metrics = APIMetrics(
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            response_time=response_time,
            request_size=request_size,
            response_size=response_size,
            user_id=user_id,
            timestamp=datetime.now()
        )
        
        self.api_metrics_history.append(metrics)
        
        # Store in database
        asyncio.create_task(self._store_api_metrics(metrics))
    
    async def _store_api_metrics(self, metrics: APIMetrics):
        """Store API metrics in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO api_metrics (
                        timestamp, endpoint, method, status_code,
                        response_time, request_size, response_size, user_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    metrics.timestamp.isoformat(),
                    metrics.endpoint,
                    metrics.method,
                    metrics.status_code,
                    metrics.response_time,
                    metrics.request_size,
                    metrics.response_size,
                    metrics.user_id
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"Error storing API metrics: {e}")
    
    def get_performance_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get performance summary for the last N hours"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                since_time = (datetime.now() - timedelta(hours=hours)).isoformat()
                
                # System metrics summary
                system_summary = conn.execute("""
                    SELECT 
                        AVG(cpu_percent) as avg_cpu,
                        MAX(cpu_percent) as max_cpu,
                        AVG(memory_percent) as avg_memory,
                        MAX(memory_percent) as max_memory,
                        AVG(disk_percent) as avg_disk,
                        MAX(disk_percent) as max_disk
                    FROM system_metrics 
                    WHERE timestamp > ?
                """, (since_time,)).fetchone()
                
                # API metrics summary
                api_summary = conn.execute("""
                    SELECT 
                        COUNT(*) as total_requests,
                        AVG(response_time) as avg_response_time,
                        MAX(response_time) as max_response_time,
                        COUNT(CASE WHEN status_code >= 400 THEN 1 END) as error_count,
                        COUNT(CASE WHEN status_code >= 500 THEN 1 END) as server_error_count
                    FROM api_metrics 
                    WHERE timestamp > ?
                """, (since_time,)).fetchone()
                
                # Recent alerts
                alerts = conn.execute("""
                    SELECT * FROM performance_alerts 
                    WHERE timestamp > ? AND resolved = 0 
                    ORDER BY timestamp DESC LIMIT 10
                """, (since_time,)).fetchall()
                
                return {
                    "period_hours": hours,
                    "system": {
                        "avg_cpu": system_summary[0] or 0,
                        "max_cpu": system_summary[1] or 0,
                        "avg_memory": system_summary[2] or 0,
                        "max_memory": system_summary[3] or 0,
                        "avg_disk": system_summary[4] or 0,
                        "max_disk": system_summary[5] or 0,
                    },
                    "api": {
                        "total_requests": api_summary[0] or 0,
                        "avg_response_time": api_summary[1] or 0,
                        "max_response_time": api_summary[2] or 0,
                        "error_count": api_summary[3] or 0,
                        "server_error_count": api_summary[4] or 0,
                        "error_rate": (api_summary[3] / max(api_summary[0], 1)) * 100 if api_summary[0] else 0,
                    },
                    "alerts": [dict(zip([col[0] for col in conn.description], alert)) for alert in alerts],
                    "generated_at": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error generating performance summary: {e}")
            return {"error": str(e)}

class PerformanceDecorator:
    """Decorator for monitoring function performance"""
    
    def __init__(self, collector: PerformanceCollector):
        self.collector = collector
    
    def monitor_function(self, category: str = "function", 
                        include_args: bool = False):
        """Decorator to monitor function execution time"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    status = "success"
                    return result
                except Exception as e:
                    status = "error"
                    raise
                finally:
                    execution_time = time.time() - start_time
                    metric = PerformanceMetric(
                        name=f"{func.__name__}_execution_time",
                        value=execution_time,
                        unit="seconds",
                        timestamp=datetime.now(),
                        category=category,
                        tags={
                            "function": func.__name__,
                            "status": status,
                            "args_count": len(args) if include_args else None,
                            "kwargs_count": len(kwargs) if include_args else None,
                        }
                    )
                    self.collector.metrics_buffer.append(metric)
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    status = "success"
                    return result
                except Exception as e:
                    status = "error"
                    raise
                finally:
                    execution_time = time.time() - start_time
                    metric = PerformanceMetric(
                        name=f"{func.__name__}_execution_time",
                        value=execution_time,
                        unit="seconds",
                        timestamp=datetime.now(),
                        category=category,
                        tags={
                            "function": func.__name__,
                            "status": status,
                            "args_count": len(args) if include_args else None,
                            "kwargs_count": len(kwargs) if include_args else None,
                        }
                    )
                    self.collector.metrics_buffer.append(metric)
            
            # Return appropriate wrapper based on function type
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper
        
        return decorator

# Global performance collector instance
performance_collector = PerformanceCollector()

def get_performance_collector() -> PerformanceCollector:
    """Get the global performance collector instance"""
    return performance_collector

# Performance monitoring decorators
def monitor_performance(category: str = "function"):
    """Decorator for monitoring function performance"""
    return PerformanceDecorator(performance_collector).monitor_function(category)

# Example usage and testing
async def main():
    """Example usage of performance monitoring system"""
    
    collector = PerformanceCollector()
    
    # Start performance collection
    collection_task = asyncio.create_task(collector.start_collection())
    
    # Simulate some API requests
    for i in range(10):
        collector.record_api_request(
            endpoint="/api/patients",
            method="GET",
            status_code=200,
            response_time=0.5 + (i * 0.1),
            request_size=1024,
            response_size=2048,
            user_id=f"user_{i % 3}"
        )
        await asyncio.sleep(0.1)
    
    # Wait a bit for metrics collection
    await asyncio.sleep(15)
    
    # Get performance summary
    summary = collector.get_performance_summary(hours=1)
    
    print("🔍 Performance Summary:")
    print(f"   CPU Usage: Avg {summary['system']['avg_cpu']:.1f}%, Max {summary['system']['max_cpu']:.1f}%")
    print(f"   Memory Usage: Avg {summary['system']['avg_memory']:.1f}%, Max {summary['system']['max_memory']:.1f}%")
    print(f"   API Requests: {summary['api']['total_requests']}")
    print(f"   Avg Response Time: {summary['api']['avg_response_time']:.3f}s")
    print(f"   Error Rate: {summary['api']['error_rate']:.1f}%")
    print(f"   Active Alerts: {len(summary['alerts'])}")
    
    # Stop collection
    await collector.stop_collection()

if __name__ == "__main__":
    asyncio.run(main())