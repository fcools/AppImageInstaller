"""
AppImage Manager GUI module.

Provides a graphical interface for managing installed AppImages,
allowing users to view, launch, and uninstall AppImage applications.
"""

import sys
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from .appimage_manager import AppImageManager, AppImageInfo
from .desktop_integration import DesktopIntegration
from .gui_dialogs import dialogs, DialogResult

# Try to import GUI frameworks
try:
    import tkinter as tk
    from tkinter import ttk, messagebox
    HAS_TKINTER = True
except ImportError:
    HAS_TKINTER = False

# GTK support removed for simplicity - using Tkinter only


class AppImageManagerGUI:
    """
    GUI for managing installed AppImages.
    
    Provides a window with a list of installed AppImages and options
    to launch or uninstall them.
    """
    
    def __init__(self):
        """Initialize the AppImage manager GUI."""
        self.manager = AppImageManager()
        self.desktop = DesktopIntegration()
        self.apps = []
        self.selected_app = None
        self.dialogs = None  # Will be initialized after creating GUI
        
        # Try Tkinter first for better compatibility
        if HAS_TKINTER:
            self._create_tkinter_gui()
            # Initialize dialogs with parent window for proper integration
            from .gui_dialogs import NativeDialogs
            self.dialogs = NativeDialogs(parent_window=self.tk_root)
        else:
            raise RuntimeError("No GUI framework available. Please install tkinter.")
    
    def show(self) -> None:
        """Show the manager window."""
        if hasattr(self, 'tk_root'):
            self._show_tkinter()
        else:
            raise RuntimeError("GUI not properly initialized")
    
    def _create_tkinter_gui(self) -> None:
        """Create Tkinter-based GUI."""
        self.tk_root = tk.Tk()
        self.tk_root.title("AppImage Manager")
        self.tk_root.geometry("800x600")
        
        # Main frame
        main_frame = ttk.Frame(self.tk_root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title = ttk.Label(main_frame, text="Installed AppImage Applications", 
                         font=('TkDefaultFont', 14, 'bold'))
        title.pack(anchor=tk.W, pady=(0, 10))
        
        # Treeview with scrollbars
        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Columns: Name, Version, Install Date, Path, Index
        self.tk_tree = ttk.Treeview(tree_frame, columns=('version', 'date', 'path', 'index'), show='tree headings')
        self.tk_tree.heading('#0', text='Application')
        self.tk_tree.heading('version', text='Version')
        self.tk_tree.heading('date', text='Installed')
        self.tk_tree.heading('path', text='Location')
        
        self.tk_tree.column('#0', width=200, minwidth=150)
        self.tk_tree.column('version', width=100, minwidth=80)
        self.tk_tree.column('date', width=120, minwidth=100)
        self.tk_tree.column('path', width=300, minwidth=200)
        self.tk_tree.column('index', width=0, minwidth=0, stretch=False)  # Hidden column
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tk_tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.tk_tree.xview)
        self.tk_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack tree and scrollbars
        self.tk_tree.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Selection handler
        self.tk_tree.bind('<<TreeviewSelect>>', self._on_tk_selection_changed)
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(anchor=tk.E, pady=(10, 0))
        
        # Buttons
        self.tk_launch_btn = ttk.Button(button_frame, text="Launch", 
                                       command=self._on_tk_launch, state=tk.DISABLED)
        self.tk_launch_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.tk_uninstall_btn = ttk.Button(button_frame, text="Uninstall", 
                                          command=self._on_tk_uninstall, state=tk.DISABLED)
        self.tk_uninstall_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.tk_icon_btn = ttk.Button(button_frame, text="Find Icon", 
                                     command=self._on_tk_find_icon, state=tk.DISABLED)
        self.tk_icon_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        refresh_btn = ttk.Button(button_frame, text="Refresh", command=self._on_tk_refresh)
        refresh_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        close_btn = ttk.Button(button_frame, text="Close", command=self.tk_root.destroy)
        close_btn.pack(side=tk.LEFT)
        
        # Load initial data
        self._refresh_tk_list()
    
    def _refresh_tk_list(self) -> None:
        """Refresh the Tkinter app list."""
        # Clear existing items
        for item in self.tk_tree.get_children():
            self.tk_tree.delete(item)
        
        # Load installed apps
        self.apps = self._load_installed_apps()
        
        # Add to tree  
        for i, app in enumerate(self.apps):
            install_date = self._format_date(app.installed_date)
            item_id = self.tk_tree.insert('', 'end', text=app.name, values=(
                app.version,
                install_date,
                app.appimage_path,
                str(i)  # Store app index as a value
            ))
    
    def _load_installed_apps(self) -> List[AppImageInfo]:
        """Load list of installed AppImages."""
        registry = self.manager._load_registry()
        apps = []
        
        for path, data in registry.items():
            try:
                app = AppImageInfo(**data)
                apps.append(app)
            except Exception:
                # Skip invalid entries
                continue
        
        # Sort by name
        apps.sort(key=lambda x: x.name.lower())
        return apps
    
    def _format_date(self, date_str: str) -> str:
        """Format date string for display."""
        if not date_str:
            return "Unknown"
        
        try:
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return dt.strftime("%Y-%m-%d %H:%M")
        except Exception:
            return date_str
    
    def _process_gtk_events_and_refresh(self) -> None:
        """Process pending GTK events and then refresh the GUI to avoid conflicts."""
        # Process any pending GTK events before refreshing Tkinter GUI
        try:
            import gi
            gi.require_version('Gtk', '3.0')
            from gi.repository import Gtk
            while Gtk.events_pending():
                Gtk.main_iteration()
        except:
            pass
        # Now refresh the GUI
        self.tk_root.after(50, self._refresh_tk_list)
    
    # Tkinter event handlers
    def _on_tk_selection_changed(self, event) -> None:
        """Handle Tkinter selection change."""
        selection = self.tk_tree.selection()
        if selection:
            item = selection[0]
            try:
                # Get values tuple and extract the index (last element)
                values = self.tk_tree.item(item, 'values')
                app_index = int(values[3])  # index is the 4th value (0-based)
                self.selected_app = self.apps[app_index]
                self.tk_launch_btn.config(state=tk.NORMAL)
                self.tk_uninstall_btn.config(state=tk.NORMAL)
                # Enable icon button if app has no custom icon or uses default
                has_default_icon = (not self.selected_app.icon_path or 
                                  self.selected_app.icon_path == 'application-x-executable' or
                                  'application' in self.selected_app.icon_path)
                self.tk_icon_btn.config(state=tk.NORMAL if has_default_icon else tk.DISABLED)
            except (ValueError, IndexError):
                self.selected_app = None
                self.tk_launch_btn.config(state=tk.DISABLED)
                self.tk_uninstall_btn.config(state=tk.DISABLED)
                self.tk_icon_btn.config(state=tk.DISABLED)
        else:
            self.selected_app = None
            self.tk_launch_btn.config(state=tk.DISABLED)
            self.tk_uninstall_btn.config(state=tk.DISABLED)
            self.tk_icon_btn.config(state=tk.DISABLED)
    
    def _on_tk_launch(self) -> None:
        """Handle Tkinter launch button."""
        if self.selected_app:
            self._launch_app(self.selected_app)
    
    def _on_tk_uninstall(self) -> None:
        """Handle Tkinter uninstall button."""
        if self.selected_app:
            self._uninstall_app(self.selected_app)
    
    def _on_tk_refresh(self) -> None:
        """Handle Tkinter refresh button."""
        self._refresh_tk_list()
    
    def _on_tk_find_icon(self) -> None:
        """Handle Tkinter find icon button."""
        if self.selected_app:
            self._find_icon_for_app(self.selected_app)
    
    def _show_tkinter(self) -> None:
        """Show Tkinter window and start main loop."""
        self.tk_root.mainloop()
    
    # Common functionality
    def _launch_app(self, app: AppImageInfo) -> None:
        """Launch the selected application."""
        try:
            if self.desktop.launch_appimage(app.exec_command):
                pass  # Success, no message needed
            else:
                self.dialogs.show_error(
                    "Launch Failed",
                    f"Could not launch '{app.name}'.\n\n"
                    f"The application file may be missing or corrupted."
                )
        except Exception as e:
            self.dialogs.show_error(
                "Launch Error",
                f"Error launching '{app.name}': {str(e)}"
            )
    
    def _uninstall_app(self, app: AppImageInfo) -> None:
        """Uninstall the selected application."""
        response = self.dialogs.show_question(
            "Confirm Uninstall",
            f"Are you sure you want to uninstall '{app.name}'?\n\n"
            f"This will remove:\n"
            f"• Application shortcuts\n"
            f"• Menu entries\n"
            f"• Installed application files\n\n"
            f"Click 'Yes' to uninstall or 'No' to cancel."
        )
        
        if response == DialogResult.YES:
            try:
                # Remove desktop file
                if app.desktop_file_path:
                    self.desktop.remove_desktop_file(app.desktop_file_path)
                
                # Remove desktop shortcut
                self.desktop.remove_desktop_shortcut(app)
                
                # Uninstall AppImage
                if self.manager.uninstall_appimage(app.appimage_path):
                    # Use global GTK dialogs (no parent window) and properly handle event loops
                    from .gui_dialogs import dialogs
                    dialogs.show_info(
                        "Uninstall Successful",
                        f"'{app.name}' has been successfully uninstalled.\n\n"
                        f"All shortcuts and menu entries have been removed."
                    )
                    # Process GTK events and refresh GUI
                    self._process_gtk_events_and_refresh()
                else:
                    self.dialogs.show_error(
                        "Uninstall Failed",
                        f"Could not completely uninstall '{app.name}'."
                    )
                    
            except Exception as e:
                self.dialogs.show_error(
                    "Uninstall Error",
                    f"Error during uninstallation: {str(e)}"
                )
    

    
    def _find_icon_for_app(self, app: AppImageInfo) -> None:
        """Find and apply a better icon for the selected application."""
        # Ask user for consent to search web
        response = self.dialogs.show_question(
            "Search for Icon",
            f"Would you like to search the web for a better icon for '{app.name}'?\n\n"
            f"This will:\n"
            f"• Search safe, known icon sources\n"
            f"• Download and apply a better icon if found\n"
            f"• Only search for common, well-known applications\n\n"
            f"Click 'Yes' to search online or 'No' to use local system icons only."
        )
        
        if response == DialogResult.YES:
            # Show progress message
            self.tk_root.config(cursor="wait")
            self.tk_root.update()
            
            try:
                # Search for web icon
                icon_path = self.manager.search_web_icon(app.name, app.version)
                
                if icon_path:
                    # Update the app's icon path
                    app.icon_path = icon_path
                    
                    # Update in registry
                    registry = self.manager._load_registry()
                    abs_path = str(Path(app.appimage_path).absolute())
                    if abs_path in registry:
                        registry[abs_path]['icon_path'] = icon_path
                        self.manager._save_registry(registry)
                    
                    # Recreate desktop file with new icon
                    if app.desktop_file_path:
                        self.desktop.remove_desktop_file(app.desktop_file_path)
                    
                    app.desktop_file_path = self.desktop.create_desktop_file(app)
                    self.desktop.create_desktop_shortcut(app)
                    
                    # Use global GTK dialogs (no parent window) and properly handle event loops
                    from .gui_dialogs import dialogs
                    dialogs.show_info(
                        "Icon Updated",
                        f"Successfully found and applied a new icon for '{app.name}'!"
                    )
                    # Process GTK events and refresh GUI
                    self._process_gtk_events_and_refresh()
                else:
                    # Use global GTK dialogs (no parent window)
                    from .gui_dialogs import dialogs
                    dialogs.show_info(
                        "No Icon Found",
                        f"Could not find a suitable icon for '{app.name}' online.\n"
                        f"The application will continue to use the default icon."
                    )
                    
            except Exception as e:
                self.dialogs.show_error(
                    "Icon Search Error",
                    f"Error searching for icon: {str(e)}"
                )
            finally:
                self.tk_root.config(cursor="")
        
        else:
            # Try to find better system icon
            system_icon = self.manager._find_system_icon(app.name)
            if system_icon and system_icon != app.icon_path:
                # Update the app's icon path
                app.icon_path = system_icon
                
                # Update in registry
                registry = self.manager._load_registry()
                abs_path = str(Path(app.appimage_path).absolute())
                if abs_path in registry:
                    registry[abs_path]['icon_path'] = system_icon
                    self.manager._save_registry(registry)
                
                # Recreate desktop file with new icon
                if app.desktop_file_path:
                    self.desktop.remove_desktop_file(app.desktop_file_path)
                
                app.desktop_file_path = self.desktop.create_desktop_file(app)
                self.desktop.create_desktop_shortcut(app)
                
                # Use global GTK dialogs (no parent window) and properly handle event loops
                from .gui_dialogs import dialogs
                dialogs.show_info(
                    "Icon Updated",
                    f"Successfully updated the icon for '{app.name}' using a system icon!"
                )
                # Process GTK events and refresh GUI
                self._process_gtk_events_and_refresh()
            else:
                # Use global GTK dialogs (no parent window)
                from .gui_dialogs import dialogs
                dialogs.show_info(
                    "No Better Icon",
                    f"Could not find a better system icon for '{app.name}'.\n"
                    f"The application will continue to use the current icon."
                )


def main():
    """Main entry point for the AppImage Manager GUI."""
    try:
        gui = AppImageManagerGUI()
        gui.show()
    except Exception as e:
        print(f"Error starting AppImage Manager: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
