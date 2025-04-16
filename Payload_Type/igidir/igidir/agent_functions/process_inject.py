from mythic_container.MythicCommandBase import *
from mythic_container.MythicRPC import *
import json

class ProcessInjectArguments(TaskArguments):
    def __init__(self, command_line, **kwargs):
        super().__init__(command_line, **kwargs)
        self.args = [
            CommandParameter(
                name="pid",
                type=ParameterType.Number,
                description="PID of process to inject into",
                parameter_group_info=[ParameterGroupInfo(required=True)]
            ),
            CommandParameter(
                name="shellcode",
                type=ParameterType.String,
                description="Base64 encoded shellcode to inject",
                parameter_group_info=[ParameterGroupInfo(required=True)]
            ),
        ]

    async def parse_arguments(self):
        if len(self.command_line) > 0:
            if self.command_line[0] == "{":
                self.load_args_from_json_string(self.command_line)
            else:
                raise ValueError("Missing JSON arguments")
        else:
            raise ValueError("Missing arguments")

class ProcessInjectCommand(CommandBase):
    cmd = "process_inject"
    needs_admin = False
    help_cmd = "process_inject { \"pid\": 1234, \"shellcode\": \"base64...\" }"
    description = "Inject shellcode into a remote process"
    version = 1
    author = "@igidir"
    argument_class = ProcessInjectArguments
    attackmapping = ["T1055"]

    async def create_tasking(self, task: MythicTask) -> MythicTask:
        pid = task.args.get_arg("pid")
        shellcode = task.args.get_arg("shellcode")
        
        task.display_params = f"Injecting into PID {pid} with {len(shellcode)} bytes of shellcode"
        return task

    async def process_response(self, response: AgentResponse):
        pass