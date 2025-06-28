"""
AppImage Handler module for AppImage Installer.

Main orchestrator that handles the complete workflow when an AppImage file
is opened, including checking registration status, showing dialogs, and
managing installation/uninstallation.
"""

import sys
from pathlib import Path
from typing import Optional

from .appimage_manager import AppImageManager, AppImageInfo
from .desktop_integration import DesktopIntegration
from .gui_dialogs import dialogs, DialogResult


class AppImageHandler:
    """
    Main handler for AppImage files.
    
    Orchestrates the complete workflow when an AppImage is opened:
    - Check if registered
    - Show appropriate dialogs
    - Handle installation/uninstallation
    - Launch applications
    """
    
    def __init__(self):
        """Initialize the AppImage handler with required components."""
        self.manager = AppImageManager()
        self.desktop = DesktopIntegration()
    
    def handle_appimage(self, appimage_path: str) -> bool:
        """
        Handle an AppImage file according to the main workflow.
        
        Args:
            appimage_path (str): Path to the AppImage file.
            
        Returns:
            bool: True if handling was successful, False otherwise.
        """
        try:
            # Validate AppImage
            if not self.manager.is_appimage(appimage_path):
                dialogs.show_error(
                    "Invalid File",
                    f"The file '{Path(appimage_path).name}' is not a valid AppImage file."
                )
                return False
            
            # Check if already registered
            if self.manager.is_registered(appimage_path):
                return self._handle_registered_appimage(appimage_path)
            else:
                return self._handle_unregistered_appimage(appimage_path)
                
        except Exception as e:
            dialogs.show_error(
                "Error",
                f"An error occurred while handling the AppImage:\n{str(e)}"
            )
            return False
    
    def _handle_registered_appimage(self, appimage_path: str) -> bool:
        """
        Handle an AppImage that is already registered.
        
        Args:
            appimage_path (str): Path to the AppImage file.
            
        Returns:
            bool: True if handling was successful, False otherwise.
        """
        try:
            # Get registered info
            info = self.manager.get_registered_info(appimage_path)
            if not info:
                # Inconsistent state - treat as unregistered
                return self._handle_unregistered_appimage(appimage_path)
            
            app_name = info.name
            
            # Ask user what to do
            response = dialogs.show_question(
                f"AppImage Already Installed",
                f"The AppImage '{app_name}' is already installed on your system.\n\n"
                f"What would you like to do?\n\n"
                f"• Click 'Yes' to uninstall it\n"
                f"• Click 'No' to launch it"
            )
            
            if response == DialogResult.YES:
                # Uninstall the AppImage
                return self._uninstall_appimage(info)
            else:
                # Launch the AppImage (use exec_command which points to the executable copy)
                return self._launch_appimage(info.exec_command, app_name)
                
        except Exception as e:
            dialogs.show_error(
                "Error",
                f"Error handling registered AppImage: {str(e)}"
            )
            return False
    
    def _handle_unregistered_appimage(self, appimage_path: str) -> bool:
        """
        Handle an AppImage that is not registered.
        
        Args:
            appimage_path (str): Path to the AppImage file.
            
        Returns:
            bool: True if handling was successful, False otherwise.
        """
        try:
            # Extract AppImage information
            info = self.manager.extract_appimage_info(appimage_path)
            if not info:
                dialogs.show_error(
                    "Extraction Failed",
                    "Could not extract information from the AppImage file."
                )
                return False
            
            app_name = info.name
            
            # Ask user if they want to install
            response = dialogs.show_question(
                "Install AppImage?",
                f"Would you like to install '{app_name}' to your system?\n\n"
                f"This will:\n"
                f"• Create a launcher shortcut\n"
                f"• Add it to your applications menu\n"
                f"• Launch the application\n\n"
                f"Click 'Yes' to install and launch, or 'No' to cancel."
            )
            
            if response == DialogResult.YES:
                # Install and launch the AppImage
                return self._install_appimage(info)
            else:
                # User cancelled
                return True
                
        except Exception as e:
            dialogs.show_error(
                "Error",
                f"Error handling unregistered AppImage: {str(e)}"
            )
            return False
    
    def _install_appimage(self, info: AppImageInfo) -> bool:
        """
        Install an AppImage to the system.
        
        Args:
            info (AppImageInfo): AppImage information.
            
        Returns:
            bool: True if installation was successful, False otherwise.
        """
        try:
            # Install AppImage (copy to storage and register)
            # This updates info.exec_command to point to the executable copy
            if not self.manager.install_appimage(info):
                dialogs.show_error(
                    "Installation Failed",
                    "Could not install AppImage to system."
                )
                return False
            
            # Create desktop file (after installation so exec_command points to copy)
            desktop_path = self.desktop.create_desktop_file(info)
            if not desktop_path:
                # Clean up on failure
                self.manager.uninstall_appimage(info.appimage_path)
                dialogs.show_error(
                    "Installation Failed",
                    "Could not create launcher shortcut."
                )
                return False
            
            # Update info with desktop file path
            info.desktop_file_path = desktop_path
            
            # Create desktop shortcut (optional)
            self.desktop.create_desktop_shortcut(info)
            
            # Show success message
            dialogs.show_info(
                "Installation Successful",
                f"'{info.name}' has been successfully installed!\n\n"
                f"You can now find it in your applications menu."
            )
            
            # Launch the application (use exec_command which points to the executable copy)
            return self._launch_appimage(info.exec_command, info.name)
            
        except Exception as e:
            dialogs.show_error(
                "Installation Error",
                f"Error during installation: {str(e)}"
            )
            return False
    
    def _uninstall_appimage(self, info: AppImageInfo) -> bool:
        """
        Uninstall an AppImage from the system.
        
        Args:
            info (AppImageInfo): AppImage information.
            
        Returns:
            bool: True if uninstallation was successful, False otherwise.
        """
        try:
            # Remove desktop file
            if info.desktop_file_path:
                self.desktop.remove_desktop_file(info.desktop_file_path)
            
            # Remove desktop shortcut
            self.desktop.remove_desktop_shortcut(info)
            
            # Uninstall AppImage (remove copy and unregister)
            self.manager.uninstall_appimage(info.appimage_path)
            
            # Show success message
            dialogs.show_info(
                "Uninstall Successful",
                f"'{info.name}' has been successfully uninstalled from your system."
            )
            
            return True
            
        except Exception as e:
            dialogs.show_error(
                "Uninstall Error",
                f"Error during uninstallation: {str(e)}"
            )
            return False
    
    def _launch_appimage(self, appimage_path: str, app_name: str) -> bool:
        """
        Launch an AppImage application.
        
        Args:
            appimage_path (str): Path to the AppImage file.
            app_name (str): Name of the application for error messages.
            
        Returns:
            bool: True if launch was successful, False otherwise.
        """
        try:
            if self.desktop.launch_appimage(appimage_path):
                return True
            else:
                dialogs.show_error(
                    "Launch Failed",
                    f"Could not launch '{app_name}'.\n\n"
                    f"Please check that the AppImage file is valid and executable."
                )
                return False
                
        except Exception as e:
            dialogs.show_error(
                "Launch Error",
                f"Error launching '{app_name}': {str(e)}"
            )
            return False


def main():
    """
    Main entry point for command-line usage.
    
    Usage: python -m src.appimage_handler <appimage_file>
    """
    if len(sys.argv) != 2:
        print("Usage: appimage-installer <appimage_file>")
        sys.exit(1)
    
    appimage_path = sys.argv[1]
    
    if not Path(appimage_path).exists():
        print(f"Error: File '{appimage_path}' not found.")
        sys.exit(1)
    
    handler = AppImageHandler()
    success = handler.handle_appimage(appimage_path)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main() 