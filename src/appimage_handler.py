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
            
            # Check if there's already an installed version of the same application
            existing_version = self.manager.find_installed_version(info)
            
            if existing_version:
                # Found an existing version - offer update
                return self._handle_version_update(info, existing_version)
            else:
                # No existing version - fresh install
                return self._handle_fresh_install(info)
                
        except Exception as e:
            dialogs.show_error(
                "Error",
                f"Error handling unregistered AppImage: {str(e)}"
            )
            return False
    
    def _handle_version_update(self, new_info: AppImageInfo, existing_info: AppImageInfo) -> bool:
        """
        Handle installation of a new version when an existing version is already installed.
        
        Args:
            new_info (AppImageInfo): Information about the new AppImage.
            existing_info (AppImageInfo): Information about the existing installed version.
            
        Returns:
            bool: True if handling was successful, False otherwise.
        """
        try:
            app_name = new_info.name
            new_version = new_info.version
            existing_version = existing_info.version
            
            # Compare versions
            is_newer = self.manager.is_newer_version(new_version, existing_version)
            
            if is_newer:
                # New version is newer
                response = dialogs.show_question(
                    "Update Available",
                    f"A newer version of '{app_name}' is available!\n\n"
                    f"Installed version: {existing_version}\n"
                    f"New version: {new_version}\n\n"
                    f"Would you like to update to the new version?\n\n"
                    f"This will:\n"
                    f"• Replace the current version\n"
                    f"• Keep your launcher shortcuts\n"
                    f"• Launch the updated application\n\n"
                    f"Click 'Yes' to update or 'No' to cancel."
                )
            elif self.manager.compare_versions(new_version, existing_version) == 0:
                # Same version
                response = dialogs.show_question(
                    "Same Version Detected",
                    f"'{app_name}' version {existing_version} is already installed.\n\n"
                    f"Would you like to reinstall it?\n\n"
                    f"This will:\n"
                    f"• Replace the current installation\n"
                    f"• Keep your launcher shortcuts\n"
                    f"• Launch the application\n\n"
                    f"Click 'Yes' to reinstall or 'No' to cancel."
                )
            else:
                # New version is older
                response = dialogs.show_question(
                    "Older Version Detected",
                    f"You are trying to install an older version of '{app_name}'.\n\n"
                    f"Installed version: {existing_version}\n"
                    f"This version: {new_version}\n\n"
                    f"Would you like to downgrade to this version?\n\n"
                    f"This will:\n"
                    f"• Replace the newer version\n"
                    f"• Keep your launcher shortcuts\n"
                    f"• Launch the application\n\n"
                    f"Click 'Yes' to downgrade or 'No' to cancel."
                )
            
            if response == DialogResult.YES:
                # User wants to update/reinstall/downgrade
                return self._perform_update(new_info, existing_info)
            else:
                # User cancelled
                return True
                
        except Exception as e:
            dialogs.show_error(
                "Update Error",
                f"Error handling version update: {str(e)}"
            )
            return False
    
    def _handle_fresh_install(self, info: AppImageInfo) -> bool:
        """
        Handle fresh installation of an AppImage (no existing version).
        
        Args:
            info (AppImageInfo): AppImage information.
            
        Returns:
            bool: True if handling was successful, False otherwise.
        """
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
    
    def _perform_update(self, new_info: AppImageInfo, existing_info: AppImageInfo) -> bool:
        """
        Perform the actual update by removing the old version and installing the new one.
        
        Args:
            new_info (AppImageInfo): Information about the new AppImage.
            existing_info (AppImageInfo): Information about the existing version.
            
        Returns:
            bool: True if update was successful, False otherwise.
        """
        try:
            # Preserve the desktop file path and icon path from existing installation
            preserved_desktop_path = existing_info.desktop_file_path
            preserved_icon_path = existing_info.icon_path
            
            # Remove the old version (but keep desktop integration for seamless update)
            old_exec_path = Path(existing_info.exec_command) if existing_info.exec_command else None
            if old_exec_path and old_exec_path.exists() and old_exec_path.parent == self.manager.appimage_storage:
                old_exec_path.unlink()
            
            # Unregister the old version from registry
            self.manager.unregister_appimage(existing_info.appimage_path)
            
            # Use preserved icon if the new version doesn't have a good one
            if preserved_icon_path and (not new_info.icon_path or new_info.icon_path == 'application-x-executable'):
                new_info.icon_path = preserved_icon_path
            
            # Install the new version
            if not self.manager.install_appimage(new_info):
                dialogs.show_error(
                    "Update Failed",
                    "Could not install the new version to system."
                )
                return False
            
            # Update desktop file with new information
            if preserved_desktop_path:
                self.desktop.remove_desktop_file(preserved_desktop_path)
            
            desktop_path = self.desktop.create_desktop_file(new_info)
            if not desktop_path:
                dialogs.show_error(
                    "Update Failed",
                    "Could not update launcher shortcut."
                )
                return False
            
            # Update info with desktop file path
            new_info.desktop_file_path = desktop_path
            
            # Create desktop shortcut (optional)
            self.desktop.create_desktop_shortcut(new_info)
            
            # Show success message
            action = "updated" if self.manager.is_newer_version(new_info.version, existing_info.version) else "reinstalled"
            dialogs.show_info(
                "Update Successful",
                f"'{new_info.name}' has been successfully {action}!\n\n"
                f"New version: {new_info.version}\n"
                f"You can find it in your applications menu."
            )
            
            # Launch the updated application
            return self._launch_appimage(new_info.exec_command, new_info.name)
            
        except Exception as e:
            dialogs.show_error(
                "Update Error",
                f"Error during update: {str(e)}"
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