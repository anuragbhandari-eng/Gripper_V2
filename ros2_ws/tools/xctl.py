"""Tiny X11 helper (ctypes, no installs): move a window, move/drag the mouse with XTEST."""
import ctypes, sys, time
X = ctypes.cdll.LoadLibrary('libX11.so.6'); T = ctypes.cdll.LoadLibrary('libXtst.so.6')
X.XOpenDisplay.restype = ctypes.c_void_p
X.XMoveWindow.argtypes = [ctypes.c_void_p, ctypes.c_ulong, ctypes.c_int, ctypes.c_int]
X.XRaiseWindow.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
X.XFlush.argtypes = [ctypes.c_void_p]; X.XSync.argtypes = [ctypes.c_void_p, ctypes.c_int]
T.XTestFakeMotionEvent.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_ulong]
T.XTestFakeButtonEvent.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_int, ctypes.c_ulong]
d = X.XOpenDisplay(None)

def move_window(wid, x, y):
    X.XMoveWindow(d, wid, x, y); X.XSync(d, 0)

def raise_window(wid):
    X.XRaiseWindow(d, wid); X.XSync(d, 0)

class _ClientMessage(ctypes.Structure):
    _fields_ = [('type', ctypes.c_int), ('serial', ctypes.c_ulong), ('send_event', ctypes.c_int),
                ('display', ctypes.c_void_p), ('window', ctypes.c_ulong), ('message_type', ctypes.c_ulong),
                ('format', ctypes.c_int), ('l', ctypes.c_long * 5)]

class _XEvent(ctypes.Union):
    _fields_ = [('xclient', _ClientMessage), ('pad', ctypes.c_long * 24)]

def keep_above(wid):
    """Ask the window manager to keep a window above the others (EWMH _NET_WM_STATE_ABOVE)."""
    X.XInternAtom.restype = ctypes.c_ulong; X.XInternAtom.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int]
    X.XDefaultRootWindow.restype = ctypes.c_ulong; X.XDefaultRootWindow.argtypes = [ctypes.c_void_p]
    X.XSendEvent.argtypes = [ctypes.c_void_p, ctypes.c_ulong, ctypes.c_int, ctypes.c_long, ctypes.c_void_p]
    ev = _XEvent(); m = ev.xclient
    m.type = 33; m.send_event = 1; m.display = d; m.window = wid; m.format = 32
    m.message_type = X.XInternAtom(d, b'_NET_WM_STATE', 0)
    m.l[0] = 1; m.l[1] = X.XInternAtom(d, b'_NET_WM_STATE_ABOVE', 0); m.l[2] = 0; m.l[3] = 2
    X.XSendEvent(d, X.XDefaultRootWindow(d), 0, (1 << 20) | (1 << 19), ctypes.byref(ev)); X.XSync(d, 0)

def mouse(x, y):
    T.XTestFakeMotionEvent(d, -1, int(x), int(y), 0); X.XFlush(d)

def button(down):
    T.XTestFakeButtonEvent(d, 1, 1 if down else 0, 0); X.XFlush(d)

def drag(x0, y, x1, seconds, steps=60):
    mouse(x0, y); time.sleep(0.05); button(True); time.sleep(0.05)
    for i in range(1, steps + 1):
        mouse(x0 + (x1 - x0) * i / steps, y); time.sleep(seconds / steps)
    time.sleep(0.05); button(False)

if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'move': move_window(int(sys.argv[2], 0), int(sys.argv[3]), int(sys.argv[4]))
    elif cmd == 'raise': raise_window(int(sys.argv[2], 0))
    elif cmd == 'above': keep_above(int(sys.argv[2], 0))
    elif cmd == 'mouse': mouse(int(sys.argv[2]), int(sys.argv[3]))
