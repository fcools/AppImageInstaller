#!/bin/bash
"""
Build script for creating native distribution packages.

Creates .deb, .rpm, and other native packages for easy installation
on different Linux distributions.
"""

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Project information
PROJECT_NAME="appimage-installer"
VERSION="1.1.0"
DESCRIPTION="Simple tool for managing AppImage files on Linux"
MAINTAINER="AppImage Installer Project <contact@example.com>"
HOMEPAGE="https://github.com/fcools/AppImageInstaller"

# Build directory
BUILD_DIR="$(pwd)/build"
DIST_DIR="$(pwd)/dist"

echo -e "${GREEN}Building AppImage Installer packages...${NC}"

# Clean previous builds
rm -rf "$BUILD_DIR" "$DIST_DIR"
mkdir -p "$BUILD_DIR" "$DIST_DIR"

# Function to build DEB package
build_deb() {
    echo -e "${YELLOW}Building .deb package...${NC}"
    
    DEB_DIR="$BUILD_DIR/deb"
    mkdir -p "$DEB_DIR"
    
    # Create directory structure
    mkdir -p "$DEB_DIR/usr/local/bin"
    mkdir -p "$DEB_DIR/usr/local/lib/appimage-installer"
    mkdir -p "$DEB_DIR/DEBIAN"
    mkdir -p "$DEB_DIR/usr/share/applications"
    mkdir -p "$DEB_DIR/usr/share/doc/$PROJECT_NAME"
    
    # Copy application files
    cp -r ../src/* "$DEB_DIR/usr/local/lib/appimage-installer/"
    
    # Create wrapper script
    cat > "$DEB_DIR/usr/local/bin/appimage-installer" << 'EOF'
#!/bin/bash
cd /usr/local/lib/appimage-installer
python3 -m main "$@"
EOF
    chmod +x "$DEB_DIR/usr/local/bin/appimage-installer"
    
    # Create desktop file for file associations
    cat > "$DEB_DIR/usr/share/applications/appimage-installer.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=AppImage Installer
Comment=Install and manage AppImage applications
Exec=/usr/local/bin/appimage-installer %f
Icon=application-x-executable
StartupNotify=false
NoDisplay=true
MimeType=application/x-appimage;
Categories=System;
EOF
    
    # Create control file
    cat > "$DEB_DIR/DEBIAN/control" << EOF
Package: $PROJECT_NAME
Version: $VERSION
Section: utils
Priority: optional
Architecture: all
Depends: python3 (>= 3.8), python3-gi, python3-pil, python3-magic
Maintainer: $MAINTAINER
Description: $DESCRIPTION
 Makes AppImage installation as easy as double-clicking, with automatic
 desktop integration and native system dialogs.
Homepage: $HOMEPAGE
EOF
    
    # Create postinst script
    cat > "$DEB_DIR/DEBIAN/postinst" << 'EOF'
#!/bin/bash
set -e

# Register file associations
if [ "$1" = "configure" ]; then
    # Update MIME database
    if command -v update-mime-database >/dev/null 2>&1; then
        update-mime-database /usr/share/mime || true
    fi
    
    # Update desktop database
    if command -v update-desktop-database >/dev/null 2>&1; then
        update-desktop-database /usr/share/applications || true
    fi
    
    echo "AppImage Installer has been installed successfully!"
    echo "You can now double-click AppImage files to install them."
fi
EOF
    chmod +x "$DEB_DIR/DEBIAN/postinst"
    
    # Create prerm script
    cat > "$DEB_DIR/DEBIAN/prerm" << 'EOF'
#!/bin/bash
set -e

if [ "$1" = "remove" ]; then
    # Unregister file associations
    /usr/local/bin/appimage-installer --unregister || true
fi
EOF
    chmod +x "$DEB_DIR/DEBIAN/prerm"
    
    # Copy documentation
    cp ../README.md "$DEB_DIR/usr/share/doc/$PROJECT_NAME/"
    
    # Build the package
    dpkg-deb --build "$DEB_DIR" "$DIST_DIR/${PROJECT_NAME}_${VERSION}_all.deb"
    
    echo -e "${GREEN}✓ DEB package created: $DIST_DIR/${PROJECT_NAME}_${VERSION}_all.deb${NC}"
}

# Function to build RPM package
build_rpm() {
    echo -e "${YELLOW}Building .rpm package...${NC}"
    
    if ! command -v rpmbuild >/dev/null 2>&1; then
        echo -e "${RED}rpmbuild not found. Install rpm-build package.${NC}"
        return 1
    fi
    
    RPM_DIR="$BUILD_DIR/rpm"
    mkdir -p "$RPM_DIR"/{BUILD,RPMS,SOURCES,SPECS,SRPMS}
    
    # Create tarball
    TAR_NAME="${PROJECT_NAME}-${VERSION}"
    tar -czf "$RPM_DIR/SOURCES/$TAR_NAME.tar.gz" -C .. \
        --transform "s,^,$TAR_NAME/," \
        src/ README.md requirements.txt
    
    # Create spec file
    cat > "$RPM_DIR/SPECS/$PROJECT_NAME.spec" << EOF
Name:           $PROJECT_NAME
Version:        $VERSION
Release:        1%{?dist}
Summary:        $DESCRIPTION
License:        MIT
URL:            $HOMEPAGE
Source0:        %{name}-%{version}.tar.gz
BuildArch:      noarch

Requires:       python3 >= 3.8
Requires:       python3-gobject
Requires:       python3-pillow
Requires:       python3-magic

%description
Makes AppImage installation as easy as double-clicking, with automatic
desktop integration and native system dialogs.

%prep
%setup -q

%build
# Nothing to build

%install
rm -rf %{buildroot}
mkdir -p %{buildroot}/usr/local/bin
mkdir -p %{buildroot}/usr/local/lib/%{name}
mkdir -p %{buildroot}/usr/share/applications

# Install application files
cp -r src/* %{buildroot}/usr/local/lib/%{name}/

# Create wrapper script
cat > %{buildroot}/usr/local/bin/%{name} << 'EOFWRAPPER'
#!/bin/bash
cd /usr/local/lib/%{name}
python3 -m main "\$@"
EOFWRAPPER
chmod +x %{buildroot}/usr/local/bin/%{name}

# Install desktop file
cat > %{buildroot}/usr/share/applications/%{name}.desktop << EOFDESKTOP
[Desktop Entry]
Version=1.0
Type=Application
Name=AppImage Installer
Comment=Install and manage AppImage applications
Exec=/usr/local/bin/%{name} %%f
Icon=application-x-executable
StartupNotify=false
NoDisplay=true
MimeType=application/x-appimage;
Categories=System;
EOFDESKTOP

%files
/usr/local/bin/%{name}
/usr/local/lib/%{name}/*
/usr/share/applications/%{name}.desktop

%post
# Update databases
update-mime-database /usr/share/mime &>/dev/null || :
update-desktop-database /usr/share/applications &>/dev/null || :

%preun
# Unregister file associations
/usr/local/bin/%{name} --unregister &>/dev/null || :

%changelog
* $(date '+%a %b %d %Y') Packager <packager@example.com> - $VERSION-1
- Initial package
EOF
    
    # Build the RPM
    rpmbuild --define "_topdir $RPM_DIR" -ba "$RPM_DIR/SPECS/$PROJECT_NAME.spec"
    
    # Copy to dist directory
    cp "$RPM_DIR/RPMS/noarch/${PROJECT_NAME}-${VERSION}-1"*.rpm "$DIST_DIR/"
    
    echo -e "${GREEN}✓ RPM package created in $DIST_DIR/${NC}"
}

# Function to create installation script
create_install_script() {
    echo -e "${YELLOW}Creating installation script...${NC}"
    
    cat > "$DIST_DIR/install.sh" << 'EOF'
#!/bin/bash
# AppImage Installer - Easy Installation Script

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}AppImage Installer - Installation Script${NC}"
echo "======================================="

# Detect distribution
if [ -f /etc/os-release ]; then
    . /etc/os-release
    DISTRO=$ID
    VERSION_ID=$VERSION_ID
else
    echo -e "${RED}Cannot detect Linux distribution${NC}"
    exit 1
fi

echo -e "Detected distribution: ${GREEN}$PRETTY_NAME${NC}"

# Function to install dependencies
install_dependencies() {
    echo -e "${YELLOW}Installing dependencies...${NC}"
    
    case $DISTRO in
        ubuntu|debian|linuxmint)
            sudo apt update
            sudo apt install -y python3 python3-pip python3-gi python3-gi-cairo \
                gir1.2-gtk-3.0 python3-pil python3-magic libmagic1
            ;;
        fedora)
            sudo dnf install -y python3 python3-pip python3-gobject gtk3-devel \
                python3-pillow python3-magic
            ;;
        centos|rhel)
            sudo yum install -y python3 python3-pip python3-gobject gtk3-devel \
                python3-pillow python3-magic
            ;;
        arch|manjaro)
            sudo pacman -S --needed python python-pip python-gobject gtk3 \
                python-pillow python-magic
            ;;
        opensuse*|sled|sles)
            sudo zypper install -y python3 python3-pip python3-gobject \
                gtk3-devel python3-Pillow python3-magic
            ;;
        *)
            echo -e "${YELLOW}Unknown distribution. Please install manually:${NC}"
            echo "- Python 3.8+"
            echo "- python3-pip"
            echo "- python3-gobject (GTK bindings)"
            echo "- python3-pillow (image processing)"
            echo "- python3-magic (file type detection)"
            read -p "Continue anyway? (y/N): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                exit 1
            fi
            ;;
    esac
}

# Function to download and install
install_appimage_installer() {
    echo -e "${YELLOW}Installing AppImage Installer...${NC}"
    
    # Create temporary directory
    TEMP_DIR=$(mktemp -d)
    cd "$TEMP_DIR"
    
    # Download source
    echo "Downloading source code..."
         curl -L https://github.com/fcools/AppImageInstaller/archive/main.tar.gz \
         -o appimage-installer.tar.gz
    
    # Extract
    tar -xzf appimage-installer.tar.gz
    cd AppImageInstaller-main
    
    # Install using pip
    pip3 install --user .
    
    # Add ~/.local/bin to PATH if not already there
    if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
        export PATH="$HOME/.local/bin:$PATH"
    fi
    
    # Register file associations
    echo "Registering file associations..."
    appimage-installer --register
    
    # Cleanup
    cd /
    rm -rf "$TEMP_DIR"
}

# Main installation
echo -e "${YELLOW}This script will install AppImage Installer and its dependencies.${NC}"
read -p "Continue? (Y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Nn]$ ]]; then
    exit 0
fi

install_dependencies
install_appimage_installer

echo
echo -e "${GREEN}✓ AppImage Installer has been installed successfully!${NC}"
echo
echo -e "${BLUE}Usage:${NC}"
echo "• Double-click any .AppImage file to install it"
echo "• Or run: appimage-installer myapp.AppImage"
echo
echo -e "${BLUE}Commands:${NC}"
echo "• appimage-installer --register    # Register file associations"
echo "• appimage-installer --unregister  # Unregister file associations"
echo "• appimage-installer --help        # Show help"
echo
echo -e "${YELLOW}Note: You may need to log out and log back in for file associations to work.${NC}"
EOF
    
    chmod +x "$DIST_DIR/install.sh"
    echo -e "${GREEN}✓ Installation script created: $DIST_DIR/install.sh${NC}"
}

# Function to create Flatpak manifest
create_flatpak_manifest() {
    echo -e "${YELLOW}Creating Flatpak manifest...${NC}"
    
    mkdir -p "$BUILD_DIR/flatpak"
    
    cat > "$BUILD_DIR/flatpak/org.example.AppImageInstaller.yml" << EOF
app-id: org.example.AppImageInstaller
runtime: org.freedesktop.Platform
runtime-version: '22.08'
sdk: org.freedesktop.Sdk
command: appimage-installer
finish-args:
  - --share=ipc
  - --socket=x11
  - --socket=wayland
  - --device=dri
  - --filesystem=home
  - --filesystem=/tmp
  - --share=network
  - --talk-name=org.freedesktop.FileManager1

modules:
  - name: appimage-installer
    buildsystem: simple
    build-commands:
      - pip3 install --prefix=/app .
    sources:
      - type: dir
        path: ../..
EOF
    
    echo -e "${GREEN}✓ Flatpak manifest created: $BUILD_DIR/flatpak/org.example.AppImageInstaller.yml${NC}"
    echo -e "${YELLOW}To build Flatpak: flatpak-builder build-dir org.example.AppImageInstaller.yml${NC}"
}

# Main execution
echo "Select packages to build:"
echo "1) All packages"
echo "2) DEB package only" 
echo "3) RPM package only"
echo "4) Installation script only"
echo "5) Flatpak manifest only"
read -p "Enter choice (1-5): " choice

case $choice in
    1)
        build_deb
        build_rpm
        create_install_script
        create_flatpak_manifest
        ;;
    2)
        build_deb
        ;;
    3)
        build_rpm
        ;;
    4)
        create_install_script
        ;;
    5)
        create_flatpak_manifest
        ;;
    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

echo
echo -e "${GREEN}Build complete! Check the $DIST_DIR directory.${NC}"
echo
echo -e "${BLUE}Installation options for users:${NC}"
echo "• DEB: sudo dpkg -i ${PROJECT_NAME}_${VERSION}_all.deb"
echo "• RPM: sudo rpm -i ${PROJECT_NAME}-${VERSION}-1.*.rpm"  
echo "• Script: bash install.sh"
echo "• Flatpak: Use the manifest to build and install" 