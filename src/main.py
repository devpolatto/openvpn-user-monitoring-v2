import os
import sys
import time
import argparse
from typing import List, Dict
from dotenv import load_dotenv

from azure.core.exceptions import AzureError
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from elasticsearch import Elasticsearch

load_dotenv()

# pylint: disable=R0903
class ElasticsearchHandler:
    def __init__(self, host: str, username: str, password: str) -> None:
        self.host = host
        self.username = username
        self.password = password

        self.es = Elasticsearch(
            hosts=self.host, basic_auth=(self.username, self.password)
        )

    def send_to_elasticsearch(self, client_info: Dict[str, str]) -> None:
        client_info["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        self.es.index(index='openvpn', body=client_info)


def get_secret_from_keyvault(vault_url, secret_name) -> str:
    credential = DefaultAzureCredential()
    secret_client = SecretClient(vault_url=vault_url, credential=credential)

    try:
        secret = secret_client.get_secret(secret_name)
        return secret.value
    except AzureError as e:
        print(f"Error getting secret '{secret_name}': {e}")
        sys.exit(1)

def parse_status_file(status_file_path: str) -> List[str]:
    client_list_lines: List[str] = []
    try:
        with open(status_file_path, 'r', encoding='utf-8') as status_file:
            for line in status_file:
                if line.startswith("CLIENT_LIST"):
                    client_list_lines.append(line.strip())
    except FileNotFoundError:
        print("Status file not found.")
        sys.exit(1)
    return client_list_lines

def parse_client_list_lines(client_list_lines: List[str]) -> List[Dict[str, str]]:
    connected_clients: List[Dict[str, str]] = []
    current_time = time.time()
    for line in client_list_lines:
        columns = line.split(',')
        if len(columns) >= 11:
            user = columns[1]
            real_address = columns[2].split(':')[0]
            virtual_address = columns[3]
            bytes_received = int(columns[5])
            bytes_sent = int(columns[6])
            connected_since = columns[7]

            # Convert connected_since to a UNIX timestamp
            connected_since_timestamp = time.mktime(
                time.strptime(connected_since, "%Y-%m-%d %H:%M:%S")
            )
            # Calculate the difference in minutes
            minutes_elapsed = (current_time - connected_since_timestamp) / 60
            client_info: Dict[str, str] = {
                "user": user,
                "public_ip": real_address,
                "private_ip": virtual_address,
                "bytes_received": bytes_received,
                "bytes_sent": bytes_sent,
                "Connected_since": minutes_elapsed
            }
            connected_clients.append(client_info)
    return connected_clients

# Main function
def main(status_file_path: str, time_interval: int) -> None:
    az_keyvault_url: str = ""

    es_username: str = get_secret_from_keyvault(
        vault_url=az_keyvault_url,
        secret_name=''
    )
    es_password: str = get_secret_from_keyvault(
        vault_url=az_keyvault_url,
        secret_name=''
    )
    es_handler = ElasticsearchHandler(
        host=os.getenv("ELASTICSEARCH_HOST"),
        username=es_username,
        password=es_password
    )

    try:
        while True:
            client_list_lines: List[str] = parse_status_file(status_file_path)
            connected_clients: List[Dict[str, str]] = parse_client_list_lines(client_list_lines)
            for client_info in connected_clients:
                es_handler.send_to_elasticsearch(client_info)

            print("Sent connected client's information to Elasticsearch.")
            time.sleep(time_interval)
    except KeyboardInterrupt:
        print("Monitoring stopped.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OpenVPN status file monitor")
    parser.add_argument(
        "-s", "--status-file",
        default="/var/log/openvpn/openvpn-status.log",
        help="Path to the OpenVPN status file"
    )
    parser.add_argument("-i", "--interval", default=60, help="Log collection interval")
    args = parser.parse_args()

    main(args.status_file, args.interval)
