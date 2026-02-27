# Monitoring Minecraft Bedrock Server Activity and Auto-Shutdown Script
The python script (`main.py`) is designed to monitor the activity of a Minecraft Bedrock server and automatically shut it down if no players have been active for a specified number of checks. 

It continuously checks for player activity on the server at defined intervals. If it detects that no players have been active for a certain number of consecutive checks, it will wait for a specified amount of time before shutting down the server. This helps to save resources by ensuring that the server is not running unnecessarily when there are no players.

It is designed to be run in Google Cloud Platform (GCP) and uses the GCP API to shut down the server instance when necessary. 
## Configuration
To configure the script, you need to set the following environment variables in a `.env` file:
### Required environment variables:
- `SERVER_IP`: The IP address of your Minecraft Bedrock server (default is 127.0.0.1, which is localhost).
- `SERVER_PORT`: The port number your Minecraft Bedrock server is running on (default is 19132).
- `CHECK_NUM`: The number of consecutive checks with no players before the server is shut down (default is 30).
- `CHECK_INTERVAL`: The time in seconds between each check for player activity (default is 60 seconds).
- `WAIT_BEFORE_SHUTDOWN`: The time in seconds to wait before shutting down the server after the last check indicates no players (default is 60 seconds). This allows for a grace period in case players return to the server shortly after the last check.
### Optional environment variables:
- `PROJECT_ID`: The GCP project ID where your Minecraft server instance is running. 
- `ZONE`: The GCP zone where your Minecraft server instance is located.
- `INSTANCE_NAME`: The name of your Minecraft server instance in GCP


If they are not set, the script will attempt to retrieve this information from the metadata server if it is running on a GCP VM instance. However, if you want to run the script outside of the VM instance, you will need to set these environment variables with the appropriate values for your GCP project and instance.
You can use the provided `.env-template` file to create your own `.env` file with the appropriate values for your server.
## Usage
1. Clone the repository and navigate to the project directory.
2. Create a `.env` file in the project root directory and populate it with the necessary environment variables as described above.
3. Run the script using different methods:
    - Run the script using Python:
        1. Ensure you have the required dependencies installed (e.g., using `pip install .`).
        (Use `pip install -e .` for development mode to allow for easy updates to the code.)
        2. Execute the script:
        ```bash
        python main.py
        ```
    - Run the script using [uv](https://docs.astral.sh/uv/), a python package and project manager
        1. Ensure you have uv installed and set up in your environment.
        2. Install the project dependencies:
        ```bash
        uv sync
        ```
        3. Run the script:
        ```bash
        uv run main.py
        ```
    - Run the script with Docker:
        1. Build the Docker image:
        ```bash
        docker build -t mc-server-monitor .
        ```
        2. Run the Docker container, ensuring to pass the environment variables:
        ```bash
        docker run --rm --env-file .env mc-server-monitor
        ```
        Optionally, you can use `docker-compose` to manage the container along with the Minecraft server:
        1. Create a `docker-compose.yml` file with the following content:
        ```yaml
        services:
            server-monitor:
                build: <path-to-your-project-directory>
                env_file: <path-to-your-project-directory>/.env
                restart: 'unless-stopped'
                logging:
                driver: gcplogs # Use Google Cloud Logging driver
                options:
                    gcp-log-cmd: "true"
                depends_on:
                    <the-minecraft-server-name>
        ```

        Replace `<path-to-your-project-directory>` with the actual path to your project directory and `<the-minecraft-server-name>` with the name of your Minecraft server service if you are using Docker Compose to manage both the server and the monitor.

        2. build the docker image
        ```bash
        docker-compose build
        ```
        3. Start the container:
        ```bash
        docker-compose up -d
        ```
## Notice
- It is designed to be run in Google Cloud Platform (GCP) and uses the GCP API to shut down the server instance when necessary. Make sure to set up the appropriate permissions and credentials for the script to access the GCP API. 
- Currently, it only supports GCP for shutting down the server instance. If you are using a different cloud provider or hosting solution, you will need to modify the shutdown logic in the script to work with your specific environment.