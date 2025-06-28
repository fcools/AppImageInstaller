# AppImage Installer

A simple and intuitive tool for managing AppImage files on Linux. Makes AppImage installation as easy as double-clicking, with automatic desktop integration and native system dialogs.

## 🎯 Features

- **One-Click Installation**: Double-click any AppImage file to install it
- **Desktop Integration**: Automatic creation of launcher shortcuts and menu entries
- **Native Look**: Uses system-native dialog boxes (GTK/Tkinter)
- **Cross-Distro**: Works on all major Linux distributions
- **Registry Management**: Keeps track of installed AppImages for easy uninstall
- **Icon Extraction**: Automatically extracts and processes application icons
- **XDG Compliant**: Follows Linux desktop standards

## 🚀 Quick Start

### 🎯 **For Novice Users (Easiest)**

**One-command installation** - Just copy and paste this into your terminal:

```bash
curl -sSL https://raw.githubusercontent.com/fcools/AppImageInstaller/main/easy-install.sh | bash
```

That's it! The script will:
- ✅ Detect your Linux distribution automatically
- ✅ Install all required dependencies  
- ✅ Download and install AppImage Installer
- ✅ Set up file associations for double-click functionality

### 📦 **Native Package Installation**

Choose the package for your distribution:

**Ubuntu/Debian/Linux Mint:**
```bash
wget https://github.com/fcools/AppImageInstaller/releases/download/v1.0.0/appimage-installer_1.0.0_all.deb
sudo dpkg -i appimage-installer_1.0.0_all.deb
```

**Fedora/RHEL/CentOS:**
```bash
wget https://github.com/fcools/AppImageInstaller/releases/download/v1.0.0/appimage-installer-1.0.0-1.noarch.rpm
sudo rpm -i appimage-installer-1.0.0-1.noarch.rpm
```

**Arch Linux (AUR):**
```bash
yay -S appimage-installer
# or
paru -S appimage-installer
```

### 🐍 **For Python Users**

#### Option 1: From PyPI
```bash
pip install appimage-installer
appimage-installer --register
```

#### Option 2: From Source
```bash
git clone https://github.com/fcools/AppImageInstaller.git
cd AppImageInstaller
pip install -e .
appimage-installer --register
```

### 📱 **Universal Package (Flatpak)**

```bash
flatpak install flathub org.example.AppImageInstaller
```

Now you can double-click any .AppImage file to install it!

## 📖 Usage

### Double-Click Installation

1. **Download** any AppImage file
2. **Double-click** the AppImage file
3. **Choose** to install when prompted
4. **Done!** The app is now in your applications menu

### Command Line Usage

```bash
# Install/manage a specific AppImage
appimage-installer myapp.AppImage

# Open GUI Manager to view and manage all installed apps
appimage-installer --manage

# Register file associations
appimage-installer --register

# Unregister file associations  
appimage-installer --unregister

# Show help
appimage-installer --help
```

### 🖥️ GUI Manager

The AppImage Manager provides a convenient graphical interface for managing your installed AppImage applications:

![AppImage Manager](docs/manager-screenshot.png)

**Features:**
- View all installed AppImage applications in one place
- Launch applications directly from the manager
- Uninstall applications even if original files are deleted
- Sort by name, version, or installation date
- Shows installation location and details

**Access the Manager:**
- Command line: `appimage-installer --manage`
- Applications menu: Search for "AppImage Manager"
- Perfect for managing apps when original .AppImage files are missing

### User Experience Flow

When you double-click an AppImage:

- **If not installed**: Shows installation dialog → Creates desktop entry → Launches app
- **If already installed**: Shows uninstall/launch dialog → Acts accordingly

## 🛠️ Requirements

### System Requirements
- Linux distribution with XDG support
- Python 3.8 or higher
- Tkinter (for GUI Manager) - usually `python3-tk` package
- GTK 3.0+ (optional, for enhanced native dialogs)

### Python Dependencies
- `PyGObject>=3.42.0` (for GTK dialogs)
- `Pillow>=9.0.0` (for icon processing)
- `python-magic>=0.4.24` (for file type detection)
- `packaging>=21.0` (for version handling)

### Optional System Packages

For optimal functionality, install these system packages:

**Ubuntu/Debian:**
```bash
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0 libmagic1 python3-tk
```

**Fedora:**
```bash
sudo dnf install python3-gobject gtk3-devel python3-magic
```

**Arch Linux:**
```bash
sudo pacman -S python-gobject gtk3 python-magic
```

## 🏗️ Architecture

The project is organized into modular components:

```
src/
├── appimage_manager.py     # Core AppImage operations
├── desktop_integration.py  # Desktop file creation
├── gui_dialogs.py         # Native dialog system
├── file_association.py    # File type registration
├── appimage_handler.py    # Main workflow orchestrator
└── main.py               # CLI entry point
```

### Key Components

- **AppImage Manager**: Handles detection, metadata extraction, and registry
- **Desktop Integration**: Creates .desktop files and launcher shortcuts
- **GUI Dialogs**: Provides native system dialogs with GTK/Tkinter fallback
- **File Association**: Manages .AppImage MIME type registration
- **Main Handler**: Orchestrates the complete installation/uninstallation workflow

## 🧪 Development

### Setting Up Development Environment

```bash
git clone https://github.com/fcools/AppImageInstaller.git
cd AppImageInstaller

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install in development mode
pip install -e .[dev]
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test file
pytest tests/test_appimage_manager.py
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint code
flake8 src/ tests/
```

## 📁 File Locations

The installer follows XDG Base Directory specifications:

- **Desktop files**: `~/.local/share/applications/`
- **Icons**: `~/.local/share/icons/hicolor/`
- **Registry**: `~/.local/share/appimage-installer/registry.json`
- **MIME types**: `~/.local/share/mime/packages/`
- **AppImages**: `~/Applications/` (configurable)

## 🔧 Configuration

Currently, the installer uses sensible defaults. Future versions will include:

- Custom AppImage storage location
- Icon size preferences  
- Desktop shortcut options
- Automatic updates

## 🤝 Contributing

Contributions are welcome! Please read our contributing guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guidelines
- Add unit tests for new functionality
- Update documentation for API changes
- Use type hints for function signatures
- Write descriptive commit messages

## 🐛 Troubleshooting

### Common Issues

**AppImage not recognized:**
- Ensure the file is executable: `chmod +x myapp.AppImage`
- Check file integrity: download the AppImage again

**GTK dialogs not working:**
- Install GTK development packages (see Requirements section)
- Fallback to Tkinter dialogs should work automatically

**File association not working:**
- Re-run: `appimage-installer --register`
- Log out and log back in
- Check if another program handles .AppImage files

### Getting Help

- Check existing [Issues](https://github.com/fcools/AppImageInstaller/issues)
- Create a new issue with detailed information
- Include your Linux distribution and Python version

## 📜 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [AppImage project](https://appimage.org/) for the portable application format
- [XDG Base Directory Specification](https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html)
- [Desktop Entry Specification](https://specifications.freedesktop.org/desktop-entry-spec/desktop-entry-spec-latest.html)

## 🚧 Roadmap

- [ ] Enhanced icon extraction with fallback icons
- [ ] Configuration file support  
- [ ] AppImage update checking
- [ ] Integration with software centers
- [ ] Batch installation support
- [ ] Plugin system for custom handlers

---

**Made with ❤️ for the Linux community** 