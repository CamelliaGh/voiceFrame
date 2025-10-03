"""
Prometheus metrics for VoiceFrame application
"""
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response
import time
import psutil
import os

# Request metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

# Application metrics
ACTIVE_SESSIONS = Gauge(
    'voiceframe_active_sessions_total',
    'Number of active sessions'
)

PDF_GENERATION_COUNT = Counter(
    'voiceframe_pdf_generation_total',
    'Total PDF generations',
    ['status']  # success, error
)

PDF_GENERATION_DURATION = Histogram(
    'voiceframe_pdf_generation_duration_seconds',
    'PDF generation duration in seconds'
)

AUDIO_PROCESSING_COUNT = Counter(
    'voiceframe_audio_processing_total',
    'Total audio processing operations',
    ['status']  # success, error
)

AUDIO_PROCESSING_DURATION = Histogram(
    'voiceframe_audio_processing_duration_seconds',
    'Audio processing duration in seconds'
)

FILE_UPLOAD_COUNT = Counter(
    'voiceframe_file_upload_total',
    'Total file uploads',
    ['file_type', 'status']  # photo, audio, success, error
)

FILE_UPLOAD_SIZE = Histogram(
    'voiceframe_file_upload_size_bytes',
    'File upload size in bytes',
    ['file_type']
)

# System metrics
SYSTEM_CPU_USAGE = Gauge(
    'voiceframe_system_cpu_usage_percent',
    'System CPU usage percentage'
)

SYSTEM_MEMORY_USAGE = Gauge(
    'voiceframe_system_memory_usage_percent',
    'System memory usage percentage'
)

SYSTEM_DISK_USAGE = Gauge(
    'voiceframe_system_disk_usage_percent',
    'System disk usage percentage',
    ['mountpoint']
)

# Database metrics
DATABASE_CONNECTIONS = Gauge(
    'voiceframe_database_connections_active',
    'Active database connections'
)

DATABASE_QUERY_DURATION = Histogram(
    'voiceframe_database_query_duration_seconds',
    'Database query duration in seconds',
    ['operation']  # select, insert, update, delete
)

# Cache metrics
CACHE_HITS = Counter(
    'voiceframe_cache_hits_total',
    'Total cache hits',
    ['cache_type']  # redis, memory
)

CACHE_MISSES = Counter(
    'voiceframe_cache_misses_total',
    'Total cache misses',
    ['cache_type']
)

# Error metrics
ERROR_COUNT = Counter(
    'voiceframe_errors_total',
    'Total application errors',
    ['error_type', 'component']  # validation, database, external_api, etc.
)

def update_system_metrics():
    """Update system metrics"""
    # CPU usage
    cpu_percent = psutil.cpu_percent(interval=1)
    SYSTEM_CPU_USAGE.set(cpu_percent)

    # Memory usage
    memory = psutil.virtual_memory()
    SYSTEM_MEMORY_USAGE.set(memory.percent)

    # Disk usage
    for partition in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(partition.mountpoint)
            disk_percent = (usage.used / usage.total) * 100
            SYSTEM_DISK_USAGE.labels(mountpoint=partition.mountpoint).set(disk_percent)
        except PermissionError:
            # Skip partitions we can't access
            continue

def get_metrics_response():
    """Get metrics in Prometheus format"""
    # Update system metrics before returning
    update_system_metrics()

    return Response(
        generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )

class MetricsMiddleware:
    """Middleware to collect request metrics"""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        method = scope["method"]
        path = scope["path"]

        # Start timer
        start_time = time.time()

        # Track request
        REQUEST_COUNT.labels(method=method, endpoint=path, status="").inc()

        # Process request
        status_code = 200

        async def send_wrapper(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
                # Update request count with actual status
                REQUEST_COUNT.labels(method=method, endpoint=path, status=str(status_code)).inc()
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as e:
            # Track errors
            ERROR_COUNT.labels(error_type=type(e).__name__, component="middleware").inc()
            raise
        finally:
            # Record duration
            duration = time.time() - start_time
            REQUEST_DURATION.labels(method=method, endpoint=path).observe(duration)

# Utility functions for tracking specific operations
def track_pdf_generation(func):
    """Decorator to track PDF generation metrics"""
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            PDF_GENERATION_COUNT.labels(status="success").inc()
            return result
        except Exception as e:
            PDF_GENERATION_COUNT.labels(status="error").inc()
            ERROR_COUNT.labels(error_type=type(e).__name__, component="pdf_generation").inc()
            raise
        finally:
            duration = time.time() - start_time
            PDF_GENERATION_DURATION.observe(duration)
    return wrapper

def track_audio_processing(func):
    """Decorator to track audio processing metrics"""
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            AUDIO_PROCESSING_COUNT.labels(status="success").inc()
            return result
        except Exception as e:
            AUDIO_PROCESSING_COUNT.labels(status="error").inc()
            ERROR_COUNT.labels(error_type=type(e).__name__, component="audio_processing").inc()
            raise
        finally:
            duration = time.time() - start_time
            AUDIO_PROCESSING_DURATION.observe(duration)
    return wrapper

def track_file_upload(file_type: str, file_size: int, success: bool):
    """Track file upload metrics"""
    status = "success" if success else "error"
    FILE_UPLOAD_COUNT.labels(file_type=file_type, status=status).inc()
    if success:
        FILE_UPLOAD_SIZE.labels(file_type=file_type).observe(file_size)

def track_database_query(operation: str, duration: float):
    """Track database query metrics"""
    DATABASE_QUERY_DURATION.labels(operation=operation).observe(duration)

def track_cache_hit(cache_type: str):
    """Track cache hit"""
    CACHE_HITS.labels(cache_type=cache_type).inc()

def track_cache_miss(cache_type: str):
    """Track cache miss"""
    CACHE_MISSES.labels(cache_type=cache_type).inc()

def track_error(error_type: str, component: str):
    """Track application errors"""
    ERROR_COUNT.labels(error_type=error_type, component=component).inc()
