from __future__ import annotations

import argparse
import ctypes
import json
import queue
import sys
import threading
import time
import tkinter as tk
from ctypes import wintypes
from pathlib import Path

APP_TITLE = "EZStudioLab Assistant"
STATUS_SCHEMA = "ezstudio.assistant-local-status.v1"

WM_APP = 0x8000
WM_TRAY = WM_APP + 17
WM_LBUTTONDBLCLK = 0x0203
WM_LBUTTONUP = 0x0202
WM_DESTROY = 0x0002

NIM_ADD = 0x00000000
NIM_DELETE = 0x00000002
NIF_MESSAGE = 0x00000001
NIF_ICON = 0x00000002
NIF_TIP = 0x00000004
IDI_APPLICATION = 32512

user32 = ctypes.windll.user32
shell32 = ctypes.windll.shell32
kernel32 = ctypes.windll.kernel32

LRESULT = ctypes.c_ssize_t
WNDPROC = ctypes.WINFUNCTYPE(
    LRESULT,
    wintypes.HWND,
    wintypes.UINT,
    wintypes.WPARAM,
    wintypes.LPARAM,
)


class GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", wintypes.DWORD),
        ("Data2", wintypes.WORD),
        ("Data3", wintypes.WORD),
        ("Data4", ctypes.c_ubyte * 8),
    ]


class NOTIFYICONDATAW(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("hWnd", wintypes.HWND),
        ("uID", wintypes.UINT),
        ("uFlags", wintypes.UINT),
        ("uCallbackMessage", wintypes.UINT),
        ("hIcon", wintypes.HICON),
        ("szTip", wintypes.WCHAR * 128),
        ("dwState", wintypes.DWORD),
        ("dwStateMask", wintypes.DWORD),
        ("szInfo", wintypes.WCHAR * 256),
        ("uTimeoutOrVersion", wintypes.UINT),
        ("szInfoTitle", wintypes.WCHAR * 64),
        ("dwInfoFlags", wintypes.DWORD),
        ("guidItem", GUID),
        ("hBalloonIcon", wintypes.HICON),
    ]


class WNDCLASSW(ctypes.Structure):
    _fields_ = [
        ("style", wintypes.UINT),
        ("lpfnWndProc", WNDPROC),
        ("cbClsExtra", ctypes.c_int),
        ("cbWndExtra", ctypes.c_int),
        ("hInstance", wintypes.HINSTANCE),
        ("hIcon", wintypes.HICON),
        ("hCursor", wintypes.HANDLE),
        ("hbrBackground", wintypes.HBRUSH),
        ("lpszMenuName", wintypes.LPCWSTR),
        ("lpszClassName", wintypes.LPCWSTR),
    ]


class NativeTrayIcon:
    def __init__(self, ui_events: queue.Queue[str], lifecycle_path: Path) -> None:
        self.ui_events = ui_events
        self.lifecycle_path = lifecycle_path
        self.thread: threading.Thread | None = None
        self.ready = threading.Event()
        self.hwnd: int | None = None
        self._wndproc = WNDPROC(self._window_proc)
        self._class_name = f"EZStudioLabAssistantTray_{id(self):x}"
        self._nid: NOTIFYICONDATAW | None = None

    def _log(self, event: str) -> None:
        self.lifecycle_path.parent.mkdir(parents=True, exist_ok=True)
        with self.lifecycle_path.open("a", encoding="utf-8") as handle:
            handle.write(f"{time.time():.6f} {event}\n")

    def _window_proc(self, hwnd, msg, wparam, lparam):
        if msg == WM_TRAY:
            event = int(lparam) & 0xFFFF
            if event in (WM_LBUTTONDBLCLK, WM_LBUTTONUP):
                self.ui_events.put("show")
                self._log("TRAY_RESTORE_REQUEST")
            return 0

        if msg == WM_DESTROY:
            user32.PostQuitMessage(0)
            return 0

        return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

    def start(self) -> None:
        self.thread = threading.Thread(
            target=self._run,
            name="ezstudio-native-tray",
            daemon=True,
        )
        self.thread.start()

        if not self.ready.wait(timeout=5):
            raise RuntimeError("tray_start_timeout")
        if self.hwnd is None:
            raise RuntimeError("tray_start_failed")

    def _run(self) -> None:
        hinstance = kernel32.GetModuleHandleW(None)

        wc = WNDCLASSW()
        wc.lpfnWndProc = self._wndproc
        wc.hInstance = hinstance
        wc.lpszClassName = self._class_name
        wc.hIcon = user32.LoadIconW(None, ctypes.c_void_p(IDI_APPLICATION))

        if not user32.RegisterClassW(ctypes.byref(wc)):
            self._log("TRAY_REGISTER_CLASS_FAILED")
            self.ready.set()
            return

        hwnd = user32.CreateWindowExW(
            0,
            self._class_name,
            APP_TITLE,
            0,
            0,
            0,
            0,
            0,
            None,
            None,
            hinstance,
            None,
        )
        if not hwnd:
            self._log("TRAY_CREATE_WINDOW_FAILED")
            self.ready.set()
            return

        icon = user32.LoadIconW(None, ctypes.c_void_p(IDI_APPLICATION))

        nid = NOTIFYICONDATAW()
        nid.cbSize = ctypes.sizeof(NOTIFYICONDATAW)
        nid.hWnd = hwnd
        nid.uID = 1
        nid.uFlags = NIF_MESSAGE | NIF_ICON | NIF_TIP
        nid.uCallbackMessage = WM_TRAY
        nid.hIcon = icon
        nid.szTip = APP_TITLE

        if not shell32.Shell_NotifyIconW(NIM_ADD, ctypes.byref(nid)):
            self._log("TRAY_ADD_FAILED")
            user32.DestroyWindow(hwnd)
            self.ready.set()
            return

        self.hwnd = hwnd
        self._nid = nid
        self._log("TRAY_ADD_OK")
        self.ready.set()

        msg = wintypes.MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))

        shell32.Shell_NotifyIconW(NIM_DELETE, ctypes.byref(nid))
        self._log("TRAY_END")


class StatusWindow:
    def __init__(self, root_dir: Path) -> None:
        self.root_dir = root_dir
        self.status_path = root_dir / "logs" / "assistant.status.json"
        self.commit_path = root_dir / "DEPLOYED_COMMIT.txt"
        self.version_path = root_dir / "VERSION"
        self.lifecycle_path = root_dir / "logs" / "status_window.lifecycle.log"
        self.ui_events: queue.Queue[str] = queue.Queue()

        self.root = tk.Tk()
        self.root.title(f"{APP_TITLE} v{self._read_version()}")
        self.root.geometry("420x245")
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self.hide)

        tk.Label(
            self.root,
            text=f"{APP_TITLE} v{self._read_version()}",
            font=("Segoe UI", 14, "bold"),
            anchor="w",
        ).place(x=18, y=16)

        self.state_label = tk.Label(
            self.root,
            text="ARRÊTÉ",
            font=("Segoe UI", 12, "bold"),
            anchor="w",
        )
        self.state_label.place(x=18, y=57)

        self.activity_label = tk.Label(
            self.root,
            text="Assistant arrêté",
            font=("Segoe UI", 10),
            anchor="w",
            justify="left",
            wraplength=365,
        )
        self.activity_label.place(x=18, y=89)

        self.build_label = tk.Label(
            self.root,
            text="Build : -",
            font=("Segoe UI", 9),
            anchor="w",
        )
        self.build_label.place(x=18, y=143)

        self.contact_label = tk.Label(
            self.root,
            text="Dernier contact : -",
            font=("Segoe UI", 9),
            anchor="w",
        )
        self.contact_label.place(x=18, y=169)

        tk.Label(
            self.root,
            text="Le bouton [X] masque cette fenêtre ; le worker continue.",
            font=("Segoe UI", 8),
            fg="#666666",
            anchor="w",
        ).place(x=18, y=197)

        self._log("WINDOW_START")

        self.tray = NativeTrayIcon(self.ui_events, self.lifecycle_path)
        self.tray.start()

        self.root.after(150, self._poll_ui_events)
        self.root.after(250, self._refresh_status)

    def _log(self, event: str) -> None:
        self.lifecycle_path.parent.mkdir(parents=True, exist_ok=True)
        with self.lifecycle_path.open("a", encoding="utf-8") as handle:
            handle.write(f"{time.time():.6f} {event}\n")

    def hide(self) -> None:
        self._log("USER_CLOSE_HIDE")
        self.root.withdraw()

    def show(self) -> None:
        self._log("WINDOW_RESTORE")
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def _poll_ui_events(self) -> None:
        try:
            while True:
                event = self.ui_events.get_nowait()
                if event == "show":
                    self.show()
        except queue.Empty:
            pass

        self.root.after(150, self._poll_ui_events)

    def _read_version(self) -> str:
        try:
            value = self.version_path.read_text(encoding="utf-8-sig").strip()
        except OSError:
            return "-"
        return value or "-"

    def _read_commit(self) -> str:
        try:
            value = self.commit_path.read_text(encoding="utf-8-sig").strip()
        except OSError:
            return "-"
        return value[:12] if value else "-"

    def _read_status(self) -> dict | None:
        try:
            payload = json.loads(self.status_path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError):
            return None

        if payload.get("schema") != STATUS_SCHEMA:
            return None

        return payload

    def _refresh_status(self) -> None:
        self.build_label.configure(text=f"Build : {self._read_commit()}")

        payload = self._read_status()

        if payload is None:
            state = "ARRÊTÉ"
            activity = "Assistant arrêté"
            contact = "Dernier contact : -"
        else:
            raw_state = str(payload.get("state") or "").upper()
            activity = str(payload.get("activity") or "").strip() or "En veille"

            try:
                age = max(0.0, time.time() - float(payload.get("at_epoch") or 0))
            except (TypeError, ValueError):
                age = 999999.0

            if raw_state == "STOPPED":
                state = "ARRÊTÉ"
            elif raw_state == "ERROR":
                state = "ERREUR"
            elif age > 15:
                state = "PÉRIMÉ"
                activity = "Aucun heartbeat récent"
            elif raw_state in {"BUSY", "OCCUPIED", "CLAIMED", "PROCESSING"}:
                state = "OCCUPÉ"
            else:
                state = "EN LIGNE"

            contact = f"Dernier contact : {int(age)} s"

        self.state_label.configure(text=state)
        self.activity_label.configure(text=activity)
        self.contact_label.configure(text=contact)
        self.root.after(1000, self._refresh_status)

    def run(self) -> None:
        self.root.mainloop()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    args = parser.parse_args()

    if sys.platform != "win32":
        raise RuntimeError("windows_only_status_window")

    StatusWindow(Path(args.root)).run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
