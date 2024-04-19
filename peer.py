import tqdm
import os, threading, platform
import socket

IP = "localhost"
PORT = 4456
ADDR = (IP, PORT)

PEER_SERVER_IP = 'localhost'
PEER_SERVER_PORT = 5111

FORMAT = "utf-8"
SIZE = 1024
PEER_PATH = "client_data"
PEER1_PATH = "peer_data"
SERVER_DATA_PATH = "server_data" #need define

client_list = []

def separate_string(data):
    data = data.replace("[", "")
    data = data.replace("]", "")
    data = data.replace("\'", "")
    data = data.replace(" ", "")
    splitData = data.split(",")
    for i in range(1, len(splitData), 2):
        splitData[i] = int(splitData[i])
    return splitData

def handlePconnect(conn, addr):
    print(f"Sender: {addr}")
    data = conn.recv(1024).decode()
    print(data)
    conn.send("Chuan bi nhan ne".encode())

    # filename = "2114391.png"
    filename = conn.recv(1024).decode()

    filepath = os.path.join(SERVER_DATA_PATH, filename)

    with open(f"{filepath}", "rb") as f:
        text = f.read()
    
    size = os.path.getsize(filepath)

    send_data = f"Start downloading..@{size}"
    conn.send(send_data.encode(FORMAT))

    conn.recv(SIZE)
    
    if(text):
        conn.sendall(text)
        # conn.recv(SIZE).decode(FORMAT)
    conn.send(b"<END>")

    # print("end")

    conn.recv(SIZE)

    f.close()

    # send_data = "OK@File downloaded successfully."
    # p_client.send(send_data.encode(FORMAT))


def peer_client(host, port, filename):
    p_client = socket.socket()
    p_client.connect((host, port))

    mes = "Ok bro"
    p_client.send(mes.encode(FORMAT))
    print(p_client.recv(1024).decode())

    print(f"Receiver: {p_client.getsockname()}")

    # filename = "2114391.png"
    p_client.send(filename.encode(FORMAT))

    filepath = os.path.join(PEER_PATH, filename)

    # send_data = f"{cmd}@{filename}"
    # client.send(send_data.encode(FORMAT))

    start = p_client.recv(SIZE).decode(FORMAT)
    mes, size = start.split('@')
    p_client.send(mes.encode(FORMAT))
    
    if mes == "Start downloading..":
        print(mes)
        file_byte = b""

        done = False

        progress = tqdm.tqdm(unit = "B", unit_scale = True, unit_divisor = 1000,
                            total = int(size))

        while not done:
            # print("Down..")
            data = p_client.recv(SIZE)
            # print(file_byte)
            
            if data[-5:] == b"<END>":
                file_byte += data[:-5]
                done = True
                p_client.send("OK".encode(FORMAT))
            else:
                # print(data)
                file_byte += data
                # client.send("OK".encode(FORMAT))
            # print("end if")
            progress.update(SIZE)
            # print("end 1 loop")

        with open(filepath, "wb") as f:
            f.write(file_byte)

        p_client.send("Finished Downloading.".encode(FORMAT))  

    
    

def peer_server(p_server):
    p_server.listen(10)

    while True:
        try:
            print("wait....")
            conn, addr = p_server.accept()
            print("connected")
            thrHandle = threading.Thread(target=handlePconnect, args=(conn, addr))
            thrHandle.start()
        except:
            print("Your connection is not successful.")
            break

def recv(client):
    while True:
        print("startloop")
        data = client.recv(SIZE).decode(FORMAT)
        cmd, msg = data.split("@")

        if cmd == "DISCONNECTED":
            print(f"[SERVER]: {msg}")
            break
        elif cmd == "OK":
            print(f"{msg}")
        elif cmd == "FIND":
            print(f"{msg}")
            filepath = os.path.join(SERVER_DATA_PATH, msg)

            if(os.path.exists(filepath)):
                client.send("YES".encode())

            # thrFind = threading.Thread(target=findF, args=(client,msg))
            # thrFind.start()

        elif cmd == "GIVE":
            print(f"{msg}")
            otherPeer = msg.split(",")

            peerName = otherPeer[0]
            peerName = peerName.replace("'", "")
            peerPort = int(otherPeer[1])
            
            print(peerName)
            print(peerPort)
            # peerName = "localhost"
            thrClient = threading.Thread(target=peer_client, args=(peerName, peerPort))
            thrClient.start()
        #     if(peerName) print((PEER_SERVER_IP, PEER_SERVER_PORT))



def sen(client):
    # thr1 = threading.Thread(target=recv, args=(client, ))
    # thr1.start()
    while True:
        print("startloop")
        data = client.recv(SIZE).decode(FORMAT)
        print(data)
        data = data.split("@")
        cmd, msg = data[0], data[1]

        if cmd == "DISCONNECTED":
            print(f"[SERVER]: {msg}")
            break
        elif cmd == "OK":
            print(f"{msg}")
        elif cmd == "FIND":
            print(f"{msg}")
            filepath = os.path.join(SERVER_DATA_PATH, msg)

            if(os.path.exists(filepath)):
                client.send("YES".encode())

            # thrFind = threading.Thread(target=findF, args=(client,msg))
            # thrFind.start()

        elif cmd == "GIVE":
            print(f"{msg}")
            otherPeer = msg.split(",")

            peerName = otherPeer[0]
            peerName = peerName.replace("'", "")
            peerPort = int(otherPeer[1])
            
            print(peerName)
            print(peerPort)
            # peerName = "localhost"
            thrClient = threading.Thread(target=peer_client, args=(peerName, peerPort, data[2]))
            thrClient.start()
        #     if(peerName) print((PEER_SERVER_IP, PEER_SERVER_PORT))

        # if(cmd != "FIND") :
        # print("bef")
        data = input("> ")
        # print(data)
        data = data.split(" ")
        # print(data)
        cmd = data[0]
        # print(cmd)
        # print("af")

        if cmd == "HELP":
            client.send(cmd.encode(FORMAT))
        elif cmd == "LOGOUT":
            client.send(cmd.encode(FORMAT))
            break
        elif cmd == "PEERS":
            client.send(cmd.encode(FORMAT))
        elif cmd == "REQ":
            client.send(f"{cmd}@{data[1]}".encode(FORMAT))
            # client.send(f"{cmd}@'{data[1]}', {data[2]}".encode(FORMAT))
            # thrClient = threading.Thread(target=peer_client, args=(data[1], int(data[2])))
            # thrClient.start()

        elif cmd == "LIST":
            client.send(cmd.encode(FORMAT))
        elif cmd == "DELETE":
            client.send(f"{cmd}@{data[1]}".encode(FORMAT))
        elif cmd == "UPLOAD":
            filename = data[1]

            # filepath = os.path.join(PEER_PATH, filename)

            # with open(f"{filepath}", "rb") as f:
            #     text = f.read()

            # filename = filepath.split("/")[-1]
            # filesize = os.path.getsize(filepath)

            # send_data = f"{cmd}@{filename}@{filesize}"
            send_data = f"{cmd}@{filename}"
            client.send(send_data.encode(FORMAT))

            # mes = client.recv(SIZE).decode(FORMAT)
            # print(mes)
            
            # if start == "Start uploading..":
            #     print(start)
            #     if(text) :
            #         client.sendall(text)
            #         print(client.recv(SIZE).decode(FORMAT))
            #     client.send("<END>".encode(FORMAT))

            #     f.close()
            
        elif cmd == "DOWNLOAD":
            filename = data[1]

            peerIp = data[2]
            peerport = data[3]

            # peername = peername.split(",")

            # peerIp = peername[0]
            # peerport = int(peername[1])
            client.send(f"{cmd}@{filename}:{peerIp} {peerport}".encode(FORMAT))

            # filename = data[1]

            # filepath = os.path.join(PEER_PATH, filename)

            # send_data = f"{cmd}@{filename}"
            # client.send(send_data.encode(FORMAT))

            # start = client.recv(SIZE).decode(FORMAT)
            # mes, size = start.split('@')
            # client.send(mes.encode(FORMAT))
            
            # if mes == "Start downloading..":
            #     print(mes)
            #     file_byte = b""

            #     done = False

            #     progress = tqdm.tqdm(unit = "B", unit_scale = True, unit_divisor = 1000,
            #                         total = int(size))

            #     while not done:
            #         # print("Down..")
            #         data = client.recv(SIZE)
            #         # print(file_byte)
                    
            #         if data[-5:] == b"<END>":
            #             file_byte += data[:-5]
            #             done = True
            #             client.send("OK".encode(FORMAT))
            #         else:
            #             # print(data)
            #             file_byte += data
            #             # client.send("OK".encode(FORMAT))
            #         # print("end if")
            #         progress.update(SIZE)
            #         # print("end 1 loop")

            #     with open(filepath, "wb") as f:
            #         f.write(file_byte)

            #     client.send("Finished Downloading.".encode(FORMAT))  
        else:
            print("pass")
            client.send("pass".encode())

        print("endloop")

    print("Disconnected from the server.")
    client.close()

def main():
    client_to_tracker = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_to_tracker.connect(ADDR)

    
        # thr2 = threading.Thread(target=handle_client, args=(client, ))
        # thr2.start()
        # thr1 = threading.Thread(target=receive, args=(client, ))
        # thr1.start()
    message = "NOPE"
    p_server = socket.socket()
    p_server.bind((PEER_SERVER_IP, PEER_SERVER_PORT))
    print(p_server.getsockname())

    client_to_tracker.send(str(p_server.getsockname()).encode(FORMAT))
    ser = threading.Thread(target = peer_server, args = (p_server,))
    ser.start()

    sen(client_to_tracker)
    
    # while message != "bye":
    #     message = input(" -> ")  # again take input
    #     try:
    #         match message:
    #             case "ADD LIST":
    #                 client_to_tracker.send(message.encode())
    #                 data = client_to_tracker.recv(1024).decode()
    #                 client_to_tracker.send(str(PEER_SERVER_PORT).encode())
    #             case "GET LIST":
    #                 client_to_tracker.send(message.encode())
    #                 data = client_to_tracker.recv(1024).decode()
    #                 myList = separate_string(data)
    #                 print(myList)
    #             case "HELLO":
    #                 for i in range(0, len(client_list), 2):
    #                     cle = threading.Thread(target= peer_client, args= (str(myList[i]), myList[i+1]))
    #                     cle.start()
    #             case _:
    #                 client_to_tracker.send(message.encode())
    #                 data = client_to_tracker.recv(1024).decode()
    #                 print(data)
    #     except:
    #         print("error")
    #         break

    
    # client_to_tracker.close()
    try:
        p_server.close()
    except:
        ser.join()
        print("Disconnected from the server.")        
    

if __name__ == "__main__":
    main()
    # print("haha")