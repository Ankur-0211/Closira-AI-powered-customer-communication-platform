

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Closira Enquiry Backend"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # SQLite database URL — file-based for persistence
    DATABASE_URL: str = "sqlite:///./closira.db"

    # Log file directory (relative to project root)
    LOG_DIR: str = "app/logs"
    LOG_FILE: str = "app/logs/app.log"

    class Config:
        env_file = ".env"
        extra = "ignore"



settings = Settings()