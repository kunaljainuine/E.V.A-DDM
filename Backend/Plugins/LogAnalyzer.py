import logging
from datetime import datetime
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Any
from Backend.PluginSystem import Plugin

logger = logging.getLogger("LogAnalyzer")

class LogAnalyzer(Plugin):
    """Plugin for analyzing log files and generating reports"""
    
    def __init__(self):
        self.log_stats = defaultdict(int)
        self.error_patterns = defaultdict(list)
        self.performance_metrics = defaultdict(list)
        
    def initialize(self) -> None:
        """Initialize the log analyzer"""
        logger.info("Initializing Log Analyzer plugin")
        self.log_directory = Path("Logs")
        if not self.log_directory.exists():
            self.log_directory.mkdir(parents=True)
            
    def execute(self, *args, **kwargs) -> Dict[str, Any]:
        """
        Analyze log files and generate statistics
        
        Returns:
            Dict[str, Any]: Analysis results including error patterns and performance metrics
        """
        try:
            logger.info("Starting log analysis")
            self._analyze_logs()
            return self._generate_report()
            
        except Exception as e:
            logger.error(f"Error during log analysis: {e}", exc_info=True)
            raise
            
    def cleanup(self) -> None:
        """Cleanup resources"""
        logger.info("Cleaning up Log Analyzer plugin")
        self.log_stats.clear()
        self.error_patterns.clear()
        self.performance_metrics.clear()
        
    def _analyze_logs(self) -> None:
        """Analyze all log files in the log directory"""
        try:
            for log_file in self.log_directory.glob("*.log"):
                logger.debug(f"Analyzing log file: {log_file}")
                self._process_log_file(log_file)
                
        except Exception as e:
            logger.error(f"Error analyzing logs: {e}", exc_info=True)
            raise
            
    def _process_log_file(self, log_file: Path) -> None:
        """
        Process a single log file
        
        Args:
            log_file (Path): Path to the log file
        """
        try:
            with open(log_file, 'r') as f:
                for line in f:
                    self._process_log_line(line)
                    
        except Exception as e:
            logger.error(f"Error processing log file {log_file}: {e}", exc_info=True)
            
    def _process_log_line(self, line: str) -> None:
        """
        Process a single log line
        
        Args:
            line (str): Log line to process
        """
        try:
            # Count log levels
            for level in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
                if f"] {level} " in line:
                    self.log_stats[level] += 1
                    
            # Track errors and their patterns
            if '] ERROR ' in line:
                error_msg = line.split('] ERROR ')[-1].strip()
                self.error_patterns[error_msg].append(datetime.now().isoformat())
                
            # Extract performance metrics (example: response times)
            if 'response_time=' in line:
                try:
                    response_time = float(line.split('response_time=')[-1].split()[0])
                    self.performance_metrics['response_times'].append(response_time)
                except ValueError:
                    pass
                    
        except Exception as e:
            logger.error(f"Error processing log line: {e}", exc_info=True)
            
    def _generate_report(self) -> Dict[str, Any]:
        """
        Generate analysis report
        
        Returns:
            Dict[str, Any]: Report containing analysis results
        """
        try:
            logger.info("Generating analysis report")
            
            # Calculate performance statistics
            response_times = self.performance_metrics.get('response_times', [])
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            
            report = {
                'log_level_distribution': dict(self.log_stats),
                'total_errors': len(self.error_patterns),
                'most_common_errors': sorted(
                    [(error, len(dates)) for error, dates in self.error_patterns.items()],
                    key=lambda x: x[1],
                    reverse=True
                )[:5],
                'performance_metrics': {
                    'average_response_time': avg_response_time,
                    'total_requests': len(response_times)
                }
            }
            
            logger.info("Analysis report generated successfully")
            return report
            
        except Exception as e:
            logger.error(f"Error generating report: {e}", exc_info=True)
            raise

# Example usage:
if __name__ == "__main__":
    analyzer = LogAnalyzer()
    analyzer.initialize()
    try:
        results = analyzer.execute()
        print("Analysis Results:")
        print(f"Log Level Distribution: {results['log_level_distribution']}")
        print(f"Total Errors: {results['total_errors']}")
        print("Most Common Errors:")
        for error, count in results['most_common_errors']:
            print(f"  - {error}: {count} occurrences")
        print(f"Performance Metrics: {results['performance_metrics']}")
    finally:
        analyzer.cleanup() 