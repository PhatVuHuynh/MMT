import random
import tkinter as tk
from tkinter import ttk
import threading
import socket
import queue
from tkinter import messagebox
from peer import *
from tracker import *
from tkinter import filedialog
from folder import *


def update_list(event=None):
    def update_treeview(tree, folder, parent=''):
        if isinstance(folder, Folder):
        # Add the folder to the Treeview
            folder_id = tree.insert(parent, 'end', text=folder.name, values=('',folder.size, folder.status, 'Folder', folder.path))
            folder.treeview_id = folder_id
            # Add all files in the folder to the Treeview
            for file in folder.files:
                file_id = tree.insert(folder_id, 'end', text=file.name, values=(file.file_hash, file.size, file.status, 'File', file.path))
                file.treeview_id = file_id
            # Recursively add subfolders and their files
            for subfolder in folder.child_folders:
                update_treeview(tree, subfolder, folder_id)
                
        elif isinstance(folder, File):
            folder_id = tree.insert(parent, 'end', text=folder.name, values=(folder.file_hash, folder.size, folder.status, 'File', folder.path))
            folder.treeview_id = folder_id
    global tree
    # folder_list = peer_to_tk_q.get(block=False)
    global folder_list
    folder_list =[
            File(r"C:\Users\tuankiet\Desktop\MMT\folder.py",status=''),
            Folder(r"C:\Users\tuankiet\Desktop\MMT\download",status='Downloaded'),
            File(r"C:\Users\tuankiet\Desktop\MMT\README.md", status=''),
            Folder(r"C:\Users\tuankiet\Desktop\MMT\peer_data", status=''),
            Folder(r"C:\Users\tuankiet\Desktop\MMT\share",status='') 
        ]
    for folder in folder_list:
        update_treeview(tree, folder)

            
def on_right_click(event):
    # Identify the Treeview item that was clicked
    item_id = tree.identify_row(event.y)
    if item_id:
        # Get the item type (File or Folder) and Status
        item_values = tree.item(item_id, 'values')
        item_status = item_values[2]
        
        # Create a context menu
        context_menu = tk.Menu(tree, tearoff=0)
        
        # Add "Download" command to the context menu
        context_menu.add_command(label="Download", command=lambda: download_files())
        
        # Disable the "Download" option if the item status is "Downloaded"
        if item_status == 'Downloaded' or item_status == 'Downloading':
            context_menu.entryconfig("Download", state=tk.DISABLED)
        
        # Show the context menu at the mouse position
        context_menu.post(event.x_root, event.y_root)


def download_files():
    # Get all selected items
    selected_items = tree.selection()
    for item_id in selected_items:
        file_name = tree.item(item_id, 'text')
        file_hash = tree.item(item_id, 'values')[0]
        file_type = tree.item(item_id, 'values')[3]
        path_parts = []
        current_item = item_id
        # Implement the download logic here
        while True:
            parent_id = tree.parent(current_item)
            if not current_item:  # If there's no parent, we've reached the top
                break
            # Prepend the name of the current item to the path parts
            path_parts.insert(0, tree.item(current_item, 'text'))
            current_item = parent_id
        # Join the parts with underscores to get the desired format
        relative_path = '/'.join(path_parts)
        file_hash = tree.item(item_id, 'values')[0]
        # Print the tuple with hash and relative path
        print (relative_path)
        if file_type == "File":
            pass
            
        elif file_type == "Folder":
            pass



root = tk.Tk()

tree = ttk.Treeview(root, selectmode='extended')
# tree['columns'] = ('Size', 'Type', 'Status')  # Add a new column for status
tree['columns'] = ('Hash', 'Size', 'Status', 'Type','Path')
tree.column('#0', width=150, minwidth=150, stretch=tk.NO)
tree.column('Hash', width=200, minwidth=200, stretch=tk.NO)
tree.column('Size', width=70, minwidth=70, stretch=tk.NO)
tree.column('Status', width=120, minwidth=120, stretch=tk.NO)  # Adjust the width as needed
tree.column('Type', width=100, minwidth=100, stretch=tk.NO)
tree.column('Path', width=270, minwidth=270, stretch=tk.NO)

tree.heading('#0', text='Name', anchor=tk.W)
tree.heading('Hash', text='Hash', anchor=tk.W)
tree.heading('Size', text='Size (Bytes)', anchor=tk.W)
tree.heading('Status', text='Status', anchor=tk.W)  # Add a heading for the new column
tree.heading('Type', text='Type', anchor=tk.W)
tree.heading('Path', text='Path', anchor=tk.W)
# folder1 = tree.insert('', 'end', text='Folder 1', values=('10 KB', 'Folder', 'Downloading'))
# sub_item1 = tree.insert(folder1, 'end', text='File 1', values=('2 KB', 'Text File', 'Completed'))
# sub_item2 = tree.insert(folder1, 'end', text='File 2', values=('3 KB', 'Image File', 'In Progress'))

# folder2 = tree.insert('', 'end', text='Folder 2', values=('20 KB', 'Folder', 'Paused'))
# sub_item3 = tree.insert(folder2, 'end', text='File 3', values=('5 KB', 'PDF File', 'Queued'))

# Bind right-click to on_right_click function


tree.pack(fill="both", expand=True)

update_list()

tree.bind("<Button-3>", on_right_click)

root.mainloop()