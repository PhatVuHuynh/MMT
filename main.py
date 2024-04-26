import random
import tkinter as tk
from tkinter import ttk
import threading
import socket
import queue
from tkinter import messagebox
from peer import *
from tracker import *

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
    ipv4addr = get_local_ipv4()
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
    UI = tk.Frame(tabs)   # second page
    tabs.add(console, text='Console')
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
        
    backend_thread.start()
    root.mainloop()
