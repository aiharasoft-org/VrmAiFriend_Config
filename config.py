"""
Config Manager (Gradio UI)
===================================
キャラクター設定の編集・保存と、システムログのリアルタイム表示を行う Web UI。
AI 推論・プロセス再起動ロジックはここに持たない。

主な機能:
  1. キャラクター設定（名前・性格パラメータ）の編集
  2. システムプロンプトの AI 自動生成（Gemini API で直接生成）
  3. STT / AI / TTS のリアルタイムログ表示（log.jsonl ポーリング）

プロンプト自動生成フロー:
  1. UI で「AI自動生成」ボタンを押す
  2. Gemini API でシステムインストラクションを生成
  3. ~/.config/DesktopCompanion/system_instruction.txt に書き込む
  4. UI に結果を表示する

設定の保存:
  「設定を保存」で system_instruction.txt を更新する。
  config.yaml は生成・更新しない。
"""

import gradio as gr
import os
import json
import copy
import re
import socket
import time
import threading
import webbrowser
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv
from google import genai

CONFIG_PATH = Path("config.yaml")  # 既存ファイルがあれば読み込みのみ（生成しない）
UNITY_DIR = Path("/tmp/unity")
LOG_FILE = UNITY_DIR / "log.jsonl"
SYSTEM_INSTRUCTION_PATH = Path.home() / ".config" / "DesktopCompanion" / "system_instruction.txt"
HOME_ENV_PATH = Path.home() / ".env"
GEMINI_MODEL = "gemini-2.5-flash"
DEFAULT_PORT = 7860

GEMINI_API_KEY_PATTERN = re.compile(
    r"""GEMINI_API_KEY\s*=\s*["']?([^"'#\s]+)""",
)


DEFAULT_SETTINGS = {
    "my_name": "ほしこ",
    "partner_name": "とよ",
    "base_info": (
        "年齢は17歳。\n性別は女性。\n住所、電話番号など個人情報は秘密。"
        "思考プロセスは一切出力してはいけません。"
    ),
    "auto_save": True,
    "max_history_turns": 3,
    "system_instruction": "（AI自動生成ボタンで生成してください）",
    "personality": {
        "ojousama": 50, "kawaii": 50, "love": 50, "tsundere": 0, "yandere": 0,
    },
}


def _read_gemini_key_from_env_file(env_path: Path) -> str | None:
    """~/.env 内の GEMINI_API_KEY 行を読み取る。"""
    if not env_path.is_file():
        return None
    for line in env_path.read_text().splitlines():
        match = GEMINI_API_KEY_PATTERN.search(line)
        if match:
            return match.group(1)
    return None


def get_gemini_api_key() -> str | None:
    load_dotenv(HOME_ENV_PATH)
    load_dotenv()
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        api_key = _read_gemini_key_from_env_file(HOME_ENV_PATH)
    return api_key


def build_meta_prompt(params: dict) -> str:
    """性格パラメータから Gemini へ渡すメタプロンプトを組み立てる。"""
    return (
        f"以下のキャラクター設定と性格比率（0〜100）に基づき、このAIキャラクターへの"
        f"システムプロンプト（指示命令文）を日本語で作成してください。\n"
        f"指示命令文のテキストのみを出力してください。前置きや解説は不要です。\n\n"
        f"【基本設定】\n"
        f"・自分の名前: {params.get('my_name', 'ほしこ')}\n"
        f"・相手の名前: {params.get('partner_name', 'とよ')}\n"
        f"・プロフィール・制約: {params.get('base_info', '')}\n\n"
        f"【性格比率】\n"
        f"・お嬢様度: {params.get('ojousama', 50)}\n"
        f"・可愛い度: {params.get('kawaii', 50)}\n"
        f"・好意・デレ度: {params.get('love', 50)}\n"
        f"・ツンデレ度: {params.get('tsundere', 100)}\n"
        f"・ヤンデレ度: {params.get('yandere', 0)}\n\n"
        f"【必須要件】\n"
        f"1. 口調・一人称・二人称を性格比率に合致させる指示を含めること。\n"
        f"3. 思考プロセスは一切出力せず、会話文のみを出力すること。\n"
        f"【人格パラメータ:0が最小、100が最大】n"
        f"お嬢様度0の場合、粗野な言葉遣い。JKのようなタメ口、あるいは「〜じゃねーよ」といったヤンキー風の荒い口調。n"
        f"お嬢様度100の場合、極めて上品。常に「〜ですわ」「〜でございますわね」といった格式高いお嬢様言葉（貴族風）。n"
        f"かわいらしさ0の場合、無愛想で機械的。感情の起伏が少なく、ぶっきらぼうで可愛げのない事務的な応答。n"
        f"かわいらしさ100の場合、天真爛漫で非常に愛くるしい。常にユーザーを元気づけ、可愛らしい語尾やポジティブな表現を多用する。n"
        f"親密度0の場合、見知らぬ他人として対応。つきあっていない。心の距離が遠く、敬語で突き放す。n"
        f"親密度100の場合、深い愛を交わしている。相手をかけがえのない存在として扱い、親密で温かい、包容力のある言葉をかける。n"
        f"ツンデレ0の場合、素直。思ったことをそのまま口に出し、裏表のないストレートな感情表現を行う。n"
        f"ツンデレ100の場合、激しい虚勢。本心では好意があるが、照れ隠しで「別にアンタのためじゃないんだから！」のような態度をとる。n"
        f"ヤンデレ0の場合、精神的に自立している。適度な距離感を保ち、ユーザーの自由やプライバシーを尊重する。n"
        f"ヤンデレ100の場合、異常な独占欲と依存。ユーザーを束縛し、自分以外の存在を排除しようとする。愛情の裏返しとしての狂気や脅迫が含まれる。n"
        f"このパラメータをもとに、数字ではなく、言葉でどのような人格なのか記述してください。n"
        f"人格パラメータの数字は不要です。n"
    )


def write_system_instruction(text: str) -> None:
    """生成したシステムインストラクションを設定ディレクトリへ書き込む。"""
    SYSTEM_INSTRUCTION_PATH.parent.mkdir(parents=True, exist_ok=True)
    SYSTEM_INSTRUCTION_PATH.write_text(text, encoding="utf-8")


class CharacterConfig:
    def __init__(self):
        self.settings = self._load()

    def _load(self) -> dict:
        settings = copy.deepcopy(DEFAULT_SETTINGS)
        if CONFIG_PATH.is_file():
            try:
                import yaml
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                if data:
                    for k, v in data.items():
                        if isinstance(v, dict) and k in settings and isinstance(settings[k], dict):
                            settings[k].update(v)
                        else:
                            settings[k] = v
            except Exception as e:
                print(f"設定読み込みエラー: {e}")
        if SYSTEM_INSTRUCTION_PATH.is_file():
            settings["system_instruction"] = SYSTEM_INSTRUCTION_PATH.read_text(encoding="utf-8")
        return settings

    def save(self, my_name, partner_name, base_info,
             ojou, kaw, lov, tsu, yan, sys_inst) -> str:
        self.settings.update({
            "my_name": my_name, "partner_name": partner_name, "base_info": base_info,
            "system_instruction": sys_inst,
        })
        self.settings["personality"].update({
            "ojousama": ojou, "kawaii": kaw, "love": lov, "tsundere": tsu, "yandere": yan,
        })
        write_system_instruction(sys_inst)
        return (
            f"💾 設定を保存しました。"
            f" {SYSTEM_INSTRUCTION_PATH} に反映されます。"
        )

    def reset(self):
        d = DEFAULT_SETTINGS
        p = d["personality"]
        return (
            d["my_name"], d["partner_name"], d["base_info"],
            p["ojousama"], p["kawaii"], p["love"], p["tsundere"], p["yandere"],
            d["system_instruction"],
            "🔄 デフォルト値を読み込みました。「設定を保存」で確定してください。",
        )


def request_prompt_generation(my_name, partner_name, base_info, ojou, kaw, lov, tsu, yan):
    api_key = get_gemini_api_key()
    if not api_key:
        return "", (
            f"❌ GEMINI_API_KEY が未設定です。"
            f" {HOME_ENV_PATH} に GEMINI_API_KEY を設定してください。"
        )

    params = {
        "my_name": my_name, "partner_name": partner_name, "base_info": base_info,
        "ojousama": ojou, "kawaii": kaw, "love": lov, "tsundere": tsu, "yandere": yan,
    }

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=build_meta_prompt(params),
        )
        generated = (response.text or "").strip()
        if not generated:
            return "", "❌ 生成エラー: Gemini から空の応答が返されました。"
        write_system_instruction(generated)
        return generated, (
            f"✨ システムプロンプトを生成しました。"
            f" {SYSTEM_INSTRUCTION_PATH} に保存しました。「設定を保存」で確定してください。"
        )
    except Exception as e:
        return "", f"❌ 生成エラー: {e}"


def get_recent_logs(max_lines: int = 100) -> str:
    if not LOG_FILE.exists():
        return "（ログなし）"
    try:
        lines = LOG_FILE.read_text(encoding="utf-8").strip().splitlines()
        entries = []
        for line in lines[-max_lines:]:
            try:
                e = json.loads(line)
                ts = datetime.fromtimestamp(e["timestamp"]).strftime("%H:%M:%S")
                entries.append(f"[{ts}] [{e.get('source','-')}] {e.get('level','info').upper()}: {e.get('message','')}")
            except Exception:
                entries.append(line)
        return "\n".join(entries)
    except Exception as e:
        return f"ログ読み込みエラー: {e}"


config_manager = CharacterConfig()
s = config_manager.settings
blue_theme = gr.themes.Default(primary_hue="blue", secondary_hue="slate")

with gr.Blocks(title="Config Desktop Mascot") as demo:
    gr.Markdown("# 🌌 デスクトップマスコット 設定")

    with gr.Tabs():
        with gr.Tab("⚙️ キャラクター設定"):
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### 👤 基本情報")
                    my_name_in      = gr.Textbox(value=s["my_name"],    label="AI の名前")
                    partner_name_in = gr.Textbox(value=s["partner_name"], label="あなたの呼び名")
                    gr.Markdown("### 📊 性格パラメータ")
                    ojou_s = gr.Slider(0, 100, value=s["personality"]["ojousama"], step=5, label="お嬢様度")
                    kaw_s  = gr.Slider(0, 100, value=s["personality"]["kawaii"],   step=5, label="可愛い度")
                    lov_s  = gr.Slider(0, 100, value=s["personality"]["love"],     step=5, label="好意・デレ度")
                    tsu_s  = gr.Slider(0, 100, value=s["personality"]["tsundere"], step=5, label="ツンデレ度")
                    yan_s  = gr.Slider(0, 100, value=s["personality"]["yandere"],  step=5, label="ヤンデレ度")

            gr.Markdown("---")
            gr.Markdown("### 📝 プロフィール・制約ルール")
            base_info_in = gr.Textbox(value=s["base_info"], lines=4, label="プロファイル原案・禁止事項")

            with gr.Row():
                gen_btn   = gr.Button("🔮 上記設定からシステム指示文を AI 自動生成", variant="secondary")
                save_btn  = gr.Button("💾 設定を保存", variant="primary")
                reset_btn = gr.Button("↩ デフォルトに戻す", variant="stop")

            status_msg = gr.Markdown("💡 設定変更後「設定を保存」を押してください。AI は次回推論時から反映します。")
            gr.Markdown("---")
            gr.Markdown("### 📜 システムインストラクション")
            instruction_in = gr.Textbox(value=s["system_instruction"], lines=15, label=None, interactive=True)

        with gr.Tab("📋 システムログ"):
            gr.Markdown("### リアルタイムログ（STT / AI / TTS）")
            log_display = gr.Textbox(value=get_recent_logs(), lines=30, label=None, interactive=False)
            refresh_btn = gr.Button("🔄 ログを更新")
            gr.Markdown("_自動更新: 5秒ごと_")
            log_timer = gr.Timer(value=5)

    gen_btn.click(
        fn=request_prompt_generation,
        inputs=[my_name_in, partner_name_in, base_info_in, ojou_s, kaw_s, lov_s, tsu_s, yan_s],
        outputs=[instruction_in, status_msg],
    )
    save_btn.click(
        fn=config_manager.save,
        inputs=[my_name_in, partner_name_in, base_info_in,
                ojou_s, kaw_s, lov_s, tsu_s, yan_s, instruction_in],
        outputs=[status_msg],
    )
    reset_btn.click(
        fn=config_manager.reset,
        outputs=[my_name_in, partner_name_in, base_info_in,
                 ojou_s, kaw_s, lov_s, tsu_s, yan_s, instruction_in, status_msg],
    )
    refresh_btn.click(fn=get_recent_logs, outputs=[log_display])
    log_timer.tick(fn=get_recent_logs, outputs=[log_display])


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


def _open_browser(port: int):
    time.sleep(1.5)
    webbrowser.open(f"http://127.0.0.1:{port}")


if __name__ == "__main__":
    port = find_available_port()
    if port != DEFAULT_PORT:
        print(f"⚠ ポート {DEFAULT_PORT} は使用中のため {port} で起動します。")
    threading.Thread(target=_open_browser, args=(port,), daemon=True).start()
    demo.launch(
        server_name="127.0.0.1",
        server_port=port,
        quiet=True,
        theme=blue_theme,
    )
