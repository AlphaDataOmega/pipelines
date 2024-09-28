import os
import paramiko
from datetime import datetime
from blueprints.function_calling_blueprint import Pipeline as FunctionCallingBlueprint


class Pipeline(FunctionCallingBlueprint):
    class Valves(FunctionCallingBlueprint.Valves):
        # Add your custom parameters here
        SSH_USERNAME: str = ""
        SSH_PASSWORD: str = ""
        SSH_HOST: str = ""
        SSH_PORT: int = 22
        pass

    class Tools:
        def __init__(self, pipeline) -> None:
            self.pipeline = pipeline

        def get_current_time(self) -> str:
            """
            Get the current time.
            """
            now = datetime.now()
            current_time = now.strftime("%H:%M:%S")
            return f"Current Time = {current_time}"

        def run_ssh_command(self, command: str) -> str:
            """
            SSH into the server, run a command, and return the output.
            
            :param command: The command to run.
            :return: The output of the command.
            """
            ssh_username = self.pipeline.valves.SSH_USERNAME
            ssh_password = self.pipeline.valves.SSH_PASSWORD
            ssh_host = self.pipeline.valves.SSH_HOST
            ssh_port = self.pipeline.valves.SSH_PORT

            if not (ssh_username and ssh_password and ssh_host):
                return "SSH credentials or host not set, please provide them."

            # Establish SSH connection
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            try:
                client.connect(
                    hostname=ssh_host,
                    username=ssh_username,
                    password=ssh_password,
                    port=ssh_port
                )
                stdin, stdout, stderr = client.exec_command(command)
                output = stdout.read().decode('utf-8')
                errors = stderr.read().decode('utf-8')
                
                if errors:
                    return f"Error: {errors.strip()}"
                
                return f"Output: {output.strip()}"

            except Exception as e:
                return f"SSH Connection Error: {str(e)}"

            finally:
                # Close the connection
                client.close()

    def __init__(self):
        super().__init__()
        self.name = "SSH Tools Pipeline"
        self.valves = self.Valves(
            **{
                **self.valves.model_dump(),
                "pipelines": ["*"],  # Connect to all pipelines
                "SSH_USERNAME": os.getenv("SSH_USERNAME", ""),
                "SSH_PASSWORD": os.getenv("SSH_PASSWORD", ""),
                "SSH_HOST": os.getenv("SSH_HOST", ""),
                "SSH_PORT": int(os.getenv("SSH_PORT", "22")),
            },
        )
        self.tools = self.Tools(self)
