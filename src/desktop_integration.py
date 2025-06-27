"""
Desktop Integration module for AppImage Installer.

Handles creation and management of .desktop files, launcher shortcuts,
and system integration for AppImage files.
"""

import os
import subprocess
from pathlib import Path
from typing import Optional
from .appimage_manager import AppImageInfo


class DesktopIntegration:
    """
    Handles desktop integration for AppImage files.
    
    Creates .desktop files, manages launcher shortcuts, and provides
    system integration following XDG specifications.
    """
    
    def __init__(self):
        """Initialize desktop integration with XDG paths."""
        self.home_dir = Path.home()
        self.data_dir = self._get_data_dir()
        self.applications_dir = self.data_dir / "applications"
        self.desktop_dir = self.home_dir / "Desktop"
        
        # Ensure directories exist
        self.applications_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_data_dir(self) -> Path:
        """Get XDG data directory."""
        xdg_data = os.environ.get('XDG_DATA_HOME')
        if xdg_data:
            return Path(xdg_data)
        return self.home_dir / ".local" / "share"
    
    def create_desktop_file(self, info: AppImageInfo) -> Optional[str]:
        """
        Create a .desktop file for the AppImage.
        
        Args:
            info (AppImageInfo): AppImage information.
            
        Returns:
            Optional[str]: Path to created .desktop file or None if failed.
        """
        try:
            # Generate desktop file name
            safe_name = self._sanitize_filename(info.name)
            desktop_filename = f"{safe_name}.desktop"
            desktop_path = self.applications_dir / desktop_filename
            
            # Create desktop file content
            desktop_content = self._generate_desktop_content(info)
            
            # Write desktop file
            with open(desktop_path, 'w', encoding='utf-8') as f:
                f.write(desktop_content)
            
            # Make executable
            os.chmod(desktop_path, 0o755)
            
            # Update desktop database
            self._update_desktop_database()
            
            return str(desktop_path)
            
        except Exception as e:
            print(f"Error creating desktop file: {e}")
            return None
    
    def remove_desktop_file(self, desktop_file_path: str) -> bool:
        """
        Remove a .desktop file.
        
        Args:
            desktop_file_path (str): Path to the .desktop file.
            
        Returns:
            bool: True if removal successful, False otherwise.
        """
        try:
            desktop_path = Path(desktop_file_path)
            if desktop_path.exists():
                desktop_path.unlink()
            
            # Update desktop database
            self._update_desktop_database()
            
            return True
            
        except Exception as e:
            print(f"Error removing desktop file: {e}")
            return False
    
    def create_desktop_shortcut(self, info: AppImageInfo) -> bool:
        """
        Create a desktop shortcut (optional, only if desktop directory exists).
        
        Args:
            info (AppImageInfo): AppImage information.
            
        Returns:
            bool: True if creation successful or not needed, False if failed.
        """
        try:
            # Only create if Desktop directory exists
            if not self.desktop_dir.exists():
                return True  # Not an error, just not needed
            
            # Generate desktop shortcut name
            safe_name = self._sanitize_filename(info.name)
            shortcut_filename = f"{safe_name}.desktop"
            shortcut_path = self.desktop_dir / shortcut_filename
            
            # Create desktop file content
            desktop_content = self._generate_desktop_content(info)
            
            # Write shortcut file
            with open(shortcut_path, 'w', encoding='utf-8') as f:
                f.write(desktop_content)
            
            # Make executable
            os.chmod(shortcut_path, 0o755)
            
            return True
            
        except Exception as e:
            print(f"Error creating desktop shortcut: {e}")
            return False
    
    def remove_desktop_shortcut(self, info: AppImageInfo) -> bool:
        """
        Remove desktop shortcut.
        
        Args:
            info (AppImageInfo): AppImage information.
            
        Returns:
            bool: True if removal successful or not needed, False if failed.
        """
        try:
            if not self.desktop_dir.exists():
                return True
            
            safe_name = self._sanitize_filename(info.name)
            shortcut_filename = f"{safe_name}.desktop"
            shortcut_path = self.desktop_dir / shortcut_filename
            
            if shortcut_path.exists():
                shortcut_path.unlink()
            
            return True
            
        except Exception as e:
            print(f"Error removing desktop shortcut: {e}")
            return False
    
    def _sanitize_filename(self, name: str) -> str:
        """
        Sanitize a name for use as filename.
        
        Args:
            name (str): Original name.
            
        Returns:
            str: Sanitized filename.
        """
        # Remove invalid characters and replace spaces
        safe_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-"
        sanitized = "".join(c if c in safe_chars else "_" for c in name)
        
        # Remove multiple underscores and trim
        while "__" in sanitized:
            sanitized = sanitized.replace("__", "_")
        
        return sanitized.strip("_")
    
    def _generate_desktop_content(self, info: AppImageInfo) -> str:
        """
        Generate .desktop file content.
        
        Args:
            info (AppImageInfo): AppImage information.
            
        Returns:
            str: Desktop file content.
        """
        # Build categories string
        categories = ";".join(info.categories) if info.categories else "Application"
        if not categories.endswith(";"):
            categories += ";"
        
        # Build MIME types string
        mime_types = ";".join(info.mime_types) if info.mime_types else ""
        if mime_types and not mime_types.endswith(";"):
            mime_types += ";"
        
        # Generate desktop content
        content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name={info.name}
Comment={info.description}
Exec={info.exec_command}
Icon={info.icon_path if info.icon_path else 'application-x-executable'}
Categories={categories}
Terminal=false
StartupNotify=true
StartupWMClass={info.name}
"""
        
        if mime_types:
            content += f"MimeType={mime_types}\n"
        
        if info.version and info.version != 'Unknown':
            content += f"X-AppImage-Version={info.version}\n"
        
        content += f"X-AppImage-Path={info.appimage_path}\n"
        content += "X-AppImage-Installer=true\n"
        
        return content
    
    def _update_desktop_database(self) -> None:
        """Update the desktop database to refresh application cache."""
        try:
            # Try to update desktop database
            subprocess.run([
                'update-desktop-database', str(self.applications_dir)
            ], capture_output=True, timeout=10)
        except Exception:
            # Silent fail - not critical
            pass
    
    def launch_appimage(self, appimage_path: str) -> bool:
        """
        Launch an AppImage file.
        
        Args:
            appimage_path (str): Path to the AppImage file.
            
        Returns:
            bool: True if launch successful, False otherwise.
        """
        try:
            path = Path(appimage_path)
            
            # Ensure file is executable
            if not os.access(path, os.X_OK):
                os.chmod(path, 0o755)
            
            # Launch AppImage in background
            subprocess.Popen([str(path)], 
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.DEVNULL)
            
            return True
            
        except Exception as e:
            print(f"Error launching AppImage: {e}")
            return False 