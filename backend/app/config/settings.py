"""
应用配置模块

包含应用的所有配置项
"""
import os
from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """应用配置类"""
    # 基本设置
    APP_NAME: str = "AI答题系统"
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    
    # 服务器设置
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # CORS设置
    CORS_ORIGINS: List[str] = os.getenv("CORS_ORIGINS", "*").split(",")
    
    # 数据库设置
    DATABASE_URL: str = os.getenv("DATABASE_URL", "mongodb://localhost:27017/ai_quiz")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # LLM设置
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    LLM_API_URL: str = os.getenv("LLM_API_URL", "https://api.openai.com/v1")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4-turbo")
    
    # 其他API密钥
    YUNWU_DEFAULT_API_KEY: str = os.getenv("YUNWU_DEFAULT_API_KEY", "")
    YUNWU_AZ_API_KEY: str = os.getenv("YUNWU_AZ_API_KEY", "")
    BOCHA_API_KEY: str = os.getenv("BOCHA_API_KEY", "")
    FIRECRAWL_API_KEY: str = os.getenv("FIRECRAWL_API_KEY", "")
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    
    # 答题设置
    DEFAULT_QUIZ_QUESTIONS: int = int(os.getenv("DEFAULT_QUIZ_QUESTIONS", "3"))
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

# 创建全局设置实例
settings = Settings()

if __name__ == "__main__":
    # 用于调试配置
    import json
    print(json.dumps(settings.dict(), indent=4, ensure_ascii=False)) 