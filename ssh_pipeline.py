import paramiko
import os
from paramiko.ssh_exception import SSHException, NoValidConnectionsError
from blueprints.function_calling_blueprint import Pipeline as FunctionCallingBlueprint


class SSHCommandPipeline(FunctionCallingBlueprint):
    """
    SSHCommandPipeline: A pipeline for running commands on a remote server via SSH.
    """

    class Valves(FunctionCallingBlueprint.Valves):
        """
        Define the parameters required for SSH connection. This includes server IP, port, username, password, and optional SSH keys.
        """
        SERVER_IP: str = ""
        SSH_PORT: int = 22
        USERNAME: str = ""
        PASSWORD: str = ""
        PRIVATE_KEY: str = ""  # Path to an SSH private key if using passwordless login

    class Tools:
        """
        Contains the tools necessary to make an SSH connection and execute commands on the server.
        """

        def __init__(self, pipeline):
            self.pipeline = pipeline
            self.ssh_client = None

        def establish_ssh_connection(self) -> dict:
            """
            Establish an SSH connection to the server.

            :return: A message indicating the result of the SSH connection attempt.
            """
            valves = self.pipeline.valves
            try:
                # Initialize the SSH Client
                self.ssh_client = paramiko.SSHClient()
                self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # Automatically accept unknown host keys

                # Build connection configuration (password or private key)
                if valves.PRIVATE_KEY:
                    # Connect using a private key
                    private_key = paramiko.RSAKey.from_private_key_file(valves.PRIVATE_KEY)
                    self.ssh_client.connect(
                        hostname=valves.SERVER_IP,
                        port=valves.SSH_PORT,
                        username=valves.USERNAME,
                        pkey=private_key,
                    )
                else:
                    # Connect using username and password
                    if not valves.PASSWORD:
                        return {"error": "No password or SSH key provided for authentication."}

                    self.ssh_client.connect(
                        hostname=valves.SERVER_IP,
                        port=valves.SSH_PORT,
                        username=valves.USERNAME,
                        password=valves.PASSWORD,
                    )

                return {"status": f"Successfully connected to {valves.SERVER_IP}."}
            except (SSHException, NoValidConnectionsError) as e:
                return {"error": f"Failed to establish an SSH connection: {str(e)}"}

        def run_command(self, command: str) -> dict:
            """
            Run a command on the connected server.

            :return: Output or error from the command's execution.
            """
            if self.ssh_client is None:
                return {"error": "SSH connection not established."}

            try:
                stdin, stdout, stderr = self.ssh_client.exec_command(command)
                command_output = stdout.read().decode("utf-8")
                command_error = stderr.read().decode("utf-8")

                if command_error:
                    return {"command": command, "error": command_error}
                return {"command": command, "output": command_output.strip()}

            except SSHException as e:
                return {"error": f"Failed to run command: {str(e)}"}

        def close_ssh_connection(self) -> dict:
            """
            Close the SSH connection.

            :return: Confirmation message about connection closure.
            """
            if self.ssh_client:
                self.ssh_client.close()
                return {"status": "SSH connection closed."}
            return {"error": "No SSH connection to close."}

    def __init__(self):
        super().__init__()
        self.name = "SSH Command Pipeline"  # The name used to identify the pipeline
        self.valves = self.Valves(
            **{
                **self.valves.model_dump(),
                "pipelines": ["*"],  # Connect with all pipelines
                "SERVER_IP": os.getenv("SERVER_IP", ""),  # Allow environment variables for sensitive values
                "USERNAME": os.getenv("SSH_USERNAME", ""),
                "PASSWORD": os.getenv("SSH_PASSWORD", ""),
                "PRIVATE_KEY": os.getenv("PRIVATE_KEY", ""),  # Optionally use private key instead of password
            }
        )
        self.tools = self.Tools(self)

    def call(self, function_name: str, *args, **kwargs):
        """
        Call specific tools dynamically based on the function name passed. This is how Open-WebUI's function calling works.
        You need to resolve the correct callable function to run.
        """
        if hasattr(self.tools, function_name):
            # Fetch the function dynamically and execute with provided arguments
            func = getattr(self.tools, function_name)
            return func(*args, **kwargs)
        else:
            return {"error": f"Function '{function_name}' not found in this pipeline."}


# Example Usage (will be handled by Open-WebUI, but here for standalone testing)
if __name__ == "__main__":
    pipeline = SSHCommandPipeline()

    # Example Usage: Establish SSH connection
    print(pipeline.call("establish_ssh_connection"))

    # Example: Execute a command (e.g., listing directories)
    print(pipeline.call("run_command", command="ls -l"))

    # Example: Close connection
    print(pipeline.call("close_ssh_connection"))
