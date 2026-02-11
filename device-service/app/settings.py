from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://device_service:device_service@localhost:5432/device_service"

    jwt_issuer: str = "device-service"
    jwt_audience: str = "device-service"
    jwt_algorithm: str = "HS256"
    jwt_secret: str = "dev-only-secret-change-me"

    device_service_token: str = "dev-shared-secret"



settings = Settings()
