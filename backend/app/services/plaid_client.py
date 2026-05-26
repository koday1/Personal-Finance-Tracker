import plaid
from plaid.api import plaid_api

from app.core.config import settings


def _plaid_host() -> str:
    env = settings.plaid_env.lower()
    if env == "production":
        return plaid.Environment.Production
    if env == "development":
        return plaid.Environment.Development
    return plaid.Environment.Sandbox


def get_plaid_client() -> plaid_api.PlaidApi:
    configuration = plaid.Configuration(
        host=_plaid_host(),
        api_key={
            "clientId": settings.plaid_client_id,
            "secret": settings.plaid_secret,
        },
    )
    return plaid_api.PlaidApi(plaid.ApiClient(configuration))
