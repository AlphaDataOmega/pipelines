from blueprints.function_calling_blueprint import Pipeline as FunctionCallingBlueprint


class Pipeline(FunctionCallingBlueprint):
    class Valves(FunctionCallingBlueprint.Valves):
        """
        Valves class to hold any configuration parameters.
        This example keeps it empty for simplicity.
        """
        pass

    class Tools:
        """
        Tools class that exposes functions available to the pipeline.
        The tools contain minimal functionality for testing.
        """

        def __init__(self, pipeline) -> None:
            # Pass the pipeline instance
            self.pipeline = pipeline

        def get_current_time(self) -> str:
            """
            A simple method to return a hardcoded time for testing.
            :return: A test string "Current Time".
            """
            return "Current Time: 12:00:00"

        def test_function(self) -> str:
            """
            A simple test method to ensure the pipeline is detected and working.
            :return: A success message.
            """
            return "Pipeline is working!"

    def __init__(self):
        super().__init__()
        # Set a unique name for this pipeline
        self.name = "Basic Test Pipeline"

        # Initialize Valves and Tools
        self.valves = self.Valves(**self.valves.model_dump())
        self.tools = self.Tools(self)
