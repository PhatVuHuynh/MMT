import socket
import threading, os
import json
import math

TRACKER_IP = '192.168.1.166'
TRACKER_PORT = 9999

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
                data = client_socket.recv(1024)
                print(data)
                if not data:
                    break
                data = json.loads(data.decode())
                command = data['command']

                if command == 'register':

                    pieces = []
                    for size in data['sizes']:
                        temp = math.ceil(size/1024)
                        pieces.append(temp)

                    self.peers[addr] = {
                        'folders': [],
                        'files': data['files'],
                        'ip': data['ip'],
                        'port': data['port'],
                        'sizes': data['sizes'],
                        'pieces': pieces
                    }
                    print(f"Registered {addr} with files: {data['files']}, IP: {data['ip']}, Port: {data['port']}")
                elif command == 'request':
                    print(data)
                    filename = data['file']
                    # print(filename[-2:])
                    if(filename[-1:] == "\\"):
                        available_peers = []
                        for peer_addr, peer_info in self.peers.items():
                            for file in peer_info['files']:
                                print(file)
                                # a="a\\sda"
                                # a.startswith()
                                print(file.startswith(filename))
                                if file.startswith(filename) :
                                    available_peers.append(
                                    {
                                        'ip': peer_info['ip'],
                                        'port': peer_info['port'],
                                        'file': file,
                                        'size': peer_info['sizes'][peer_info['files'].index(file)],
                                        'pieces': peer_info['pieces'][peer_info['files'].index(file)]
                                    })
                    else:
                        available_peers = [
                            {
                                'ip': peer_info['ip'],
                                'port': peer_info['port'],
                                'file': filename,
                                'size': peer_info['sizes'][peer_info['files'].index(filename)],
                                'pieces': peer_info['pieces'][peer_info['files'].index(filename)]
                            }
                            for peer_addr, peer_info in self.peers.items() if filename in peer_info['files']
                        ]
                    print(available_peers)
                    response = json.dumps({"peers": available_peers}).encode()
                    client_socket.send(response)

                elif command == 'LIST':
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

                elif command == 'UPLOAD':
                    try:
                        print(data['metainfo'])
                        for metainfo in data['metainfo']:
                            if(metainfo['is_folder']):
                                # for metainfo in data['metainfo']:
                                self.peers[addr]['folders'].append(metainfo['name'])
                                print(metainfo)
                                for file in metainfo['files']:
                                    print(1)
                                    self.peers[addr]['sizes'].append(metainfo['sizes'][metainfo['files'].index(file)])
                                    print(1)
                                    self.peers[addr]['pieces'].append(metainfo['num_pieces'][metainfo['files'].index(file)])
                                    print(1)
                                    file = os.path.join(metainfo['name'], file)
                                    # print(1)
                                    self.peers[addr]['files'].append(file)
                                    print(file)
                            else:
                                # metainfo = data['metainfo']
                                print(metainfo)
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

                # elif command == 'DOWNLOAD':
                #     filename = data['file']
                #     ip = data['ip']
                #     port = int(data['port'])

                #     available_peer = {}

                #     for peer_addr, peer_info in self.peers.items():
                #         if filename in peer_info['files'] and ip == peer_info['ip'] and port == peer_info['port']:
                #             available_peer = {
                #                 'ip': peer_info['ip'],
                #                 'port': peer_info['port'],
                #                 'file': filename,
                #                 'size': peer_info['sizes'][peer_info['files'].index(filename)],
                #                 'pieces': peer_info['pieces'][peer_info['files'].index(filename)]
                #             }
                        
                #     # print(type(available_peers))
                #     response = json.dumps(available_peer).encode()
                #     client_socket.send(response)
                #     pass
                else:
                    pass
        finally:
            client_socket.close()

if __name__ == "__main__":
    tracker = Tracker()
    tracker.start_server()