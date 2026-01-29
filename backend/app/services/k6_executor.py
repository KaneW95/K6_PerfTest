"""K6 executor service."""
import asyncio
import json
import os
import subprocess
from datetime import datetime
from typing import Optional, Callable, Dict, Any

from ..config import settings


class K6Executor:
    """Execute K6 tests and stream output."""
    
    def __init__(self):
        self.k6_path = settings.K6_PATH
        self.results_dir = settings.RESULTS_DIR
        self.current_process: Optional[subprocess.Popen] = None
    
    async def run(
        self,
        script_path: str,
        execution_id: int,
        on_log: Optional[Callable[[str], None]] = None,
        on_complete: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_error: Optional[Callable[[str], None]] = None,
    ) -> Dict[str, Any]:
        """
        Run K6 test script.
        
        Args:
            script_path: Path to K6 script file
            execution_id: Execution ID for result file naming
            on_log: Callback for log messages
            on_complete: Callback when test completes
            on_error: Callback for errors
            
        Returns:
            Test result summary
        """
        # Prepare result file path
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_file = os.path.join(
            self.results_dir, 
            f"result_{execution_id}_{timestamp}.json"
        )
        
        # Build command with --no-color for cleaner output
        # Use --verbose for more detailed progress output
        cmd = [
            self.k6_path,
            "run",
            "--out", f"json={result_file}",
            "--no-color",
            script_path
        ]
        
        logs = []
        result_summary = None
        
        try:
            # Start K6 process with separate stdout and stderr
            self.current_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                encoding='utf-8',
                errors='replace'
            )
            
            if on_log:
                await on_log(f"[INFO] Starting K6 test: {os.path.basename(script_path)}")
                await on_log(f"[INFO] Command: {' '.join(cmd)}")
            
            # Read stdout and stderr concurrently
            import threading
            import queue
            
            output_queue = queue.Queue()
            
            def read_stream(stream, stream_name):
                """Read from a stream and put lines into the queue."""
                try:
                    for line in iter(stream.readline, ''):
                        if line:
                            # Clean up progress lines (remove carriage returns)
                            cleaned_line = line.rstrip('\r\n')
                            if cleaned_line:
                                output_queue.put((stream_name, cleaned_line))
                except Exception as e:
                    output_queue.put(('error', str(e)))
                finally:
                    output_queue.put((stream_name, None))  # Signal end
            
            # Start reader threads
            stdout_thread = threading.Thread(
                target=read_stream, 
                args=(self.current_process.stdout, 'stdout')
            )
            stderr_thread = threading.Thread(
                target=read_stream, 
                args=(self.current_process.stderr, 'stderr')
            )
            
            stdout_thread.daemon = True
            stderr_thread.daemon = True
            stdout_thread.start()
            stderr_thread.start()
            
            # Process output from both streams
            capturing_summary = False
            summary_lines = []
            streams_closed = 0
            last_progress_time = datetime.now()
            
            while streams_closed < 2:
                try:
                    stream_name, line = output_queue.get(timeout=0.1)
                    
                    if line is None:
                        streams_closed += 1
                        continue
                    
                    logs.append(line)
                    
                    # Check if this is a progress line (contains VUs, iterations, etc.)
                    is_progress = any(keyword in line for keyword in [
                        'running', 'VUs', 'iterations', 'complete', 
                        'default', 'iters/s', 'reqs/s', '%'
                    ])
                    
                    # Check for JSON summary output
                    if line.strip().startswith('{'):
                        capturing_summary = True
                    
                    if capturing_summary:
                        summary_lines.append(line)
                    
                    if on_log:
                        # Add progress indicator for progress lines
                        if is_progress and 'running' in line.lower():
                            await on_log(f"[PROGRESS] {line}")
                        else:
                            await on_log(line)
                    
                except queue.Empty:
                    # Check if process has ended
                    if self.current_process.poll() is not None:
                        # Give threads a moment to finish
                        await asyncio.sleep(0.1)
                        if output_queue.empty():
                            break
                    continue
                
                # Small yield for async cooperation
                await asyncio.sleep(0.01)
            
            # Wait for threads to finish
            stdout_thread.join(timeout=1)
            stderr_thread.join(timeout=1)
            
            # Get return code
            return_code = self.current_process.wait()
            
            # Parse summary if available
            if summary_lines:
                try:
                    summary_text = "\n".join(summary_lines)
                    result_summary = json.loads(summary_text)
                except json.JSONDecodeError:
                    pass
            
            # Try to parse result file if summary not captured
            if not result_summary and os.path.exists(result_file):
                result_summary = self._parse_result_file(result_file)
            
            # Extract Max RPS from logs (often more accurate/peak than avg per second)
            if result_summary and logs:
                try:
                    import re
                    max_log_rps = 0
                    for log in logs:
                        # Match patterns like: " 398.5/s" or " 398/s"
                        # Be careful to avoid false positives, usually typically at end of line or preceded by space
                        # K6 log format: "default   [  22% ] 050/100 VUs  1m02.3s/5m00s  49.2/s"
                        matches = re.findall(r'\s(\d+\.?\d*)/s', log)
                        if matches:
                            for m in matches:
                                try:
                                    val = float(m)
                                    # Filter out unrealistic values if needed, but K6 is usually right
                                    if val > max_log_rps:
                                        max_log_rps = val
                                except ValueError:
                                    pass
                    
                    if max_log_rps > result_summary.get("rps_max", 0):
                        result_summary["rps_max"] = max_log_rps
                        # Also update "rps" (avg) if max is significantly higher? No, keep avg as avg.
                except Exception as e:
                    print(f"Error parsing RPS from logs: {e}")

            if return_code == 0:
                if on_log:
                    await on_log("[INFO] Test completed successfully")
                if on_complete and result_summary:
                    on_complete(result_summary)
            else:
                error_msg = f"K6 exited with code {return_code}"
                if on_log:
                    await on_log(f"[ERROR] {error_msg}")
                if on_error:
                    on_error(error_msg)
            
            return {
                "success": return_code == 0,
                "return_code": return_code,
                "result_file": result_file if os.path.exists(result_file) else None,
                "summary": result_summary,
                "logs": logs,
            }
            
        except Exception as e:
            error_msg = f"Error running K6: {str(e)}"
            if on_log:
                await on_log(f"[ERROR] {error_msg}")
            if on_error:
                on_error(error_msg)
            
            return {
                "success": False,
                "error": error_msg,
                "logs": logs,
            }
        finally:
            self.current_process = None
    
    def stop(self):
        """Stop currently running K6 process."""
        if self.current_process:
            self.current_process.terminate()
            try:
                self.current_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.current_process.kill()
            self.current_process = None
    
    def _parse_result_file(self, result_file: str) -> Optional[Dict[str, Any]]:
        """Parse K6 JSON output file to extract metrics."""
        try:
            metrics = {
                "http_reqs": 0,
                "http_req_duration": {"avg": 0, "min": 0, "max": 0, "p90": 0, "p95": 0},
                "http_req_failed": 0,
                "iterations": 0,
                "vus": 0,
                "vus_max": 0,
                "duration": 0,
                "rps": 0,
                "rps_max": 0,
            }
            
            durations = []
            timestamps = []  # Track timestamps for RPS calculation
            rps_by_second = {}  # Count requests per second
            
            with open(result_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        metric_type = data.get("type")
                        metric_name = data.get("metric")
                        
                        if metric_type == "Point":
                            value = data.get("data", {}).get("value", 0)
                            timestamp = data.get("data", {}).get("time", "")
                            
                            if metric_name == "http_reqs":
                                metrics["http_reqs"] += int(value)
                                # Extract second for RPS calculation
                                if timestamp:
                                    try:
                                        # Parse ISO timestamp and get second
                                        ts_str = timestamp[:19]  # Get YYYY-MM-DDTHH:MM:SS
                                        if ts_str not in rps_by_second:
                                            rps_by_second[ts_str] = 0
                                        rps_by_second[ts_str] += int(value)
                                        timestamps.append(timestamp)
                                    except:
                                        pass
                            elif metric_name == "http_req_duration":
                                durations.append(value)
                            elif metric_name == "http_req_failed":
                                if value:
                                    metrics["http_req_failed"] += int(value)
                            elif metric_name == "iterations":
                                metrics["iterations"] += int(value)
                            elif metric_name == "vus":
                                metrics["vus"] = max(metrics["vus"], int(value))
                            elif metric_name == "vus_max":
                                metrics["vus_max"] = max(metrics["vus_max"], int(value))
                                
                    except json.JSONDecodeError:
                        continue

            # Calculate actual test duration from timestamps
            if timestamps:
                try:
                    timestamps.sort()
                    start_time = datetime.fromisoformat(timestamps[0].replace('Z', '+00:00'))
                    end_time = datetime.fromisoformat(timestamps[-1].replace('Z', '+00:00'))
                    duration_seconds = (end_time - start_time).total_seconds()
                    # Ensure duration is at least 1 second to avoid division by zero
                    metrics["duration"] = max(duration_seconds * 1000, 1000)
                except Exception as e:
                    print(f"Error calculating duration: {e}")
                    pass
            
            # Calculate duration statistics
            if durations:
                durations.sort()
                n = len(durations)
                metrics["http_req_duration"] = {
                    "avg": sum(durations) / n,
                    "min": durations[0],
                    "max": durations[-1],
                    "p90": durations[int(n * 0.9)] if n > 0 else 0,
                    "p95": durations[int(n * 0.95)] if n > 0 else 0,
                }
            
            # Calculate RPS metrics
            if rps_by_second:
                rps_values = list(rps_by_second.values())
                metrics["rps"] = sum(rps_values) / len(rps_values) if rps_values else 0
                metrics["rps_max"] = max(rps_values) if rps_values else 0
                metrics["duration"] = len(rps_values) * 1000  # Duration in ms
            
            # Try to extract Max RPS from logs (often more accurate/peak than avg per second)
            log_max_rps = 0
            import re
            rps_pattern = re.compile(r'(\d+\.?\d*)/s')
            
            # We don't have access to 'logs' here directly unless passed or read?
            # logs are in self.run, not passed to _parse_result_file.
            # So return metrics, and update in run() method.
            
            return metrics
            
        except Exception as e:
            print(f"Error parsing result file: {e}")
            return None
