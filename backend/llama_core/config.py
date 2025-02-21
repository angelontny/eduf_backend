from functools import lru_cache
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    hugging_face_token: str
    cohere_key: str
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()
