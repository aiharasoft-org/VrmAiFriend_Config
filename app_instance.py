"""
VrmAiFriend Config の起動制御（既存サーバー停止・再起動・ポート掃除）。

Gradio を import する前に使えるよう、標準ライブラリのみで実装する。
"""

from __future__ import annotations

import atexit
import os
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "VrmAiFriend"
SOCKET_PATH = CONFIG_DIR / "config_app.sock"
DEFAULT_PORT = 7860
OPEN_COMMAND = b"open\n"


def find_available_port(start: int = DEFAULT_PORT, end: int = DEFAULT_PORT + 20) -> int:
    """指定範囲で空いている TCP ポートを探す。"""
    for port in range(start, end + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    raise OSError(f"ポート {start}-{end} に空きがありません。")


def _is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        return sock.connect_ex(("127.0.0.1", port)) == 0


def _is_server_responding(port: int, timeout: float = 2.0) -> bool:
    url = f"http://127.0.0.1:{port}/"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return resp.status < 500
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def _is_server_responding_with_retries(
    port: int,
    *,
    attempts: int = 3,
    interval: float = 0.4,
) -> bool:
    for attempt in range(attempts):
        if _is_server_responding(port):
            return True
        if attempt + 1 < attempts:
            time.sleep(interval)
    return False


def _pids_listening_on_port(port: int) -> list[int]:
    result = subprocess.run(
        ["lsof", "-ti", f"tcp:{port}", "-sTCP:LISTEN"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return []
    pids: list[int] = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            pids.append(int(line))
        except ValueError:
            continue
    return pids


def _command_line_for_pid(pid: int) -> str:
    result = subprocess.run(
        ["ps", "-p", str(pid), "-o", "command="],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def _is_our_server_pid(pid: int) -> bool:
    if pid == os.getpid():
        return False
    cmd = _command_line_for_pid(pid)
    if not cmd:
        return False
    if "VrmAiFriendConfigServer" in cmd:
        return True
    server_script = str(Path(__file__).resolve().parent / "server.py")
    return server_script in cmd or cmd.rstrip().endswith("server.py")


def _kill_pids(pids: list[int], *, force: bool = False) -> bool:
    sig = signal.SIGKILL if force else signal.SIGTERM
    killed = False
    for pid in pids:
        try:
            os.kill(pid, sig)
            killed = True
        except (ProcessLookupError, PermissionError):
            continue
    return killed


def _kill_processes_on_port(port: int, *, force: bool = False) -> bool:
    pids = [pid for pid in _pids_listening_on_port(port) if pid != os.getpid()]
    return _kill_pids(pids, force=force)


def _cleanup_stale_port(port: int) -> None:
    """応答しない古いプロセスだけを終了する。"""
    if _is_server_responding_with_retries(port):
        return
    if not _kill_processes_on_port(port):
        return
    for _ in range(10):
        time.sleep(0.2)
        if not _is_port_in_use(port):
            return
    if _is_port_in_use(port) and not _is_server_responding_with_retries(port):
        _kill_processes_on_port(port, force=True)
        time.sleep(0.3)


def app_url(port: int) -> str:
    return f"http://127.0.0.1:{port}/"


def open_app_in_browser(port: int = DEFAULT_PORT) -> None:
    """macOS では `open` コマンドで URL を開く。"""
    url = app_url(port)
    if sys.platform == "darwin":
        subprocess.run(["open", url], check=False)
        return
    import webbrowser

    webbrowser.open(url)


def stop_running_server(port: int = DEFAULT_PORT) -> None:
    """稼働中の VrmAiFriendConfigServer を停止し、関連ソケットを掃除する。"""
    _remove_socket_file()

    our_pids = [pid for pid in _pids_listening_on_port(port) if _is_our_server_pid(pid)]
    if not our_pids:
        return

    _kill_pids(our_pids)
    for _ in range(25):
        time.sleep(0.2)
        remaining = [pid for pid in _pids_listening_on_port(port) if _is_our_server_pid(pid)]
        if not remaining:
            return

    _kill_pids(
        [pid for pid in _pids_listening_on_port(port) if _is_our_server_pid(pid)],
        force=True,
    )
    time.sleep(0.3)


def try_delegate_to_running_instance(port: int = DEFAULT_PORT) -> bool:
    """
    稼働中インスタンスへブラウザ表示を依頼する。
    成功時は呼び出し元が即終了してよい。
    """
    if _try_socket_delegate():
        return True
    if _is_server_responding_with_retries(port):
        open_app_in_browser(port)
        return True
    return False


def wait_for_server(port: int = DEFAULT_PORT, *, timeout: float = 90.0) -> bool:
    """バックグラウンドサーバーの起動完了を待つ。"""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if _is_server_responding(port, timeout=1.0):
            return True
        time.sleep(0.3)
    return False


START_LOCK_PATH = CONFIG_DIR / "config_app_starting.lock"


def acquire_start_lock(*, timeout: float = 30.0) -> bool:
    """同時起動でサーバーが二重に立ち上がるのを防ぐ。"""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            fd = os.open(START_LOCK_PATH, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(fd)
            return True
        except FileExistsError:
            time.sleep(0.3)
    return False


def release_start_lock() -> None:
    try:
        START_LOCK_PATH.unlink(missing_ok=True)
    except OSError:
        pass


def _server_executable() -> str:
    if getattr(sys, "frozen", False):
        bundled = Path(sys.executable).parent / "VrmAiFriendConfigServer"
        if bundled.exists():
            return str(bundled)
    return sys.executable


def _server_command() -> list[str]:
    if getattr(sys, "frozen", False):
        return [_server_executable()]
    root = Path(__file__).resolve().parent
    return [sys.executable, str(root / "server.py")]


def spawn_detached_server() -> subprocess.Popen[bytes]:
    """Gradio サーバーをバックグラウンドプロセスとして起動する。"""
    return subprocess.Popen(
        _server_command(),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )


def _try_socket_delegate() -> bool:
    if not SOCKET_PATH.exists():
        return False
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.settimeout(1.0)
            client.connect(str(SOCKET_PATH))
            client.sendall(OPEN_COMMAND)
        return True
    except OSError:
        return False


def _remove_socket_file() -> None:
    try:
        SOCKET_PATH.unlink(missing_ok=True)
    except OSError:
        pass


def _serve_instance_socket(port: int) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    _remove_socket_file()

    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(str(SOCKET_PATH))
    server.listen(5)
    server.settimeout(1.0)

    while True:
        try:
            conn, _ = server.accept()
        except TimeoutError:
            continue
        except OSError:
            break
        with conn:
            try:
                data = conn.recv(64)
            except OSError:
                continue
            if data.strip() == OPEN_COMMAND.strip():
                open_app_in_browser(port)


def start_instance_socket_server(port: int) -> None:
    """既存インスタンスへの再表示依頼を受け付ける。"""
    import threading

    thread = threading.Thread(
        target=_serve_instance_socket,
        args=(port,),
        name="config-app-socket",
        daemon=True,
    )
    thread.start()
    atexit.register(_remove_socket_file)


def prepare_launch_port() -> int:
    """起動用ポートを決定し、必要なら古いプロセスを掃除する。"""
    port = DEFAULT_PORT
    if not _is_port_in_use(port):
        return port

    _cleanup_stale_port(port)
    if not _is_port_in_use(port):
        return port

    fallback_port = find_available_port()
    if fallback_port != DEFAULT_PORT:
        print(f"⚠ ポート {DEFAULT_PORT} は解放できないため {fallback_port} で起動します。")
    return fallback_port
