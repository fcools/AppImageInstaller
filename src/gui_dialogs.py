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
    
    def __init__(self):
        """Initialize the dialog system with the best available toolkit."""
        self._gtk_available = self._check_gtk()
        self._toolkit = "gtk" if self._gtk_available else "tkinter"
    
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
            return self._show_tkinter_dialog(DialogType.INFO, title, message)
    
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
            return self._show_tkinter_dialog(DialogType.QUESTION, title, message)
    
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
            return self._show_tkinter_dialog(DialogType.ERROR, title, message)
    
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
    
    def _show_tkinter_dialog(self, dialog_type: DialogType, title: str, message: str) -> DialogResult:
        """
        Show a Tkinter dialog as fallback.
        
        Args:
            dialog_type (DialogType): Type of dialog to show.
            title (str): Dialog title.
            message (str): Dialog message.
            
        Returns:
            DialogResult: User's response.
        """
        try:
            import tkinter as tk
            from tkinter import messagebox
            
            # Hide the root window
            root = tk.Tk()
            root.withdraw()
            
            if dialog_type == DialogType.QUESTION:
                result = messagebox.askyesno(title, message)
                root.destroy()
                return DialogResult.YES if result else DialogResult.NO
            elif dialog_type == DialogType.ERROR:
                messagebox.showerror(title, message)
                root.destroy()
                return DialogResult.OK
            else:  # INFO
                messagebox.showinfo(title, message)
                root.destroy()
                return DialogResult.OK
                
        except Exception as e:
            # Last resort: print to console
            print(f"Dialog Error: {title}")
            print(f"Message: {message}")
            print(f"Error: {e}")
            return DialogResult.OK


# Global instance for easy access
dialogs = NativeDialogs() 