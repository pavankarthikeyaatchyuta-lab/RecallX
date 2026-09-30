import sys
import psutil

try:
    import win32gui
    import win32process
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False


def get_active_window_info() -> tuple[str, str]:
    """
    Returns (application_name, window_title) of current active foreground window.
    Works robustly on Windows 11 with 64-bit PID masking.
    """
    if not HAS_WIN32 or sys.platform != "win32":
        return ("Desktop", "Active Workspace")

    try:
        hwnd = win32gui.GetForegroundWindow()
        if not hwnd:
            return ("Desktop", "Windows Desktop")

        title = win32gui.GetWindowText(hwnd).strip()

        # Get process ID
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        # Ensure unsigned 32-bit integer PID for 64-bit Windows
        pid = pid & 0xFFFFFFFF

        app_name = "Unknown Application"
        if pid > 0:
            try:
                proc = psutil.Process(pid)
                app_name = proc.name()
                # Clean up .exe extension for cleaner display
                if app_name.lower().endswith(".exe"):
                    app_name = app_name[:-4]
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                app_name = "System Application"

        if not title:
            title = app_name

        return (app_name, title)
    except Exception:
        return ("Desktop", "Active Workspace")
