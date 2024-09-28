import os
import paramiko
from blueprints.function_calling_blueprint import Pipeline as FunctionCallingBlueprint


class Pipeline(FunctionCallingBlueprint):
    class Valves(FunctionCallingBlueprint.Valves):
        """
        Valves class for configuring SSH connection parameters like IP, username and password 
        or private key.
        """
        SSH_SERVER_IP: str = ""
        SSH_PORT: int = 22
        SSH_USERNAME: str = ""
        SSH_PASSWORD: str = ""
        SSH_PRIVATE_KEY_PATH: str = ""  # Optional: for key-based authentication
    
    class Tools:
        def __init__(self, pipeline) -> None:
            self.pipeline = pipeline
            self.ssh_client = None

        def connect_ssh(self) -> str:
            """
            Establish SSH connection using saved parameters from Valves (server, user, password, key).
            
            :return: Success message or error message.
            """
            valves = self.pipeline.valves
            
            # Check if necessary values are provided
            if not valves.SSH_SERVER_IP or not valves.SSH_USERNAME:
                return "SSH connection failed: Server IP and Username are required."
            
            try:
                # Initialize the client
                self.ssh_client = paramiko.SSHClient()
                self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

                # Use key-based authentication if SSH_PRIVATE_KEY_PATH is provided
                if valves.SSH_PRIVATE_KEY_PATH:
                    private_key = paramiko.RSAKey.from_private_key_file(valves.SSH_PRIVATE_KEY_PATH)
                    self.ssh_client.connect(
                        hostname=valves.SSH_SERVER_IP,
                        port=valves.SSH_PORT,
                        username=valves.SSH_USERNAME,
                        pkey=private_key
                    )
                else:
                    # Use username and password if key is not provided
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
            Run specified command on the connected SSH server.
            :param command: Command to run on the remote server.
            :return: Command output or error.
            """
            if not self.ssh_client:
                return "SSH connection not established. Cannot run the command."

            try:
                stdin, stdout, stderr = self.ssh_client.exec_command(command)
                output = stdout.read().decode()
                error = stderr.read().decode()
                
                if error:
                    return f"Command execution error: {error}"
                
                return output.strip()
            
            except Exception as e:
                return f"Exception while running command: {str(e)}"
        
        def close_ssh_connection(self) -> str:
            """
            Close the SSH connection.
            :return: Success message or error if already closed.
            """
            if self.ssh_client:
                self.ssh_client.close()
                self.ssh_client = None
                return "SSH connection closed."
            return "No active SSH connection to close."

    def __init__(self):
        super().__init__()
        # Set the name of the pipeline
        self.name = "SSH Tools Pipeline"
        
        # Load values into valves, using environment variables for sensitive SSH credentials
        self.valves = self.Valves(
            **{
                **self.valves.model_dump(),
                "pipelines": ["*"],  # Connect this pipeline with others in your setup
                "SSH_SERVER_IP": os.getenv("SSH_SERVER_IP", ""),            # Server IP
                "SSH_PORT": int(os.getenv("SSH_PORT", 22)),                 # SSH Port (22 by default)
                "SSH_USERNAME": os.getenv("SSH_USERNAME", ""),              # Server username
                "SSH_PASSWORD": os.getenv("SSH_PASSWORD", ""),              # Server password (if no SSH key)
                "SSH_PRIVATE_KEY_PATH": os.getenv("SSH_PRIVATE_KEY_PATH", "")  # SSH private key file path (optional)
            }
        )
        
        # Bind the Tools class
        self.tools = self.Tools(self)


# Standalone usage example (outside of Open-WebUI) — purely for local testing:
if __name__ == "__main__":
    # Create an instance of the pipeline
    ssh_pipeline = Pipeline()

    # Connect to the server via SSH
    print(ssh_pipeline.tools.connect_ssh())

    # Run a command remotely (example command: 'ls -la')
    print(ssh_pipeline.tools.run_command("ls -la"))

    # Close the SSH connection
    print(ssh_pipeline.tools.close_ssh_connection())
