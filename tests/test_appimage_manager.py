"""
Unit tests for AppImage Manager module.

Tests the core functionality including AppImage detection, metadata extraction,
registry management, and version update handling.
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from src.appimage_manager import AppImageManager, AppImageInfo


class TestAppImageManager:
    """Test cases for AppImageManager class."""
    
    def setup_method(self):
        """Set up test environment before each test."""
        # Create temporary directory for test files
        self.temp_dir = Path(tempfile.mkdtemp())
        
        # Mock the manager to use temporary directories
        self.manager = AppImageManager()
        self.manager.config_dir = self.temp_dir / "config"
        self.manager.data_dir = self.temp_dir / "data"
        self.manager.appimage_storage = self.temp_dir / "Applications"
        self.manager.registry_file = self.temp_dir / "config" / "appimage-installer" / "registry.json"
        
        # Create directories
        self.manager._ensure_directories()
        
        # Sample AppImage info for testing
        self.sample_info = AppImageInfo(
            name="Test App",
            version="1.0.0",
            description="Test application",
            icon_path="test-icon.png",
            desktop_file_path="test.desktop",
            appimage_path="/path/to/test.AppImage",
            exec_command="/path/to/test.AppImage",
            categories=["Development"],
            mime_types=["text/plain"],
            installed_date="2023-01-01T12:00:00"
        )
    
    def teardown_method(self):
        """Clean up after each test."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_appimage_detection(self):
        """Test AppImage file detection."""
        # Create test files
        appimage_file = self.temp_dir / "test.AppImage"
        regular_file = self.temp_dir / "test.txt"
        
        # Create AppImage file with signature
        appimage_file.write_bytes(b"#!/bin/sh\nAppImage signature here\x00" + b"A" * 1000)
        regular_file.write_text("Not an AppImage")
        
        # Make AppImage executable
        appimage_file.chmod(0o755)
        
        # Test detection
        assert self.manager.is_appimage(str(appimage_file))
        assert not self.manager.is_appimage(str(regular_file))
        assert not self.manager.is_appimage("/nonexistent/file.AppImage")
    
    def test_registry_operations(self):
        """Test registry save and load operations."""
        # Test save and load registry
        test_registry = {
            "/path/to/app1.AppImage": {
                "name": "App 1",
                "version": "1.0.0"
            },
            "/path/to/app2.AppImage": {
                "name": "App 2", 
                "version": "2.0.0"
            }
        }
        
        # Save registry
        assert self.manager._save_registry(test_registry)
        
        # Load registry
        loaded_registry = self.manager._load_registry()
        assert loaded_registry == test_registry
        
        # Test loading non-existent registry
        self.manager.registry_file.unlink()
        empty_registry = self.manager._load_registry()
        assert empty_registry == {}
    
    def test_appimage_registration(self):
        """Test AppImage registration and unregistration."""
        # Register AppImage
        assert self.manager.register_appimage(self.sample_info)
        
        # Check if registered
        assert self.manager.is_registered(self.sample_info.appimage_path)
        
        # Get registered info
        retrieved_info = self.manager.get_registered_info(self.sample_info.appimage_path)
        assert retrieved_info is not None
        assert retrieved_info.name == self.sample_info.name
        assert retrieved_info.version == self.sample_info.version
        
        # Unregister AppImage
        assert self.manager.unregister_appimage(self.sample_info.appimage_path)
        
        # Check if unregistered
        assert not self.manager.is_registered(self.sample_info.appimage_path)
        assert self.manager.get_registered_info(self.sample_info.appimage_path) is None

    def test_version_comparison(self):
        """Test version comparison functionality."""
        # Test semantic version comparison
        assert self.manager.compare_versions("1.0.0", "2.0.0") == -1
        assert self.manager.compare_versions("2.0.0", "1.0.0") == 1
        assert self.manager.compare_versions("1.0.0", "1.0.0") == 0
        
        # Test with different version formats
        assert self.manager.compare_versions("1.2.3", "1.2.4") == -1
        assert self.manager.compare_versions("2.1.0", "2.0.9") == 1
        assert self.manager.compare_versions("1.0", "1.0.0") == 0
        
        # Test with unknown versions
        assert self.manager.compare_versions("Unknown", "1.0.0") == -1
        assert self.manager.compare_versions("1.0.0", "Unknown") == 1
        assert self.manager.compare_versions("Unknown", "Unknown") == 0
        
        # Test is_newer_version convenience method
        assert self.manager.is_newer_version("2.0.0", "1.0.0")
        assert not self.manager.is_newer_version("1.0.0", "2.0.0")
        assert not self.manager.is_newer_version("1.0.0", "1.0.0")

    def test_app_name_normalization(self):
        """Test application name normalization for version detection."""
        # Test basic normalization
        assert self.manager._normalize_app_name("GIMP") == "gimp"
        assert self.manager._normalize_app_name("Test App") == "test app"
        
        # Test version removal
        assert self.manager._normalize_app_name("GIMP-3.0.4") == "gimp"
        assert self.manager._normalize_app_name("Test App v1.2.3") == "test app"
        assert self.manager._normalize_app_name("App-v2.5.1-x86_64") == "app"
        
        # Test architecture removal
        assert self.manager._normalize_app_name("App-x86_64") == "app"
        assert self.manager._normalize_app_name("App-amd64-AppImage") == "app"
        
        # Test common suffix removal
        assert self.manager._normalize_app_name("App-portable") == "app"
        assert self.manager._normalize_app_name("App-linux") == "app"
        assert self.manager._normalize_app_name("App-appimage") == "app"

    def test_same_application_detection(self):
        """Test detection of same applications with different naming."""
        # Test exact matches
        assert self.manager._are_same_application("gimp", "gimp")
        assert self.manager._are_same_application("test app", "test app")
        
        # Test substring matches
        assert self.manager._are_same_application("gimp", "gimp image editor")
        assert self.manager._are_same_application("vs code", "visual studio code")
        assert self.manager._are_same_application("firefox", "firefox browser")
        
        # Test non-matches
        assert not self.manager._are_same_application("gimp", "inkscape")
        assert not self.manager._are_same_application("vs code", "atom")
        
        # Test edge cases
        assert not self.manager._are_same_application("", "app")
        assert not self.manager._are_same_application("app", "")
        assert not self.manager._are_same_application("", "")

    def test_find_installed_version(self):
        """Test finding installed versions of the same application."""
        # Create test registry with multiple applications
        gimp_info = AppImageInfo(
            name="GIMP",
            version="3.0.4",
            description="Image editor",
            icon_path="gimp.png",
            desktop_file_path="gimp.desktop",
            appimage_path="/path/to/GIMP-3.0.4-x86_64.AppImage",
            exec_command="/home/user/Applications/GIMP.AppImage",
            categories=["Graphics"],
            mime_types=["image/png"],
            installed_date="2023-01-01T12:00:00"
        )
        
        firefox_info = AppImageInfo(
            name="Firefox",
            version="120.0",
            description="Web browser",
            icon_path="firefox.png",
            desktop_file_path="firefox.desktop",
            appimage_path="/path/to/Firefox-120.0.AppImage",
            exec_command="/home/user/Applications/Firefox.AppImage",
            categories=["Network"],
            mime_types=["text/html"],
            installed_date="2023-01-01T12:00:00"
        )
        
        # Register both applications
        self.manager.register_appimage(gimp_info)
        self.manager.register_appimage(firefox_info)
        
        # Test finding existing versions
        new_gimp_info = AppImageInfo(
            name="GIMP Image Editor",  # Slightly different name
            version="3.0.5",
            description="Image editor",
            icon_path="",
            desktop_file_path="",
            appimage_path="/path/to/GIMP-3.0.5-x86_64.AppImage",
            exec_command="/path/to/GIMP-3.0.5-x86_64.AppImage",
            categories=["Graphics"],
            mime_types=[],
            installed_date=""
        )
        
        # Should find the existing GIMP installation
        found_version = self.manager.find_installed_version(new_gimp_info)
        assert found_version is not None
        assert found_version.name == "GIMP"
        assert found_version.version == "3.0.4"
        
        # Test with completely different application
        new_app_info = AppImageInfo(
            name="Blender",
            version="4.0.0",
            description="3D creation suite",
            icon_path="",
            desktop_file_path="",
            appimage_path="/path/to/Blender-4.0.0.AppImage",
            exec_command="/path/to/Blender-4.0.0.AppImage",
            categories=["Graphics"],
            mime_types=[],
            installed_date=""
        )
        
        # Should not find any existing version
        found_version = self.manager.find_installed_version(new_app_info)
        assert found_version is None

    def test_version_parsing(self):
        """Test version string parsing into numeric components."""
        # Test standard semantic versions
        assert self.manager._parse_version("1.2.3") == [1, 2, 3]
        assert self.manager._parse_version("10.20.30") == [10, 20, 30]
        
        # Test versions with extra text
        assert self.manager._parse_version("v1.2.3-beta") == [1, 2, 3]
        assert self.manager._parse_version("Version 2.5.1 Release") == [2, 5, 1]
        
        # Test versions with different separators
        assert self.manager._parse_version("1-2-3") == [1, 2, 3]
        assert self.manager._parse_version("1_2_3") == [1, 2, 3]
        
        # Test edge cases
        assert self.manager._parse_version("") == []
        assert self.manager._parse_version("no-numbers") == []
        assert self.manager._parse_version("123") == [123]

    @patch('src.appimage_manager.shutil.copy2')
    @patch('src.appimage_manager.os.chmod')
    def test_copy_to_storage(self, mock_chmod, mock_copy):
        """Test copying AppImage to storage directory."""
        # Create a source file
        source_file = self.temp_dir / "test.AppImage"
        source_file.write_text("test content")
        
        # Test successful copy
        target_path = self.manager._copy_to_storage(str(source_file), "Test App")
        
        # Verify calls and return value
        assert target_path is not None
        assert target_path.name == "Test_App.AppImage"
        mock_copy.assert_called_once()
        mock_chmod.assert_called_once_with(target_path, 0o755)
        
        # Test filename conflict handling
        # Create existing file to simulate conflict
        existing_file = self.manager.appimage_storage / "Test_App.AppImage"
        existing_file.touch()
        
        target_path = self.manager._copy_to_storage(str(source_file), "Test App")
        assert target_path is not None
        assert target_path.name == "Test_App_1.AppImage"

    def test_filename_sanitization(self):
        """Test filename sanitization for safe storage."""
        # Test basic sanitization
        assert self.manager._sanitize_filename("Test App") == "Test_App"
        assert self.manager._sanitize_filename("App with Spaces") == "App_with_Spaces"
        
        # Test special character removal
        assert self.manager._sanitize_filename("App/Name\\Test") == "App_Name_Test"
        assert self.manager._sanitize_filename("App:Name*Test") == "App_Name_Test"
        
        # Test multiple underscore cleanup
        assert self.manager._sanitize_filename("App___Name") == "App_Name"
        assert self.manager._sanitize_filename("___App___") == "App"
        
        # Test edge cases
        assert self.manager._sanitize_filename("") == ""
        assert self.manager._sanitize_filename("___") == ""


if __name__ == "__main__":
    pytest.main([__file__]) 