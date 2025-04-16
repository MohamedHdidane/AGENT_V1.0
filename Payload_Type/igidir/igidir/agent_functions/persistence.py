from mythic_container.MythicCommandBase import *
from mythic_container.MythicRPC import *
import json

class PersistenceArguments(TaskArguments):
    def __init__(self, command_line, **kwargs):
        super().__init__(command_line, **kwargs)
        self.args = [
            CommandParameter(
                name="method",
                type=ParameterType.ChooseOne,
                choices=["registry", "scheduled_task", "startup_folder"],
                description="Persistence method to use",
                parameter_group_info=[ParameterGroupInfo(required=True)]
            ),
        ]

    async def parse_arguments(self):
        if len(self.command_line) > 0:
            if self.command_line[0] == "{":
                self.load_args_from_json_string(self.command_line)
            else:
                self.add_arg("method", self.command_line)
        else:
            self.add_arg("method", "registry")

class PersistenceCommand(CommandBase):
    cmd = "persistence"
    needs_admin = True
    help_cmd = "persistence [registry|scheduled_task|startup_folder]"
    description = "Establish persistence using various methods"
    version = 1
    author = "@igidir"
    argument_class = PersistenceArguments
    attackmapping = ["T1547", "T1053"]

    async def create_tasking(self, task: MythicTask) -> MythicTask:
        method = task.args.get_arg("method")
        task.display_params = f"Establishing persistence via {method}"
        return task

    async def process_response(self, response: AgentResponse):
        pass