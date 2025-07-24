from config.configuration import get_env_variables
from futures_client import FuturesClient


def create_futures_client():
    env_vars = get_env_variables()
    return FuturesClient(env_vars["API_KEY"], env_vars["API_SECRET"])