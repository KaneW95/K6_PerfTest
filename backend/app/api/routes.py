"""API routes for test configuration and execution."""
import asyncio
import httpx
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import TestConfig, TestExecution
from ..schemas import (
    TestConfigCreate,
    TestConfigUpdate,
    TestConfigResponse,
    TestExecutionResponse,
    RunTestRequest,
)
from ..services import K6ScriptGenerator, K6Executor
from ..websocket import manager

router = APIRouter()


# =============================================================================
# Debug Request Schema
# =============================================================================

class DebugRequest(BaseModel):
    """Schema for debug request."""
    url: str
    method: str = "GET"
    headers: Dict[str, str] = {}
    body: Optional[str] = None


class DebugResponse(BaseModel):
    """Schema for debug response."""
    status: int
    duration: float
    headers: Dict[str, str]
    body: str


# =============================================================================
# Test Configuration CRUD
# =============================================================================

@router.post("/configs", response_model=TestConfigResponse, tags=["Configurations"])
def create_config(config: TestConfigCreate, db: Session = Depends(get_db)):
    """Create a new test configuration."""
    # Convert headers to JSON-serializable format
    headers_data = None
    if config.headers:
        headers_data = [{"key": h.key, "value": h.value} for h in config.headers]
    
    # Convert stages to JSON-serializable format
    stages_data = None
    if config.stages:
        stages_data = [{"duration": s.duration, "target": s.target} for s in config.stages]
    
    # Convert thresholds to JSON-serializable format
    thresholds_data = None
    if config.thresholds:
        thresholds_data = [{"metric": t.metric, "condition": t.condition} for t in config.thresholds]
    
    db_config = TestConfig(
        name=config.name,
        url=config.url,
        method=config.method,
        headers=headers_data,
        body=config.body,
        vus=config.vus,
        duration=config.duration,
        stages=stages_data,
        thresholds=thresholds_data,
    )
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    return db_config


@router.get("/configs", response_model=List[TestConfigResponse], tags=["Configurations"])
def list_configs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all test configurations."""
    configs = db.query(TestConfig).offset(skip).limit(limit).all()
    return configs


@router.get("/configs/{config_id}", response_model=TestConfigResponse, tags=["Configurations"])
def get_config(config_id: int, db: Session = Depends(get_db)):
    """Get a specific test configuration."""
    config = db.query(TestConfig).filter(TestConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")
    return config


@router.put("/configs/{config_id}", response_model=TestConfigResponse, tags=["Configurations"])
def update_config(config_id: int, config: TestConfigUpdate, db: Session = Depends(get_db)):
    """Update a test configuration."""
    db_config = db.query(TestConfig).filter(TestConfig.id == config_id).first()
    if not db_config:
        raise HTTPException(status_code=404, detail="Configuration not found")
    
    update_data = config.model_dump(exclude_unset=True)
    
    # Convert nested objects
    if "headers" in update_data and update_data["headers"] is not None:
        update_data["headers"] = [{"key": h.key, "value": h.value} for h in config.headers]
    if "stages" in update_data and update_data["stages"] is not None:
        update_data["stages"] = [{"duration": s.duration, "target": s.target} for s in config.stages]
    if "thresholds" in update_data and update_data["thresholds"] is not None:
        update_data["thresholds"] = [{"metric": t.metric, "condition": t.condition} for t in config.thresholds]
    
    for key, value in update_data.items():
        setattr(db_config, key, value)
    
    db.commit()
    db.refresh(db_config)
    return db_config


@router.delete("/configs/{config_id}", tags=["Configurations"])
def delete_config(config_id: int, db: Session = Depends(get_db)):
    """Delete a test configuration."""
    db_config = db.query(TestConfig).filter(TestConfig.id == config_id).first()
    if not db_config:
        raise HTTPException(status_code=404, detail="Configuration not found")
    
    db.delete(db_config)
    db.commit()
    return {"message": "Configuration deleted"}


# =============================================================================
# Debug API - For testing requests before load testing
# =============================================================================

@router.post("/debug", response_model=DebugResponse, tags=["Debug"])
async def debug_request(request: DebugRequest):
    """Send a debug request to test the API endpoint."""
    try:
        start_time = datetime.now()
        
        async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
            response = await client.request(
                method=request.method,
                url=request.url,
                headers=request.headers,
                content=request.body if request.body else None,
            )
        
        duration = (datetime.now() - start_time).total_seconds() * 1000
        
        # Convert headers to dict
        response_headers = dict(response.headers)
        
        return DebugResponse(
            status=response.status_code,
            duration=round(duration, 2),
            headers=response_headers,
            body=response.text[:10000],  # Limit response body size
        )
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Request failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


# =============================================================================
# Test Execution
# =============================================================================

@router.get("/executions", response_model=List[TestExecutionResponse], tags=["Executions"])
def list_executions(
    config_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List test executions."""
    query = db.query(TestExecution)
    if config_id:
        query = query.filter(TestExecution.config_id == config_id)
    executions = query.order_by(TestExecution.created_at.desc()).offset(skip).limit(limit).all()
    return executions


@router.get("/executions/{execution_id}", response_model=TestExecutionResponse, tags=["Executions"])
def get_execution(execution_id: int, db: Session = Depends(get_db)):
    """Get a specific test execution."""
    execution = db.query(TestExecution).filter(TestExecution.id == execution_id).first()
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    return execution


# =============================================================================
# WebSocket for Real-time Test Execution
# =============================================================================

@router.websocket("/ws/test")
async def websocket_test_endpoint(websocket: WebSocket, db: Session = Depends(get_db)):
    """WebSocket endpoint for running tests with real-time logs."""
    await manager.connect(websocket)
    
    current_executor = None
    execution_task = None
    
    try:
        while True:
            # Wait for test request
            data = await websocket.receive_json()
            action = data.get("action")
            
            if action == "run":
                # Stop existing test if running
                if current_executor:
                    current_executor.stop()
                
                # Run test in background task
                current_executor = K6Executor()
                execution_task = asyncio.create_task(
                    run_test_via_websocket(websocket, data, db, current_executor)
                )
                
            elif action == "stop":
                if current_executor:
                    current_executor.stop()
                    await manager.send_log(websocket, "[INFO] Received stop command, terminating test...")
                else:
                    await manager.send_message(websocket, {
                        "type": "info",
                        "message": "No test is currently running"
                    })
            else:
                await manager.send_error(websocket, f"Unknown action: {action}")
                
    except WebSocketDisconnect:
        if current_executor:
            current_executor.stop()
        manager.disconnect(websocket)
    except Exception as e:
        if current_executor:
            current_executor.stop()
        await manager.send_error(websocket, str(e))
        manager.disconnect(websocket)


async def run_test_via_websocket(websocket: WebSocket, data: dict, db: Session, executor: K6Executor):
    """Run a test and stream logs via WebSocket."""
    try:
        # Extract test configuration from request
        config_data = data.get("config", {})
        
        # Validate required fields
        if not config_data.get("url"):
            await manager.send_error(websocket, "URL is required")
            return
        
        # Send starting status
        await manager.send_status(websocket, "starting")
        
        # Extract configuration - two-level mode structure
        config_name = config_data.get("name", "Quick Test")
        load_category = config_data.get("loadCategory", "vus")
        load_sub_mode = config_data.get("loadSubMode", "simple")
        
        headers_data = config_data.get("headers", [])
        stages_data = config_data.get("stages", [])
        rps_stages_data = config_data.get("rpsStages", [])
        thresholds_data = config_data.get("thresholds", [])
        
        # Create config record
        db_config = TestConfig(
            name=config_name,
            url=config_data["url"],
            method=config_data.get("method", "GET"),
            headers=headers_data,
            body=config_data.get("body"),
            vus=config_data.get("vus", 1),
            duration=config_data.get("duration", "30s"),
            stages=stages_data if stages_data else None,
            thresholds=thresholds_data if thresholds_data else None,
        )
        db.add(db_config)
        db.commit()
        db.refresh(db_config)
        
        # Create execution record
        execution = TestExecution(
            config_id=db_config.id,
            status="running",
            start_time=datetime.utcnow()
        )
        db.add(execution)
        db.commit()
        db.refresh(execution)
        
        # Send execution info
        await manager.send_message(websocket, {
            "type": "execution_started",
            "execution_id": execution.id,
            "config_id": db_config.id
        })
        
        # Generate K6 script with two-level mode parameters
        generator = K6ScriptGenerator()
        
        script_path = generator.generate(
            name=config_name,
            url=config_data["url"],
            method=config_data.get("method", "GET"),
            headers=headers_data,
            body=config_data.get("body"),
            load_category=load_category,
            load_sub_mode=load_sub_mode,
            vus=config_data.get("vus", 1),
            duration=config_data.get("duration", "30s"),
            stages=stages_data if stages_data else None,
            rps=config_data.get("rps", 100),
            pre_allocated_vus=config_data.get("preAllocatedVUs", 10),
            max_vus=config_data.get("maxVUs", 100),
            rps_stages=rps_stages_data if rps_stages_data else None,
            thresholds=thresholds_data if thresholds_data else None,
            stop_on_failure=config_data.get("stopOnFailure", False),
        )
        
        await manager.send_log(websocket, f"Generated script: {script_path}")
        await manager.send_status(websocket, "running")
        
        # Run K6 test
        # Executor passed from endpoint
        # executor = K6Executor()
        
        async def on_log(log: str):
            await manager.send_log(websocket, log)
        
        result = await executor.run(
            script_path=script_path,
            execution_id=execution.id,
            on_log=on_log,
        )
        
        # Update execution record
        execution.end_time = datetime.utcnow()
        execution.status = "completed" if result.get("success") else "failed"
        execution.result_summary = result.get("summary")
        execution.result_file = result.get("result_file")
        logs_text = "\n".join(result.get("logs", []))
        # Truncate to 5MB (Keep tail)
        max_log_size = 5 * 1024 * 1024
        if len(logs_text) > max_log_size:
             logs_text = "...[Logs Truncated due to size]...\n" + logs_text[-max_log_size:]
        execution.logs = logs_text
        db.commit()
        
        # Send completion status and result
        await manager.send_status(websocket, execution.status)
        await manager.send_result(websocket, {
            "execution_id": execution.id,
            "success": result.get("success", False),
            "summary": result.get("summary"),
        })
        
    except Exception as e:
        await manager.send_error(websocket, f"Error running test: {str(e)}")
        await manager.send_status(websocket, "failed")


