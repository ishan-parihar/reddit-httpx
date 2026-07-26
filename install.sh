#!/usr/bin/env bash
set -euo pipefail

# ─── reddit-httpx installer ───────────────────────────────────────────────
# curl -sSL https://raw.githubusercontent.com/ishan-parihar/reddit-httpx/main/install.sh | bash
#
# Installs reddit-httpx globally via pipx (preferred) or pip + manual PATH.
# ──────────────────────────────────────────────────────────────────────────

REPO="https://github.com/ishan-parihar/reddit-httpx.git"
BIN="reddit-httpx"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()  { echo -e "${GREEN}▸${NC} $*"; }
warn()  { echo -e "${YELLOW}▸${NC} $*"; }
err()   { echo -e "${RED}▸${NC} $*" >&2; }

# ── Check Python ≥ 3.12 ──────────────────────────────────────────────────
check_python() {
    local py=""
    for cmd in python3 python3.14 python3.13 python3.12; do
        if command -v "$cmd" &>/dev/null; then
            if "$cmd" -c "import sys; exit(0 if sys.version_info >= (3, 12) else 1)" 2>/dev/null; then
                py="$cmd"
                break
            fi
        fi
    done
    if [[ -z "$py" ]]; then
        err "Python 3.12+ not found. Install it first:"
        err "  https://www.python.org/downloads/"
        exit 1
    fi
    info "Using $py ($($py --version 2>&1 | awk '{print $2}'))"
    echo "$py"
}

# ── Try pipx first (cleanest global install) ──────────────────────────────
install_pipx() {
    local py="$1"
    if command -v pipx &>/dev/null; then
        info "Installing via pipx..."
        pipx install --force "$REPO"
        return 0
    fi

    # Try installing pipx itself
    if "$py" -m pip install --user pipx &>/dev/null 2>&1; then
        "$py" -m pipx ensurepath 2>/dev/null || true
        export PATH="$HOME/.local/bin:$PATH"
        if command -v pipx &>/dev/null; then
            info "pipx installed. Installing $BIN via pipx..."
            pipx install --force "$REPO"
            return 0
        fi
    fi
    return 1
}

# ── Fallback: pip install --user + symlink ────────────────────────────────
install_pip() {
    local py="$1"
    local pip_cmd="$py -m pip install --user"

    info "Installing via pip (user site)..."
    $pip_cmd --force-reinstall "git+${REPO}.git" 2>/dev/null \
        || $pip_cmd "git+${REPO}.git"

    # Find the installed binary
    local user_bin="$HOME/.local/bin"
    if [[ -f "$user_bin/$BIN" ]]; then
        info "Binary at $user_bin/$BIN"
    else
        # pip install --user may put scripts somewhere else
        local site_bin
        site_bin=$("$py" -c "import site; print(site.USER_SITE)" 2>/dev/null | sed 's|site-packages|scripts|')
        if [[ -f "$site_bin/$BIN" ]]; then
            info "Binary at $site_bin/$BIN"
            mkdir -p "$user_bin"
            ln -sf "$site_bin/$BIN" "$user_bin/$BIN"
        else
            warn "Could not locate installed binary. Check: $py -m pip show reddit-httpx-mcp"
            return 0
        fi
    fi

    # Ensure ~/.local/bin is in PATH
    if [[ ":$PATH:" != *":$user_bin:"* ]]; then
        warn "$user_bin is not in your PATH."
        warn "Add this to your shell profile (~/.bashrc, ~/.zshrc, etc.):"
        warn "  export PATH=\"\$HOME/.local/bin:\$PATH\""
    fi
}

# ── Verify ────────────────────────────────────────────────────────────────
verify() {
    export PATH="$HOME/.local/bin:$PATH"
    if command -v "$BIN" &>/dev/null; then
        local version
        version=$("$BIN" --help 2>&1 | head -1 || true)
        info "Installed successfully: $version"
        info "Run '$BIN --help' to get started"
        info "Run '$BIN --login' to import browser cookies"
    else
        warn "Binary not found on PATH. You may need to restart your shell."
        info "Or run: $HOME/.local/bin/$BIN --help"
    fi
}

# ── Main ──────────────────────────────────────────────────────────────────
main() {
    info "Installing reddit-httpx..."
    echo ""

    local py
    py=$(check_python)

    if install_pipx "$py"; then
        info "pipx install complete"
    elif install_pip "$py"; then
        info "pip install complete"
    else
        err "Install failed. Try manually:"
        err "  git clone $REPO && cd reddit-httpx && pip install -e ."
        exit 1
    fi

    echo ""
    verify
}

main "$@"
