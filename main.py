import os
import logging
import time
import requests
from mcstatus import BedrockServer 
from dotenv import load_dotenv
from google.cloud import compute_v1


def main():
    logging_format = "[%(asctime)s] %(levelname)s: %(message)s"
    logging.basicConfig(level=logging.INFO, format=logging_format)
    load_dotenv()
    ip = os.environ.get("SERVER_IP", "127.0.0.1")
    port = os.environ.get("SERVER_PORT", "19132")
    check_num = int(os.environ.get("CHECK_NUM", "30"))  # Number of checks with no players before shutdown
    check_interval = int(os.environ.get("CHECK_INTERVAL", "60"))  # Time in seconds between checks
    wait_before_shutdown = int(os.environ.get("WAIT_BEFORE_SHUTDOWN", "60"))  # Time in seconds to wait before shutdown after last check

    no_people_count = 0
    logging.info(f"Starting server monitor for {ip}:{port} with a time limit of {check_num} checks.")
    while no_people_count < check_num:
        time.sleep(check_interval)  # Check every check_interval seconds
        try:
            server = BedrockServer.lookup(f"{ip}:{port}")
            status = server.status()
            logging.info(f"The server has {status.players.online} players online and replied in {status.latency} ms")
            if status.players.online == 0:
                logging.info(f"No one is on the server, incrementing no_people_count. {no_people_count + 1}/{check_num}")
                no_people_count += 1
            else:
                if no_people_count > 0:
                    logging.info("Players are online, resetting no_people_count.")
                else:
                    logging.info("Players are online.")
                no_people_count = 0
        except Exception as e:
            logging.error(f"Failed to connect to server {ip}:{port}: {e}. Program will exit.")
            exit(1)
    logging.info(f"No one has been on the server for {check_num} checks, waiting {wait_before_shutdown} seconds before shutting down the server.")
    time.sleep(wait_before_shutdown)
    logging.info("Shutting down the server now.")
    shutdown_instance()

def get_gcp_metadata(path):
    try:
        header = {"Metadata-Flavor": "Google"}
        response = requests.get(f"http://metadata.google.internal/computeMetadata/v1/{path}", headers=header, timeout=5)
        if response.status_code == 200:
            return response.text
        else:
            logging.error(f"Failed to get GCP metadata with path {path}: {response.status_code} {response.text}")
            return None
    except Exception as e:
        logging.error(f"Error while getting GCP metadata: {e}")
        return None

def shutdown_instance(): 
    logging.info("Attempt to get the instance information from environment variables")   
    project_id = os.environ.get("PROJECT_ID")
    zone = os.environ.get("ZONE")
    instance_name = os.environ.get("INSTANCE_NAME")
    if project_id is None:
        logging.info("PROJECT_ID not set in environment variables, trying to get it from GCP metadata.")
        project_id = get_gcp_metadata("project/project-id")
    if zone is None:
        logging.info("ZONE not set in environment variables, trying to get it from GCP metadata.")
        zone = get_gcp_metadata("instance/zone").split("/")[-1]
    if instance_name is None:
        logging.info("INSTANCE_NAME not set in environment variables, trying to get it from GCP metadata.")
        instance_name = get_gcp_metadata("instance/name")
    if not all([project_id, zone, instance_name]):
        logging.error("Missing GCP metadata, cannot shutdown instance.")
        return
    try:
        client = compute_v1.InstancesClient()
        operation =  client.stop(project=project_id, zone=zone, instance=instance_name)
        logging.info(f"Shutdown signal sent to instance {instance_name} in project {project_id} and zone {zone}.")
        if operation.error_code:
            logging.error(f"Error while shutting down instance with error code {operation.error_code}: {operation.error_message}")
            return
        if operation.warnings:
            logging.warning(f"Warnings while shutting down instance: {operation.warnings}")
        result = operation.result(timeout=60)
        logging.info(f"Instance shutdown completed with response: {result}")
    except Exception as e:
        logging.error(f"Error while shutting down instance: {e}")

if __name__ == "__main__":
    main()
