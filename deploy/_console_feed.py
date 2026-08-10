"""Feed text into a running console process via WriteConsoleInput.
Usage: python _console_feed.py <pid> <textfile>
"""
import ctypes
import sys
import time
import ctypes.wintypes as wt

KERNEL32 = ctypes.windll.kernel32
INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value

# Console input event structures
class KEY_EVENT_RECORD(ctypes.Structure):
    _fields_ = [
        ("bKeyDown", wt.BOOL),
        ("wRepeatCount", wt.WORD),
        ("wVirtualKeyCode", wt.WORD),
        ("wVirtualScanCode", wt.WORD),
        ("UnicodeChar", wt.WCHAR),
        ("dwControlKeyState", wt.DWORD),
    ]

class INPUT_RECORD(ctypes.Structure):
    _fields_ = [
        ("EventType", wt.WORD),
        ("_pad", wt.WORD),
        ("Event", KEY_EVENT_RECORD),
    ]

KEY_EVENT = 0x0001


def attach(pid):
    KERNEL32.FreeConsole()
    if not KERNEL32.AttachConsole(pid):
        err = ctypes.get_last_error()
        raise OSError(f"AttachConsole({pid}) failed err={err}")
    # get stdin handle in THIS process (now attached to same console)
    h = KERNEL32.GetStdHandle(-10)  # STD_INPUT_HANDLE
    if not h or h == INVALID_HANDLE_VALUE:
        raise OSError("GetStdHandle stdin failed")
    return h


def feed(h, text):
    recs = (INPUT_RECORD * (len(text) * 2 + 2))()
    idx = 0
    def add(keydown, ch):
        nonlocal idx
        r = recs[idx]
        r.EventType = KEY_EVENT
        r.Event.bKeyDown = keydown
        r.Event.wRepeatCount = 1
        r.Event.wVirtualKeyCode = 0
        r.Event.wVirtualScanCode = 0
        r.Event.UnicodeChar = ch
        r.Event.dwControlKeyState = 0
        idx += 1
    for ch in text:
        add(True, ch)
        add(False, ch)
    # Enter
    add(True, "\r")
    add(False, "\r")
    written = wt.DWORD()
    ok = KERNEL32.WriteConsoleInputW(h, recs, len(recs), ctypes.byref(written))
    if not ok:
        raise OSError(f"WriteConsoleInputW failed err={ctypes.get_last_error()}")
    return written.value


def main():
    pid = int(sys.argv[1])
    text = open(sys.argv[2], encoding="utf-8").read().strip()
    h = attach(pid)
    n = feed(h, text)
    print(f"fed {n} events ({len(text)} chars + Enter) to console of pid {pid}")
    KERNEL32.FreeConsole()


if __name__ == "__main__":
    main()
