"""
File Association module for AppImage Installer.

Handles registration and management of .AppImage file type associations
with the system, enabling double-click functionality.
"""

import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional


class FileAssociation:
    """
    Manages .AppImage file type associations.
    
    Handles registration of MIME types and desktop applications
    to enable double-click functionality for .AppImage files.
    """
    
    def __init__(self):
        """Initialize file association manager."""
        self.home_dir = Path.home()
        self.data_dir = self._get_data_dir()
        self.applications_dir = self.data_dir / "applications"
        self.mime_dir = self.data_dir / "mime"
        self.packages_dir = self.mime_dir / "packages"
        
        # Ensure directories exist
        self.applications_dir.mkdir(parents=True, exist_ok=True)
        self.packages_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_data_dir(self) -> Path:
        """Get XDG data directory."""
        xdg_data = os.environ.get('XDG_DATA_HOME')
        if xdg_data:
            return Path(xdg_data)
        return self.home_dir / ".local" / "share"
    
    def register(self) -> bool:
        """
        Register .AppImage file associations.
        
        Returns:
            bool: True if registration successful, False otherwise.
        """
        try:
            # Create MIME type definition
            if not self._create_mime_type():
                return False
            
            # Create desktop application entry
            if not self._create_application_entry():
                return False
            
            # Update MIME database
            if not self._update_mime_database():
                return False
            
            # Update desktop database
            if not self._update_desktop_database():
                return False
            
            # Set as default application for AppImage MIME type
            self._set_default_application()
            
            # Force system-wide desktop database update
            self._update_system_desktop_database()
            
            return True
            
        except Exception as e:
            print(f"Error registering file associations: {e}")
            return False
    
    def unregister(self) -> bool:
        """
        Unregister .AppImage file associations.
        
        Returns:
            bool: True if unregistration successful, False otherwise.
        """
        try:
            # Remove MIME type definition
            mime_file = self.packages_dir / "appimage-installer.xml"
            if mime_file.exists():
                mime_file.unlink()
            
            # Remove desktop application entry
            app_file = self.applications_dir / "appimage-installer.desktop"
            if app_file.exists():
                app_file.unlink()
            
            # Update databases
            self._update_mime_database()
            self._update_desktop_database()
            
            return True
            
        except Exception as e:
            print(f"Error unregistering file associations: {e}")
            return False
    
    def is_registered(self) -> bool:
        """
        Check if .AppImage file associations are registered.
        
        Returns:
            bool: True if registered, False otherwise.
        """
        mime_file = self.packages_dir / "appimage-installer.xml"
        app_file = self.applications_dir / "appimage-installer.desktop"
        
        return mime_file.exists() and app_file.exists()
    
    def _create_mime_type(self) -> bool:
        """
        Create MIME type definition for .AppImage files.
        
        Returns:
            bool: True if creation successful, False otherwise.
        """
        try:
            mime_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<mime-info xmlns="http://www.freedesktop.org/standards/shared-mime-info">
    <mime-type type="application/x-appimage">
        <comment>AppImage application bundle</comment>
        <comment xml:lang="en">AppImage application bundle</comment>
        <icon name="application-x-executable"/>
        <glob pattern="*.AppImage" weight="90"/>
        <glob pattern="*.appimage" weight="90"/>
        <magic priority="80">
            <match type="string" offset="0:102400" value="AppImage"/>
        </magic>
        <magic priority="75">
            <match type="string" offset="0:102400" value="appimage"/>
        </magic>
        <sub-class-of type="application/x-executable"/>
    </mime-type>
</mime-info>'''
            
            mime_file = self.packages_dir / "appimage-installer.xml"
            with open(mime_file, 'w', encoding='utf-8') as f:
                f.write(mime_xml)
            
            return True
            
        except Exception as e:
            print(f"Error creating MIME type: {e}")
            return False
    
    def _create_application_entry(self) -> bool:
        """
        Create desktop application entry for handling .AppImage files.
        
        Returns:
            bool: True if creation successful, False otherwise.
        """
        try:
            # Get the path to our main script
            script_path = self._get_script_path()
            if not script_path:
                return False
            
            desktop_content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name=AppImage Installer
Comment=Install and manage AppImage applications
Exec={script_path} %f
Icon=application-x-executable
StartupNotify=false
NoDisplay=false
MimeType=application/x-appimage;application/x-executable;application/x-sharedlib;
Categories=System;Utility;
"""
            
            app_file = self.applications_dir / "appimage-installer.desktop"
            with open(app_file, 'w', encoding='utf-8') as f:
                f.write(desktop_content)
            
            # Make executable
            os.chmod(app_file, 0o755)
            
            return True
            
        except Exception as e:
            print(f"Error creating application entry: {e}")
            return False
    
    def _get_script_path(self) -> Optional[str]:
        """
        Get the path to the main script executable.
        
        Returns:
            Optional[str]: Path to script or None if not found.
        """
        try:
            # Check if installed via pip
            script_path = shutil.which('appimage-installer')
            if script_path:
                return script_path
            
            # Check if running from source
            current_file = Path(__file__)
            main_script = current_file.parent / "main.py"
            if main_script.exists():
                python_exe = shutil.which('python3') or shutil.which('python')
                if python_exe:
                    return f"{python_exe} {main_script.absolute()}"
            
            return None
            
        except Exception:
            return None
    
    def _update_mime_database(self) -> bool:
        """
        Update the MIME database.
        
        Returns:
            bool: True if update successful, False otherwise.
        """
        try:
            # Try to update MIME database
            result = subprocess.run([
                'update-mime-database', str(self.mime_dir)
            ], capture_output=True, timeout=30)
            
            return result.returncode == 0
            
        except Exception:
            # Silent fail - not critical
            return True
    
    def _set_default_application(self) -> bool:
        """
        Explicitly set our application as the default for AppImage MIME type.
        
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            result = subprocess.run([
                'xdg-mime', 'default', 'appimage-installer.desktop', 'application/x-appimage'
            ], capture_output=True, timeout=30)
            
            return result.returncode == 0
            
        except Exception:
            return False
    
    def _update_system_desktop_database(self) -> bool:
        """
        Update system-wide desktop database.
        
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            # Try system-wide update (requires sudo, may fail)
            subprocess.run([
                'sudo', 'update-desktop-database'
            ], capture_output=True, timeout=30)
            
            return True
            
        except Exception:
            return True  # Don't fail if we can't do system update
    
    def _update_desktop_database(self) -> bool:
        """
        Update the desktop database.
        
        Returns:
            bool: True if update successful, False otherwise.
        """
        try:
            # Try to update desktop database
            result = subprocess.run([
                'update-desktop-database', str(self.applications_dir)
            ], capture_output=True, timeout=30)
            
            return result.returncode == 0
            
        except Exception:
            # Silent fail - not critical
            return True 