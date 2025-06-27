# AppImage Installer - Project Planning

## 🎯 Project Overview
An intuitive AppImage installer that automatically handles .AppImage files when double-clicked, providing seamless installation/uninstallation with native Linux desktop integration.

## 🏗️ Architecture

### Core Components
1. **File Handler** (`appimage_handler.py`) - Main entry point for .AppImage file processing
2. **AppImage Manager** (`appimage_manager.py`) - Core logic for extraction, registration, and management
3. **Desktop Integration** (`desktop_integration.py`) - Creates .desktop files and launcher shortcuts
4. **GUI Dialogs** (`gui_dialogs.py`) - Native system dialogs using appropriate toolkit
5. **File Association** (`file_association.py`) - Registers .AppImage file type association

### Directory Structure
```
AppImageInstaller/
├── src/
│   ├── __init__.py
│   ├── main.py                 # Entry point
│   ├── appimage_handler.py     # Main file handler
│   ├── appimage_manager.py     # Core AppImage operations
│   ├── desktop_integration.py  # Desktop file creation
│   ├── gui_dialogs.py         # Native GUI dialogs
│   └── file_association.py    # File type registration
├── tests/
│   ├── __init__.py
│   └── test_*.py              # Unit tests
├── resources/
│   └── icons/                 # Default icons
├── requirements.txt
├── setup.py
├── PLANNING.md
├── TASK.md
└── README.md
```

## 🔧 Technical Decisions

### GUI Framework
- **Primary**: GTK3/4 via PyGObject (most common on Linux)
- **Fallback**: Tkinter (built into Python, universal)
- **Detection**: Auto-detect available GUI toolkit

### Cross-Distro Compatibility
- Use XDG Base Directory Specification
- Support both systemd and non-systemd distros
- Handle different desktop environments (GNOME, KDE, XFCE, etc.)

### File Locations
- **Desktop files**: `~/.local/share/applications/`
- **Icons**: `~/.local/share/icons/hicolor/`
- **AppImage storage**: `~/Applications/` (user-configurable)
- **Registry**: `~/.local/share/appimage-installer/registry.json`

### Dependencies
- `PyGObject` (GTK bindings) - optional
- `Pillow` (image processing)
- `python-magic` (file type detection)
- `configparser` (configuration)

## 🚀 User Experience Flow

1. User double-clicks .AppImage file
2. Our handler checks if AppImage is registered
3. **If registered**: Show uninstall dialog
4. **If not registered**: 
   - Extract icon and metadata
   - Create desktop entry
   - Add to launcher
   - Launch application
   - Add to registry

## 🎨 Design Principles
- **Native Look**: Use system's native dialogs and icons
- **Minimal**: Simple, clean interface
- **Safe**: Always ask before making system changes
- **Reversible**: Easy uninstall process
- **Cross-platform**: Work on all major Linux distros 