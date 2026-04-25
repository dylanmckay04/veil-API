from pathlib import Path
from pydantic import ConfigDict
from pydantic_settings import BaseSettings

_env_file = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    
    model_config = ConfigDict(env_file = str(_env_file), extra="ignore")

settings = Settings()
