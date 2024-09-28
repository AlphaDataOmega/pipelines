import os
import paramiko
from typing import Literal
from blueprints.function_calling_blueprint import Pipeline as FunctionCallingBlueprint

class Pipeline(FunctionCallingBlueprint):
    class Valves(FunctionCallingBlueprint.Valves):
        """
        Define specific SSH parameters (IP address, username, password, and private key path) inside the Valves class.
        These will be used to establish an SSH connection.
        """
        SSH_SERVER_IP: str = ""
        SSH_PORT: int = 22
        SSH_USERNAME: str = ""
        SSH_PASSWORD: str = ""
        SSH_PRIVATE_KEY_PATH: str = ""  # Optional: Path to SSH private key if passwordless login

    class Tools:
        """
        The Tools class contains all the necessary SSH operations including connecting,
        running commands, and closing the SSH connection.
        """

        def __init__(self, pipeline) -> None:
            self.pipeline = pipeline
            self.ssh_client = None

        def connect_ssh(self) -> str:
            """
            Establishes SSH connection to the server using credentials from the Valves.
            :return: Success message or error message depending on the result.
            """
            valves = self.pipeline.valves

            # Check if server IP and username are provided
            if not valves.SSH_SERVER_IP or not valves.SSH_USERNAME:
                return "SSH connection failed: Server IP and Username must be provided."

            try:
                # Initialize the SSH client
                self.ssh_client = paramiko.SSHClient()
                self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

                # Check if SSH private key path is provided and attempt to use it
                if valves.SSH_PRIVATE_KEY_PATH:
                    private_key = paramiko.RSAKey.from_private_key_file(valves.SSH_PRIVATE_KEY_PATH)
                    self.ssh_client.connect(
                        hostname=valves.SSH_SERVER_IP,
                        port=valves.SSH_PORT,
                        username=valves.SSH_USERNAME,
                        pkey=private_key
                    )
                else:
                    # Otherwise, use password-based authentication
                    self.ssh_client.connect(
                        hostname=valves.SSH_SERVER_IP,
                        port=valves.SSH_PORT,
                        username=valves.SSH_USERNAME,
                        password=valves.SSH_PASSWORD
                    )

                return f"Successfully connected to {valves.SSH_SERVER_IP}"

            except Exception as e:
                return f"Failed to establish SSH connection: {str(e)}"

        def run_command(self, command: str) -> str:
            """
            Runs a command on the connected SSH server.
            :param command: Command to execute on the remote server.
            :return: Output of the command or error message.
            """
            if not self.ssh_client:
                return "SSH connection not established. Cannot run the command."

            try:
                stdin, stdout, stderr = self.ssh_client.exec_command(command)
                output = stdout.read().decode()
                error = stderr.read().decode()
                
                # If any error is encountered during command execution, return the error
                if error:
                    return f"Command execution error: {error}"

                # Return the command output
                return output.strip()

            except Exception as e:
                return f"Exception occurred while running command: {str(e)}"

        def close_ssh_connection(self) -> str:
            """
            Close the SSH connection.
            :return: Success message once the connection is closed.
            """
            if self.ssh_client:
                self.ssh_client.close()
                return "SSH connection closed successfully."
            return "No SSH connection to close."

    def __init__(self):
        super().__init__()
        # Optionally, you can set the id and name of the pipeline.
        # Keep the id unique across pipelines to avoid conflicts!
        self.name = "SSH Tools Pipeline"
        
        # Initialize Valves class with default values or environmental variable
        # You can set API keys or credentials here for the SSH pipeline
        self.valves = self.Valves(
            **{
                **self.valves.model_dump(),
                "pipelines": ["*"],  # Connect to all pipelines
                "SSH_SERVER_IP": os.getenv("SSH_SERVER_IP", ""),      # SSH IP address (load from env if available)
                "SSH_PORT": int(os.getenv("SSH_PORT", 22)),           # SSH Port (22 is default)
                "SSH_USERNAME": os.getenv("SSH_USERNAME", ""),        # Username for SSH login
                "SSH_PASSWORD": os.getenv("SSH_PASSWORD", ""),        # Password for SSH login (leave blank for private key)
                "SSH_PRIVATE_KEY_PATH": os.getenv("SSH_PRIVATE_KEY_PATH", ""),  # Private key path (optional)
            },
        )
        
        # Initialize Tools to access SSH operations
        self.tools = self.Tools(self)


# Example of how it would be used via Open-WebUI interface:
if __name__ == "__main__":
    # Initialize the pipeline
    ssh_pipeline = Pipeline()

    # Attempt to establish an SSH connection
    print(ssh_pipeline.tools.connect_ssh())

    # Run a basic command (example "ls -la" to list directory contents)
    print(ssh_pipeline.tools.run_command("ls -la"))

    # Close the SSH connection
    print(ssh_pipeline.tools.close_ssh_connection())
