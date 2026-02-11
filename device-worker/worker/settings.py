from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    resend_api_key: str
    resend_from: str
    tenancy_service_url: str
    tenancy_service_token: str
    poll_interval_seconds: int = 5
    device_service_url: str
    device_service_token: str

    # Resilience — timeouts (seconds)
    http_timeout: float = 10.0
    http_connect_timeout: float = 5.0

    # Resilience — retry backoff
    retry_base_delay: float = 1.0
    retry_max_delay: float = 60.0
    retry_max_attempts: int = 5

    # Resilience — circuit breaker
    cb_failure_threshold: int = 5
    cb_recovery_timeout: float = 30.0


settings = Settings()
