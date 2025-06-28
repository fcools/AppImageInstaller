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
import re
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
            
            # Check if file exists
            if not path.exists():
                return False
            
            # Check filename pattern first (most reliable)
            filename = path.name
            if filename.endswith('.AppImage') or filename.endswith('.appimage'):
                # For files with correct extension, do a quick content check
                try:
                    with open(path, 'rb') as f:
                        # Read first 100KB to look for AppImage signature
                        header = f.read(100 * 1024)
                        if b'AppImage' in header or b'appimage' in header:
                            return True
                        # Even without signature, trust the filename
                        return True
                except Exception:
                    # If can't read file, still trust the filename
                    return True
            
            # For files without .AppImage extension, check MIME type and content
            try:
                mime_type = magic.from_file(str(path), mime=True)
                # Accept various executable types that might be AppImages
                if mime_type in ['application/x-executable', 'application/x-sharedlib', 'application/octet-stream']:
                    # Check for AppImage signature in content
                    with open(path, 'rb') as f:
                        header = f.read(100 * 1024)
                        return b'AppImage' in header or b'appimage' in header
            except Exception:
                pass
                
            return False
                
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
            
            # Start with basic info from filename as foundation
            basic_name = path.stem.replace('_', ' ').replace('-', ' ').title()
            
            info = AppImageInfo(
                name=basic_name,
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
            
            # Try to extract real metadata from AppImage
            extracted_info = self._extract_appimage_metadata(appimage_path)
            if extracted_info:
                # Update with extracted information
                if extracted_info.get('name'):
                    info.name = extracted_info['name']
                if extracted_info.get('version'):
                    info.version = extracted_info['version']
                if extracted_info.get('description'):
                    info.description = extracted_info['description']
                if extracted_info.get('categories'):
                    info.categories = extracted_info['categories']
                if extracted_info.get('mime_types'):
                    info.mime_types = extracted_info['mime_types']
            
            # Handle icon with multiple fallback strategies
            extracted_icon = extracted_info.get('icon_path') if extracted_info else None
            info.icon_path = self._get_icon_for_appimage(appimage_path, info.name, info.categories, extracted_icon)
            
            return info
            
        except Exception as e:
            print(f"Error extracting AppImage info: {e}")
            return None
    
    def _extract_appimage_metadata(self, appimage_path: str) -> Optional[Dict]:
        """
        Extract metadata from AppImage using appimage-extract.
        
        Args:
            appimage_path (str): Path to the AppImage file.
            
        Returns:
            Optional[Dict]: Extracted metadata or None if extraction fails.
        """
        try:
            import tempfile
            import subprocess
            
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Copy AppImage to temp directory and make executable
                appimage_copy = temp_path / "app.AppImage"
                shutil.copy2(appimage_path, appimage_copy)
                os.chmod(appimage_copy, 0o755)
                
                # Extract AppImage contents
                result = subprocess.run([
                    str(appimage_copy), '--appimage-extract'
                ], cwd=temp_path, capture_output=True, timeout=30)
                
                if result.returncode != 0:
                    return None
                
                # Look for desktop files in extracted contents
                squashfs_root = temp_path / "squashfs-root"
                if not squashfs_root.exists():
                    return None
                
                # Find main desktop file
                desktop_files = list(squashfs_root.glob("*.desktop"))
                if not desktop_files:
                    # Look in usr/share/applications
                    desktop_files = list(squashfs_root.glob("usr/share/applications/*.desktop"))
                
                if desktop_files:
                    return self._parse_desktop_file(desktop_files[0], squashfs_root)
                
                return None
                
        except Exception as e:
            print(f"Error extracting AppImage metadata: {e}")
            return None
    
    def _parse_desktop_file(self, desktop_file: Path, squashfs_root: Path) -> Dict:
        """
        Parse desktop file to extract application metadata.
        
        Args:
            desktop_file (Path): Path to desktop file.
            squashfs_root (Path): Root of extracted AppImage.
            
        Returns:
            Dict: Parsed metadata.
        """
        metadata = {}
        
        try:
            with open(desktop_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse desktop file
            for line in content.split('\n'):
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    
                    if key == 'Name':
                        metadata['name'] = value
                    elif key == 'Version':
                        metadata['version'] = value
                    elif key == 'Comment':
                        metadata['description'] = value
                    elif key == 'Categories':
                        metadata['categories'] = [cat.strip() for cat in value.split(';') if cat.strip()]
                    elif key == 'MimeType':
                        metadata['mime_types'] = [mime.strip() for mime in value.split(';') if mime.strip()]
                    elif key == 'Icon':
                        # Handle icon extraction
                        icon_path = self._extract_icon_from_appimage(value, squashfs_root)
                        if icon_path:
                            metadata['icon_path'] = icon_path
            
            return metadata
            
        except Exception as e:
            print(f"Error parsing desktop file: {e}")
            return {}
    
    def _extract_icon_from_appimage(self, icon_name: str, squashfs_root: Path) -> Optional[str]:
        """
        Extract icon from AppImage contents.
        
        Args:
            icon_name (str): Icon name from desktop file.
            squashfs_root (Path): Root of extracted AppImage.
            
        Returns:
            Optional[str]: Path to extracted icon or None.
        """
        try:
            # Common icon locations in AppImages
            icon_locations = [
                squashfs_root / icon_name,
                squashfs_root / f"{icon_name}.png",
                squashfs_root / f"{icon_name}.svg",
                squashfs_root / f"{icon_name}.ico",
                squashfs_root / f"{icon_name}.xpm",
                squashfs_root / "usr" / "share" / "icons" / "hicolor" / "**" / f"{icon_name}.*",
                squashfs_root / "usr" / "share" / "pixmaps" / f"{icon_name}.*",
                squashfs_root / "**" / f"{icon_name}.*"
            ]
            
            # Find the best icon
            best_icon = None
            best_size = 0
            
            for location_pattern in icon_locations:
                if '*' in str(location_pattern):
                    # Use glob for patterns
                    matches = list(squashfs_root.glob(str(location_pattern).replace(str(squashfs_root) + '/', '')))
                else:
                    # Direct file check
                    matches = [location_pattern] if location_pattern.exists() else []
                
                for icon_file in matches:
                    if icon_file.is_file():
                        # Prefer larger icons and certain formats
                        size_score = self._get_icon_size_score(icon_file)
                        if size_score > best_size:
                            best_icon = icon_file
                            best_size = size_score
            
            if best_icon:
                # Copy icon to our icons directory
                return self._copy_icon_to_storage(best_icon)
            
            return None
            
        except Exception as e:
            print(f"Error extracting icon: {e}")
            return None
    
    def _get_icon_size_score(self, icon_file: Path) -> int:
        """
        Get a score for icon based on size and format preference.
        
        Args:
            icon_file (Path): Path to icon file.
            
        Returns:
            int: Score (higher is better).
        """
        try:
            # Format preferences (SVG > PNG > others)
            format_scores = {'.svg': 1000, '.png': 500, '.ico': 200, '.xpm': 100}
            base_score = format_scores.get(icon_file.suffix.lower(), 50)
            
            # Try to get actual image size for raster formats
            if icon_file.suffix.lower() in ['.png', '.ico', '.jpg', '.jpeg']:
                try:
                    from PIL import Image
                    with Image.open(icon_file) as img:
                        width, height = img.size
                        # Prefer icons around 48-128px
                        size = min(width, height)
                        if 48 <= size <= 128:
                            return base_score + size
                        elif size > 128:
                            return base_score + 128 - (size - 128) // 10
                        else:
                            return base_score + size
                except:
                    pass
            
            # Guess size from filename (e.g., "48x48", "128x128")
            filename = icon_file.name.lower()
            import re
            size_match = re.search(r'(\d+)x\d+', filename)
            if size_match:
                size = int(size_match.group(1))
                return base_score + min(size, 128)
            
            return base_score
            
        except:
            return 1
    
    def _copy_icon_to_storage(self, icon_file: Path) -> str:
        """
        Copy icon to our icon storage directory.
        
        Args:
            icon_file (Path): Source icon file.
            
        Returns:
            str: Path to copied icon.
        """
        try:
            # Create icon filename based on app
            import hashlib
            import time
            
            # Create unique filename
            timestamp = str(int(time.time()))
            source_hash = hashlib.md5(str(icon_file).encode()).hexdigest()[:8]
            extension = icon_file.suffix or '.png'
            
            icon_filename = f"extracted_{timestamp}_{source_hash}{extension}"
            
            # Determine best size directory (prefer 48x48 for desktop files)
            icon_dir = self.icons_dir / "48x48" / "apps"
            icon_dir.mkdir(parents=True, exist_ok=True)
            
            target_path = icon_dir / icon_filename
            shutil.copy2(icon_file, target_path)
            
            return str(target_path)
            
        except Exception as e:
            print(f"Error copying icon to storage: {e}")
            return ""
    
    def _get_icon_for_appimage(self, appimage_path: str, app_name: str, categories: List[str], extracted_icon: Optional[str] = None) -> str:
        """
        Get icon for AppImage using multiple fallback strategies.
        
        Args:
            appimage_path (str): Path to AppImage file.
            app_name (str): Application name.
            categories (List[str]): Application categories.
            extracted_icon (Optional[str]): Icon extracted from AppImage, if any.
            
        Returns:
            str: Path to icon or icon name.
        """
        # 1. Use extracted icon if available
        if extracted_icon:
            return extracted_icon
        
        # 2. Try system icon theme search for known applications
        system_icon = self._find_system_icon(app_name)
        if system_icon:
            return system_icon
        
        # 3. Use category-based fallback icons
        category_icon = self._get_category_icon(app_name, categories)
        if category_icon:
            return category_icon
        
        # 4. Ultimate fallback
        return 'application-x-executable'
    
    def search_web_icon(self, app_name: str, version: str = "") -> Optional[str]:
        """
        Search the web for application icon (requires user consent).
        
        Args:
            app_name (str): Application name to search for.
            version (str): Application version (optional).
            
        Returns:
            Optional[str]: Path to downloaded icon or None.
        """
        try:
            import requests
            import tempfile
            from urllib.parse import quote
            
            # Create search query
            search_query = f"{app_name} application icon"
            if version and version != "Unknown":
                search_query += f" {version}"
            
            # Use DuckDuckGo Images API (doesn't require API key)
            search_url = f"https://duckduckgo.com/?q={quote(search_query)}&t=h_&iax=images&ia=images"
            
            # For now, we'll use a simple approach with common icon hosting sites
            # This is a basic implementation - in production you'd want more sophisticated search
            icon_urls = self._find_icon_urls(app_name)
            
            for url in icon_urls:
                try:
                    response = requests.get(url, timeout=10, headers={
                        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
                    })
                    
                    if response.status_code == 200 and 'image' in response.headers.get('content-type', ''):
                        # Save the image
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
                            temp_file.write(response.content)
                            temp_path = temp_file.name
                        
                        # Copy to our storage
                        return self._copy_icon_to_storage(Path(temp_path))
                        
                except:
                    continue
            
            return None
            
        except Exception as e:
            print(f"Error searching web for icon: {e}")
            return None
    
    def _find_icon_urls(self, app_name: str) -> List[str]:
        """
        Generate potential icon URLs for common applications.
        
        Args:
            app_name (str): Application name.
            
        Returns:
            List[str]: List of potential icon URLs.
        """
        name_lower = app_name.lower().replace(' ', '').replace('-', '').replace('_', '')
        
        # Common icon sources and patterns
        icon_urls = []
        
        # Known application icons (safe, common apps)
        known_apps = {
            'firefox': 'https://upload.wikimedia.org/wikipedia/commons/thumb/a/a0/Firefox_logo%2C_2019.svg/1024px-Firefox_logo%2C_2019.svg.png',
            'chrome': 'https://upload.wikimedia.org/wikipedia/commons/thumb/a/a5/Google_Chrome_icon_%28September_2014%29.svg/1024px-Google_Chrome_icon_%28September_2014%29.svg.png',
            'vlc': 'https://upload.wikimedia.org/wikipedia/commons/thumb/e/e6/VLC_Icon.svg/1024px-VLC_Icon.svg.png',
            'gimp': 'https://upload.wikimedia.org/wikipedia/commons/thumb/4/45/The_GIMP_icon_-_gnome.svg/1024px-The_GIMP_icon_-_gnome.svg.png',
            'inkscape': 'https://upload.wikimedia.org/wikipedia/commons/thumb/0/0d/Inkscape_Logo.svg/1024px-Inkscape_Logo.svg.png',
            'blender': 'https://upload.wikimedia.org/wikipedia/commons/thumb/0/0c/Blender_logo_no_text.svg/1024px-Blender_logo_no_text.svg.png',
            'krita': 'https://upload.wikimedia.org/wikipedia/commons/thumb/7/73/Calligrakrita-base.svg/1024px-Calligrakrita-base.svg.png',
            'discord': 'https://assets-global.website-files.com/6257adef93867e50d84d30e2/636e0a6918e57475a843dcad_icon_clyde_black_RGB.png',
            'telegram': 'https://upload.wikimedia.org/wikipedia/commons/thumb/8/82/Telegram_logo.svg/1024px-Telegram_logo.svg.png',
            'vscode': 'https://upload.wikimedia.org/wikipedia/commons/thumb/9/9a/Visual_Studio_Code_1.35_icon.svg/1024px-Visual_Studio_Code_1.35_icon.svg.png',
        }
        
        if name_lower in known_apps:
            icon_urls.append(known_apps[name_lower])
        
        # Alternative patterns to try
        search_variations = [
            name_lower,
            app_name.lower().replace(' ', '-'),
            app_name.lower().replace(' ', '_'),
        ]
        
        for variation in search_variations:
            if variation in known_apps:
                icon_urls.append(known_apps[variation])
        
        return icon_urls
    
    def _find_system_icon(self, app_name: str) -> Optional[str]:
        """
        Search system icon themes for application icon.
        
        Args:
            app_name (str): Application name to search for.
            
        Returns:
            Optional[str]: Icon name if found in system.
        """
        try:
            # Common system icon locations
            icon_theme_dirs = [
                Path("/usr/share/icons/hicolor"),
                Path("/usr/share/pixmaps"),
                Path.home() / ".local/share/icons/hicolor",
                Path.home() / ".icons"
            ]
            
            # Generate possible icon names
            search_names = [
                app_name.lower(),
                app_name.lower().replace(' ', '-'),
                app_name.lower().replace(' ', '_'),
                app_name.lower().replace(' ', ''),
            ]
            
            for theme_dir in icon_theme_dirs:
                if not theme_dir.exists():
                    continue
                    
                for icon_name in search_names:
                    # Look for icons in various formats
                    for ext in ['.svg', '.png', '.xpm', '.ico']:
                        for size_dir in ['scalable', '48x48', '64x64', '32x32', '128x128']:
                            icon_paths = [
                                theme_dir / size_dir / "apps" / f"{icon_name}{ext}",
                                theme_dir / f"{icon_name}{ext}",  # For pixmaps
                            ]
                            
                            for icon_path in icon_paths:
                                if icon_path.exists():
                                    return str(icon_path)
            
            return None
            
        except:
            return None
    
    def _get_category_icon(self, app_name: str, categories: List[str]) -> str:
        """
        Get appropriate icon based on application category and name heuristics.
        
        Args:
            app_name (str): Application name.
            categories (List[str]): Application categories.
            
        Returns:
            str: Icon name for the category.
        """
        name_lower = app_name.lower()
        
        # Filename/name-based heuristics
        if any(word in name_lower for word in ['browser', 'firefox', 'chrome', 'web']):
            return 'web-browser'
        elif any(word in name_lower for word in ['editor', 'code', 'vim', 'emacs', 'atom', 'vscode']):
            return 'text-editor'
        elif any(word in name_lower for word in ['player', 'vlc', 'media', 'video', 'music']):
            return 'multimedia-player'
        elif any(word in name_lower for word in ['image', 'photo', 'gimp', 'inkscape', 'draw']):
            return 'image-viewer'
        elif any(word in name_lower for word in ['game', 'play']):
            return 'applications-games'
        elif any(word in name_lower for word in ['office', 'writer', 'calc', 'document']):
            return 'application-office'
        elif any(word in name_lower for word in ['terminal', 'console', 'shell']):
            return 'utilities-terminal'
        elif any(word in name_lower for word in ['mail', 'email', 'thunderbird']):
            return 'mail-client'
        elif any(word in name_lower for word in ['chat', 'message', 'discord', 'telegram']):
            return 'chat'
        elif any(word in name_lower for word in ['develop', 'ide', 'studio']):
            return 'applications-development'
        
        # Category-based mapping
        if categories:
            category_map = {
                'AudioVideo': 'multimedia-player',
                'Audio': 'multimedia-player', 
                'Video': 'multimedia-player',
                'Development': 'applications-development',
                'Education': 'applications-education',
                'Game': 'applications-games',
                'Graphics': 'image-viewer',
                'Network': 'applications-internet',
                'Office': 'application-office',
                'Science': 'applications-science',
                'Settings': 'preferences-system',
                'System': 'applications-system',
                'Utility': 'applications-utilities',
                'WebBrowser': 'web-browser',
                'TextEditor': 'text-editor'
            }
            
            for category in categories:
                if category in category_map:
                    return category_map[category]
        
        # Default fallback
        return 'application-x-executable'
    
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
    
    def install_appimage(self, info: AppImageInfo) -> bool:
        """
        Install AppImage by copying to storage directory and updating exec path.
        
        Args:
            info (AppImageInfo): AppImage information to install.
            
        Returns:
            bool: True if installation successful, False otherwise.
        """
        try:
            # Copy AppImage to storage directory
            copied_path = self._copy_to_storage(info.appimage_path, info.name)
            if not copied_path:
                return False
            
            # Update exec command to point to the copy
            info.exec_command = str(copied_path)
            
            # Register the AppImage
            return self.register_appimage(info)
            
        except Exception as e:
            print(f"Error installing AppImage: {e}")
            return False
    
    def _copy_to_storage(self, appimage_path: str, app_name: str) -> Optional[Path]:
        """
        Copy AppImage to storage directory and make it executable.
        
        Args:
            appimage_path (str): Original AppImage path.
            app_name (str): Application name for filename.
            
        Returns:
            Optional[Path]: Path to copied file or None if failed.
        """
        try:
            source_path = Path(appimage_path)
            
            # Create safe filename
            safe_name = self._sanitize_filename(app_name)
            extension = source_path.suffix if source_path.suffix else '.AppImage'
            target_filename = f"{safe_name}{extension}"
            target_path = self.appimage_storage / target_filename
            
            # Handle filename conflicts
            counter = 1
            while target_path.exists():
                name_part = safe_name
                target_filename = f"{name_part}_{counter}{extension}"
                target_path = self.appimage_storage / target_filename
                counter += 1
            
            # Copy file
            shutil.copy2(source_path, target_path)
            
            # Make copy executable
            os.chmod(target_path, 0o755)
            
            return target_path
            
        except Exception as e:
            print(f"Error copying AppImage to storage: {e}")
            return None
    
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
    
    def uninstall_appimage(self, appimage_path: str) -> bool:
        """
        Uninstall an AppImage by removing copied file and registry entry.
        
        Args:
            appimage_path (str): Path to the original AppImage file.
            
        Returns:
            bool: True if uninstallation successful, False otherwise.
        """
        try:
            # Get registered info to find the copied file
            info = self.get_registered_info(appimage_path)
            if info and info.exec_command:
                # Remove the copied executable file
                exec_path = Path(info.exec_command)
                if exec_path.exists() and exec_path.parent == self.appimage_storage:
                    exec_path.unlink()
            
            # Unregister from registry
            return self.unregister_appimage(appimage_path)
            
        except Exception as e:
            print(f"Error uninstalling AppImage: {e}")
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

    def find_installed_version(self, new_info: AppImageInfo) -> Optional[AppImageInfo]:
        """
        Find if there's already an installed version of the same application.
        
        Args:
            new_info (AppImageInfo): Information about the new AppImage to check.
            
        Returns:
            Optional[AppImageInfo]: Information about installed version, or None if not found.
        """
        registry = self._load_registry()
        
        # Normalize the new app name for comparison
        new_name_normalized = self._normalize_app_name(new_info.name)
        
        for path, data in registry.items():
            try:
                installed_info = AppImageInfo(**data)
                installed_name_normalized = self._normalize_app_name(installed_info.name)
                
                # Check if it's the same application by name similarity
                if self._are_same_application(new_name_normalized, installed_name_normalized):
                    return installed_info
                    
            except Exception:
                continue
                
        return None

    def _normalize_app_name(self, name: str) -> str:
        """
        Normalize an application name for comparison.
        
        Args:
            name (str): Original application name.
            
        Returns:
            str: Normalized name for comparison.
        """
        # Convert to lowercase and remove common suffixes/prefixes
        normalized = name.lower().strip()
        
        # Remove version numbers, architecture info, and common suffixes
        normalized = re.sub(r'[-_\s]*v?\d+\.\d+(\.\d+)?[-_\s]*', '', normalized)
        normalized = re.sub(r'[-_\s]*(x86_64|amd64|i386|arm64|aarch64)[-_\s]*', '', normalized)
        normalized = re.sub(r'[-_\s]*(appimage|portable|linux)[-_\s]*', '', normalized)
        
        # Remove extra spaces and normalize separators
        normalized = re.sub(r'[-_\s]+', ' ', normalized).strip()
        
        return normalized

    def _are_same_application(self, name1: str, name2: str) -> bool:
        """
        Check if two normalized names represent the same application.
        
        Args:
            name1 (str): First normalized name.
            name2 (str): Second normalized name.
            
        Returns:
            bool: True if they represent the same application.
        """
        if not name1 or not name2:
            return False
            
        # Exact match
        if name1 == name2:
            return True
            
        # Check if one is a substring of the other (for different naming conventions)
        return name1 in name2 or name2 in name1

    def compare_versions(self, version1: str, version2: str) -> int:
        """
        Compare two version strings.
        
        Args:
            version1 (str): First version string.
            version2 (str): Second version string.
            
        Returns:
            int: -1 if version1 < version2, 0 if equal, 1 if version1 > version2.
        """
        if not version1 or version1 == 'Unknown':
            return -1 if version2 and version2 != 'Unknown' else 0
        if not version2 or version2 == 'Unknown':
            return 1
            
        # Try semantic version comparison
        try:
            v1_parts = self._parse_version(version1)
            v2_parts = self._parse_version(version2)
            
            # Compare each part
            for i in range(max(len(v1_parts), len(v2_parts))):
                v1_val = v1_parts[i] if i < len(v1_parts) else 0
                v2_val = v2_parts[i] if i < len(v2_parts) else 0
                
                if v1_val < v2_val:
                    return -1
                elif v1_val > v2_val:
                    return 1
                    
            return 0
            
        except Exception:
            # Fallback to string comparison
            if version1 < version2:
                return -1
            elif version1 > version2:
                return 1
            else:
                return 0

    def _parse_version(self, version: str) -> List[int]:
        """
        Parse a version string into numeric components.
        
        Args:
            version (str): Version string to parse.
            
        Returns:
            List[int]: List of numeric version components.
        """
        # Extract numeric parts from version string
        parts = re.findall(r'\d+', version)
        return [int(part) for part in parts]

    def is_newer_version(self, new_version: str, installed_version: str) -> bool:
        """
        Check if the new version is newer than the installed version.
        
        Args:
            new_version (str): Version of the new AppImage.
            installed_version (str): Version of the installed AppImage.
            
        Returns:
            bool: True if new version is newer.
        """
        return self.compare_versions(new_version, installed_version) > 0 