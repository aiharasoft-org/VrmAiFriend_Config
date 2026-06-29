"""
VrmAiFriend Config のバックグラウンド Gradio サーバー。

.app のランチャーから別プロセスとして起動され、UI プロセスは即終了する。
"""

from config import run_server

if __name__ == "__main__":
    run_server()
