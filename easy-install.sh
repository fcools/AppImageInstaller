#!/bin/bash
# AppImage Installer - One-Command Installation
# 
# This script automatically installs AppImage Installer on any Linux distribution
# Usage: curl -sSL https://raw.githubusercontent.com/fcools/AppImageInstaller/main/easy-install.sh | bash

set -e

# Colors for pretty output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# ASCII Art Header
echo -e "${BLUE}${BOLD}"
cat << "EOF"
   ___              ____                            ____           __        ____         
  / _ | ___  ___   /  _/_ _  ___ ____ ____         /  _/___  ___ / /____ _ / / /__ ____  
 / __ |/ _ \/ _ \ _/ //  ' \/ _ `/ _ `/ -_)       _/ // _ \(_-</ __/ _ `/ / / / -_) __/  
/_/ |_/ .__/ .__/___//_/_/_/\_,_/\_, /\__/       /___/_//_/___/\__/\_,_/_/_/_/\__/_/     
     /_/  /_/                  /___/                                                    
EOF
echo -e "${NC}"

echo -e "${BOLD}Easy Installation Script${NC}"
echo "========================"
echo
echo -e "${YELLOW}This script will install AppImage Installer and make .AppImage files${NC}"
echo -e "${YELLOW}installable with a simple double-click!${NC}"
echo

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo -e "${RED}❌ Please don't run this script as root (sudo)${NC}"
    echo -e "${YELLOW}The installer will ask for sudo when needed.${NC}"
    exit 1
fi

# Detect distribution
echo -e "${BLUE}🔍 Detecting your Linux distribution...${NC}"
if [ -f /etc/os-release ]; then
    . /etc/os-release
    DISTRO=$ID
    DISTRO_NAME="$PRETTY_NAME"
    echo -e "${GREEN}✓ Detected: $DISTRO_NAME${NC}"
else
    echo -e "${RED}❌ Cannot detect Linux distribution${NC}"
    exit 1
fi

# Check for required commands
check_command() {
    if ! command -v "$1" >/dev/null 2>&1; then
        echo -e "${RED}❌ Required command '$1' not found${NC}"
        return 1
    fi
}

echo -e "${BLUE}🔍 Checking system requirements...${NC}"

# Essential commands check
MISSING_COMMANDS=()
for cmd in python3 curl; do
    if ! check_command "$cmd"; then
        MISSING_COMMANDS+=("$cmd")
    fi
done

if [ ${#MISSING_COMMANDS[@]} -ne 0 ]; then
    echo -e "${RED}❌ Missing required commands: ${MISSING_COMMANDS[*]}${NC}"
    echo -e "${YELLOW}Please install them first and try again.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ System requirements met${NC}"

# Function to install dependencies based on distribution
install_dependencies() {
    echo -e "${BLUE}📦 Installing dependencies...${NC}"
    
    case $DISTRO in
        ubuntu|debian|linuxmint|pop|elementary)
            echo -e "${YELLOW}Installing packages for Debian/Ubuntu...${NC}"
            sudo apt update >/dev/null 2>&1
            sudo apt install -y python3-pip python3-gi python3-gi-cairo \
                gir1.2-gtk-3.0 python3-pil python3-magic libmagic1 \
                python3-packaging python3-tk >/dev/null 2>&1
            ;;
        fedora)
            echo -e "${YELLOW}Installing packages for Fedora...${NC}"
            sudo dnf install -y python3-pip python3-gobject gtk3-devel \
                python3-pillow python3-magic >/dev/null 2>&1
            ;;
        centos|rhel|rocky|almalinux)
            echo -e "${YELLOW}Installing packages for RHEL/CentOS...${NC}"
            sudo yum install -y python3-pip python3-gobject gtk3-devel \
                python3-pillow python3-magic >/dev/null 2>&1
            ;;
        arch|manjaro|endeavouros)
            echo -e "${YELLOW}Installing packages for Arch Linux...${NC}"
            sudo pacman -S --needed --noconfirm python-pip python-gobject gtk3 \
                python-pillow python-magic >/dev/null 2>&1
            ;;
        opensuse-leap|opensuse-tumbleweed|sled|sles)
            echo -e "${YELLOW}Installing packages for openSUSE...${NC}"
            sudo zypper install -y python3-pip python3-gobject \
                gtk3-devel python3-Pillow python3-magic >/dev/null 2>&1
            ;;
        *)
            echo -e "${YELLOW}⚠️  Unknown distribution: $DISTRO${NC}"
            echo -e "${YELLOW}Please ensure you have these packages installed:${NC}"
            echo "  • python3-pip"
            echo "  • python3-gobject (GTK bindings)"
            echo "  • python3-pillow (image processing)" 
            echo "  • python3-magic (file type detection)"
            echo
            read -p "Continue anyway? (y/N): " -n 1 -r < /dev/tty
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                exit 1
            fi
            ;;
    esac
    
    echo -e "${GREEN}✓ Dependencies installed${NC}"
}

# Function to install AppImage Installer
install_appimage_installer() {
    echo -e "${BLUE}🚀 Installing AppImage Installer...${NC}"
    
    # Create temporary directory
    TEMP_DIR=$(mktemp -d)
    cd "$TEMP_DIR"
    
    # Download source code
    echo -e "${YELLOW}📥 Downloading source code...${NC}"
    curl -sSL https://github.com/fcools/AppImageInstaller/archive/main.tar.gz \
        -o appimage-installer.tar.gz
    
    if [ ! -f appimage-installer.tar.gz ]; then
        echo -e "${RED}❌ Failed to download source code${NC}"
        exit 1
    fi
    
    # Extract
    echo -e "${YELLOW}📂 Extracting files...${NC}"
    tar -xzf appimage-installer.tar.gz
    cd AppImageInstaller-main
    
    # Install using pip (user install to avoid permission issues)
    echo -e "${YELLOW}🔧 Installing AppImage Installer...${NC}"
    
    # Handle Ubuntu 24.04+ externally managed environment
    if python3 -m pip install --user . >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Installed using pip${NC}"
    else
        echo -e "${YELLOW}Using fallback method for externally managed environment...${NC}"
        # Install dependencies from system packages and install without deps
        if [[ "$DISTRO" == "ubuntu" ]]; then
            sudo apt install -y python3-packaging >/dev/null 2>&1
        fi
        python3 -m pip install --user --break-system-packages --no-deps . >/dev/null 2>&1
    fi
    
    # Ensure ~/.local/bin is in PATH
    LOCAL_BIN="$HOME/.local/bin"
    if [[ ":$PATH:" != *":$LOCAL_BIN:"* ]]; then
        echo -e "${YELLOW}🔧 Adding $LOCAL_BIN to PATH...${NC}"
        
        # Add to .bashrc
        if [ -f "$HOME/.bashrc" ]; then
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
        fi
        
        # Add to .profile as fallback
        if [ -f "$HOME/.profile" ]; then
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.profile"
        fi
        
        # Export for current session
        export PATH="$LOCAL_BIN:$PATH"
    fi
    
    # Register file associations
    echo -e "${YELLOW}🔗 Registering file associations...${NC}"
    "$LOCAL_BIN/appimage-installer" --register >/dev/null 2>&1 || {
        echo -e "${YELLOW}⚠️  File association registration may require re-login${NC}"
    }
    
    # Cleanup
    cd /
    rm -rf "$TEMP_DIR"
    
    echo -e "${GREEN}✓ AppImage Installer installed successfully!${NC}"
}

# Function to test installation
test_installation() {
    echo -e "${BLUE}🧪 Testing installation...${NC}"
    
    if command -v appimage-installer >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Command 'appimage-installer' is available${NC}"
        
        # Test version command
        if appimage-installer --version >/dev/null 2>&1; then
            echo -e "${GREEN}✓ AppImage Installer is working correctly${NC}"
        else
            echo -e "${YELLOW}⚠️  AppImage Installer command exists but may have issues${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  Command not immediately available - may need re-login${NC}"
    fi
}

# Main installation process
echo -e "${BOLD}Ready to install AppImage Installer!${NC}"
echo
echo -e "${YELLOW}This will:${NC}"
echo "  • Install Python dependencies"
echo "  • Download and install AppImage Installer"
echo "  • Register .AppImage file associations"
echo "  • Enable double-click installation of AppImage files"
echo
read -p "Continue? (Y/n): " -n 1 -r < /dev/tty
echo

if [[ $REPLY =~ ^[Nn]$ ]]; then
    echo -e "${YELLOW}Installation cancelled.${NC}"
    exit 0
fi

echo
echo -e "${BOLD}🎬 Starting installation...${NC}"
echo

# Run installation steps
install_dependencies
install_appimage_installer
test_installation

echo
echo -e "${GREEN}${BOLD}🎉 Installation completed successfully!${NC}"
echo
echo -e "${BLUE}${BOLD}How to use:${NC}"
echo -e "${GREEN}✓${NC} Double-click any .AppImage file to install it"
echo -e "${GREEN}✓${NC} Run: ${BOLD}appimage-installer myapp.AppImage${NC}"
echo
echo -e "${BLUE}${BOLD}Available commands:${NC}"
echo -e "  ${BOLD}appimage-installer --register${NC}    # Register file associations"
echo -e "  ${BOLD}appimage-installer --unregister${NC}  # Unregister file associations"
echo -e "  ${BOLD}appimage-installer --help${NC}        # Show help"
echo
echo -e "${YELLOW}${BOLD}📝 Note:${NC} You may need to log out and log back in for"
echo -e "${YELLOW}file associations to work properly.${NC}"
echo
echo -e "${GREEN}${BOLD}🚀 AppImage Installer is ready to use!${NC}"
echo -e "${BLUE}Download any .AppImage file and double-click to try it out!${NC}" 