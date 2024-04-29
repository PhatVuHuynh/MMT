# from makeTorrent import makeTorrent
import tqdm
import os, threading, platform
import socket


IP = "localhost" # 
PORT = 4456
ADDR = (IP, PORT)
SIZE = 1024
FORMAT = "utf-8"
SERVER_DATA_PATH = "server_data" #need define

client_list = []
client_ips = []
peer_has_file = []
file_list = {}

def handle_client(conn, addr):
    print(f"[NEW CONNECTION] {addr} connected.")
    conn.send("OK@Welcome to the File Server.\nPress 'HELP' to show all command.".encode(FORMAT))

    while True:
        print(f"newloop------{addr}")
        data = conn.recv(SIZE).decode(FORMAT)
        print(data)
        data = data.split("@")
        print(data)
        cmd = data[0]
        # print(len(data))
        # if(len(data) == 2) :
        #     otherPeer = data[1].split(",")
            # print(otherPeer)

        if cmd == "LIST":
            send_data = "OK@"
            if len(file_list) == 0:
                send_data += "There is no file for you to access."
            else:
                send_data += str(file_list)
            # files = os.listdir(SERVER_DATA_PATH)
            # send_data = "OK@"

            # if len(files) == 0:
            #     send_data += "The server directory is empty"
            # else:
            #     send_data += "\n".join(f for f in files)
            conn.send(send_data.encode(FORMAT))
        elif cmd == "YES":
            peer_has_file.append(conn)
        elif cmd == "PEERS":
            send_data = "OK@"
            send_data += str(client_ips)
            conn.send(send_data.encode(FORMAT))
        elif cmd == "REQ":
            
            
            #     # print("sock------")
            # conn.send(f"FIND@{data[1]}".encode(FORMAT))
            #     # print("sock------")
            # sock = conn.recv(SIZE).decode(FORMAT)
            # print(sock)
            #     # print("sock------")
            # if(sock == "YES"):
            #     peer_has_file.append(conn)
            print(len(client_list))
            for client in client_list:
                print(client)
                # print("sock------")
                client.send(f"FIND@{data[1]}".encode(FORMAT))
                # print("sock------")
                sock = client.recv(SIZE).decode(FORMAT)
                print(sock)
                # print("sock------")
                if(sock == "YES"):
                    peer_has_file.append(client)

            print(peer_has_file)
            print(client_list)

            # if(conn == client_list[client_ips.index(data[1])]):
            #     print("adu")
            # print(client_ips[client_list.index(conn)])
            # client_list[client_ips.index(data[1])].send(f"GIVE@{client_ips[client_list.index(conn)]}".encode(FORMAT))
            conn.send(f"GIVE@{client_ips[client_list.index(peer_has_file[0])]}".encode(FORMAT))
            # conn.send(f"GIVE@{client_ips[0]}".encode(FORMAT))
            
        elif cmd == "UPLOAD":
            filename = data[1]
            temp_list = []
            
            try:
                temp_list = file_list[filename]
            except:
                file_list[filename] = []

            id = -1
            try:
                # print(file_list[client_ips[sender_server_id]])
                id = temp_list.index(client_ips[client_list.index(conn)])
            except:
                # print(file_list[client_ips[sender_server_id]])
                id = -1

            if(id < 0):
                temp_list.append(client_ips[client_list.index(conn)])
                file_list[filename] = temp_list
                conn.send("OK@Server has received your file.".encode())
            else :
                conn.send("OK@You have shared your file.".encode())
                
                

            # temp_list = file_list[client_ips[client_list.index(conn)]]
            # temp_list.append(filename)

            # file_list[client_ips[client_list.index(conn)]] = temp_list

            

            print(file_list)
            # name, size = data[1], data[2]
            # filepath = os.path.join(SERVER_DATA_PATH, name)

            # conn.send("Start uploading..".encode(FORMAT))
            
            # file_byte = b""

            # done = False

            # progress = tqdm.tqdm(unit = "B", unit_scale = True, unit_divisor = 1000,
            #                      total = int(size))

            # while not done:
            #     # print("Down..")
            #     data = conn.recv(SIZE)
            #     # print(data)
            #     if data == b"<END>":
            #         done = True
            #     else:
            #         file_byte += data
            #         conn.send("OK".encode(FORMAT))
            #     # print("end if")
            #     progress.update(SIZE)
            #     # print("end 1 loop")
            
            # with open(filepath, "wb") as f:
            #     f.write(file_byte)

            # send_data = "OK@File uploaded successfully."
            # conn.send(send_data.encode(FORMAT))

        elif cmd == "DOWNLOAD":
            rec_data = data[1]
            print(rec_data)
            rec_data = rec_data.split(":")
            print(rec_data)
            filename = rec_data[0]

            send_data = ""
            if len(file_list[filename]) == 0:
                send_data += "There is no peer for you to access."
            else:
                send_data += str(file_list[filename])
            
            print(send_data)
            conn.send(send_data.encode(FORMAT))
            print(send_data)

            peername = rec_data[1]
            peername = peername.split(",")

            peerIp = peername[0]
            peerPort = peername[1]

            sender_server_id = client_ips.index(f"'{peerIp}',{peerPort}")
            sender = client_list[sender_server_id]

            sock = -1
            try:
                sock = file_list[filename].index(client_ips[sender_server_id])
                # print(file_list[client_ips[sender_server_id]])
                # sock = file_list[client_ips[sender_server_id]].index(filename)
            except:
                
                sock = -1
            
            if(sock < 0):
                conn.send(f"OK@There is no '{filename}' in {peername}".encode(FORMAT))
            else :
                conn.send(f"GIVE@{client_ips[client_list.index(sender)]}@{filename}".encode(FORMAT))
                # conn.send(f"OK@There is '{filename}' in {peername}".encode(FORMAT))

            # peername = peername.split(",")

            # peerIp = peername[0]
            # peerport = int(peername[1])

            # print(len(client_list))
            # for client in client_list:
                # print(client)
                # print("sock------")

            # sender_server_id = client_ips.index(f"'{peerIp}',{peerPort}")
            # sender = client_list[sender_server_id]

            # sock = -1
            # try:
            #     print(file_list[client_ips[sender_server_id]])
            #     sock = file_list[client_ips[sender_server_id]].index(filename)
            # except:
                
            #     sock = -1
            
            # if(sock < 0):
            #     conn.send(f"OK@There is no '{filename}' in {peername}".encode(FORMAT))
            # else :
            #     conn.send(f"GIVE@{client_ips[client_list.index(sender)]}@{filename}".encode(FORMAT))
                # conn.send(f"OK@There is '{filename}' in {peername}".encode(FORMAT))
                

            # print(peer_has_file)
            # print(client_list)

            # if(conn == client_list[client_ips.index(data[1])]):
            #     print("adu")
            # print(client_ips[client_list.index(conn)])
            # client_list[client_ips.index(data[1])].send(f"GIVE@{client_ips[client_list.index(conn)]}".encode(FORMAT))
            

            # filename = data[1]

            # filepath = os.path.join(SERVER_DATA_PATH, filename)

            # with open(f"{filepath}", "rb") as f:
            #     text = f.read()
            
            # size = os.path.getsize(filepath)

            # send_data = f"Start downloading..@{size}"
            # conn.send(send_data.encode(FORMAT))

            # conn.recv(SIZE)
            
            # if(text):
            #     conn.sendall(text)
            #     # conn.recv(SIZE).decode(FORMAT)
            # conn.send(b"<END>")

            # # print("end")

            # conn.recv(SIZE)

            # f.close()

            # send_data = "OK@File downloaded successfully."
            # conn.send(send_data.encode(FORMAT))

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
            data += "LIST: List all peers and its file.\n"
            data += "PEERS: List all peers.\n"
            data += "REQ <file>: Find <file> and download it from 1 peer has it \n"
            data += "UPLOAD <filename>: Upload file to the server know you have it.\n"
            # data += "DOWNLOAD <path>: Download a file from  the server.\n"
            data += "DOWNLOAD <file> <peername>: Download <file> from <peername>.\n"
            # data += "DELETE <filename>: Delete a file from the server.\n"
            data += "LOGOUT: Disconnect from the server.\n"
            data += "HELP: List all the commands."

            conn.send(data.encode(FORMAT))
        else:
            conn.send("OK@metvl".encode())

    print(f"[DISCONNECTED] {addr} disconnected")
    client_list.remove(conn)
    conn.close()

# mylist = []

# def new_connection(conn, addr):
#     while True:
#         data = conn.recv(1024).decode()
#         print("Receive from client: " + str(data))
#         match data:
#             case "ADD LIST":
#                 conn.send("OK".encode())
#                 port = int(conn.recv(1024).decode())
#                 if ([addr[0]] + [port]) not in mylist:
#                     mylist.append([addr[0]]+[port])
#             case "GET LIST":
#                 conn.send(str(mylist).encode())
#             case "bye":
#                 print(f"[DISCONNECTED] {addr} disconnected")
#                 conn.send("Received".encode())
#                 client_list.remove(conn)
#                 conn.close()
#                 # print("????")
#                 return
#             case _:
#                 conn.send("Received".encode())
                
#         print(mylist)

def main():
    print("[STARTING] Server is starting")
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(ADDR)
    server.listen()
    print(f"[LISTENING] Server is listening on {IP}:{PORT}.")

    while True:
        conn, addr = server.accept()
        print(addr)

        peerSocket = conn.recv(1024).decode(FORMAT)
        peerSocket = peerSocket.replace("(", "")
        peerSocket = peerSocket.replace(")", "")

        # file_list[peerSocket] = []
        # for f in file_list:
        #     conn.send(f.key)    
        conn.send(str(file_list.keys()).encode())

        client_ips.append(peerSocket)
        client_list.append(conn)

        print(client_list)
        print(client_ips)
        # print(conn)
        # print(addr)
        print(f"[ACTIVE CONNECTIONS] {len(client_list)}")

        try:
            # thread = threading.Thread(target=handle_client, args=(conn, addr))
            thread = threading.Thread(target=handle_client, args=(conn, addr))
            thread.start()
        except:
            print("error")
            break

if __name__ == "__main__":
    main()
    print("haha")