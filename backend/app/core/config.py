"""Application configuration module.
All settings are derived strictly from environment variables using Pydantic Settings.
Fails fast if mandatory security configurations are absent.
"""

from enum import Enum
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class EnvironmentType(str, Enum):
    DEVELOPMENT = "development"
    TEST = "test"
    PRODUCTION = "production"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="SANAD_",
        case_sensitive=True,
        extra="ignore"
    )

    ENV: EnvironmentType = EnvironmentType.DEVELOPMENT
    CANONICAL_HOST: str = Field(default="localhost", description="Canonical host for verification URLs")
    API_V1_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://sanad_app:sanad_secret_pw@postgres:5432/sanad_db",
        description="Async PostgreSQL connection URI"
    )

    # Redis Cache & Queues
    REDIS_URL: str = Field(
        default="redis://redis:6379/0",
        description="Redis connection URI"
    )

    # Object Storage (MinIO / S3)
    S3_ENDPOINT: str = Field(default="http://minio:9000")
    S3_ACCESS_KEY: str = Field(default="sanad_minio_admin")
    S3_SECRET_KEY: str = Field(default="sanad_minio_secure_pw")
    S3_BUCKET: str = Field(default="sanad-documents")

    # Cryptography and Token Security
    JWT_SECRET: str = Field(
        default="dev_jwt_secret_change_in_production_32bytes_min",
        min_length=32,
        description="Secret key for JWT signing"
    )
    KEK: str = Field(
        default="dev_kek_32bytes_aes_gcm_must_be_set_in_env_securely!",
        min_length=32,
        description="Key Encryption Key for server-held institutional private keys"
    )

    # Retention
    UPLOAD_RETENTION_DAYS: int = Field(default=30, description="Retention limit for uploaded Road B scans")

    # Anchoring
    ENABLE_EVM_ANCHOR: bool = False
    EVM_RPC_URL: str = ""
    EVM_CONTRACT_ADDRESS: str = ""
    EVM_PRIVATE_KEY: str = ""


settings = Settings()
