from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    HOST: str = Field(description="the host of the application", env="HOST", default="localhost")
    PORT: str = Field(description="the port of the application", env="PORT", default="8000")

settings = Settings()