from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Personal Finance Sheets Sync"
    app_env: str = "development"
    database_url: str = "sqlite:///./finance.db"

    token_encryption_key: str = Field(default="", repr=False)

    plaid_client_id: str = Field(default="", repr=False)
    plaid_secret: str = Field(default="", repr=False)
    plaid_env: str = "sandbox"
    plaid_products: str = "transactions"
    plaid_country_codes: str = "US"
    plaid_redirect_uri: str = ""

    app_api_key: str = Field(default="", repr=False)
    default_user_id: str = "personal"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def plaid_product_list(self) -> list[str]:
        return [value.strip() for value in self.plaid_products.split(",") if value.strip()]

    @property
    def plaid_country_code_list(self) -> list[str]:
        return [value.strip() for value in self.plaid_country_codes.split(",") if value.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
