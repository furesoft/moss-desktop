import threading
import tkinter as tk
from typing import TYPE_CHECKING
from tkinter import filedialog

from gui.defaults import Defaults

if TYPE_CHECKING:
    from rm_api.models import Document

def make_tk():
    root = tk.Tk()
    root.withdraw()
    root.iconbitmap(Defaults.ICO_APP_ICON)
    return root

def open_file(title: str, types_text: str, *filetypes):
    def decorator(func):
        def wrapper(*args, **kwargs):
            def prompt_file():
                root = make_tk()
                filetypes_with_default =  [(types_text, filetypes)]
                file_name = filedialog.askopenfilename(
                    parent=root,
                    title=title,
                    filetypes=filetypes_with_default
                )
                root.destroy()
                return func(file_name, *args, **kwargs) if file_name else None
            threading.Thread(target=prompt_file).start()
        return wrapper
    return decorator

def save_file(title: str, *filetypes):
    def decorator(func):
        def wrapper(document: 'Document', *args, **kwargs):
            def prompt_file():
                root = make_tk()
                filetypes_with_default = [(f'{ext} files', f'*.{ext}') for ext in filetypes]
                file_name = filedialog.asksaveasfilename(
                    parent=root,
                    title=title,
                    defaultextension=filetypes[0],
                    initialfile=document.metadata.visible_name,
                    filetypes=filetypes_with_default
                )
                root.destroy()
                return func(file_name, document, *args, **kwargs) if file_name else None
            threading.Thread(target=prompt_file).start()
        return wrapper
    return decorator

@open_file("Import file", "Moss import types", *Defaults.IMPORT_TYPES)
def import_prompt(file_path, callback):
    callback(file_path)

@save_file("PDF export", 'pdf')
def export_prompt(file_path, document: 'Document', callback):
    # TODO: formats need work
    callback(file_path)