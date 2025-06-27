"""
Unit tests for AppImage Manager module.

Tests core functionality including AppImage detection, registry management,
and information extraction.
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

from src.appimage_manager import AppImageManager, AppImageInfo


class TestAppImageManager:
    """Test cases for AppImageManager class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.manager = AppImageManager()
    
    def test_init(self):
        """Test AppImageManager initialization."""
        assert self.manager.home_dir == Path.home()
        assert self.manager.applications_dir.exists()
        assert self.manager.registry_file.parent.exists()
    
    @patch('src.appimage_manager.magic.from_file')
    @patch('src.appimage_manager.os.access')
    @patch('builtins.open', mock_open(read_data=b'AppImage test data'))
    def test_is_appimage_valid(self, mock_access, mock_magic):
        """Test AppImage validation with valid file."""
        mock_access.return_value = True
        mock_magic.return_value = 'application/x-executable'
        
        with tempfile.NamedTemporaryFile(suffix='.AppImage') as tmp:
            result = self.manager.is_appimage(tmp.name)
            assert result is True
    
    @patch('src.appimage_manager.magic.from_file')
    @patch('src.appimage_manager.os.access')
    def test_is_appimage_invalid_mime(self, mock_access, mock_magic):
        """Test AppImage validation with invalid MIME type."""
        mock_access.return_value = True
        mock_magic.return_value = 'text/plain'
        
        with tempfile.NamedTemporaryFile(suffix='.AppImage') as tmp:
            result = self.manager.is_appimage(tmp.name)
            assert result is False
    
    def test_is_appimage_nonexistent(self):
        """Test AppImage validation with non-existent file."""
        result = self.manager.is_appimage('/nonexistent/file.AppImage')
        assert result is False
    
    def test_registry_operations(self):
        """Test registry load/save operations."""
        # Test empty registry
        registry = self.manager._load_registry()
        assert isinstance(registry, dict)
        
        # Test save registry
        test_data = {'test': 'value'}
        result = self.manager._save_registry(test_data)
        assert result is True
        
        # Test load saved registry
        loaded = self.manager._load_registry()
        assert loaded == test_data
    
    def test_register_appimage(self):
        """Test AppImage registration."""
        info = AppImageInfo(
            name="Test App",
            version="1.0",
            description="Test application",
            icon_path="",
            desktop_file_path="",
            appimage_path="/test/app.AppImage",
            exec_command="/test/app.AppImage",
            categories=["Application"],
            mime_types=[],
            installed_date=""
        )
        
        result = self.manager.register_appimage(info)
        assert result is True
        
        # Check if registered
        assert self.manager.is_registered("/test/app.AppImage")
        
        # Get registered info
        registered_info = self.manager.get_registered_info("/test/app.AppImage")
        assert registered_info is not None
        assert registered_info.name == "Test App"
    
    def test_unregister_appimage(self):
        """Test AppImage unregistration."""
        # First register an AppImage
        info = AppImageInfo(
            name="Test App",
            version="1.0",
            description="Test application",
            icon_path="",
            desktop_file_path="",
            appimage_path="/test/app.AppImage",
            exec_command="/test/app.AppImage",
            categories=["Application"],
            mime_types=[],
            installed_date=""
        )
        
        self.manager.register_appimage(info)
        assert self.manager.is_registered("/test/app.AppImage")
        
        # Now unregister
        result = self.manager.unregister_appimage("/test/app.AppImage")
        assert result is True
        assert not self.manager.is_registered("/test/app.AppImage")
    
    @patch('src.appimage_manager.magic.from_file')
    @patch('src.appimage_manager.os.access')
    @patch('builtins.open', mock_open(read_data=b'AppImage test data'))
    def test_extract_appimage_info_fallback(self, mock_access, mock_magic):
        """Test AppImage info extraction with fallback method."""
        mock_access.return_value = True
        mock_magic.return_value = 'application/x-executable'
        
        with tempfile.NamedTemporaryFile(suffix='.AppImage', delete=False) as tmp:
            tmp_path = Path(tmp.name)
            
            info = self.manager.extract_appimage_info(str(tmp_path))
            
            assert info is not None
            assert info.name == tmp_path.stem.replace('_', ' ').replace('-', ' ').title()
            assert info.appimage_path == str(tmp_path.absolute())
            assert info.exec_command == str(tmp_path.absolute())
            
            # Cleanup
            tmp_path.unlink()
    
    def test_get_registered_info_nonexistent(self):
        """Test getting info for non-registered AppImage."""
        info = self.manager.get_registered_info("/nonexistent/app.AppImage")
        assert info is None


@pytest.fixture
def sample_appimage_info():
    """Fixture providing sample AppImage info."""
    return AppImageInfo(
        name="Sample App",
        version="2.0",
        description="A sample application",
        icon_path="/path/to/icon.png",
        desktop_file_path="/path/to/desktop.file",
        appimage_path="/path/to/sample.AppImage",
        exec_command="/path/to/sample.AppImage",
        categories=["Office", "Productivity"],
        mime_types=["text/plain"],
        installed_date="2024-01-01T12:00:00"
    )


def test_appimage_info_dataclass(sample_appimage_info):
    """Test AppImageInfo dataclass functionality."""
    assert sample_appimage_info.name == "Sample App"
    assert sample_appimage_info.version == "2.0"
    assert "Office" in sample_appimage_info.categories
    
    # Test conversion to dict
    info_dict = sample_appimage_info.__dict__
    assert "name" in info_dict
    assert info_dict["name"] == "Sample App" 