import socket, threading
import os
import tqdm

IP = "localhost"
PORT = 4456
ADDR = (IP, PORT)
FORMAT = "utf-8"
SIZE = 1024
PEER_PATH = "client_data"

def write():
    pass

def receive(client):
    while True:
        data = client.recv(SIZE).decode(FORMAT)
        cmd, msg = data.split("@")

        if cmd == "DISCONNECTED":
            print(f"[SERVER]: {msg}")
            break
        elif cmd == "OK":
            print(f"{msg}")

        data = input("> ")
        data = data.split(" ")
        cmd = data[0]

        if cmd == "HELP":
            client.send(cmd.encode(FORMAT))
        elif cmd == "LOGOUT":
            client.send(cmd.encode(FORMAT))
            break
        elif cmd == "LIST":
            client.send(cmd.encode(FORMAT))
        elif cmd == "DELETE":
            client.send(f"{cmd}@{data[1]}".encode(FORMAT))
        elif cmd == "UPLOAD":
            filename = data[1]

            filepath = os.path.join(PEER_PATH, filename)

            with open(f"{filepath}", "r") as f:
                text = f.read()

            # filename = filepath.split("/")[-1]
            filesize = os.path.getsize(filepath)

            send_data = f"{cmd}@{filename}@{filesize}"
            client.send(send_data.encode(FORMAT))

            start = client.recv(SIZE).decode(FORMAT)
            # print(start)
            if start == "Start uploading..":
                if(text) :
                    client.sendall(text)
                client.send("<END>".encode(FORMAT))
            
        elif cmd == "DOWNLOAD":
            path = data[1]

            filename = path.split("/")[-1]

            filepath = os.path.join(PEER_PATH, filename)

            send_data = f"{cmd}@{path}"
            client.send(send_data.encode(FORMAT))

            start = client.recv(SIZE).decode(FORMAT)
            mes, size = start.split('@')
            client.send(mes.encode(FORMAT))
            print(mes)
            if mes == "Start downloading..":
                file_byte = b""

                done = False

                progress = tqdm.tqdm(unit = "B", unit_scale = True, unit_divisor = 1000,
                                    total = int(size))

                while not done:
                    data = client.recv(SIZE)
                    # print(data)
                    if data == b"<END>":
                        done = True
                    else:
                        file_byte += data

                    progress.update(SIZE)

                with open(filepath, "wb") as f:
                    f.write(file_byte)

                client.send("Finished Downloading.".encode(FORMAT))  

    print("Disconnected from the server.")
    client.close()

def main():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(ADDR)

    thr1 = threading.Thread(target=receive, args=(client, ))
    thr1.start()
    thr2 = threading.Thread(target=write, args=(client, ))
    thr2.start()

if __name__ == "__main__":
    main()