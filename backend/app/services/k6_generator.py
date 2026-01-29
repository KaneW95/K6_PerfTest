"""K6 script generator service."""
import json
import os
from typing import Optional, List, Dict, Any
from datetime import datetime

from ..config import settings


class K6ScriptGenerator:
    """Generate K6 test scripts from configuration."""
    
    def __init__(self):
        self.scripts_dir = settings.SCRIPTS_DIR
    
    def generate(
        self,
        name: str,
        url: str,
        method: str = "GET",
        headers: Optional[List[Dict[str, str]]] = None,
        body: Optional[str] = None,
        load_category: str = "vus",
        load_sub_mode: str = "simple",
        vus: int = 1,
        duration: str = "30s",
        stages: Optional[List[Dict[str, Any]]] = None,
        rps: int = 100,
        pre_allocated_vus: int = 10,
        max_vus: int = 100,
        rps_stages: Optional[List[Dict[str, Any]]] = None,
        thresholds: Optional[List[Dict[str, str]]] = None,
        stop_on_failure: bool = False,
        data_file: Optional[str] = None,
    ) -> str:
        """
        Generate K6 script and return the file path.
        
        Args:
            name: Test name
            url: Request URL
            method: HTTP method
            headers: Request headers (list of {key, value})
            body: Request body
            load_category: 'vus' or 'rps'
            load_sub_mode: 'simple' or 'stages'
            vus: Number of virtual users (vus simple mode)
            duration: Test duration
            stages: VU stage configuration (vus stages mode)
            rps: Requests per second (rps simple mode)
            pre_allocated_vus: Pre-allocated VUs (rps modes)
            max_vus: Maximum VUs (rps modes)
            rps_stages: RPS stage configuration (rps stages mode)
            thresholds: Threshold configuration
            
        Returns:
            Path to generated script file
        """
        script_content = self._build_script(
            url=url,
            method=method,
            headers=headers,
            body=body,
            load_category=load_category,
            load_sub_mode=load_sub_mode,
            vus=vus,
            duration=duration,
            stages=stages,
            rps=rps,
            pre_allocated_vus=pre_allocated_vus,
            max_vus=max_vus,
            rps_stages=rps_stages,
            thresholds=thresholds,
            stop_on_failure=stop_on_failure,
            data_file=data_file,
        )
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = "".join(c if c.isalnum() else "_" for c in name)
        filename = f"{safe_name}_{timestamp}.js"
        filepath = os.path.join(self.scripts_dir, filename)
        
        # Write script to file
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(script_content)
        
        return filepath
    
    def generate_preview(
        self,
        url: str,
        method: str = "GET",
        headers: Optional[List[Dict[str, str]]] = None,
        body: Optional[str] = None,
        load_category: str = "vus",
        load_sub_mode: str = "simple",
        vus: int = 1,
        duration: str = "30s",
        stages: Optional[List[Dict[str, Any]]] = None,
        rps: int = 100,
        pre_allocated_vus: int = 10,
        max_vus: int = 100,
        rps_stages: Optional[List[Dict[str, Any]]] = None,
        thresholds: Optional[List[Dict[str, str]]] = None,
        stop_on_failure: bool = False,
        data_file: Optional[str] = None,
    ) -> str:
        """Generate K6 script content without saving to file."""
        return self._build_script(
            url=url,
            method=method,
            headers=headers,
            body=body,
            load_category=load_category,
            load_sub_mode=load_sub_mode,
            vus=vus,
            duration=duration,
            stages=stages,
            rps=rps,
            pre_allocated_vus=pre_allocated_vus,
            max_vus=max_vus,
            rps_stages=rps_stages,
            thresholds=thresholds,
            stop_on_failure=stop_on_failure,
            data_file=data_file,
        )
    
    def _build_script(
        self,
        url: str,
        method: str,
        headers: Optional[List[Dict[str, str]]],
        body: Optional[str],
        load_category: str,
        load_sub_mode: str,
        vus: int,
        duration: str,
        stages: Optional[List[Dict[str, Any]]],
        rps: int,
        pre_allocated_vus: int,
        max_vus: int,
        rps_stages: Optional[List[Dict[str, Any]]],
        thresholds: Optional[List[Dict[str, str]]],
        stop_on_failure: bool = False,
        data_file: Optional[str] = None,
    ) -> str:
        """Build K6 script content."""
        
        # Build options based on two-level load mode
        options_parts = []
        
        if load_category == "vus":
            if load_sub_mode == "stages" and stages:
                # VU stages mode
                stages_json = json.dumps(stages, indent=4)
                options_parts.append(f"  stages: {stages_json}")
            else:
                # VU simple mode
                options_parts.append(f"  vus: {vus}")
                options_parts.append(f'  duration: "{duration}"')
        else:
            # RPS mode
            if load_sub_mode == "stages" and rps_stages:
                # RPS stages mode - use ramping-arrival-rate executor
                scenario = {
                    "ramping_rps": {
                        "executor": "ramping-arrival-rate",
                        "startRate": 0,
                        "timeUnit": "1s",
                        "preAllocatedVUs": pre_allocated_vus,
                        "maxVUs": max_vus,
                        "stages": rps_stages,
                    }
                }
                scenarios_json = json.dumps(scenario, indent=4)
                options_parts.append(f"  scenarios: {scenarios_json}")
            else:
                # RPS simple mode - use constant-arrival-rate executor
                scenario = {
                    "constant_rps": {
                        "executor": "constant-arrival-rate",
                        "rate": rps,
                        "timeUnit": "1s",
                        "duration": duration,
                        "preAllocatedVUs": pre_allocated_vus,
                        "maxVUs": max_vus,
                    }
                }
                scenarios_json = json.dumps(scenario, indent=4)
                options_parts.append(f"  scenarios: {scenarios_json}")
        
        # Build thresholds
        if thresholds:
            thresholds_dict = {}
            for t in thresholds:
                metric = t.get("metric", "")
                condition = t.get("condition", "")
                if metric and condition:
                    if metric not in thresholds_dict:
                        thresholds_dict[metric] = []
                    thresholds_dict[metric].append(condition)
            if thresholds_dict:
                thresholds_json = json.dumps(thresholds_dict, indent=4)
                options_parts.append(f"  thresholds: {thresholds_json}")
        
        options_str = ",\n".join(options_parts)
        
        # Build headers
        headers_dict = {}
        if headers:
            for h in headers:
                key = h.get("key", "")
                value = h.get("value", "")
                if key:
                    headers_dict[key] = value
        
        headers_json = json.dumps(headers_dict, indent=6) if headers_dict else "{}"
        
        # Build request
        method_lower = method.lower()
        
        if method_lower in ["post", "put", "patch"] and body:
            # Escape special characters for JS template literal
            body_escaped = body.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")
            
            # If data file is provided, replace {{var}} with ${item.var}
            if data_file:
                import re
                # Use non-greedy match to handle multiple variables in one line
                # Support both standard {{var}} and URL-encoded %7B%7Bvar%7D%7D
                def replace_match(match):
                    var_name = match.group(1).strip()
                    return f'${{item.{var_name}}}'
                
                # Match either {{...}} or %7B%7B...%7D%7D
                body_escaped = re.sub(r'(?:\{\{|%7B%7B)(.+?)(?:\}\}|%7D%7D)', replace_match, body_escaped)
            
            request_code = f'''const payload = `{body_escaped}`;
  
  // Log request body for the first 5 iterations for debugging
  if (exec.scenario.iterationInTest < 5) {{
      console.log(`[Iter ${{exec.scenario.iterationInTest}}] Request Body: ${{payload}}`);
  }}

  const res = http.{method_lower}(url, payload, params);'''
        else:
            if method_lower == "get":
                request_code = "const res = http.get(url, params);"
            elif method_lower == "delete":
                request_code = "const res = http.del(url, null, params);"
            else:
                request_code = f"const res = http.{method_lower}(url, null, params);"
        
        # Prepare imports
        imports = [
            "import http from 'k6/http';",
            "import { check, sleep } from 'k6';",
            "import { Rate, Trend } from 'k6/metrics';"
        ]
        
        # Add imports for data driven test
        data_loading_code = ""
        item_retrieval_code = ""
        
        if data_file:
            imports.append("import { SharedArray } from 'k6/data';")
            imports.append("import papaparse from 'https://jslib.k6.io/papaparse/5.1.1/index.js';")
            
            # Escape path for JS string
            data_file_js = data_file.replace("\\", "\\\\")
            
            data_loading_code = f'''
// Load CSV data
const data = new SharedArray('data', function () {{
  return papaparse.parse(open('{data_file_js}'), {{ header: true }}).data;
}});
'''
            item_retrieval_code = """
  // Get data row for current iteration (round-robin)
  const item = data[exec.scenario.iterationInTest % data.length];
"""

        if stop_on_failure or data_file:
            imports.append("import exec from 'k6/execution';")
        
        imports_str = "\n".join(imports)
        
        # Prepare abort logic
        abort_logic = ""
        if stop_on_failure:
            abort_logic = "exec.test.abort('Aborting test due to failure (Status ${res.status})');"

        # Build complete script
        script = f'''{imports_str}

// Custom metrics
const errorRate = new Rate('errors');
const responseTime = new Trend('response_time');
{data_loading_code}
export const options = {{
{options_str}
}};

export default function () {{
  const url = '{url}';
  {item_retrieval_code}
  const params = {{
    headers: {headers_json},
  }};
  
  {request_code}
  
  // Record metrics
  responseTime.add(res.timings.duration);
  
  // Check response
  const checkResult = check(res, {{
    'status is 2xx': (r) => r.status >= 200 && r.status < 300,
    'response time < 2000ms': (r) => r.timings.duration < 2000,
  }});
  
  errorRate.add(!checkResult);
  
  // Log error details if failed
  if (res.status >= 400 || res.status === 0) {{
    console.error(`[Request Error] Status: ${{res.status}}, URL: ${{url}}`);
    console.error(`[Request Error] Response Body: ${{res.body}}`);
    {abort_logic}
  }}
  
  sleep(1);
}}

export function handleSummary(data) {{
  return {{
    'stdout': JSON.stringify(data, null, 2),
  }};
}}
'''
        return script
