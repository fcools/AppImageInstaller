"""
Main entry point for AppImage Installer.

This module provides the primary interface for the AppImage installer,
handling command-line arguments and dispatching to the appropriate handlers.
"""

import sys
import argparse
from pathlib import Path

from .appimage_handler import AppImageHandler
from .file_association import FileAssociation


def main():
    """
    Main entry point for the AppImage installer.
    
    Handles command-line arguments and routes to appropriate functionality.
    """
    parser = argparse.ArgumentParser(
        description="AppImage Installer - Manage AppImage files on Linux",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  appimage-installer myapp.AppImage    # Install/manage an AppImage
  appimage-installer --manage          # Open GUI to manage installed apps
  appimage-installer --register        # Register file associations
  appimage-installer --unregister      # Unregister file associations
        """
    )
    
    parser.add_argument(
        'appimage_file',
        nargs='?',
        help='AppImage file to process'
    )
    
    parser.add_argument(
        '--register',
        action='store_true',
        help='Register .AppImage file associations'
    )
    
    parser.add_argument(
        '--unregister',
        action='store_true',
        help='Unregister .AppImage file associations'
    )
    
    parser.add_argument(
        '--manage',
        action='store_true',
        help='Open AppImage Manager GUI to view and manage installed apps'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='AppImage Installer 1.0.0'
    )
    
    args = parser.parse_args()
    
    try:
        # Handle file association commands
        if args.register:
            return handle_register()
        elif args.unregister:
            return handle_unregister()
        elif args.manage:
            return handle_manage()
        
        # Handle AppImage file
        if args.appimage_file:
            return handle_appimage_file(args.appimage_file)
        
        # No arguments provided
        parser.print_help()
        return 1
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1


def handle_appimage_file(appimage_file: str) -> int:
    """
    Handle an AppImage file.
    
    Args:
        appimage_file (str): Path to the AppImage file.
        
    Returns:
        int: Exit code (0 for success, 1 for error).
    """
    # Check if file exists
    appimage_path = Path(appimage_file)
    if not appimage_path.exists():
        print(f"Error: File '{appimage_file}' not found.")
        return 1
    
    # Handle the AppImage
    handler = AppImageHandler()
    success = handler.handle_appimage(str(appimage_path.absolute()))
    
    return 0 if success else 1


def handle_register() -> int:
    """
    Register .AppImage file associations.
    
    Returns:
        int: Exit code (0 for success, 1 for error).
    """
    try:
        association = FileAssociation()
        
        if association.register():
            print("Successfully registered .AppImage file associations.")
            print("You can now double-click AppImage files to install them.")
            return 0
        else:
            print("Failed to register .AppImage file associations.")
            return 1
            
    except Exception as e:
        print(f"Error registering file associations: {e}")
        return 1


def handle_unregister() -> int:
    """
    Unregister .AppImage file associations.
    
    Returns:
        int: Exit code (0 for success, 1 for error).
    """
    try:
        association = FileAssociation()
        
        if association.unregister():
            print("Successfully unregistered .AppImage file associations.")
            return 0
        else:
            print("Failed to unregister .AppImage file associations.")
            return 1
            
    except Exception as e:
        print(f"Error unregistering file associations: {e}")
        return 1


def handle_manage() -> int:
    """
    Launch the AppImage Manager GUI.
    
    Returns:
        int: Exit code (0 for success, 1 for error).
    """
    try:
        from .gui_manager import AppImageManagerGUI
        
        gui = AppImageManagerGUI()
        gui.show()
        return 0
        
    except ImportError as e:
        print(f"Error: GUI framework not available: {e}")
        print("Please install tkinter or GTK for GUI support.")
        return 1
    except Exception as e:
        print(f"Error launching AppImage Manager: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 