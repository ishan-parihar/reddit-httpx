#!/usr/bin/env bash
set -euo pipefail

# ─── reddit-lyr installer ───────────────────────────────────────────────
# curl -sSL https://raw.githubusercontent.com/ishan-parihar/reddit-lyr/main/install.sh | bash
#
# Installs reddit-lyr globally using uv (preferred) or pipx/pip as fallback.
# Handles clean system setup including uv installation and dependency management.
# ──────────────────────────────────────────────────────────────────────────

REPO="https://github.com/ishan-parihar/reddit-lyr.git"
REPO_GIT="git+${REPO}"
BIN="reddit-lyr"
MIN_PYTHON_VERSION="3.11"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

info()  { echo -e "${GREEN}▸${NC} $*"; }
warn()  { echo -e "${YELLOW}▸${NC} $*"; }
err()   { echo -e "${RED}▸${NC} $*" >&2; }
step()  { echo -e "${BLUE}▸${NC} $*"; }

# ── Check Python ≥ 3.11 ──────────────────────────────────────────────────
check_python() {
    local py=""
    for cmd in python3 python3.14 python3.13 python3.12 python3.11; do
        if command -v "$cmd" &>/dev/null; then
            if "$cmd" -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)" 2>/dev/null; then
                py="$cmd"
                break
            fi
        fi
    done
    if [[ -z "$py" ]]; then
        err "Python ${MIN_PYTHON_VERSION}+ not found. Install it first:"
        err "  https://www.python.org/downloads/"
        exit 1
    fi
    info "Using $py ($($py --version 2>&1 | awk '{print $2}'))"
    echo "$py"
}

# ── Install uv if not present ─────────────────────────────────────────────
install_uv() {
    if command -v uv &>/dev/null; then
        info "uv already installed ($(uv --version))"
        return 0
    fi

    step "Installing uv (fast Python package installer)..."
    
    # Try installing uv via official installer
    if curl -LsSf https://astral.sh/uv/install.sh | sh; then
        # Source uv environment
        export PATH="$HOME/.local/bin:$PATH"
        if command -v uv &>/dev/null; then
            info "uv installed successfully ($(uv --version))"
            return 0
        fi
    fi

    warn "uv installation failed, falling back to pip-based installation"
    return 1
}

# ── Install via uv (preferred method) ───────────────────────────────────────
install_with_uv() {
    if ! command -v uv &>/dev/null; then
        return 1
    fi

    step "Installing $BIN using uv..."
    
    # Create a temporary directory for installation
    local tmp_dir
    tmp_dir=$(mktemp -d)
    cd "$tmp_dir"

    # Clone the repository
    if ! git clone --depth 1 "$REPO" . 2>/dev/null; then
        err "Failed to clone repository"
        cd - >/dev/null
        rm -rf "$tmp_dir"
        return 1
    fi

    # Install using uv pip (try different methods)
    if uv pip install --system . 2>/dev/null; then
        # Find the installed binary location
        local bin_path
        bin_path=$(which "$BIN" 2>/dev/null || true)
        
        if [[ -n "$bin_path" ]]; then
            info "Installed successfully at $bin_path"
            cd - >/dev/null
            rm -rf "$tmp_dir"
            return 0
        fi
    elif uv pip install . 2>/dev/null; then
        # Find the installed binary location
        local bin_path
        bin_path=$(which "$BIN" 2>/dev/null || true)
        
        if [[ -n "$bin_path" ]]; then
            info "Installed successfully at $bin_path"
            cd - >/dev/null
            rm -rf "$tmp_dir"
            return 0
        fi
    fi

    cd - >/dev/null
    rm -rf "$tmp_dir"
    return 1
}

# ── Try pipx first (cleanest global install) ──────────────────────────────
install_pipx() {
    local py="$1"
    if command -v pipx &>/dev/null; then
        step "Installing via pipx..."
        if pipx install --force "$REPO_GIT"; then
            return 0
        fi
    fi

    # Try installing pipx itself
    step "Installing pipx..."
    if "$py" -m pip install --user pipx &>/dev/null 2>&1; then
        "$py" -m pipx ensurepath 2>/dev/null || true
        export PATH="$HOME/.local/bin:$PATH"
        if command -v pipx &>/dev/null; then
            step "pipx installed. Installing $BIN via pipx..."
            if pipx install --force "$REPO_GIT"; then
                return 0
            fi
        fi
    fi
    return 1
}

# ── Fallback: pip install --user + symlink ────────────────────────────────
install_pip() {
    local py="$1"
    local pip_cmd="$py -m pip install --user"

    step "Installing via pip (user site)..."
    
    # Upgrade pip first
    "$py" -m pip install --upgrade --user pip 2>/dev/null || true

    if $pip_cmd --force-reinstall "$REPO_GIT" 2>/dev/null || \
       $pip_cmd "$REPO_GIT"; then

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
                warn "Could not locate installed binary. Check: $py -m pip show reddit-lyr"
                return 0
            fi
        fi

        # Ensure ~/.local/bin is in PATH
        ensure_path "$user_bin"
        return 0
    fi
    
    return 1
}

# ── Ensure directory is in PATH ────────────────────────────────────────────
ensure_path() {
    local dir="$1"
    if [[ ":$PATH:" != *":$dir:"* ]]; then
        warn "$dir is not in your PATH."
        warn "Add this to your shell profile (~/.bashrc, ~/.zshrc, etc.):"
        warn "  export PATH=\"\$HOME/.local/bin:\$PATH\""
        
        # Try to add it automatically for common shells
        local profile=""
        if [[ -n "${ZSH_VERSION:-}" ]]; then
            profile="$HOME/.zshrc"
        elif [[ -n "${BASH_VERSION:-}" ]]; then
            profile="$HOME/.bashrc"
        fi
        
        if [[ -n "$profile" && -w "$profile" ]]; then
            if ! grep -q "PATH.*$dir" "$profile" 2>/dev/null; then
                echo "" >> "$profile"
                echo "# Added by reddit-lyr installer" >> "$profile"
                echo "export PATH=\"\$HOME/.local/bin:\$PATH\"" >> "$profile"
                info "Added PATH to $profile"
            fi
        fi
    fi
}

# ── Install dependencies if needed ─────────────────────────────────────────
install_dependencies() {
    step "Checking system dependencies..."
    
    # Check for curl
    if ! command -v curl &>/dev/null; then
        warn "curl not found. Installing..."
        if command -v apt-get &>/dev/null; then
            sudo apt-get update -qq && sudo apt-get install -y curl
        elif command -v yum &>/dev/null; then
            sudo yum install -y curl
        elif command -v pacman &>/dev/null; then
            sudo pacman -S --noconfirm curl
        else
            warn "Could not install curl automatically. Please install it manually."
        fi
    fi
    
    # Check for git
    if ! command -v git &>/dev/null; then
        warn "git not found. Installing..."
        if command -v apt-get &>/dev/null; then
            sudo apt-get update -qq && sudo apt-get install -y git
        elif command -v yum &>/dev/null; then
            sudo yum install -y git
        elif command -v pacman &>/dev/null; then
            sudo pacman -S --noconfirm git
        else
            err "git is required but not found. Please install it manually."
            exit 1
        fi
    fi
}

# ── Verify ────────────────────────────────────────────────────────────────
verify() {
    # Ensure local bin is in PATH for verification
    export PATH="$HOME/.local/bin:$PATH"
    
    if command -v "$BIN" &>/dev/null; then
        local version
        version=$("$BIN" --help 2>&1 | head -1 || true)
        info "Installed successfully: $version"
        info "Run '$BIN --help' to get started"
        info "Run '$BIN --login' to import browser cookies"
        return 0
    else
        warn "Binary not found on PATH. You may need to restart your shell."
        info "Or run: $HOME/.local/bin/$BIN --help"
        return 1
    fi
}

# ── Main ──────────────────────────────────────────────────────────────────
main() {
    info "Installing reddit-lyr..."
    echo ""

    # Install system dependencies
    install_dependencies

    # Check Python
    local py
    py=$(check_python)
    echo ""

    # Try uv first (preferred)
    if install_uv; then
        if install_with_uv; then
            echo ""
            verify
            exit 0
        fi
        warn "uv installation failed, trying pipx..."
    fi

    # Try pipx
    if install_pipx "$py"; then
        info "pipx install complete"
    # Fallback to pip
    elif install_pip "$py"; then
        info "pip install complete"
    else
        err "Install failed. Try manually:"
        err "  git clone $REPO && cd reddit-lyr && pip install -e ."
        exit 1
    fi

    echo ""
    verify
}

main "$@"
