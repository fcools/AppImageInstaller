"""
Setup script for AppImage Installer.

Provides installation and packaging configuration for the AppImage installer.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file for long description
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

setup(
    name="appimage-installer",
    version="1.0.0",
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
    zip_safe=False,
    keywords="appimage linux installer desktop integration",
    project_urls={
        "Bug Reports": "https://github.com/fcools/AppImageInstaller/issues",
        "Source": "https://github.com/fcools/AppImageInstaller",
        "Documentation": "https://github.com/fcools/AppImageInstaller#readme",
    },
) 