#!/usr/bin/env python3
"""
Production Monitoring and Logging System
Comprehensive monitoring for Outscaled.GG prediction system with metrics tracking,
performance monitoring, and production-ready logging.
"""

import logging
import time
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from functools import wraps
import traceback
from dataclasses import dataclass
from collections import defaultdict
import threading

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

@dataclass
class MetricEvent:
    """Structured metric event for monitoring"""
    timestamp: datetime
    event_type: str
    metric_name: str
    value: float
    tags: Dict[str, str]
    metadata: Dict[str, Any]

class PerformanceMonitor:
    """Production-ready performance monitoring system"""
    
    def __init__(self):
        self.metrics = defaultdict(list)
        self.counters = defaultdict(int)
        self.gauges = defaultdict(float)
        self.timers = defaultdict(list)
        self.errors = []
        self.lock = threading.Lock()
        
        # Performance thresholds
        self.thresholds = {
            'prediction_time': 1.0,  # seconds
            'api_response_time': 0.5,  # seconds
            'confidence_calculation_time': 0.1,  # seconds
            'feature_engineering_time': 0.2,  # seconds
        }
        
        # Health check metrics
        self.health_metrics = {
            'total_predictions': 0,
            'successful_predictions': 0,
            'failed_predictions': 0,
            'average_confidence': 0.0,
            'uptime_seconds': 0
        }
        
        self.start_time = time.time()
    
    def record_metric(self, metric_name: str, value: float, tags: Dict[str, str] = None, metadata: Dict[str, Any] = None):
        """Record a metric event"""
        with self.lock:
            event = MetricEvent(
                timestamp=datetime.now(),
                event_type='metric',
                metric_name=metric_name,
                value=value,
                tags=tags or {},
                metadata=metadata or {}
            )
            
            self.metrics[metric_name].append(event)
            
            # Keep only last 1000 events per metric
            if len(self.metrics[metric_name]) > 1000:
                self.metrics[metric_name] = self.metrics[metric_name][-1000:]
            
            logger.info(f"METRIC: {metric_name}={value} tags={tags}")
    
    def increment_counter(self, counter_name: str, value: int = 1, tags: Dict[str, str] = None):
        """Increment a counter metric"""
        with self.lock:
            self.counters[counter_name] += value
            self.record_metric(counter_name, self.counters[counter_name], tags)
    
    def set_gauge(self, gauge_name: str, value: float, tags: Dict[str, str] = None):
        """Set a gauge metric"""
        with self.lock:
            self.gauges[gauge_name] = value
            self.record_metric(gauge_name, value, tags)
    
    def record_timing(self, timer_name: str, duration: float, tags: Dict[str, str] = None):
        """Record timing information"""
        with self.lock:
            self.timers[timer_name].append(duration)
            
            # Keep only last 100 timings
            if len(self.timers[timer_name]) > 100:
                self.timers[timer_name] = self.timers[timer_name][-100:]
            
            # Check against thresholds
            threshold = self.thresholds.get(timer_name)
            if threshold and duration > threshold:
                logger.warning(f"PERFORMANCE: {timer_name} took {duration:.3f}s (threshold: {threshold}s)")
            
            self.record_metric(timer_name, duration, tags)
    
    def record_error(self, error_type: str, error_message: str, context: Dict[str, Any] = None):
        """Record error information"""
        with self.lock:
            error_event = {
                'timestamp': datetime.now().isoformat(),
                'error_type': error_type,
                'error_message': error_message,
                'context': context or {},
                'traceback': traceback.format_exc()
            }
            
            self.errors.append(error_event)
            
            # Keep only last 100 errors
            if len(self.errors) > 100:
                self.errors = self.errors[-100:]
            
            self.increment_counter('errors_total', tags={'error_type': error_type})
            logger.error(f"ERROR: {error_type} - {error_message} context={context}")
    
    def get_summary(self) -> Dict[str, Any]:
        """Get monitoring summary"""
        with self.lock:
            current_time = time.time()
            uptime = current_time - self.start_time
            
            summary = {
                'uptime_seconds': uptime,
                'uptime_formatted': self._format_duration(uptime),
                'counters': dict(self.counters),
                'gauges': dict(self.gauges),
                'error_count': len(self.errors),
                'recent_errors': self.errors[-5:] if self.errors else [],
                'performance_summary': self._get_performance_summary(),
                'health_status': self._get_health_status()
            }
            
            return summary
    
    def _get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary statistics"""
        perf_summary = {}
        
        for timer_name, timings in self.timers.items():
            if timings:
                perf_summary[timer_name] = {
                    'count': len(timings),
                    'avg': sum(timings) / len(timings),
                    'min': min(timings),
                    'max': max(timings),
                    'p95': self._percentile(timings, 95),
                    'threshold': self.thresholds.get(timer_name),
                    'threshold_violations': sum(1 for t in timings if t > self.thresholds.get(timer_name, float('inf')))
                }
        
        return perf_summary
    
    def _get_health_status(self) -> Dict[str, Any]:
        """Get overall system health status"""
        total_predictions = self.counters.get('predictions_total', 0)
        failed_predictions = self.counters.get('predictions_failed', 0)
        
        success_rate = 0.0
        if total_predictions > 0:
            success_rate = ((total_predictions - failed_predictions) / total_predictions) * 100
        
        health_status = 'healthy'
        if success_rate < 95:
            health_status = 'degraded'
        if success_rate < 90:
            health_status = 'unhealthy'
        
        return {
            'status': health_status,
            'success_rate': success_rate,
            'total_predictions': total_predictions,
            'failed_predictions': failed_predictions,
            'error_rate': len(self.errors) / max(1, total_predictions) * 100
        }
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile"""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    def _format_duration(self, seconds: float) -> str:
        """Format duration in human-readable format"""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            return f"{seconds/60:.1f}m"
        else:
            return f"{seconds/3600:.1f}h"

# Global monitor instance
monitor = PerformanceMonitor()

def time_function(metric_name: str = None, tags: Dict[str, str] = None):
    """Decorator to time function execution"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            function_name = metric_name or f"{func.__module__}.{func.__name__}"
            
            try:
                result = func(*args, **kwargs)
                monitor.increment_counter(f"{function_name}_success", tags=tags)
                return result
            except Exception as e:
                monitor.record_error(
                    error_type=type(e).__name__,
                    error_message=str(e),
                    context={'function': function_name, 'args': str(args)[:200]}
                )
                monitor.increment_counter(f"{function_name}_error", tags=tags)
                raise
            finally:
                duration = time.time() - start_time
                monitor.record_timing(function_name, duration, tags)
        
        return wrapper
    return decorator

def log_prediction(prediction_result: Dict[str, Any], request_data: Dict[str, Any]):
    """Log prediction with structured data"""
    logger.info("PREDICTION", extra={
        'prediction': prediction_result.get('prediction'),
        'confidence': prediction_result.get('confidence'),
        'player_names': request_data.get('player_names'),
        'prop_type': request_data.get('prop_type'),
        'prop_value': request_data.get('prop_value'),
        'expected_stat': prediction_result.get('expected_stat')
    })
    
    monitor.increment_counter('predictions_total')
    monitor.record_metric('prediction_confidence', prediction_result.get('confidence', 0))

def log_api_request(endpoint: str, method: str, status_code: int, duration: float, request_data: Dict[str, Any] = None):
    """Log API request with performance data"""
    logger.info(f"API_REQUEST: {method} {endpoint} - {status_code} ({duration:.3f}s)")
    
    monitor.record_timing('api_response_time', duration, {
        'endpoint': endpoint,
        'method': method,
        'status_code': str(status_code)
    })
    
    monitor.increment_counter('api_requests_total', tags={
        'endpoint': endpoint,
        'method': method,
        'status_code': str(status_code)
    })

def create_monitoring_report() -> Dict[str, Any]:
    """Create comprehensive monitoring report"""
    return {
        'timestamp': datetime.now().isoformat(),
        'system_summary': monitor.get_summary(),
        'performance_metrics': monitor._get_performance_summary(),
        'health_status': monitor._get_health_status(),
        'recent_errors': monitor.errors[-10:] if monitor.errors else []
    }

class ProductionLogger:
    """Production-ready structured logging"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.request_id = None
    
    def set_request_id(self, request_id: str):
        """Set request ID for correlation"""
        self.request_id = request_id
    
    def _log_with_context(self, level: str, message: str, extra: Dict[str, Any] = None):
        """Log with request context"""
        log_data = {
            'message': message,
            'request_id': self.request_id,
            'timestamp': datetime.now().isoformat()
        }
        
        if extra:
            log_data.update(extra)
        
        getattr(self.logger, level)(json.dumps(log_data))
    
    def info(self, message: str, **kwargs):
        self._log_with_context('info', message, kwargs)
    
    def warning(self, message: str, **kwargs):
        self._log_with_context('warning', message, kwargs)
    
    def error(self, message: str, **kwargs):
        self._log_with_context('error', message, kwargs)
    
    def debug(self, message: str, **kwargs):
        self._log_with_context('debug', message, kwargs)

# Global logger factory
def get_logger(name: str) -> ProductionLogger:
    """Get production logger instance"""
    return ProductionLogger(name)