from mythic_container.PayloadBuilder import *
from mythic_container.MythicCommandBase import *
import asyncio
import os
import tempfile
import zipfile
import shutil

class Igidir(PayloadBuilder):
    name = "igidir"
    build_parameters = [
        BuildParameter(
            name="output_type",
            parameter_type=BuildParameterType.ChooseOne,
            description="Choose the output type",
            choices=["py", "exe", "app"],
            default_value="py",
        ),
        BuildParameter(
            name="include_dependencies",
            parameter_type=BuildParameterType.Boolean,
            description="Include required Python dependencies",
            default_value=True,
        ),
    ]
    
    async def build(self) -> BuildResponse:
        # Get the Python script that was created in the build function of IgidirAgent
        resp = BuildResponse(status=BuildStatus.Success)
        try:
            agent_code = self.get_parameter("payload")
            output_type = self.get_parameter("output_type")
            include_dependencies = self.get_parameter("include_dependencies")
            
            if output_type == "py":
                # For Python script output
                resp.payload = agent_code
                resp.build_message = "Successfully built Python agent script"
                return resp
            
            elif output_type == "exe":
                # For executable output, use PyInstaller
                with tempfile.TemporaryDirectory() as tmpdirname:
                    # Write agent code to temp file
                    agent_file = os.path.join(tmpdirname, "agent.py")
                    with open(agent_file, "w") as f:
                        f.write(agent_code)
                    
                    # Create requirements file if including dependencies
                    if include_dependencies:
                        req_file = os.path.join(tmpdirname, "requirements.txt")
                        with open(req_file, "w") as f:
                            f.write("cryptography\n")
                            f.write("requests\n")
                            f.write("pyOpenSSL\n")
                    
                    # Create PyInstaller spec file
                    spec_file = os.path.join(tmpdirname, "agent.spec")
                    spec_content = f"""
                    # -*- mode: python ; coding: utf-8 -*-
                    a = Analysis(
                        ['{agent_file}'],
                        pathex=['{tmpdirname}'],
                        binaries=[],
                        datas=[],
                        hiddenimports=[],
                        hookspath=[],
                        runtime_hooks=[],
                        excludes=[],
                        win_no_prefer_redirects=False,
                        win_private_assemblies=False,
                        cipher=None,
                        noarchive=False,
                    )
                    pyz = PYZ(a.pure, a.zipped_data, cipher=None)
                    exe = EXE(
                        pyz,
                        a.scripts,
                        a.binaries,
                        a.zipfiles,
                        a.datas,
                        [],
                        name='igidir',
                        debug=False,
                        bootloader_ignore_signals=False,
                        strip=False,
                        upx=True,
                        upx_exclude=[],
                        runtime_tmpdir=None,
                        console=False,
                        disable_windowed_traceback=False,
                        argv_emulation=False,
                        target_arch=None,
                        codesign_identity=None,
                        entitlements_file=None,
                    )
                    """
                    with open(spec_file, "w") as f:
                        f.write(spec_content)
                    
                    # Execute PyInstaller
                    # This is a mock command since we can't actually run it in this context
                    # In a real implementation, you would execute PyInstaller here
                    # For example: os.system(f"cd {tmpdirname} && pyinstaller --onefile agent.spec")
                    
                    # Read the executable file
                    # In real implementation, you would read the output file
                    # exe_path = os.path.join(tmpdirname, "dist", "igidir.exe")
                    # with open(exe_path, "rb") as f:
                    #     exe_data = f.read()
                    
                    # For this example, we'll just return the Python script as if it was compiled
                    resp.payload = agent_code
                    resp.build_message = "Mock EXE build successful (returning Python script for demo purposes)"
            
            elif output_type == "app":
                # Mac .app bundle creation would go here
                # Similar process to the exe, but creating a Mac app bundle structure
                resp.payload = agent_code
                resp.build_message = "Mock APP build successful (returning Python script for demo purposes)"
            
            else:
                resp.status = BuildStatus.Error
                resp.build_message = f"Unsupported output type: {output_type}"
                
        except Exception as e:
            resp.status = BuildStatus.Error
            resp.build_message = f"Error during build process: {str(e)}"
            
        return resp