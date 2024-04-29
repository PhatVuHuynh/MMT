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

#TODO: SEPERATE LOGIN WINDOW AND MAIN
def timer_trigger():
    root.after(10, timer_trigger)
    timer_event()

def timer_event():
    pass
    #put function here to force it run each 10 ms

def upload_folder(): #TODO
    folder_path = filedialog.askdirectory()
    print (f"upload {folder_path}")
    if folder_path:
        tk_to_peer_q.put("UPLOAD")
        tk_to_peer_q.put(f"upload {folder_path}")
        root.after(100, update_list)
def upload_file(): #TODO
    folder_path = filedialog.askopenfilename()
    # print(folder_path)
    if folder_path:
        tk_to_peer_q.put("UPLOAD")
        tk_to_peer_q.put(f"upload {folder_path}")
        root.after(100, update_list)

def update_list():
    tk_to_peer_q.put("GET LIST")
    file_list = peer_to_tk_q.get()
    for item in tree.get_children():
        tree.delete(item)
    # Create a dictionary to hold the tree structure
    tree_structure = {}
    print(file_list)
    for item in file_list:
        parts = item.split('\\')
        node = tree_structure
        
        for part in parts:
            node = node.setdefault(part, {})

    # Function to populate the tree view
    def populate_tree(tree, parent, dictionary):
        for key, value in dictionary.items():
            child = tree.insert(parent, 'end', text=key)
            if value:
                populate_tree(tree, child, value)
    # Populate the Treeview with data
    populate_tree(tree, '', tree_structure)
    
def download_file(path:str):
    tk_to_peer_q.put("DOWNLOAD")
    command = "download " + path
    tk_to_peer_q.put(command)


def get_local_ipv4():
    try:
        # Create a socket to get the local IP address
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))  # Connect to a public DNS server
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception as e:
        print(f"Error getting local IP: {e}")
        return None

def validate_login(event = None):
    # Dummy validation for demonstration
    global url_entry
    global port_entry
    
    url = url_entry.get()
    try:
        port = int(port_entry.get())
    except ValueError:
        messagebox.showerror("Invalid port number", "The port number must be an integer")
        return
    
    tk_to_peer_q.put("CONNECT")
    tk_to_peer_q.put((url, port,))
    connect_result = peer_to_tk_q.get()
    if connect_result == True:
        show_main()
    else:
        messagebox.showerror("Connect Field", "Cannot connect to the Tracker")



def console_execute_command(event=None):
    global console_entry
    command = console_entry.get().strip()
    if command != "":
        text_area_insert (message=command, from_user=True)
        tk_to_peer_q.put("CONSOLE")
        tk_to_peer_q.put(command)
        output = peer_to_tk_q.get()
        print ("ABC")
        text_area_insert(message=output, from_user=False)

        
def text_area_insert(message:str, from_user = False):
    global console_entry
    global console_text_area
    if message != "":
        console_text_area.config(state='normal')  # Enable text area temporarily
        if from_user:
            console_text_area.insert(tk.END, f"> {message}\n")
            console_entry.delete(0, tk.END)
        else:
            console_text_area.insert(tk.END, f"{message}\n")
        console_text_area.config(state='disabled')  # Disable text area again
        console_text_area.see(tk.END)

import tkinter as tk
from tkinter import ttk, Menu

def on_right_click(event):
    # Identify the clicked item
    item_id = tree.identify_row(event.y)
    if item_id:
        # Get the item's text
        item_text = tree.item(item_id, 'text')
        # Initialize the path with the item's text
        path = item_text
        # Walk up the tree to build the full path
        parent_id = tree.parent(item_id)
        while parent_id:
            parent_text = tree.item(parent_id, 'text')
            path = parent_text + '\\' + path
            parent_id = tree.parent(parent_id)
        
        path = path.replace('\\', '/')
        # Show the full path or do something with it
        print(path)  # Or copy to clipboard, etc.

        # Create a context menu
        menu = Menu(tree, tearoff=0)
        menu.add_command(label="Download", command=lambda: download_file(path))
        # Add more menu items if needed

        # Show the context menu at the mouse position
        menu.post(event.x_root, event.y_root)



def show_main():
    # Switch to main window
    login_frame.place_forget()
    
    main_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
    root.title("Main Window")
    root.geometry("800x400")
    
def show_login():
    # Switch back to login window
    main_frame.place_forget()
    login_frame.place(relx=0.5, rely=0.5, anchor='center')
    root.title("Login")


if __name__ == "__main__":
    ipv4addr = socket.gethostbyname(socket.gethostname())
    port_number = random.randint(49152, 65535)
    peer = Peer(my_ip=ipv4addr, my_port=port_number)
    
    tk_to_peer_q = queue.Queue()
    peer_to_tk_q = queue.Queue()
    backend_thread = threading.Thread(target=peer.run, args=(tk_to_peer_q,peer_to_tk_q,  ) )
    
    root = tk.Tk()
    root.title("Connect to Tracker")
    root.resizable(False, False)
    root.protocol("WM_DELETE_WINDOW", lambda: [tk_to_peer_q.put(None), root.destroy()])

    
    root.geometry("400x200")
    login_frame = tk.Frame(root)
    login_frame.place(relx=0.5, rely=0.5, anchor='center')
    
    url_label = tk.Label(login_frame, text="Tracker URL:")
    url_label.grid(row=0, column=0, padx=10, pady=5, sticky="e")
    url_entry = tk.Entry(login_frame)
    url_entry.grid(row=0, column=1, padx=10, pady=5)

    # Port label and entry
    port_label = tk.Label(login_frame, text="Tracker Port:")
    port_label.grid(row=1, column=0, padx=10, pady=5, sticky="e")
    port_entry = tk.Entry(login_frame)
    port_entry.grid(row=1, column=1, padx=10, pady=5)

    # Login button
    login_button = tk.Button(login_frame, text="Connect", command=validate_login)
    login_button.grid(row=2, columnspan=2, padx=10, pady=10)
    url_entry.bind("<Return>", validate_login)
    port_entry.bind("<Return>", validate_login)
    



    # Main window frame (hidden by default)
    main_frame = tk.Frame(root)
    tabs = ttk.Notebook(main_frame)
    tabs.place(relx=0, rely=0, relwidth=1, relheight=1)
    console = tk.Frame(tabs)   # first page, which would get widgets gridded into it
    treeview = tk.Frame(tabs)   # second page
    tabs.add(console, text='Console')
    tabs.add(treeview, text='UI')
    
    
    #The console tab
    console_text_area = tk.Text(console, height=20, wrap=tk.WORD, state='disabled')
    console_text_area.grid(row=0, column=0, columnspan=2, sticky='nsew', padx=10, pady=10)

    # Create a vertical scroll bar
    console_scrollbar = tk.Scrollbar(console, command=console_text_area.yview)
    console_scrollbar.grid(row=0, column=2, sticky='ns')

    # Configure the grid row and column weights
    console.grid_rowconfigure(0, weight=1)
    console.grid_columnconfigure(0, weight=1)
    console.grid_columnconfigure(1, weight=0)  # Adjust the weight for the send button column

    # Attach the scroll bar to the text area
    console_text_area.config(yscrollcommand=console_scrollbar.set)

    # Create an entry widget for typing commands
    console_entry = tk.Entry(console)
    console_entry.grid(row=1, column=0, sticky='ew', padx=10)
    console_entry.bind("<Return>", console_execute_command)  # Bind the Enter key to execute the command

    # Create a send button
    console_send_button = tk.Button(console, text="Send", command=console_execute_command)
    console_send_button.grid(row=1, column=1, sticky='ew', padx=(0, 10))
        
        
    #config the tabs
    tree = ttk.Treeview(treeview)
    # tree['columns'] = ('Size', 'Type', 'Status')  # Add a new column for status
    tree['columns'] = ('Hash', 'Status', 'Type','Path')
    tree.column('#0', width=150, minwidth=150, stretch=tk.NO)
    tree.column('Hash', width=200, minwidth=200, stretch=tk.NO)
    tree.column('Status', width=120, minwidth=120, stretch=tk.NO)  # Adjust the width as needed
    tree.column('Type', width=100, minwidth=100, stretch=tk.NO)
    tree.column('Path', width=270, minwidth=270, stretch=tk.NO)
    
    tree.heading('#0', text='Name', anchor=tk.W)
    tree.heading('Hash', text='Hash', anchor=tk.W)
    tree.heading('Status', text='Status', anchor=tk.W)  # Add a heading for the new column
    tree.heading('Type', text='Type', anchor=tk.W)
    tree.heading('Path', text='Path', anchor=tk.W)
    # folder1 = tree.insert('', 'end', text='Folder 1', values=('10 KB', 'Folder', 'Downloading'))
    # sub_item1 = tree.insert(folder1, 'end', text='File 1', values=('2 KB', 'Text File', 'Completed'))
    # sub_item2 = tree.insert(folder1, 'end', text='File 2', values=('3 KB', 'Image File', 'In Progress'))

    # folder2 = tree.insert('', 'end', text='Folder 2', values=('20 KB', 'Folder', 'Paused'))
    # sub_item3 = tree.insert(folder2, 'end', text='File 3', values=('5 KB', 'PDF File', 'Queued'))

    # Bind right-click to on_right_click function
    tree.bind("<Button-3>", on_right_click)

    tree.pack(fill="both", expand=True)
    
    
    #add menubar
    # Create a 'File' menu
    menu_bar = tk.Menu(main_frame)

    file_menu = tk.Menu(menu_bar, tearoff=0)
    file_menu.add_command(label="Upload file", command=upload_file)
    file_menu.add_command(label="Upload folder", command=upload_folder)
    file_menu.add_command(label="Update list", command=update_list)
    # file_menu.add_separator()
    menu_bar.add_cascade(label="File", menu=file_menu)

    # Create an 'Options' menu
    options_menu = tk.Menu(menu_bar, tearoff=0)
    options_menu.add_command(label="Settings")
    menu_bar.add_cascade(label="Options", menu=options_menu)

    # Create a 'Help' menu
    help_menu = tk.Menu(menu_bar, tearoff=0)
    help_menu.add_command(label="About")
    menu_bar.add_cascade(label="Help", menu=help_menu)

    # Place the menu bar at the top of the window
    root.config(menu=menu_bar)
    
    #create timer
    root.after(10, timer_trigger)
    
    backend_thread.start()
    root.mainloop()
