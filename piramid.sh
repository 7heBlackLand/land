#!/bin/bash
# ==========================================================
#   MA'AT SCRIPT - Balance and Order for Python Projects ⚖️
#   Inspired by the Egyptian goddess of truth & harmony
#
#   📝 Egyptian-inspired name ideas:
#     ankh.sh     → Ankh = ancient Egyptian symbol of life 🔑
#     ra.sh       → Named after Ra, the Egyptian sun god ☀️
#     pyramid.sh  → Strong, structured, and easy to remember ⛰️
#     nile.sh     → The Nile river = lifeline of Egypt 🌊
#     scarab.sh   → Sacred scarab beetle = rebirth + protection 🪲
#     maat.sh     → Goddess of truth, order, and balance ⚖️
#
#   📖 What this script does:
#     1. Creates and manages a Python virtual environment.
#     2. Installs dependencies from requirements.txt (or creates it).
#     3. Automatically installs any missing Python packages if errors occur.
#     4. Updates requirements.txt with exact versions + metadata.
#     5. Runs a target Python file (defaults to app.py).
#     6. Logs errors and package snapshots inside requirements.txt.
# ==========================================================
# ==========================================================
#   PIRAMID SCRIPT ⛰️ + Installer
#   Balance and Order for Python Projects
# ==========================================================
#   Features:
#     ✅ Python virtualenv তৈরি ও ম্যানেজ
#     ✅ requirements.txt install/create
#     ✅ Missing package auto-install
#     ✅ requirements.txt metadata আপডেট
#     ✅ Error log capture
#     ✅ Self-installer → .bashrc / .zshrc এ piramid() ফাংশন যোগ করবে
# ==========================================================

SCRIPT_DIR="/home/gost/env-home/"
VENV_DIR="$SCRIPT_DIR/env"
REQ_FILE="$SCRIPT_DIR/requirements.txt"
TMP_LOG="$SCRIPT_DIR/.tmp_error.log"
DEFAULT_FILE="app.py"

# =============================
# Self installer function
# =============================
install_self() {
    LINE='piramid() { source /home/gost/env-home/bin/piramid.sh "$@"; }'
    COMMENT='# Added by PIRAMID setup script'

    if [[ "$SHELL" == *"zsh" ]]; then
        RC_FILE="$HOME/.zshrc"
    elif [[ "$SHELL" == *"bash" ]]; then
        RC_FILE="$HOME/.bashrc"
    else
        echo "⚠️ Unknown shell: $SHELL"
        return
    fi

    # ডুপ্লিকেট এন্ট্রি আছে কিনা চেক করো
    if grep -Fxq "$LINE" "$RC_FILE"; then
        echo "✅ PIRAMID already installed in $RC_FILE"
    else
        {
            echo ""
            echo "$COMMENT"
            echo "$LINE"
        } >> "$RC_FILE"
        echo "✅ PIRAMID function added to $RC_FILE"
        echo "🔄 Reloading $RC_FILE ..."
        source "$RC_FILE"
    fi
}

# =============================
# Run installer only first time
# =============================
if ! command -v piramid >/dev/null 2>&1; then
    echo "⚙️ First time setup: installing PIRAMID function..."
    install_self
fi

# =============================
# তারপর নিচে আগের virtualenv logic
# =============================

# ---------------- MAIN PIRAMID SCRIPT ----------------

# 1. Create virtual environment if not exists
if [ ! -d "$VENV_DIR" ]; then
    echo "⚙️ Creating virtual environment..."
    python3 -m venv "$VENV_DIR" || {
        echo "❌ Failed to create virtual environment."
        exit 1
    }
fi

# 2. Find activation script
ACTIVATE="$VENV_DIR/bin/activate"
[ -f "$VENV_DIR/Scripts/activate" ] && ACTIVATE="$VENV_DIR/Scripts/activate"

if [ ! -f "$ACTIVATE" ]; then
    echo "❌ Activation script not found."
    exit 1
fi

# Activate
source "$ACTIVATE"
echo "✅ Virtualenv activated: $VENV_DIR"

# 3. Upgrade pip
pip install --upgrade pip >/dev/null 2>&1

# 4. Install or create requirements.txt
if [ -f "$REQ_FILE" ]; then
    pip install -r "$REQ_FILE" >/dev/null 2>&1
else
    echo "⚠️ requirements.txt not found, creating a new one..."
    touch "$REQ_FILE"
fi

# 5. Function to run Python file
run_python_file() {
    python "$1" "${@:2}" 2> >(tee "$TMP_LOG" >&2)
    return $?
}

# 6. Run Python file
EXIT_CODE=0
ERROR_OUTPUT=""

if [ $# -gt 0 ]; then
    TARGET_FILE="$1"
    shift
else
    TARGET_FILE="$DEFAULT_FILE"
fi

if [ -f "$TARGET_FILE" ]; then
    echo "🚀 Running: $TARGET_FILE ..."
    run_python_file "$TARGET_FILE" "$@"
    EXIT_CODE=$?
    ERROR_OUTPUT=$(cat "$TMP_LOG")

    if [ $EXIT_CODE -ne 0 ]; then
        MISSING_PKGS=$(grep -oP "ModuleNotFoundError: No module named '\K[^']+" "$TMP_LOG" | sort -u)
        if [ -n "$MISSING_PKGS" ]; then
            echo "📦 Missing packages detected: $MISSING_PKGS"
            for pkg in $MISSING_PKGS; do
                echo "➡️ Installing: $pkg ..."
                if pip install "$pkg" >/dev/null 2>&1; then
                    VERSION=$(pip show "$pkg" | grep Version | awk '{print $2}')
                    REQ_LINE="${pkg}==${VERSION}"
                    if ! grep -Fxq "$REQ_LINE" "$REQ_FILE"; then
                        echo "$REQ_LINE" >> "$REQ_FILE"
                        echo "✅ $REQ_LINE added to requirements.txt"
                    fi
                else
                    echo "❌ Failed to install $pkg."
                fi
            done
            echo "🔄 Retrying..."
            run_python_file "$TARGET_FILE" "$@"
            EXIT_CODE=$?
            ERROR_OUTPUT=$(cat "$TMP_LOG")
        else
            echo "❌ Some other error occurred:"
            cat "$TMP_LOG"
        fi
    fi
else
    echo "❌ File not found: $TARGET_FILE"
    EXIT_CODE=1
fi

# 7. Update requirements.txt metadata
sed -i '/^# Requirements metadata$/,$d' "$REQ_FILE"
PY_VER=$(python3 --version 2>&1)
FILE_SIZE=$(stat -f%z "$REQ_FILE" 2>/dev/null || stat -c%s "$REQ_FILE")
FILE_SIZE_HR=$(du -h "$REQ_FILE" | awk '{print $1}')
PKG_LIST=$(pip freeze)

{
    echo ""
    echo "# Requirements metadata"
    echo "# Generated: $(date)"
    echo "# Python version: $PY_VER"
    echo "# Virtualenv: $VENV_DIR"
    echo "# File size: ${FILE_SIZE} bytes (${FILE_SIZE_HR})"
    echo "# Exit Code: $EXIT_CODE"
    echo "# ----------------------------------------"
    echo "# Package list snapshot:"
    echo "$PKG_LIST" | sed 's/^/# /'
    echo "# ----------------------------------------"
    echo "# Error log (if any):"
    echo "$ERROR_OUTPUT" | sed 's/^/# /'
    echo "# ========================================"
} >> "$REQ_FILE"

rm -f "$TMP_LOG"
