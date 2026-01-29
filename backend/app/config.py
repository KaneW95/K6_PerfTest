"""Application configuration."""
import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Application settings."""
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "mysql+pymysql://root:123456@localhost:3306/k6_perftest"
    )
    
    # K6
    K6_PATH: str = os.getenv("K6_PATH", "k6")
    
    # Server
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    
    # Paths
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    SCRIPTS_DIR: str = os.path.join(BASE_DIR, "scripts")
    RESULTS_DIR: str = os.path.join(BASE_DIR, "results")
    
    class Config:
        env_file = ".env"


settings = Settings()

# Ensure directories exist
os.makedirs(settings.SCRIPTS_DIR, exist_ok=True)
os.makedirs(settings.RESULTS_DIR, exist_ok=True)
