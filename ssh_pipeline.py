import os
import paramiko
from typing import Literal
from blueprints.function_calling_blueprint import Pipeline as FunctionCallingBlueprint


class Pipeline(FunctionCallingBlueprint):
    """
    Pipeline for SSH connection and command execution over a remote server.
    """

    class Valves(FunctionCallingBlueprint.Valves):
        """
        The Valves class stores the configuration for connecting to the SSH server.
        """
        SSH_SERVER_IP: str = ""            # Required SSH server IP address
        SSH_PORT: int = 22                 # Port for SSH (default: 22)
        SSH_USERNAME: str = ""             # Username for SSH login
        SSH_PASSWORD: str = ""             # Password for SSH login (optional if using SSH keys)
        SSH_PRIVATE_KEY: str = ""          # Path to SSH private key (optional)

    class Tools:
        def __init__(self, pipeline) -> None:
            self.pipeline = pipeline
            self.ssh_client = None

        def connect_ssh(self) -> str:
            """
            Establish SSH connection with the provided server using credentials from 'valves'.
            :return: Success message or error message.
            """
            valves = self.pipeline.valves

            # Check mandatory fields
            if not valves.SSH_SERVER_IP or not valves.SSH_USERNAME:
                return "SSH connection failed: Server IP and Username are required fields."

            try:
                # Initialize SSH Client
                self.ssh_client = paramiko.SSHClient()
                self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

                # If private key provided, use private key connection
                if valves.SSH_PRIVATE_KEY:
                    private_key = paramiko.RSAKey.from_private_key_file(valves.SSH_PRIVATE_KEY)
                    self.ssh_client.connect(
                        hostname=valves.SSH_SERVER_IP,
                        port=valves.SSH_PORT,
                        username=valves.SSH_USERNAME,
                        pkey=private_key
                    )
                else:
                    # Connect using password-based authentication
                    self.ssh_client.connect(
                        hostname=valves.SSH_SERVER_IP,
                        port=valves.SSH_PORT,
                        username=valves.SSH_USERNAME,
                        password=valves.SSH_PASSWORD
                    )

                return f"Successfully connected to {valves.SSH_SERVER_IP}."

            except Exception as e:
                return f"Failed to establish SSH connection: {str(e)}"

        def run_command(self, command: str) -> str:
            """
            Run a command on the connected SSH server.
            :param command: Command to execute on the remote server.
            :return: Output of the command or error message.
            """
            if self.ssh_client is None:
                return "SSH connection not established. Cannot execute command."

            try:
                stdin, stdout, stderr = self.ssh_client.exec_command(command)
                output = stdout.read().decode()
                error = stderr.read().decode()

                if error:
                    return f"Error running command: {error}"
                return output.strip()

            except Exception as e:
                return f"Exception occurred while running command: {str(e)}"

        def close_connection(self) -> str:
            """
            Close the SSH connection.
            :return: Success message or error message if no connection exists.
            """
            if self.ssh_client:
                self.ssh_client.close()
                return "SSH connection closed successfully."
            return "No SSH connection found."

    def __init__(self):
        super().__init__()
        # Define the name of the pipeline
        self.name = "SSH Command Pipeline"

        # Load valves (configuration) from environment variables or set default values
        self.valves = self.Valves(
            **{
                **self.valves.model_dump(),
                "pipelines": ["*"],  # Connect to all pipelines
                "SSH_SERVER_IP": os.getenv("SSH_SERVER_IP", ""),
                "SSH_PORT": int(os.getenv("SSH_PORT", 22)),
                "SSH_USERNAME": os.getenv("SSH_USERNAME", ""),
                "SSH_PASSWORD": os.getenv("SSH_PASSWORD", ""),
                "SSH_PRIVATE_KEY": os.getenv("SSH_PRIVATE_KEY", ""),
            }
        )

        # Initialize the tools for command execution
        self.tools = self.Tools(self)


# Example usage (via Open-WebUI):
if __name__ == "__main__":
    pipeline = Pipeline()

    # Establish SSH Connection
    print(pipeline.tools.connect_ssh())

    # Run a command on the server (example: "ls -la" might show directory contents)
    print(pipeline.tools.run_command("ls -la"))

    # Close SSH Connection
    print(pipeline.tools.close_connection())
