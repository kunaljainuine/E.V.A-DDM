import logging
import logging.handlers
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
import json
from collections import defaultdict
import psutil
import platform
import sys
import traceback
import time
import re
from dataclasses import dataclass, asdict

@dataclass
class SystemMetrics:
    """System performance metrics"""
    cpu_percent: float
    memory_percent: float
    disk_usage_percent: float
    python_memory_mb: float
    
class PerformanceMonitor:
    """Monitors system performance metrics"""
    
    @staticmethod
    def get_metrics() -> SystemMetrics:
        """Get current system metrics"""
        process = psutil.Process()
        return SystemMetrics(
            cpu_percent=psutil.cpu_percent(),
            memory_percent=psutil.virtual_memory().percent,
            disk_usage_percent=psutil.disk_usage('/').percent,
            python_memory_mb=process.memory_info().rss / 1024 / 1024
        )

def setup_logging(module_name: str, log_level: str = "DEBUG") -> logging.Logger:
    """
    Configure logging for a specific module with enhanced features
    
    Args:
        module_name (str): Name of the module requesting logging
        log_level (str): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
    Returns:
        logging.Logger: Configured logger instance
    """
    # Create logs directory if it doesn't exist
    log_dir = Path("Logs")
    log_dir.mkdir(exist_ok=True)
    
    # Create module-specific log file with timestamp
    timestamp = datetime.now().strftime("%Y%m%d")
    log_file = log_dir / f"{module_name}_{timestamp}.log"
    
    # Create logger
    logger = logging.getLogger(module_name)
    logger.setLevel(getattr(logging, log_level))
    
    # Prevent adding handlers multiple times
    if not logger.handlers:
        # File handler with rotation
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(getattr(logging, log_level))
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Create formatters and add it to the handlers
        file_formatter = logging.Formatter(
            '%(asctime)s [%(name)s] %(levelname)s [%(filename)s:%(lineno)d] - %(message)s - metrics={%(metrics)s}',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_formatter = logging.Formatter(
            '[%(name)s] %(levelname)s %(message)s'
        )
        
        # Add custom filter to inject performance metrics
        class MetricsFilter(logging.Filter):
            def filter(self, record):
                metrics = PerformanceMonitor.get_metrics()
                record.metrics = f"cpu={metrics.cpu_percent:.1f}%,mem={metrics.memory_percent:.1f}%,disk={metrics.disk_usage_percent:.1f}%,py_mem={metrics.python_memory_mb:.1f}MB"
                return True
                
        file_handler.addFilter(MetricsFilter())
        
        file_handler.setFormatter(file_formatter)
        console_handler.setFormatter(console_formatter)
        
        # Add handlers to the logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        # Log system information on first setup
        logger.info(
            "Logger initialized - "
            f"Python {sys.version}, "
            f"Platform: {platform.platform()}, "
            f"CPU Cores: {psutil.cpu_count()}, "
            f"Total Memory: {psutil.virtual_memory().total / (1024**3):.1f}GB"
        )
    
    return logger

class LogAnalyzer:
    """Analyzes log files and generates comprehensive reports"""
    
    def __init__(self):
        self.logger = setup_logging("LogAnalyzer")
        self.log_dir = Path("Logs")
        self.stats = defaultdict(lambda: defaultdict(int))
        self.error_patterns = defaultdict(list)
        self.performance_metrics = defaultdict(list)
        self.system_metrics = defaultdict(list)
        self.api_calls = defaultdict(list)
        self.user_interactions = defaultdict(list)
        
    def analyze_logs(self, days: Optional[int] = None) -> Dict[str, Any]:
        """
        Analyze log files and generate a comprehensive report
        
        Args:
            days (Optional[int]): Number of days of logs to analyze. None for all logs.
            
        Returns:
            Dict[str, Any]: Analysis results
        """
        try:
            self.logger.info(f"Starting log analysis for past {days if days else 'all'} days")
            self._process_log_files(days)
            report = self._generate_report()
            
            # Save report to file
            report_file = self.log_dir / f"analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=4)
            
            self.logger.info(f"Analysis report saved to {report_file}")
            return report
            
        except Exception as e:
            self.logger.error(f"Error during log analysis: {e}", exc_info=True)
            raise
            
    def _process_log_files(self, days: Optional[int] = None) -> None:
        """Process log files within the specified time range"""
        cutoff_date = None
        if days:
            cutoff_date = datetime.now() - timedelta(days=days)
            
        for log_file in self.log_dir.glob("*.log"):
            try:
                # Extract date from filename
                date_str = re.search(r'\d{8}', log_file.name)
                if date_str:
                    file_date = datetime.strptime(date_str.group(), '%Y%m%d')
                    if cutoff_date and file_date < cutoff_date:
                        continue
                        
                self.logger.debug(f"Processing log file: {log_file}")
                module_name = log_file.stem.split('_')[0]
                
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        self._process_log_line(line, module_name)
                        
            except Exception as e:
                self.logger.error(f"Error processing {log_file}: {e}")
                
    def _process_log_line(self, line: str, module_name: str) -> None:
        """Process a single log line with enhanced pattern matching"""
        try:
            # Extract timestamp
            timestamp_match = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
            timestamp = timestamp_match.group(1) if timestamp_match else None
            
            # Count log levels
            for level in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
                if f"] {level} " in line:
                    self.stats[module_name][level] += 1
                    break
                    
            # Track errors with context
            if '] ERROR ' in line:
                error_msg = line.split('] ERROR ')[-1].strip()
                context = {}
                
                # Extract file and line number if available
                file_line_match = re.search(r'\[(.*?):(\d+)\]', line)
                if file_line_match:
                    context['file'] = file_line_match.group(1)
                    context['line'] = int(file_line_match.group(2))
                
                # Extract system metrics if available
                metrics_match = re.search(r'metrics=\{(.*?)\}', line)
                if metrics_match:
                    metrics_str = metrics_match.group(1)
                    metrics = dict(item.split('=') for item in metrics_str.split(','))
                    context['system_metrics'] = metrics
                
                self.error_patterns[error_msg].append({
                    'timestamp': timestamp,
                    'module': module_name,
                    'context': context
                })
                
            # Extract performance metrics
            metrics_match = re.search(r'metrics=\{(.*?)\}', line)
            if metrics_match:
                metrics_str = metrics_match.group(1)
                try:
                    metrics = dict(item.split('=') for item in metrics_str.split(','))
                    self.system_metrics[module_name].append({
                        'timestamp': timestamp,
                        'metrics': {k: float(v.rstrip('%').rstrip('MB')) for k, v in metrics.items()}
                    })
                except ValueError:
                    pass
                    
            # Track API calls
            if 'API request' in line:
                self.api_calls[module_name].append({
                    'timestamp': timestamp,
                    'details': line.split('API request')[-1].strip()
                })
                
            # Track user interactions
            if 'User input:' in line or 'Generated response:' in line:
                self.user_interactions[module_name].append({
                    'timestamp': timestamp,
                    'interaction': line.split(': ', 1)[-1].strip()
                })
                    
        except Exception as e:
            self.logger.error(f"Error processing log line: {e}")
            
    def _generate_report(self) -> Dict[str, Any]:
        """Generate enhanced analysis report"""
        try:
            self.logger.info("Generating analysis report")
            
            # Calculate module-specific metrics
            module_metrics = self._calculate_module_metrics()
            
            # Calculate system performance trends
            system_trends = self._calculate_system_trends()
            
            # Get error patterns and stack traces
            error_analysis = self._analyze_errors()
            
            # Analyze API usage patterns
            api_analysis = self._analyze_api_usage()
            
            # Analyze user interactions
            user_analysis = self._analyze_user_interactions()
            
            report = {
                'timestamp': datetime.now().isoformat(),
                'log_level_distribution': dict(self.stats),
                'error_analysis': error_analysis,
                'performance_metrics': module_metrics,
                'system_performance': system_trends,
                'api_usage': api_analysis,
                'user_interaction_analysis': user_analysis,
                'summary': {
                    'total_modules': len(self.stats),
                    'total_log_entries': sum(
                        sum(levels.values())
                        for levels in self.stats.values()
                    ),
                    'total_errors': sum(len(occurrences) for occurrences in self.error_patterns.values()),
                    'total_api_calls': sum(len(calls) for calls in self.api_calls.values()),
                    'total_user_interactions': sum(len(interactions) for interactions in self.user_interactions.values())
                }
            }
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating report: {e}", exc_info=True)
            raise
            
    def _calculate_module_metrics(self) -> Dict[str, Any]:
        """Calculate detailed metrics for each module"""
        module_metrics = {}
        
        for module, metrics in self.system_metrics.items():
            if metrics:
                timestamps = [m['timestamp'] for m in metrics]
                cpu_values = [m['metrics']['cpu'] for m in metrics]
                mem_values = [m['metrics']['mem'] for m in metrics]
                
                module_metrics[module] = {
                    'cpu_usage': {
                        'average': sum(cpu_values) / len(cpu_values),
                        'max': max(cpu_values),
                        'min': min(cpu_values)
                    },
                    'memory_usage': {
                        'average': sum(mem_values) / len(mem_values),
                        'max': max(mem_values),
                        'min': min(mem_values)
                    },
                    'activity_period': {
                        'start': min(timestamps),
                        'end': max(timestamps)
                    }
                }
                
        return module_metrics
        
    def _calculate_system_trends(self) -> Dict[str, Any]:
        """Calculate system performance trends"""
        all_metrics = []
        for module_metrics in self.system_metrics.values():
            all_metrics.extend(module_metrics)
            
        if not all_metrics:
            return {}
            
        # Sort by timestamp
        all_metrics.sort(key=lambda x: x['timestamp'])
        
        # Calculate trends
        return {
            'overall_trends': {
                'cpu_trend': self._calculate_trend([m['metrics']['cpu'] for m in all_metrics]),
                'memory_trend': self._calculate_trend([m['metrics']['mem'] for m in all_metrics])
            },
            'peak_times': {
                'cpu': max(all_metrics, key=lambda x: x['metrics']['cpu'])['timestamp'],
                'memory': max(all_metrics, key=lambda x: x['metrics']['mem'])['timestamp']
            }
        }
        
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction and magnitude"""
        if len(values) < 2:
            return "insufficient_data"
            
        start_avg = sum(values[:3]) / min(3, len(values))
        end_avg = sum(values[-3:]) / min(3, len(values))
        
        diff = end_avg - start_avg
        if abs(diff) < 1:
            return "stable"
        elif diff > 0:
            return "increasing"
        else:
            return "decreasing"
            
    def _analyze_errors(self) -> Dict[str, Any]:
        """Analyze error patterns and contexts"""
        error_counts = [
            {
                'error': error,
                'count': len(occurrences),
                'modules': list(set(o['module'] for o in occurrences)),
                'first_occurrence': min(o['timestamp'] for o in occurrences),
                'last_occurrence': max(o['timestamp'] for o in occurrences),
                'contexts': [o['context'] for o in occurrences if 'context' in o],
                'frequency': len(occurrences) / len(set(o['timestamp'].split()[0] for o in occurrences))  # errors per day
            }
            for error, occurrences in self.error_patterns.items()
        ]
        
        error_counts.sort(key=lambda x: x['count'], reverse=True)
        
        return {
            'total_errors': sum(len(occurrences) for occurrences in self.error_patterns.values()),
            'most_common_errors': error_counts[:5],
            'error_frequency_by_module': {
                module: sum(1 for e in self.error_patterns.values() for o in e if o['module'] == module)
                for module in self.stats.keys()
            }
        }
        
    def _analyze_api_usage(self) -> Dict[str, Any]:
        """Analyze API usage patterns"""
        api_stats = {}
        
        for module, calls in self.api_calls.items():
            if calls:
                timestamps = [c['timestamp'] for c in calls]
                api_stats[module] = {
                    'total_calls': len(calls),
                    'first_call': min(timestamps),
                    'last_call': max(timestamps),
                    'calls_per_hour': len(calls) / max(1, (datetime.strptime(max(timestamps), '%Y-%m-%d %H:%M:%S') - 
                                                         datetime.strptime(min(timestamps), '%Y-%m-%d %H:%M:%S')).total_seconds() / 3600)
                }
                
        return api_stats
        
    def _analyze_user_interactions(self) -> Dict[str, Any]:
        """Analyze user interaction patterns"""
        interaction_stats = {}
        
        for module, interactions in self.user_interactions.items():
            if interactions:
                timestamps = [i['timestamp'] for i in interactions]
                interaction_stats[module] = {
                    'total_interactions': len(interactions),
                    'first_interaction': min(timestamps),
                    'last_interaction': max(timestamps),
                    'interactions_per_hour': len(interactions) / max(1, (datetime.strptime(max(timestamps), '%Y-%m-%d %H:%M:%S') - 
                                                                       datetime.strptime(min(timestamps), '%Y-%m-%d %H:%M:%S')).total_seconds() / 3600)
                }
                
        return interaction_stats

# Example usage
if __name__ == "__main__":
    analyzer = LogAnalyzer()
    try:
        # Analyze last 7 days of logs
        report = analyzer.analyze_logs(days=7)
        
        print("\nLog Analysis Report:")
        print(f"\nSummary:")
        print(f"- Total Modules: {report['summary']['total_modules']}")
        print(f"- Total Log Entries: {report['summary']['total_log_entries']}")
        print(f"- Total Errors: {report['summary']['total_errors']}")
        print(f"- Total API Calls: {report['summary']['total_api_calls']}")
        print(f"- Total User Interactions: {report['summary']['total_user_interactions']}")
        
        print("\nSystem Performance Trends:")
        if report.get('system_performance', {}).get('overall_trends'):
            trends = report['system_performance']['overall_trends']
            print(f"- CPU Usage Trend: {trends['cpu_trend']}")
            print(f"- Memory Usage Trend: {trends['memory_trend']}")
        
        print("\nMost Common Errors:")
        for error in report['error_analysis']['most_common_errors']:
            print(f"\n- Error: {error['error']}")
            print(f"  Count: {error['count']}")
            print(f"  Frequency: {error['frequency']:.2f} per day")
            print(f"  Modules: {', '.join(error['modules'])}")
            print(f"  First Occurrence: {error['first_occurrence']}")
            print(f"  Last Occurrence: {error['last_occurrence']}")
            
        print("\nAPI Usage by Module:")
        for module, stats in report.get('api_usage', {}).items():
            print(f"\n{module}:")
            print(f"  Total Calls: {stats['total_calls']}")
            print(f"  Calls per Hour: {stats['calls_per_hour']:.2f}")
            
        print("\nUser Interaction Analysis:")
        for module, stats in report.get('user_interaction_analysis', {}).items():
            print(f"\n{module}:")
            print(f"  Total Interactions: {stats['total_interactions']}")
            print(f"  Interactions per Hour: {stats['interactions_per_hour']:.2f}")
            
    except Exception as e:
        print(f"Error analyzing logs: {e}")
        traceback.print_exc() 