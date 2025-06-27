# Packaging Guide for AppImage Installer

This directory contains tools and configurations for packaging AppImage Installer for different Linux distributions and package managers.

## 📦 Available Package Formats

### 1. Native Distribution Packages
- **DEB packages** - For Debian, Ubuntu, Linux Mint, etc.
- **RPM packages** - For Fedora, RHEL, CentOS, openSUSE, etc.

### 2. Universal Packages
- **Flatpak** - Cross-distribution sandboxed packages
- **Snap** - Ubuntu's universal package format (planned)

### 3. Installation Scripts
- **easy-install.sh** - One-command installation for any distribution
- **install.sh** - Generic installation script from source

## 🛠️ Building Packages

### Prerequisites

Install required build tools:

**For DEB packages:**
```bash
sudo apt install dpkg-dev
```

**For RPM packages:**
```bash
# Fedora/RHEL
sudo dnf install rpm-build rpmlint

# Ubuntu/Debian
sudo apt install rpm
```

**For Flatpak:**
```bash
sudo apt install flatpak-builder  # Ubuntu/Debian
sudo dnf install flatpak-builder  # Fedora
```

### Building All Packages

Run the interactive build script:

```bash
cd packaging
./build-packages.sh
```

Select from the menu:
1. **All packages** - Build DEB, RPM, and create installation scripts
2. **DEB package only** - For Debian/Ubuntu distributions  
3. **RPM package only** - For Red Hat based distributions
4. **Installation script only** - Create portable installation script
5. **Flatpak manifest only** - Generate Flatpak build configuration

### Building Individual Packages

#### DEB Package
```bash
cd packaging
./build-packages.sh
# Select option 2
```

Creates: `dist/appimage-installer_1.0.0_all.deb`

#### RPM Package  
```bash
cd packaging
./build-packages.sh
# Select option 3
```

Creates: `dist/appimage-installer-1.0.0-1.noarch.rpm`

#### Flatpak
```bash
cd packaging
./build-packages.sh
# Select option 5

# Then build the Flatpak
cd build/flatpak
flatpak-builder build-dir org.example.AppImageInstaller.yml --install
```

## 📋 Package Details

### DEB Package Information
- **Package Name**: `appimage-installer`
- **Architecture**: `all` (architecture-independent)
- **Dependencies**: 
  - `python3 (>= 3.8)`
  - `python3-gi`
  - `python3-pil` 
  - `python3-magic`
- **Section**: `utils`
- **Priority**: `optional`

### RPM Package Information
- **Package Name**: `appimage-installer`
- **Architecture**: `noarch`
- **Dependencies**:
  - `python3 >= 3.8`
  - `python3-gobject`
  - `python3-pillow`
  - `python3-magic`

### File Locations
Both packages install files to:
- **Binary**: `/usr/local/bin/appimage-installer`
- **Library**: `/usr/local/lib/appimage-installer/`
- **Desktop file**: `/usr/share/applications/appimage-installer.desktop`
- **Documentation**: `/usr/share/doc/appimage-installer/`

## 🚀 Distribution Workflow

### For GitHub Releases

1. **Build packages**:
   ```bash
   cd packaging
   ./build-packages.sh
   # Select option 1 (All packages)
   ```

2. **Upload to GitHub release**:
   - DEB package: `dist/appimage-installer_1.0.0_all.deb`
   - RPM package: `dist/appimage-installer-1.0.0-1.noarch.rpm`
   - Installation script: `dist/install.sh`

3. **Update download URLs** in README.md

### For Package Repositories

#### Debian/Ubuntu PPA
1. Build source package
2. Upload to Launchpad PPA
3. Wait for automatic building

#### Fedora COPR
1. Create COPR project
2. Upload SRPM or link to Git repository
3. Enable automatic building

#### Arch Linux AUR
1. Create PKGBUILD file
2. Submit to AUR
3. Maintain package updates

#### Flatpak (Flathub)
1. Submit manifest to Flathub repository
2. Pass review process
3. Package becomes available in all distributions

## 🧪 Testing Packages

### Testing DEB Package
```bash
# Install in virtual machine or container
sudo dpkg -i appimage-installer_1.0.0_all.deb

# Test functionality
appimage-installer --version
appimage-installer --help

# Test file associations
# (Download a test AppImage and double-click)

# Uninstall
sudo apt remove appimage-installer
```

### Testing RPM Package
```bash
# Install
sudo rpm -i appimage-installer-1.0.0-1.noarch.rpm

# Test functionality
appimage-installer --version

# Uninstall  
sudo rpm -e appimage-installer
```

### Testing Installation Script
```bash
# Test in clean environment
bash install.sh

# Verify installation
which appimage-installer
appimage-installer --version
```

## 🔧 Customization

### Modifying Package Information

Edit variables in `build-packages.sh`:
```bash
PROJECT_NAME="appimage-installer"
VERSION="1.0.0"
DESCRIPTION="Simple tool for managing AppImage files on Linux"
MAINTAINER="Your Name <your.email@example.com>"
HOMEPAGE="https://github.com/fcools/AppImageInstaller"
```

### Adding Dependencies

**For DEB packages**, edit the `Depends` line in the control file section.

**For RPM packages**, edit the `Requires` lines in the spec file section.

### Changing Install Locations

Modify the directory creation and file copying sections in the respective build functions.

## 📝 Release Checklist

Before creating a new release:

- [ ] Update version numbers in:
  - [ ] `setup.py`
  - [ ] `src/__init__.py`
  - [ ] `packaging/build-packages.sh`
  - [ ] Package control files
- [ ] Test all package formats
- [ ] Update README.md with new download URLs
- [ ] Create Git tag
- [ ] Build and upload packages to GitHub release
- [ ] Update package repositories (PPA, COPR, AUR, etc.)
- [ ] Announce release

## 🆘 Troubleshooting

### Common Issues

**dpkg-deb command not found:**
```bash
sudo apt install dpkg-dev
```

**rpmbuild command not found:**
```bash
sudo dnf install rpm-build  # Fedora
sudo apt install rpm        # Ubuntu
```

**Permission denied during package installation:**
- Ensure you're using `sudo` for system package installation
- For user installations, use pip with `--user` flag

**File association not working after installation:**
- Log out and log back in
- Run `update-mime-database` and `update-desktop-database` manually
- Check if another application is handling .AppImage files 