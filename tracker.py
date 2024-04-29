import socket
import threading, os
import json
import math

TRACKER_IP = socket.gethostbyname(socket.gethostname())
TRACKER_PORT = 9999
PIECE_SIZE = 2 ** 20

class Tracker:
    def __init__(self, host=TRACKER_IP, port=TRACKER_PORT):
        self.host = host
        self.port = port
        self.peers = {}  # Dictionary to hold peer information

    def start_server(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()
        print(f"Tracker running on {self.host}:{self.port}")
        while True:
            client_socket, addr = self.server_socket.accept()
            threading.Thread(target=self.handle_client, args=(client_socket, addr)).start()

    def get_host(self):
        return self.host
    
    def get_port(self):
        return self.port
    
    def get_peers(self):
        return self.peers

    def handle_client(self, client_socket, addr):
        try:
            while True:
                # print(addr)
                try:
                    data = client_socket.recv(PIECE_SIZE)
                except:
                    # print(self.peers)
                    self.peers.pop(addr)
                    # print(self.peers)
                    return
                
                print(data)
                if not data:
                    break
                data = json.loads(data.decode())
                command = data['command']

                if command == 'register':

                    pieces = []
                    for size in data['sizes']:
                        temp = math.ceil(size/PIECE_SIZE)
                        pieces.append(temp)

                    self.peers[addr] = {
                        'folders': [],
                        'files': data['files'],
                        'ip': data['ip'],
                        'port': data['port'],
                        'sizes': data['sizes'],
                        'hashes': data['hashes'],
                        'pieces': pieces
                    }
                    # print(f"Registered {addr} with files: {data['files']}, IP: {data['ip']}, Port: {data['port']}")
                    response = (f"Registered {addr} with container: {data['files']}, IP: {data['ip']}, Port: {data['port']}")
                    client_socket.send(response.encode())

                elif command == 'request':
                    # print(data)
                    filename = data['file']
                    # print(filename[-2:])
                    if(filename[-1:] == "/"):
                        available_peers = []
                        for peer_addr, peer_info in self.peers.items():
                            for file in peer_info['files']:
                                # print(file)
                                # a="a\\sda"
                                # a.startswith()
                                # print(file.startswith(filename))
                                if file.startswith(filename) :
                                    available_peers.append(
                                    {
                                        'ip': peer_info['ip'],
                                        'port': peer_info['port'],
                                        'file': file,
                                        'hash': peer_info['hashes'][peer_info['files'].index(file)],
                                        'size': peer_info['sizes'][peer_info['files'].index(file)],
                                        'pieces': peer_info['pieces'][peer_info['files'].index(file)]
                                    })
                    else:
                        available_peers = [
                            {
                                'ip': peer_info['ip'],
                                'port': peer_info['port'],
                                'file': filename,
                                'hash': peer_info['hashes'][peer_info['files'].index(filename)],
                                'size': peer_info['sizes'][peer_info['files'].index(filename)],
                                'pieces': peer_info['pieces'][peer_info['files'].index(filename)]
                            }
                            for peer_addr, peer_info in self.peers.items() if filename in peer_info['files']
                        ]
                    print(available_peers)
                    response = json.dumps({"peers": available_peers}).encode()
                    client_socket.send(response)

                elif command == 'list':
                    available_files = []
                    for peer_addr, peer_info in self.peers.items():
                        for file in peer_info['files']:
                            try:
                                available_files.index(file)
                            except:
                                available_files.append(file)
                    print(available_files)
                    response = json.dumps(available_files).encode()
                    # print("in")
                    client_socket.send(response)

                elif command == 'upload':
                    try:
                        print(data['metainfo'])
                        for metainfo in data['metainfo']:
                            if(metainfo['is_folder']):
                                # for metainfo in data['metainfo']:
                                self.peers[addr]['folders'].append(metainfo['name'])
                                print(metainfo)
                                for file in metainfo['files']:
                                    print(1)
                                    self.peers[addr]['hashes'].append(metainfo['hashes'][metainfo['files'].index(file)])
                                    self.peers[addr]['sizes'].append(metainfo['sizes'][metainfo['files'].index(file)])
                                    print(1)
                                    self.peers[addr]['pieces'].append(metainfo['num_pieces'][metainfo['files'].index(file)])
                                    print(1)
                                    file = os.path.join(metainfo['name'], file)
                                    file = os.path.normpath(file).replace("\\", "/")
                                    # print(1)
                                    self.peers[addr]['files'].append(file)
                                    print(file)
                            else:
                                # metainfo = data['metainfo']
                                print(metainfo)
                                self.peers[addr]['hashes'].append(metainfo['hashes'])
                                self.peers[addr]['sizes'].append(metainfo['sizes'])
                                print(metainfo['sizes'])
                                self.peers[addr]['pieces'].append(metainfo['num_pieces'])
                                print(metainfo['num_pieces'])
                                file = metainfo['files']
                                # file = os.path.join(metainfo['name'], file)
                                # print(1)
                                self.peers[addr]['files'].append(file)
                                print(file)
                        
                        print(self.peers[addr])
                        client_socket.send("Server has received your file.".encode())
                    except Exception as e:
                        print(e)
                        client_socket.send("Server can't received your file.".encode())

                elif command == 'help':
                    response = ""
                    response += "list: List all shared files.\n"
                    response += "upload <filename>: Upload file(s)/folder to the server. Ex: upload a,b.txt\n"
                    response += "download <file>: Download file(s)/folder from other peer(s). Ex: download a,b.txt\n"
                    response += "logout: Disconnect from the server.\n"
                    response += "help: List all the commands."
                    
                    client_socket.send(response.encode())

                elif command == 'logout':
                    print(1)
                    try:
                        print(2)
                        self.peers.pop(addr)
                        print(3)
                        response = "Disconnected from the server."
                        print(5)
                        client_socket.send(response.encode())
                        print(6)
                        return
                    except:
                        print(4)
                        response = "There is an error while logging out."
                    
                    
                else:
                    pass
        finally:
            client_socket.close()

if __name__ == "__main__":
    tracker = Tracker()
    tracker.start_server()

# import socket
# import threading, os
# import json
# import math
# from container import *

# TRACKER_IP = socket.gethostbyname(socket.gethostname())
# TRACKER_PORT = 9999
# PIECE_SIZE = 2 ** 20

# class Tracker:
#     def __init__(self, host=TRACKER_IP, port=TRACKER_PORT):
#         self.host = host
#         self.port = port
#         self.peers = {}  # Dictionary to hold peer information

#     def start_server(self):
#         self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#         self.server_socket.bind((self.host, self.port))
#         self.server_socket.listen()
#         print(f"Tracker running on {self.host}:{self.port}")
#         while True:
#             client_socket, addr = self.server_socket.accept()
#             threading.Thread(target=self.handle_client, args=(client_socket, addr)).start()

#     def get_host(self):
#         return self.host
    
#     def get_port(self):
#         return self.port
    
#     def get_peers(self):
#         return self.peers

#     def handle_client(self, client_socket, addr):
#         try:
#             while True:
#                 # print(addr)
#                 try:
#                     data = client_socket.recv(PIECE_SIZE)
#                 except:
#                     print(self.peers)
#                     self.peers.pop(addr)
#                     print(self.peers)
#                     return
                
#                 print(data)
#                 if not data:
#                     break
#                 data = json.loads(data.decode())
#                 command = data['command']

#                 if command == 'register':

#                     pieces = []
#                     for c in data['container']:
#                         temp = math.ceil(c.get_size()/PIECE_SIZE)
#                         c.set_pieces(temp)

#                     self.peers[addr] = {
#                         # 'folders': [],
#                         # 'files': data['files'],
#                         'container': data['container'],
#                         'ip': data['ip'],
#                         'port': data['port'],
#                         # 'sizes': data['sizes'],
#                         # 'hashes': data['hashes'],
#                         # 'pieces': pieces
#                     }
                    # response = (f"Registered {addr} with container: {data['container']}, IP: {data['ip']}, Port: {data['port']}")
                    # client_socket.send(response.encode())
#                 elif command == 'request':
#                     print(data)
#                     filename = data['file']
#                     # print(filename[-2:])
#                     if(filename[-1:] == "/"):
#                         available_peers = []
#                         for peer_addr, peer_info in self.peers.items():
#                             for conts in peer_info['container']:
#                                 # print(file)
#                                 # a="a\\sda"
#                                 # a.startswith()
#                                 # print(file.startswith(filename))
#                                 print(conts)
#                                 print(1)
#                                 for c in conts:
#                                     c = json.loads(c)
#                                     print(c)
#                                     print(2)
#                                     if c['name'] == filename:
#                                         available_peers.append(
#                                         {
#                                             'ip': peer_info['ip'],
#                                             'port': peer_info['port'],
#                                             'file': c.get_name(),
#                                             # 'hash': peer_info['hashes'][peer_info['files'].index(file)],
#                                             # 'size': peer_info['sizes'][peer_info['files'].index(file)],
#                                             # 'pieces': peer_info['pieces'][peer_info['files'].index(file)]
#                                         })
#                     else:
#                         available_peers = [
#                             {
#                                 'ip': peer_info['ip'],
#                                 'port': peer_info['port'],
#                                 'file': filename,
#                                 # 'hash': peer_info['hashes'][peer_info['files'].index(filename)],
#                                 # 'size': peer_info['sizes'][peer_info['files'].index(filename)],
#                                 # 'pieces': peer_info['pieces'][peer_info['files'].index(filename)]
#                             }
#                             for peer_addr, peer_info in self.peers.items() if filename in peer_info['files']
#                         ]
#                     print(available_peers)
#                     response = json.dumps({"peers": available_peers}).encode()
#                     client_socket.send(response)

#                 elif command == 'list':
#                     available_files = []
#                     for peer_addr, peer_info in self.peers.items():
#                         for conts in peer_info['container']:
#                             # if(c.get_type() == 'file'):
#                             print(conts)
#                             print(1)
#                             for c in conts:
#                                 c = json.loads(c)
#                                 print(c)
#                                 print(type(c))
#                                 print(2)
#                                 try:
#                                     available_files.index(c['name'])
#                                 except:
#                                     available_files.append(c['name'])
#                     print(available_files)
#                     response = json.dumps(available_files).encode()
#                     # print("in")
#                     client_socket.send(response)

#                 elif command == 'upload':
#                     try:
#                         print(data['metainfo'])
#                         for metainfo in data['metainfo']:
#                             # if(metainfo['container'].get_type() == 'folder'):
#                                 # for metainfo in data['metainfo']:
#                             self.peers[addr]['container'].append(metainfo['container'])
#                             print(metainfo)
#                                 # for file in metainfo['files']:
#                                 #     print(1)
#                                 #     self.peers[addr]['hashes'].append(metainfo['hashes'][metainfo['files'].index(file)])
#                                 #     self.peers[addr]['sizes'].append(metainfo['sizes'][metainfo['files'].index(file)])
#                                 #     print(1)
#                                 #     self.peers[addr]['pieces'].append(metainfo['num_pieces'][metainfo['files'].index(file)])
#                                 #     print(1)
#                                 #     file = os.path.join(metainfo['name'], file)
#                                 #     file = os.path.normpath(file).replace("\\", "/")
#                                 #     # print(1)
#                                 #     self.peers[addr]['files'].append(file)
#                                 #     print(file)
#                             # else:
#                             #     # metainfo = data['metainfo']
#                             #     print(metainfo)
#                             #     self.peers[addr]['hashes'].append(metainfo['hashes'])
#                             #     self.peers[addr]['sizes'].append(metainfo['sizes'])
#                             #     print(metainfo['sizes'])
#                             #     self.peers[addr]['pieces'].append(metainfo['num_pieces'])
#                             #     print(metainfo['num_pieces'])
#                             #     file = metainfo['files']
#                             #     # file = os.path.join(metainfo['name'], file)
#                             #     # print(1)
#                             #     self.peers[addr]['files'].append(file)
#                             #     print(file)
                        
#                         print(self.peers[addr])
#                         client_socket.send("Server has received your file.".encode())
#                     except Exception as e:
#                         print(e)
#                         client_socket.send("Server can't received your file.".encode())

#                 elif command == 'help':
#                     response = ""
#                     response += "list: List all shared files.\n"
#                     response += "upload <filename>: Upload file(s)/folder to the server. Ex: upload a,b.txt\n"
#                     response += "download <file>: Download file(s)/folder from other peer(s). Ex: download a,b.txt\n"
#                     response += "logout: Disconnect from the server.\n"
#                     response += "help: List all the commands."
                    
#                     client_socket.send(response.encode())

#                 elif command == 'logout':
#                     print(1)
#                     try:
#                         print(2)
#                         self.peers.pop(addr)
#                         print(3)
#                         response = "Disconnected from the server."
#                         print(5)
#                         client_socket.send(response.encode())
#                         print(6)
#                         return
#                     except:
#                         print(4)
#                         response = "There is an error while logging out."
                    
                    
#                 else:
#                     pass
#         finally:
#             client_socket.close()

# if __name__ == "__main__":
#     tracker = Tracker()
#     tracker.start_server()