"""Pydantic schemas for test configuration."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class StageConfig(BaseModel):
    """Stage configuration for ramping."""
    duration: str = Field(..., description="阶段持续时间，如 '30s', '1m'")
    target: int = Field(..., description="目标VU数")


class ThresholdConfig(BaseModel):
    """Threshold configuration."""
    metric: str = Field(..., description="指标名称，如 'http_req_duration'")
    condition: str = Field(..., description="条件，如 'p(95)<500'")


class HeaderItem(BaseModel):
    """Header key-value pair."""
    key: str
    value: str


class TestConfigBase(BaseModel):
    """Base test configuration schema."""
    name: str = Field(..., min_length=1, max_length=100, description="配置名称")
    url: str = Field(..., min_length=1, max_length=500, description="请求URL")
    method: str = Field(default="GET", description="HTTP方法")
    headers: Optional[List[HeaderItem]] = Field(default=None, description="请求头列表")
    body: Optional[str] = Field(default=None, description="请求体")
    vus: int = Field(default=1, ge=1, le=1000, description="虚拟用户数")
    duration: str = Field(default="30s", description="持续时间")
    stages: Optional[List[StageConfig]] = Field(default=None, description="阶段配置")
    thresholds: Optional[List[ThresholdConfig]] = Field(default=None, description="阈值配置")


class TestConfigCreate(TestConfigBase):
    """Schema for creating test configuration."""
    pass


class TestConfigUpdate(BaseModel):
    """Schema for updating test configuration."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    url: Optional[str] = Field(None, min_length=1, max_length=500)
    method: Optional[str] = None
    headers: Optional[List[HeaderItem]] = None
    body: Optional[str] = None
    vus: Optional[int] = Field(None, ge=1, le=1000)
    duration: Optional[str] = None
    stages: Optional[List[StageConfig]] = None
    thresholds: Optional[List[ThresholdConfig]] = None


class TestConfigResponse(TestConfigBase):
    """Schema for test configuration response."""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TestExecutionCreate(BaseModel):
    """Schema for creating test execution."""
    config_id: int


class TestExecutionResponse(BaseModel):
    """Schema for test execution response."""
    id: int
    config_id: int
    status: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    result_summary: Optional[Dict[str, Any]] = None
    result_file: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class RunTestRequest(BaseModel):
    """Schema for running a test directly without saving config."""
    name: str = Field(default="Quick Test", description="测试名称")
    url: str = Field(..., description="请求URL")
    method: str = Field(default="GET", description="HTTP方法")
    headers: Optional[List[HeaderItem]] = Field(default=None, description="请求头")
    body: Optional[str] = Field(default=None, description="请求体")
    vus: int = Field(default=1, ge=1, le=1000, description="虚拟用户数")
    duration: str = Field(default="30s", description="持续时间")
    stages: Optional[List[StageConfig]] = Field(default=None, description="阶段配置")
    thresholds: Optional[List[ThresholdConfig]] = Field(default=None, description="阈值配置")
