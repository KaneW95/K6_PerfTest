"""Database models for test configuration and execution."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship

from ..database import Base


class TestConfig(Base):
    """Test configuration model."""
    
    __tablename__ = "test_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment="配置名称")
    url = Column(String(500), nullable=False, comment="请求URL")
    method = Column(String(10), nullable=False, default="GET", comment="HTTP方法")
    headers = Column(JSON, nullable=True, comment="请求头")
    body = Column(Text, nullable=True, comment="请求体")
    vus = Column(Integer, nullable=False, default=1, comment="虚拟用户数")
    duration = Column(String(20), nullable=False, default="30s", comment="持续时间")
    stages = Column(JSON, nullable=True, comment="阶段配置")
    thresholds = Column(JSON, nullable=True, comment="阈值配置")
    data_file = Column(String(255), nullable=True, comment="数据文件路径")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    
    # Relationships
    executions = relationship("TestExecution", back_populates="config")


class TestExecution(Base):
    """Test execution record model."""
    
    __tablename__ = "test_executions"
    
    id = Column(Integer, primary_key=True, index=True)
    config_id = Column(Integer, ForeignKey("test_configs.id"), nullable=False, comment="关联配置ID")
    status = Column(String(20), nullable=False, default="pending", comment="状态")
    start_time = Column(DateTime, nullable=True, comment="开始时间")
    end_time = Column(DateTime, nullable=True, comment="结束时间")
    result_summary = Column(JSON, nullable=True, comment="结果摘要")
    result_file = Column(String(255), nullable=True, comment="结果文件路径")
    from sqlalchemy.dialects.mysql import LONGTEXT
    logs = Column(LONGTEXT, nullable=True, comment="执行日志")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    
    # Relationships
    config = relationship("TestConfig", back_populates="executions")
