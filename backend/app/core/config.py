from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+asyncpg://media_user:media_password@localhost:5432/media_processing"
    database_url_sync: str = "postgresql://media_user:media_password@localhost:5432/media_processing"
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"
    upload_dir: str = "./uploads"
    max_upload_size_mb: int = 10
    allowed_extensions: str = "jpg,jpeg,png,webp"
    cors_origins: str = "http://localhost:5173,http://localhost:3000,https://media-processing-frontend-9zoc.onrender.com"
    log_level: str = "INFO"
    secret_key: str = "dev-secret-key"

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    @property
    def allowed_extension_set(self) -> set[str]:
        return {ext.strip().lower() for ext in self.allowed_extensions.split(",") if ext.strip()}

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
