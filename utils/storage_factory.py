from azure_table_storage import AzureTableStorage
from azure.storage.queue import QueueClient

from config.configuration import get_env_variables


def create_table_storage_client(table_name: str):
    env_vars = get_env_variables()
    return AzureTableStorage(
        connection_string=env_vars["AZURE_STORAGE_CONNECTION_STRING"],
        table_name=table_name
    )

def create_queue_client(queue_name: str):
    env_vars = get_env_variables()
    return QueueClient.from_connection_string(
        conn_str=env_vars["AZURE_STORAGE_CONNECTION_STRING"],
        queue_name=queue_name
    )
