import os
import logging
import subprocess
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
    time_limit = int(os.environ.get("TIME_LIMIT", "5"))  # Number of checks with no players before shutdown
    check_interval = int(os.environ.get("CHECK_INTERVAL", "60"))  # Time in seconds between checks
    no_people_count = 0
    logging.info(f"Starting server monitor for {ip}:{port} with a time limit of {time_limit} checks.")
    while no_people_count < time_limit:
        time.sleep(check_interval)  # Check every check_interval seconds
        try:
            server = BedrockServer.lookup(f"{ip}:{port}")
            status = server.status()
            logging.info(f"The server has {status.players.online} players online and replied in {status.latency} ms")
            if status.players.online == 0:
                logging.info(f"No one is on the server, incrementing no_people_count. {no_people_count + 1}/{time_limit}")
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
    logging.info(f"No one has been on the server for {time_limit} checks, shutting down the server.")
    stop_bedrock_container()
    logging.info("Finished stopping the container, now shutting down the instance.")
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
    project_id = get_gcp_metadata("project/project-id")
    zone = get_gcp_metadata("instance/zone").split("/")[-1]
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

def stop_bedrock_container():
    service_name = os.environ.get("SERVICE_NAME")
    if not service_name:
        logging.error("SERVICE_NAME environment variable is not set, cannot stop container, and the instance will be stopped directly. Please set SERVICE_NAME to the name of the container in the cloud run instance if you want to stop the container instead of the whole instance.")
        return
    try:
        stop_process = subprocess.check_call(["docker", "compose", "exec","--user", "root", service_name, "send-command", "stop"])
        logging.info(f"Sent stop command to container {service_name}, waiting for it to stop.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error while sending stop command to container {service_name}: {e}. The instance will be stopped directly.")
        return
    time.sleep(180)
    logging.info(f"Finished waiting for container {service_name} to stop.")

if __name__ == "__main__":
    main()
