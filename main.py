import tkinter as tk
from tkinter import ttk
import threading
from tkinter import messagebox
from peer import *
from tracker import *

def validate_login():
    # Dummy validation for demonstration
    url = url_entry.get()
    port = port_entry.get()
    global peer
    if peer.connect_tracker(url=url, port=port) == True:
        show_main()
    else:
        messagebox.showerror("Connect Field", "Cannot connect to the Tracker")

def show_main():
    # Populate the list with some names
    names = ["Alice", "Bob", "Charlie", "David"]
    for name in names:
        names_list.insert(tk.END, name)

    # Switch to main window
    login_frame.place_forget()
    main_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
    root.title("Main Window")
    root.geometry("800x400")

def console_execute_command(event=None):
    pass

def show_login():
    # Switch back to login window
    main_frame.place_forget()
    login_frame.place(relx=0.5, rely=0.5, anchor='center')
    root.title("Login")


if __name__ == "__main__":
    peer = Peer()
    
    root = tk.Tk()
    root.title("Connect to Tracker")
    root.resizable(False, False)
    
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
    login_button = tk.Button(login_frame, text="Login", command=validate_login)
    login_button.grid(row=2, columnspan=2, padx=10, pady=10)



    # Main window frame (hidden by default)
    main_frame = tk.Frame(root)
    tabs = ttk.Notebook(main_frame)
    tabs.place(relx=0, rely=0, relwidth=1, relheight=1)
    console = Frame(tabs)   # first page, which would get widgets gridded into it
    UI = Frame(tabs)   # second page
    tabs.add(Console, text='Console')
    tabs.add(UI, text='UI')
    
    
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
        
    root.mainloop()
