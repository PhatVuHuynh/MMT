import platform
import tqdm
import os
import socket
import threading

IP = "localhost" # 
PORT = 4456
ADDR = (IP, PORT)
SIZE = 1024
FORMAT = "utf-8"
SERVER_DATA_PATH = "server_data" #need define

client_list = []

def handle_client(conn, addr):
    print(f"[NEW CONNECTION] {addr} connected.")
    conn.send("OK@Welcome to the File Server.\nPress 'HELP' to show all command.".encode(FORMAT))

    while True:
        data = conn.recv(SIZE).decode(FORMAT)
        data = data.split("@")
        cmd = data[0]

        if cmd == "LIST":
            files = os.listdir(SERVER_DATA_PATH)
            send_data = "OK@"

            if len(files) == 0:
                send_data += "The server directory is empty"
            else:
                send_data += "\n".join(f for f in files)
            conn.send(send_data.encode(FORMAT))

        elif cmd == "UPLOAD":
            name, size = data[1], data[2]
            filepath = os.path.join(SERVER_DATA_PATH, name)

            conn.send("Start uploading..".encode(FORMAT))
            
            file_byte = b""

            done = False

            progress = tqdm.tqdm(unit = "B", unit_scale = True, unit_divisor = 1000,
                                 total = int(size))

            while not done:
                data = conn.recv(SIZE)
                
                if data == b"<END>":
                    done = True
                else:
                    file_byte += data

                progress.update(SIZE)
            
            with open(filepath, "wb") as f:
                f.write(file_byte)

            send_data = "OK@File uploaded successfully."
            conn.send(send_data.encode(FORMAT))

        elif cmd == "DOWNLOAD":
            filename = data[1]

            filepath = os.path.join(SERVER_DATA_PATH, filename)

            with open(f"{filepath}", "rb") as f:
                text = f.read()
            
            size = os.path.getsize(filepath)

            send_data = f"Start downloading..@{size}"
            conn.send(send_data.encode(FORMAT))

            conn.recv(SIZE)
            
            conn.sendall(text)
            conn.send("<END>".encode(FORMAT))

            conn.recv(SIZE)

            send_data = "OK@File downloaded successfully."
            conn.send(send_data.encode(FORMAT))

        elif cmd == "DELETE":
            files = os.listdir(SERVER_DATA_PATH)
            send_data = "OK@"
            filename = data[1]

            if len(files) == 0:
                send_data += "The server directory is empty"
            else:
                if filename in files:
                    if(platform.system() == "Linux"):
                        filepath = f"rm ./"
                    else:
                        filepath = f"del .\\"

                    filepath += os.path.join(SERVER_DATA_PATH, filename)

                    print(filepath)
                    os.system(filepath)
                    send_data += "File deleted successfully."
                else:
                    send_data += "File not found."

            conn.send(send_data.encode(FORMAT))

        elif cmd == "LOGOUT":
            break
        elif cmd == "HELP":
            data = "OK@"
            data += "LIST: List all the files from the server.\n"
            data += "UPLOAD <path>: Upload a file to the server.\n"
            data += "DOWNLOAD <path>: Download a file from  the server.\n"
            data += "DELETE <filename>: Delete a file from the server.\n"
            data += "LOGOUT: Disconnect from the server.\n"
            data += "HELP: List all the commands."

            conn.send(data.encode(FORMAT))

    print(f"[DISCONNECTED] {addr} disconnected")
    client_list.remove(conn)
    conn.close()

def main():
    print("[STARTING] Server is starting")
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(ADDR)
    server.listen()
    print(f"[LISTENING] Server is listening on {IP}:{PORT}.")

    while True:
        conn, addr = server.accept()
        client_list.append(conn)

        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()
        print(f"[ACTIVE CONNECTIONS] {client_list.count()}")

if __name__ == "__main__":
    main()