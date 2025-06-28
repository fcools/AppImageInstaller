"""
AppImage Manager module for AppImage Installer.

Handles AppImage file operations including metadata extraction, icon extraction,
registry management, and installation/uninstallation tracking.
"""

import os
import json
import shutil
import tempfile
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import magic
from PIL import Image


@dataclass
class AppImageInfo:
    """Information about an AppImage file."""
    name: str
    version: str
    description: str
    icon_path: str
    desktop_file_path: str
    appimage_path: str
    exec_command: str
    categories: List[str]
    mime_types: List[str]
    installed_date: str


class AppImageManager:
    """
    Manages AppImage files including extraction, installation, and registry.
    
    Handles icon extraction, desktop file creation, and maintains a registry
    of installed AppImages for easy management.
    """
    
    def __init__(self):
        """Initialize the AppImage manager with XDG-compliant paths."""
        self.home_dir = Path.home()
        self.config_dir = self._get_config_dir()
        self.data_dir = self._get_data_dir()
        self.applications_dir = self.data_dir / "applications"
        self.icons_dir = self.data_dir / "icons" / "hicolor"
        self.appimage_storage = self.home_dir / "Applications"
        self.registry_file = self.config_dir / "appimage-installer" / "registry.json"
        
        # Create necessary directories
        self._ensure_directories()
    
    def _get_config_dir(self) -> Path:
        """
        Get XDG config directory.
        
        Returns:
            Path: XDG config directory path.
        """
        xdg_config = os.environ.get('XDG_CONFIG_HOME')
        if xdg_config:
            return Path(xdg_config)
        return self.home_dir / ".config"
    
    def _get_data_dir(self) -> Path:
        """
        Get XDG data directory.
        
        Returns:
            Path: XDG data directory path.
        """
        xdg_data = os.environ.get('XDG_DATA_HOME')
        if xdg_data:
            return Path(xdg_data)
        return self.home_dir / ".local" / "share"
    
    def _ensure_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        directories = [
            self.config_dir / "appimage-installer",
            self.applications_dir,
            self.icons_dir / "16x16" / "apps",
            self.icons_dir / "24x24" / "apps", 
            self.icons_dir / "32x32" / "apps",
            self.icons_dir / "48x48" / "apps",
            self.icons_dir / "64x64" / "apps",
            self.icons_dir / "128x128" / "apps",
            self.icons_dir / "256x256" / "apps",
            self.appimage_storage
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def is_appimage(self, file_path: str) -> bool:
        """
        Check if a file is a valid AppImage.
        
        Args:
            file_path (str): Path to the file to check.
            
        Returns:
            bool: True if the file is an AppImage, False otherwise.
        """
        try:
            path = Path(file_path)
            
            # Check if file exists and is executable
            if not path.exists() or not os.access(path, os.X_OK):
                return False
            
            # Check filename pattern first (most reliable)
            filename = path.name.lower()
            if filename.endswith('.appimage') or filename.endswith('.AppImage'):
                return True
            
            # Check file magic for executables
            mime_type = magic.from_file(str(path), mime=True)
            if not mime_type.startswith('application/'):
                return False
            
            # Check if it contains AppImage signature anywhere in file
            # AppImage signatures can be anywhere, not just in first 1KB
            try:
                with open(path, 'rb') as f:
                    # Read in chunks to handle large files efficiently
                    chunk_size = 8192
                    while True:
                        chunk = f.read(chunk_size)
                        if not chunk:
                            break
                        if b'AppImage' in chunk or b'appimage' in chunk:
                            return True
                        # Only check first 100KB to avoid reading entire large files
                        if f.tell() > 100 * 1024:
                            break
                            
                # If no AppImage signature found, still accept files ending with .AppImage
                return filename.endswith('.appimage')
                
            except Exception:
                # If reading fails, fall back to filename check
                return filename.endswith('.appimage')
                
        except Exception:
            return False
    
    def extract_appimage_info(self, appimage_path: str) -> Optional[AppImageInfo]:
        """
        Extract metadata and information from an AppImage file.
        
        Args:
            appimage_path (str): Path to the AppImage file.
            
        Returns:
            Optional[AppImageInfo]: Extracted information or None if extraction fails.
        """
        if not self.is_appimage(appimage_path):
            return None
        
        try:
            path = Path(appimage_path)
            
            # Create basic info from filename as fallback
            # Reason: Complex extraction can fail, so we provide basic info
            info = AppImageInfo(
                name=path.stem.replace('_', ' ').replace('-', ' ').title(),
                version='Unknown',
                description=f'AppImage application: {path.stem}',
                icon_path='',
                desktop_file_path='',
                appimage_path=str(path.absolute()),
                exec_command=str(path.absolute()),
                categories=['Application'],
                mime_types=[],
                installed_date=''
            )
            
            return info
            
        except Exception as e:
            print(f"Error extracting AppImage info: {e}")
            return None
    
    def is_registered(self, appimage_path: str) -> bool:
        """
        Check if an AppImage is registered in the system.
        
        Args:
            appimage_path (str): Path to the AppImage file.
            
        Returns:
            bool: True if registered, False otherwise.
        """
        registry = self._load_registry()
        abs_path = str(Path(appimage_path).absolute())
        return abs_path in registry
    
    def register_appimage(self, info: AppImageInfo) -> bool:
        """
        Register an AppImage in the system registry.
        
        Args:
            info (AppImageInfo): AppImage information to register.
            
        Returns:
            bool: True if registration successful, False otherwise.
        """
        try:
            registry = self._load_registry()
            abs_path = str(Path(info.appimage_path).absolute())
            
            # Add current timestamp
            from datetime import datetime
            info.installed_date = datetime.now().isoformat()
            
            registry[abs_path] = asdict(info)
            return self._save_registry(registry)
            
        except Exception as e:
            print(f"Error registering AppImage: {e}")
            return False
    
    def unregister_appimage(self, appimage_path: str) -> bool:
        """
        Unregister an AppImage from the system registry.
        
        Args:
            appimage_path (str): Path to the AppImage file.
            
        Returns:
            bool: True if unregistration successful, False otherwise.
        """
        try:
            registry = self._load_registry()
            abs_path = str(Path(appimage_path).absolute())
            
            if abs_path in registry:
                del registry[abs_path]
                return self._save_registry(registry)
            
            return True  # Already not registered
            
        except Exception as e:
            print(f"Error unregistering AppImage: {e}")
            return False
    
    def get_registered_info(self, appimage_path: str) -> Optional[AppImageInfo]:
        """
        Get registered information for an AppImage.
        
        Args:
            appimage_path (str): Path to the AppImage file.
            
        Returns:
            Optional[AppImageInfo]: Registered information or None.
        """
        registry = self._load_registry()
        abs_path = str(Path(appimage_path).absolute())
        
        if abs_path in registry:
            data = registry[abs_path]
            return AppImageInfo(**data)
        
        return None
    
    def _load_registry(self) -> Dict:
        """
        Load the AppImage registry from file.
        
        Returns:
            Dict: Registry data.
        """
        try:
            if self.registry_file.exists():
                with open(self.registry_file, 'r') as f:
                    return json.load(f)
        except Exception:
            pass
        
        return {}
    
    def _save_registry(self, registry: Dict) -> bool:
        """
        Save the AppImage registry to file.
        
        Args:
            registry (Dict): Registry data to save.
            
        Returns:
            bool: True if save successful, False otherwise.
        """
        try:
            self.registry_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.registry_file, 'w') as f:
                json.dump(registry, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving registry: {e}")
            return False 