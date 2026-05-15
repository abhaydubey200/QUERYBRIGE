import os
import sys
from loguru import logger
from pydantic import ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

class QueryBridgeSettings(BaseSettings):
    """
    Validation schema for QueryBridge environment variables.
    Enforces production-grade requirements on startup.
    """
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    # Infrastructure
    DATABASE_URL: str
    REDIS_URL: str
    
    # Security
    JWT_SECRET: str
    ENCRYPTION_KEY: str
    
    # AI
    NVIDIA_API_KEY: str
    
    # Runtime
    ENV: str = "production"
    LOG_LEVEL: str = "info"

def validate_environment():
    """
    Validates all required environment variables.
    Blocks startup with clear diagnostics if validation fails.
    """
    logger.info("Initializing Enterprise Environment Validation...")
    
    try:
        settings = QueryBridgeSettings()
        
        # Check for placeholder values in production
        if settings.ENV == "production":
            placeholders = ["replace-this", "your-", "password123"]
            for field, value in settings.model_dump().items():
                if any(p in str(value).lower() for p in placeholders):
                    logger.warning(f"SECURITY ALERT: Default/Placeholder value detected for {field}")
        
        logger.info("Environment validation successful.")
        return settings
        
    except ValidationError as e:
        logger.error("FATAL: Environment Validation Failed")
        for error in e.errors():
            loc = " -> ".join(str(l) for l in error['loc'])
            logger.error(f"  [MISSING/INVALID] {loc}: {error['msg']}")
        
        print("\n" + "="*50)
        print("QUERYBRIDGE STARTUP BLOCKED: INVALID ENVIRONMENT")
        print("Please check your .env file against .env.example")
        print("="*50 + "\n")
        sys.exit(1)

if __name__ == "__main__":
    validate_environment()
