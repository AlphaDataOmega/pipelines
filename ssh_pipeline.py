import paramiko
import os

class SSHPipeline:
    class Valves:
        def __init__(self):
            self.username = ""
            self.password = ""
            self.server_ip = ""
            self.port = 22  # Default SSH Port 22

    class Tools:
        def __init__(self, pipeline):
            self.pipeline = pipeline
            self.ssh_client = None

        def establish_ssh_connection(self) -> str:
            """
            Establishes an SSH connection with the server.
            """
            if not self.pipeline.valves.username or not self.pipeline.valves.password:
                return "No username or password provided."

            if not self.pipeline.valves.server_ip:
                return "No server IP provided."

            try:
                self.ssh_client = paramiko.SSHClient()
                self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                self.ssh_client.connect(
                    hostname=self.pipeline.valves.server_ip,
                    username=self.pipeline.valves.username,
                    password=self.pipeline.valves.password,
                    port=self.pipeline.valves.port,
                )
                return f"Successfully connected to {self.pipeline.valves.server_ip}."
            except Exception as e:
                return f"Failed to establish SSH connection: {str(e)}"

        def run_command(self, command: str) -> str:
            """
            Runs a command on the connected server.
            """
            if self.ssh_client is None:
                return "SSH connection not established. Cannot execute command."

            try:
                stdin, stdout, stderr = self.ssh_client.exec_command(command)
                output = stdout.read().decode()
                error = stderr.read().decode()

                if error:
                    return f"Error running command: {error}"
                return output
            except Exception as e:
                return f"Failed to run command: {str(e)}"

        def close_ssh_connection(self) -> str:
            """
            Closes the SSH connection.
            """
            if self.ssh_client is not None:
                self.ssh_client.close()
                return "SSH connection closed."
            return "No SSH connection to close."

    def __init__(self):
        self.name = "SSH Pipeline"
        self.valves = self.Valves()
        self.tools = self.Tools(self)

    def set_credentials(self, username: str, password: str):
        """
        Set login credentials for SSH.
        """
        self.valves.username = username
        self.valves.password = password

    def set_server_details(self, server_ip: str, port: int = 22):
        """
        Set server IP and SSH port (default: 22).
        """
        self.valves.server_ip = server_ip
        self.valves.port = port


# Example of how to use the SSH Pipeline:

if __name__ == "__main__":
    # Initialize the pipeline
    ssh_pipeline = SSHPipeline()

    # Set credentials and server details
    ssh_pipeline.set_credentials(username="your_username", password="your_password")
    ssh_pipeline.set_server_details(server_ip="192.168.1.10", port=22)

    # Establish SSH connection and run a test command
    connection_message = ssh_pipeline.tools.establish_ssh_connection()
    print(connection_message)

    if "Successfully connected" in connection_message:
        # If connection is successful, run commands
        output = ssh_pipeline.tools.run_command("ls -l")
        print(f"Command Output:\n{output}")

        # After the command is executed, close the connection
        close_message = ssh_pipeline.tools.close_ssh_connection()
        print(close_message)
