"""
VrmAiFriend Config のエントリポイント（.app 本体）。

サーバーは別プロセスで起動し、このプロセスはブラウザを開いたあと即終了する。
"""

from __future__ import annotations

import os
import sys

from app_instance import (
    DEFAULT_PORT,
    acquire_start_lock,
    open_app_in_browser,
    prepare_launch_port,
    release_start_lock,
    spawn_detached_server,
    stop_running_server,
    wait_for_server,
)


def main() -> None:
    if not acquire_start_lock():
        os._exit(0)

    try:
        stop_running_server(DEFAULT_PORT)
        prepare_launch_port()
        spawn_detached_server()
        if wait_for_server(DEFAULT_PORT, timeout=90):
            open_app_in_browser(DEFAULT_PORT)
    finally:
        release_start_lock()

    os._exit(0)


if __name__ == "__main__":
    main()
