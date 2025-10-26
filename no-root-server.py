#!/usr/bin/env python3
import os
import stat
from pathlib import Path

# -------- Global Configuration --------
INSTALL_PATH = Path.home() / "all-project" / "bin"
COMMAND_NAME = "server"
SCRIPT_NAME = "theblackland-server-install.py"
REMOTE_SCRIPT_URL = "REMOTE_SCRIPT_URL"  # future update URL placeholder
DEFAULT_PORT = 8080  # গ্লোবাল ডিফল্ট পোর্ট


def make_executable(path):
    path.chmod(path.stat().st_mode | stat.S_IEXEC)


def install_script():
    INSTALL_PATH.mkdir(parents=True, exist_ok=True)
    script_path = INSTALL_PATH / COMMAND_NAME

    # -----------------------------------------------------------
    # Bash Script Template (main CLI logic)
    # -----------------------------------------------------------
    bash_script = f"""#!/bin/bash
# =======================================================
#  Simple Local Python Server Manager (by TheBlackLand)
# =======================================================

CONFIG_FILE="$HOME/.server_config"
DEFAULT_PORT={DEFAULT_PORT}

# ----- Load configuration -----
load_config() {{
    if [ -f "$CONFIG_FILE" ]; then
        source "$CONFIG_FILE"
    fi
    DEFAULT_PORT=${{DEFAULT_PORT:-{DEFAULT_PORT}}}
}}

# ----- Save configuration -----
save_config() {{
    echo "DEFAULT_PORT=$DEFAULT_PORT" > "$CONFIG_FILE"
}}

# ----- Utility -----
check_port() {{
    lsof -ti tcp:$1 2>/dev/null
}}

random_port() {{
    shuf -i 1025-65535 -n 1
}}

# ----- Server Management -----
start_server() {{
    load_config
    if [ "$PORT" == "any" ]; then
        PORT=$(random_port)
    fi
    PORT=${{PORT:-$DEFAULT_PORT}}
    SERVE_PATH=$(pwd)

    PID=$(check_port $PORT)
    if [ ! -z "$PID" ]; then
        PROC_NAME=$(ps -p $PID -o comm=)
        if [[ "$PROC_NAME" == "python3" || "$PROC_NAME" == "python" ]]; then
            echo "⚠️ Port $PORT already used by Python server (PID: $PID). Killing old process..."
            kill -9 $PID 2>/dev/null
            sleep 1
        else
            echo "❌ Port $PORT already in use by another process: $PROC_NAME (PID: $PID)"
            echo "   Not killing it for safety. Please use another port."
            exit 1
        fi
    fi

    LOG_FILE="/tmp/server_$(whoami)_${{PORT}}.log"

    echo "🚀 Starting server on port $PORT ..."
    nohup python3 -m http.server $PORT --directory "$SERVE_PATH" --bind 0.0.0.0 > "$LOG_FILE" 2>&1 &
    NEW_PID=$!
    echo "✅ Server started (PID: $NEW_PID)"
    echo "📂 Serving from: $SERVE_PATH"
    echo "📜 Log file: $LOG_FILE"
}}

stop_server() {{
    if [ "$PORT" == "all" ] || [ -z "$PORT" ]; then
        echo "🛑 Stopping all running Python HTTP servers..."
        ps aux | grep "[p]ython3 -m http.server" | awk '{{print $2}}' | xargs -r kill -9 2>/dev/null
    else
        PID=$(check_port $PORT)
        if [ -z "$PID" ]; then
            echo "❌ No server running on port $PORT"
            exit 1
        fi
        PROC_NAME=$(ps -p $PID -o comm=)
        if [[ "$PROC_NAME" == "python3" || "$PROC_NAME" == "python" ]]; then
            echo "🛑 Stopping server on port $PORT (PID: $PID)"
            kill -9 $PID 2>/dev/null
        else
            echo "⚠️ Port $PORT is used by another process ($PROC_NAME). Skipping."
        fi
    fi
}}

restart_server() {{
    load_config
    PORT=${{PORT:-$DEFAULT_PORT}}
    echo "🔁 Restarting server on port $PORT ..."
    PID=$(check_port $PORT)
    if [ ! -z "$PID" ]; then
        PROC_NAME=$(ps -p $PID -o comm=)
        if [[ "$PROC_NAME" == "python3" || "$PROC_NAME" == "python" ]]; then
            kill -9 $PID 2>/dev/null
            sleep 1
        else
            echo "⚠️ Port $PORT used by another process ($PROC_NAME). Cannot restart."
            exit 1
        fi
    fi
    start_server
}}

show_status() {{
    if [ "$PORT" == "" ]; then
        echo "📊 Active Python HTTP servers:"
        ps aux | grep "[p]ython3 -m http.server" || echo "No active servers."
        echo ""
        echo "👉 Use: server status [port] to view live logs"
    else
        LOG_FILE="/tmp/server_$(whoami)_${{PORT}}.log"
        if [ ! -f "$LOG_FILE" ]; then
            echo "⚠️ No log file found for port $PORT"
            exit 1
        fi
        echo "---------------------------------------------"
        echo "📡 Live Log View for Port $PORT (Ctrl+C to exit)"
        echo "---------------------------------------------"
        tail -f "$LOG_FILE"
    fi
}}

destroy_server() {{
    echo "🧹 Removing server setup..."
    rm -f "{INSTALL_PATH}/{COMMAND_NAME}"
    rm -f /tmp/server_*.log
    rm -f "$CONFIG_FILE"
    sed -i '/{COMMAND_NAME}/d' ~/.bashrc 2>/dev/null
    sed -i '/{COMMAND_NAME}/d' ~/.zshrc 2>/dev/null
    echo "✅ Server command removed successfully."
}}

update_self() {{
    echo "⬆️ Checking for latest version..."
    echo "✅ Already up-to-date (placeholder)."
}}

set_global_port() {{
    if [[ "$PORT" =~ ^[0-9]+$ ]]; then
        DEFAULT_PORT=$PORT
        save_config
        echo "✅ Global default port set to $PORT"
    else
        echo "❌ Invalid port number: $PORT"
        exit 1
    fi
}}

# ------------- Command Parser -------------
CMD="$1"
PORT="$2"

case "$CMD" in
    start|"")
        start_server
        ;;
    stop|exit)
        stop_server
        ;;
    restart)
        restart_server
        ;;
    status)
        show_status
        ;;
    destroy)
        destroy_server
        ;;
    update)
        update_self
        ;;
    set-port)
        set_global_port
        ;;
    help|-h|--help)
        echo "🆘 Usage:"
        echo "  server                                  → Start on global/default port"
        echo "  server [port|any]                       → Start on specific/random port"
        echo "  server stop [port|all]                  → Stop one or all servers"
        echo "  server restart [port]                   → Restart server"
        echo "  server status [port]                    → View server logs"
        echo "  server set-port [port]                  → Set global default port"
        echo "  server update                           → Self-update (future)"
        echo "  server destroy                          → Uninstall everything"
        ;;
    [0-9]*|any)
        PORT=$CMD
        start_server
        ;;
    *)
        echo "⚠️ Unknown command: $CMD"
        echo "👉 Try: server help"
        ;;
esac
"""

    # ----- Write bash script -----
    with open(script_path, "w") as f:
        f.write(bash_script)
    make_executable(script_path)

    # ----- Add PATH to rc files -----
    for rc_file in [Path.home() / ".bashrc", Path.home() / ".zshrc"]:
        export_line = f'export PATH="{INSTALL_PATH}:$PATH"'
        if rc_file.exists():
            content = rc_file.read_text()
        else:
            content = ""
        if export_line not in content:
            with open(rc_file, "a") as f:
                f.write(f"\n# Add server command\n{export_line}\n")

    # ----- Activate PATH Immediately -----
    os.system("source ~/.bashrc 2>/dev/null || source ~/.zshrc 2>/dev/null")

    print("\\n🎉 Installation Complete!")
    print(f"👉 Default Port: {DEFAULT_PORT}")
    print("👉 Run: server help          → Show all commands")
    print("👉 Run: server               → Start on default/global port")
    print("👉 Run: server any           → Start on random port")
    print("👉 Run: server set-port 5000 → Change global default port")
    print("👉 Run: server stop all      → Stop all servers\\n")


if __name__ == "__main__":
    print(f"🚀 Running installer: {SCRIPT_NAME}")
    try:
        install_script()
    except Exception as e:
        print(f"❌ Installation failed:\\n{{e}}")
