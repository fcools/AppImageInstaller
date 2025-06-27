# 🚀 AppImage Installer - Installation Guide

**Make AppImage files installable with just a double-click!**

Choose the installation method that works best for you:

## 🎯 **Easiest Option (Recommended for Everyone)**

**One-command installation** - Works on any Linux distribution:

```bash
curl -sSL https://raw.githubusercontent.com/fcools/AppImageInstaller/main/easy-install.sh | bash
```

Just copy-paste this command into your terminal and press Enter. The script will:
- ✅ Automatically detect your Linux distribution
- ✅ Install all required dependencies
- ✅ Download and install AppImage Installer  
- ✅ Set up file associations for double-click functionality

**After installation**: Log out and log back in, then double-click any `.AppImage` file!

---

## 📦 **Native Packages (Distribution-Specific)**

### Ubuntu/Debian/Linux Mint
```bash
wget https://github.com/fcools/AppImageInstaller/releases/download/v1.0.0/appimage-installer_1.0.0_all.deb
sudo dpkg -i appimage-installer_1.0.0_all.deb
```

### Fedora/RHEL/CentOS/Rocky Linux
```bash
wget https://github.com/fcools/AppImageInstaller/releases/download/v1.0.0/appimage-installer-1.0.0-1.noarch.rpm
sudo rpm -i appimage-installer-1.0.0-1.noarch.rpm
```

### Arch Linux/Manjaro
```bash
# Using AUR helper (yay/paru)
yay -S appimage-installer

# Or manually
git clone https://aur.archlinux.org/appimage-installer.git
cd appimage-installer
makepkg -si
```

### openSUSE
```bash
# Add COPR repository first
sudo zypper addrepo https://download.copr.fedorainfracloud.org/results/username/appimage-installer/opensuse-leap-15.4/
sudo zypper install appimage-installer
```

---

## 📱 **Universal Packages**

### Flatpak (Works on all distributions)
```bash
flatpak install flathub org.example.AppImageInstaller
```

### Snap (Ubuntu and others)
```bash
sudo snap install appimage-installer
```

---

## 🐍 **For Python Developers**

### From PyPI
```bash
pip install appimage-installer
appimage-installer --register
```

### From Source
```bash
git clone https://github.com/fcools/AppImageInstaller.git
cd AppImageInstaller
pip install -e .
appimage-installer --register
```

---

## ✅ **Verify Installation**

After installation, test that it works:

```bash
# Check if command is available
appimage-installer --version

# Register file associations (if not done automatically)
appimage-installer --register
```

**Test it**: Download any `.AppImage` file and double-click it!

---

## 🆘 **Troubleshooting**

### File associations not working?
```bash
# Re-register file associations
appimage-installer --register

# Log out and log back in
# OR restart your desktop session
```

### Command not found?
- **For pip installs**: Add `~/.local/bin` to your PATH
- **For system installs**: Try logging out and back in
- **Check installation**: `which appimage-installer`

### Dependencies missing?
The one-command installer should handle this automatically. For manual installations:

**Ubuntu/Debian:**
```bash
sudo apt install python3-gi python3-pil python3-magic
```

**Fedora:**
```bash
sudo dnf install python3-gobject python3-pillow python3-magic
```

**Arch:**
```bash
sudo pacman -S python-gobject python-pillow python-magic
```

---

## 🎯 **What Happens After Installation?**

1. **Double-click any `.AppImage` file**
2. **If not installed**: Shows "Install AppImage?" dialog
   - Creates launcher shortcut
   - Adds to applications menu  
   - Launches the app
3. **If already installed**: Shows "Uninstall or Launch?" dialog
   - Choose to remove or run the app

**That's it!** AppImage files now work like regular installers.

---

## 📞 **Need Help?**

- 📖 **Full documentation**: [README.md](README.md)
- 🐛 **Report issues**: [GitHub Issues](https://github.com/fcools/AppImageInstaller/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/fcools/AppImageInstaller/discussions)

**Made with ❤️ for the Linux community** 