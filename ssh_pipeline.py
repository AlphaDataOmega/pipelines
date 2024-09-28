from blueprints.function_calling_blueprint import Pipeline as FunctionCallingBlueprint

class Pipeline(FunctionCallingBlueprint):
    class Valves(FunctionCallingBlueprint.Valves):
        TEST_VALVE: str = "Test Value"

    class Tools:
        def __init__(self, pipeline):
            self.pipeline = pipeline

        def test_method(self) -> str:
            """
            A simple method to confirm if the pipeline is loaded and working.
            :return: A simple confirmation message.
            """
            return "Pipeline Successfully Loaded!"

    def __init__(self):
        super().__init__()
        self.name = "Basic Test Pipeline"  # Ensure a unique name
        self.valves = self.Valves()
        self.tools = self.Tools(self)
