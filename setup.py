"""
Setup script for AppImage Installer.

Provides installation and packaging configuration for the AppImage installer.
"""

from setuptools import setup, find_packages
from pathlib import Path
import glob

# Read the README file for long description
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

# Collect icon files for installation
def collect_icon_files():
    """Collect all icon files for installation."""
    icon_files = []
    icons_dir = this_directory / "icons"
    
    if icons_dir.exists():
        # Find all icon directories
        for size_dir in icons_dir.glob("hicolor/*/apps/"):
            size = size_dir.parent.name
            target_dir = f"share/icons/hicolor/{size}/apps"
            icon_file = size_dir / "appimage-installer.png"
            if icon_file.exists():
                # Use relative path
                relative_path = str(icon_file.relative_to(this_directory))
                icon_files.append((target_dir, [relative_path]))
        
        # Add index.theme
        index_theme = icons_dir / "hicolor" / "index.theme"
        if index_theme.exists():
            # Use relative path
            relative_path = str(index_theme.relative_to(this_directory))
            icon_files.append(("share/icons/hicolor", [relative_path]))
    
    return icon_files

data_files = collect_icon_files()

setup(
    name="appimage-installer",
    version="1.2.0",
    author="AppImage Installer Project",
    author_email="",
    description="A simple tool for managing AppImage files on Linux",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/fcools/AppImageInstaller",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Desktop Environment",
        "Topic :: System :: Installation/Setup",
        "Topic :: Utilities",
    ],
    python_requires=">=3.8",
    install_requires=[
        "PyGObject>=3.42.0",
        "Pillow>=9.0.0",
        "python-magic>=0.4.24",
        "packaging>=21.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "appimage-installer=src.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.md", "*.txt"],
    },
    data_files=data_files,
    zip_safe=False,
    keywords="appimage linux installer desktop integration",
    project_urls={
        "Bug Reports": "https://github.com/fcools/AppImageInstaller/issues",
        "Source": "https://github.com/fcools/AppImageInstaller",
        "Documentation": "https://github.com/fcools/AppImageInstaller#readme",
    },
) 