"""
GUI Dialogs module for AppImage Installer.

Provides cross-platform native dialog boxes that integrate with the host system's
look and feel. Supports GTK (primary) and Tkinter (fallback).
"""

import os
import sys
from typing import Optional, Tuple
from enum import Enum


class DialogType(Enum):
    """Types of dialogs available."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    QUESTION = "question"


class DialogResult(Enum):
    """Dialog response results."""
    YES = "yes"
    NO = "no"
    OK = "ok"
    CANCEL = "cancel"


class NativeDialogs:
    """
    Native dialog system that adapts to the available GUI toolkit.
    
    Prioritizes GTK for better Linux integration, falls back to Tkinter
    if GTK is not available.
    """
    
    def __init__(self, parent_window=None):
        """Initialize the dialog system with the best available toolkit.
        
        Args:
            parent_window: Optional parent window for dialogs (Tkinter root window).
        """
        self._gtk_available = self._check_gtk()
        self._toolkit = "gtk" if self._gtk_available else "tkinter"
        self._parent_window = parent_window
    
    def _check_gtk(self) -> bool:
        """
        Check if GTK is available on the system.
        
        Returns:
            bool: True if GTK is available, False otherwise.
        """
        try:
            import gi
            gi.require_version('Gtk', '3.0')
            from gi.repository import Gtk
            return True
        except (ImportError, ValueError):
            return False
    
    def show_info(self, title: str, message: str) -> DialogResult:
        """
        Show an information dialog.
        
        Args:
            title (str): Dialog title.
            message (str): Dialog message.
            
        Returns:
            DialogResult: Always returns OK for info dialogs.
        """
        if self._toolkit == "gtk":
            return self._show_gtk_dialog(DialogType.INFO, title, message)
        else:
            return self._show_tkinter_dialog(DialogType.INFO, title, message, self._parent_window)
    
    def show_question(self, title: str, message: str) -> DialogResult:
        """
        Show a yes/no question dialog.
        
        Args:
            title (str): Dialog title.
            message (str): Dialog message.
            
        Returns:
            DialogResult: YES or NO based on user choice.
        """
        if self._toolkit == "gtk":
            return self._show_gtk_dialog(DialogType.QUESTION, title, message)
        else:
            return self._show_tkinter_dialog(DialogType.QUESTION, title, message, self._parent_window)
    
    def show_error(self, title: str, message: str) -> DialogResult:
        """
        Show an error dialog.
        
        Args:
            title (str): Dialog title.
            message (str): Dialog message.
            
        Returns:
            DialogResult: Always returns OK for error dialogs.
        """
        if self._toolkit == "gtk":
            return self._show_gtk_dialog(DialogType.ERROR, title, message)
        else:
            return self._show_tkinter_dialog(DialogType.ERROR, title, message, self._parent_window)
    
    def _show_gtk_dialog(self, dialog_type: DialogType, title: str, message: str) -> DialogResult:
        """
        Show a GTK dialog.
        
        Args:
            dialog_type (DialogType): Type of dialog to show.
            title (str): Dialog title.
            message (str): Dialog message.
            
        Returns:
            DialogResult: User's response.
        """
        try:
            import gi
            gi.require_version('Gtk', '3.0')
            from gi.repository import Gtk
            
            # Create dialog based on type
            if dialog_type == DialogType.QUESTION:
                dialog = Gtk.MessageDialog(
                    message_type=Gtk.MessageType.QUESTION,
                    buttons=Gtk.ButtonsType.YES_NO,
                    text=title
                )
            elif dialog_type == DialogType.ERROR:
                dialog = Gtk.MessageDialog(
                    message_type=Gtk.MessageType.ERROR,
                    buttons=Gtk.ButtonsType.OK,
                    text=title
                )
            else:  # INFO
                dialog = Gtk.MessageDialog(
                    message_type=Gtk.MessageType.INFO,
                    buttons=Gtk.ButtonsType.OK,
                    text=title
                )
            
            dialog.format_secondary_text(message)
            dialog.set_title("AppImage Installer")
            
            # Show dialog and get response
            response = dialog.run()
            dialog.destroy()
            
            # Convert GTK response to our enum
            if response == Gtk.ResponseType.YES:
                return DialogResult.YES
            elif response == Gtk.ResponseType.NO:
                return DialogResult.NO
            else:
                return DialogResult.OK
                
        except Exception:
            # Fallback to tkinter if GTK fails
            return self._show_tkinter_dialog(dialog_type, title, message)
    
    def _show_tkinter_dialog(self, dialog_type: DialogType, title: str, message: str, parent=None) -> DialogResult:
        """
        Show a Tkinter dialog as fallback.
        
        Args:
            dialog_type (DialogType): Type of dialog to show.
            title (str): Dialog title.
            message (str): Dialog message.
            parent: Optional parent window to use instead of creating new root.
            
        Returns:
            DialogResult: User's response.
        """
        try:
            import tkinter as tk
            from tkinter import messagebox
            
            # For GUI Manager, use custom modal dialog to avoid messagebox issues
            if parent is not None and dialog_type == DialogType.INFO:
                return self._show_custom_info_dialog(title, message, parent)
            
            # Use existing parent window if available, otherwise create temporary root
            if parent is not None:
                # Ensure parent window is updated and responsive
                parent.update_idletasks()
                root = parent
                should_destroy = False
            else:
                # Create temporary root window for standalone dialogs
                root = tk.Tk()
                root.withdraw()
                should_destroy = True
            
            if dialog_type == DialogType.QUESTION:
                result = messagebox.askyesno(title, message, parent=root)
                if should_destroy:
                    root.destroy()
                return DialogResult.YES if result else DialogResult.NO
            elif dialog_type == DialogType.ERROR:
                messagebox.showerror(title, message, parent=root)
                if should_destroy:
                    root.destroy()
                return DialogResult.OK
            else:  # INFO
                messagebox.showinfo(title, message, parent=root)
                if should_destroy:
                    root.destroy()
                return DialogResult.OK
                
        except Exception as e:
            # Last resort: print to console
            print(f"Dialog Error: {title}")
            print(f"Message: {message}")
            print(f"Error: {e}")
            return DialogResult.OK
    
    def _show_custom_info_dialog(self, title: str, message: str, parent) -> DialogResult:
        """
        Show a custom info dialog that doesn't have messagebox issues.
        
        Args:
            title (str): Dialog title.
            message (str): Dialog message.
            parent: Parent window.
            
        Returns:
            DialogResult: Always OK for info dialogs.
        """
        try:
            import tkinter as tk
            from tkinter import ttk
            
            # Create modal dialog window
            dialog = tk.Toplevel(parent)
            dialog.title("AppImage Installer")
            dialog.resizable(False, False)
            dialog.grab_set()  # Make modal
            dialog.transient(parent)  # Keep on top of parent
            
            # Center the dialog on parent
            dialog.geometry("400x150")
            parent.update_idletasks()
            x = parent.winfo_x() + (parent.winfo_width() // 2) - 200
            y = parent.winfo_y() + (parent.winfo_height() // 2) - 75
            dialog.geometry(f"+{x}+{y}")
            
            # Create content frame
            main_frame = ttk.Frame(dialog, padding="20")
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            # Title label
            title_label = ttk.Label(main_frame, text=title, font=('TkDefaultFont', 12, 'bold'))
            title_label.pack(anchor=tk.W, pady=(0, 10))
            
            # Message label
            msg_label = ttk.Label(main_frame, text=message, wraplength=350, justify=tk.LEFT)
            msg_label.pack(anchor=tk.W, pady=(0, 20))
            
            # Button frame
            button_frame = ttk.Frame(main_frame)
            button_frame.pack(anchor=tk.E)
            
            # Result variable
            result = [DialogResult.OK]
            
            def on_ok():
                result[0] = DialogResult.OK
                dialog.destroy()
            
            def on_close():
                result[0] = DialogResult.OK
                dialog.destroy()
            
            # OK button
            ok_btn = ttk.Button(button_frame, text="OK", command=on_ok)
            ok_btn.pack()
            ok_btn.focus()
            
            # Handle window close
            dialog.protocol("WM_DELETE_WINDOW", on_close)
            
            # Bind Enter key to OK
            dialog.bind('<Return>', lambda e: on_ok())
            dialog.bind('<Escape>', lambda e: on_close())
            
            # Wait for dialog to close
            dialog.wait_window()
            
            return result[0]
            
        except Exception as e:
            print(f"Custom dialog error: {e}")
            # Fallback to console
            print(f"INFO: {title}")
            print(f"Message: {message}")
            return DialogResult.OK


# Global instance for easy access
dialogs = NativeDialogs() 