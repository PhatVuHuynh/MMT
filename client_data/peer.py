import socket, math
import json, hashlib
import threading
import sys
import os
import tqdm

TRACKER_IP = ''
TRACKER_PORT = None
MY_IP = socket.gethostbyname(socket.gethostname())
PIECE_SIZE = 2 ** 20
FORMAT = 'utf-8'
MAX_LISTEN = 100

class Peer:
    # init peer
    def __init__(self, tracker_host, tracker_port, my_ip, my_port, files):
        self.tracker_host = tracker_host
        self.tracker_port = int(tracker_port)
        self.my_ip = my_ip
        self.my_port = int(my_port)
        self.files = files

        # print(MY_IP)
        
        self.part_data_lock = threading.Lock()

        sizes, hashes = [],[]
        for file in files:
            sizes.append(os.path.getsize(file))
            part_hash = self.create_hash_file(file)
            hashes.append(part_hash)
        
        self.hashes = hashes
        self.sizes = sizes
        
        # connect to tracker
        flag = self.connect_tracker()
        if(flag):
            self.register_with_tracker()
            
            # socket to connect other peer
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.bind((self.my_ip, self.my_port))
            self.server_socket.listen(MAX_LISTEN)
            
            # while True:   
            #     client_socket, addr = self.server_socket.accept()
            threading.Thread(target=self.accept_connections, daemon=False).start()

    def get_tracker_host(self):
        return self.tracker_host
    
    def get_tracker_port(self):
        return self.tracker_port
    
    def get_my_ip(self):
        return self.my_ip
    
    def get_my_port(self):
        return self.my_port
    
    def get_files(self):
        return self.files

    def connect_tracker(self):
        try:
            self.client_to_tracker = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            print(self.tracker_host)
            print(self.tracker_port)
            self.client_to_tracker.connect((self.tracker_host, self.tracker_port))
            print("Connect to tracker successfully.")
            return True
        except:
            print("Can't connect to tracker")
            return False

    def register_with_tracker(self):
        message = json.dumps({
            'command': 'register',
            'files': self.files,
            'ip': self.my_ip,
            'port': self.my_port,
            'sizes': self.sizes,
            'hashes': self.hashes
        })
        self.client_to_tracker.send(message.encode())

    #Tạo tổng hash của file_name
    def create_hash_file(self, file_name):
        hash_sum = ""
        with open(file_name, 'rb') as file:
            piece_offset = 0
            piece = file.read(PIECE_SIZE)
            while piece:
                piece_hash = hashlib.sha256(piece).hexdigest()
                hash_sum += piece_hash
                piece_offset += len(piece)
                piece = file.read(PIECE_SIZE)

        return hash_sum
    
    def create_hash_data(self, data):
        sum_hash = ""
        offset = 0
        
        while offset < len(data):
            piece = data[offset:offset+PIECE_SIZE]
            piece_hash = hashlib.sha256(piece).hexdigest()
            sum_hash += piece_hash
            offset += PIECE_SIZE
        
        return sum_hash
    
# lấy info peer từ tracker, yêu cầu kết nối và nhận file:
    # lấy info peer
    def request_peerS_info(self, filename):
        # with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        #     client_socket.connect((self.tracker_host, self.tracker_port))
        message = json.dumps({'command': 'request', 'file': filename})
        # print(1)
        # print(filename)
        with self.part_data_lock:
            self.client_to_tracker.send(message.encode())
            response = self.client_to_tracker.recv(PIECE_SIZE)
        if not response:
            print("No data received")
            return None
        try:
            return json.loads(response.decode())
        except json.JSONDecodeError:
            print("Failed to decode JSON from response")
            return None

    # def request_peer_info(self, filename, ip, port):
    #     message = json.dumps({'command': 'DOWNLOAD', 
    #                                   'file': filename,
    #                                   'ip': ip,
    #                                   'port': port
    #                                 }).encode()
    #     self.client_to_tracker.send(message)
    #     response = self.client_to_tracker.recv(PIECE_SIZE)
    #     if not response:
    #         print(f"No data received from {ip}, {port}")
    #         return None
    #     try:
    #         return json.loads(response.decode())
    #     except json.JSONDecodeError:
    #         print("Failed to decode JSON from response")
    #         return None

    # receive file (dữ liệu nhận ghi vào filename)
    def download_piece(self, ip_sender, port_sender, filename, start, end, part_data):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((ip_sender, port_sender))

            # s.send(filename.encode())

            # s.recv(PIECE_SIZE)

            # s.send(str(start).encode())

            # s.recv(PIECE_SIZE)

            # s.send(str(end).encode())

            # print(start, " ", end)

            # Sending filename, start, and end as a single message separated by a special character
            message = f"{filename}:{start}:{end}"
            s.send(message.encode())

            # Await confirmation before continuing
            response = s.recv(PIECE_SIZE).decode()
            if response == "done":
                print(f"Start: {start}, End: {end} sent successfully.")
            else:
                print("Failed to send data correctly.")

            # received_file_name = s.recv(PIECE_SIZE).decode()
            # print(received_file_name," ")

            # file_size = s.recv(PIECE_SIZE).decode()
            # print(file_size," ")

            # file = open(received_file_name, "wb")

            file_bytes = b""

            done = False

            progress = tqdm.tqdm(unit="B", unit_scale=True, 
                                 unit_divisor=1000, 
                                 total=int(end-start))
            
            while not done:
                data = s.recv(PIECE_SIZE)
                # print(data)
                if data[-5:] == b"<END>":
                    done = True
                    file_bytes += data[:-5]
                else:
                    file_bytes += data
                progress.update(PIECE_SIZE)
                # input("wait")

            with self.part_data_lock:
                part_data.append((start, file_bytes))

            # file.write(file_bytes)

        except Exception as e:
            print(f"Error in download_file: {e}")
        finally:
            s.close()

    
# lắng nghe, chấp nhận kết nối và gửi file:
    # chấp nhận kết nối
    def accept_connections(self):
        while True:
            client_socket, addr = self.server_socket.accept()
            threading.Thread(target=self.handle_peer, args=(client_socket,), daemon=False).start()

    # send file
    def handle_peer(self, client_socket):
        try:
            # filename = client_socket.recv(PIECE_SIZE).decode()
            # print(filename)

            # client_socket.send("done".encode())

            # start = client_socket.recv(PIECE_SIZE).decode()

            # client_socket.send("done".encode())

            # end = client_socket.recv(PIECE_SIZE).decode()
            
            # print(start," ", end)
            # print(type(start))

            data = client_socket.recv(PIECE_SIZE).decode()
            if data:
                parts = data.split(':')  # Split the received data by ':'
                if len(parts) == 3:
                    filename, start_str, end_str = parts
                    print(f"Filename: {filename}")
                    start = int(start_str)  # Convert start to integer
                    end = int(end_str)      # Convert end to integer
                    print(f"Start: {start}, End: {end}, Type of start: {type(start)}")

                    # Send confirmation back to sender
                    client_socket.send("done".encode())
                else:
                    print("Received data is not formatted correctly.")
                    client_socket.send("error".encode())
            else:
                print("No data received.")

            # print(filename)
            # print(self.files)
            if filename in self.files:
                # file_size = os.path.getsize(filename)
                # client_socket.sendall(f"{filename:<PIECE_SIZE}".encode())
                # client_socket.sendall(f"{file_size:<PIECE_SIZE}".encode())
                with open(filename, 'rb') as file:
                    file.seek(start)
                    numbytes = end - start
                    data = file.read(numbytes)
                    # print(data)
                    client_socket.sendall(data)
                    # print("end")
                    client_socket.send(b"<END>")
                    # print("end")
                file.close()

        except Exception as e:
            print(f"Error: {e}")
        finally:
            client_socket.close()

    def sen_process(self, data):
        # print(data)
        cmd = data[0].strip().lower()
        if cmd == "help":
            self.client_to_tracker.send(cmd.encode(FORMAT))
            res = self.client_to_tracker.recv(PIECE_SIZE).decode()

            print(res)
        elif cmd == "logout":
            # print("Disconnected from the server.")
            self.client_to_tracker.send(cmd.encode(FORMAT))
            print(self.client_to_tracker.recv(PIECE_SIZE).decode())
            return
        elif cmd == "list":
            message = json.dumps({'command': 'list'})
            
            self.client_to_tracker.send(message.encode())
            
            response = self.client_to_tracker.recv(1024).decode()
            
            peer_list = json.loads(response)
            
            print(peer_list)
        elif cmd == "upload":
            file_paths = data[1]

            file_paths = file_paths.split(",")

            metainfo = []
            files = []
            invalid = False
            
            for file_path in file_paths:
                # Check if the input path is a file or a directory
                if os.path.isdir(file_path):
                    # Multiple-file mode
                    
                    sizes = []
                    pieces = []
                    hashes = []
                    
                    for root, _, filenames in os.walk(file_path):
                        print(root)
                        print(filenames)
                        for filename in filenames:
                            file_abs_path = os.path.join(root, filename)
                            file_rel_path = os.path.relpath(file_abs_path, file_path)
                            
                            file_size = os.path.getsize(file_abs_path)
                            files.append(file_rel_path)
                            sizes.append(file_size)
                            hash = self.create_hash_file(file_abs_path)
                            hashes.append(hash)

                            self.files.append(file_abs_path)
                            self.sizes.append(file_size)
                            self.hashes.append(hash)

                            pieces.append(math.ceil(file_size/PIECE_SIZE))
                    
                    metainfo.append({
                        'name': file_path,
                        'is_folder': True,
                        'files': files, #['b.txt','temp.png']
                        'sizes': sizes, #[23,1500]
                        'num_pieces': pieces, #[1,2]
                        'hashes': hashes 
                    })
                
                elif os.path.isfile(file_path):
                    size = os.path.getsize(file_path)
                    files.append(('', size))
                    hash = self.create_hash_file(file_path)
                    
                    self.files.append(file_path)
                    self.sizes.append(size)
                    self.hashes.append(hash)

                    num_piece = math.ceil(size/PIECE_SIZE)
                    
                    metainfo.append({
                        'name': '',
                        'is_folder': False,
                        'files': file_path,
                        'sizes': size,
                        'num_pieces': num_piece,
                        'hashes': hash
                    })

                else:
                    invalid = True
                    print("Invalid input path.")
                    return

                print(files)
                files = []

            if(invalid):
                return
            
            print(metainfo)

            message = json.dumps({'command': 'upload', 'metainfo': metainfo}).encode()
            print(message)
            self.client_to_tracker.send(message)

            response = self.client_to_tracker.recv(1024).decode()
            print(response)
            
        elif cmd == "download":
            filename = data[1]

            # peerIp = data[2]
            # peerport = data[3]

            filename = filename.split(",")
            temp_list = []

            for file in filename:
                if(file[-1:] == "\\"):
                    if(os.path.exists(file) == False):
                        os.mkdir(file)
                    peer_req = self.request_peerS_info(file)
                    print(peer_req)
                    for p in peer_req['peers']:
                        temp_list.append(p['file'])
                    filename.remove(file)

            for f in temp_list:
                filename.append(f)                        

            print(filename)

            self.manage_downloads(filename)
        else:
            print("pass")
            # self.client_to_tracker.send("pass".encode())

    def sen(self):
        while True:
            data = input("> ")
            data = data.split(" ")

            thrSen = threading.Thread(target=self.sen_process, args=(data,))
            thrSen.start()
            # print("endloop")
    
    def download_file(self, file_name, part_data):
        peer_info = self.request_peerS_info(file_name)
        # print(peer_info)
        if peer_info:
            size, pieces, hash = 0,0,''
            print(peer_info)
            for p in peer_info['peers']:
                print(p['ip'], " ", p['port'], " ", p['file'], " ", p['size'], p['pieces'])
                size = p['size']
                pieces = p['pieces']
                hash = p['hash']

            ip_list = []
            port_list = []
            lastpiece_size = size % PIECE_SIZE
            for p in peer_info['peers']:
                ip_list.append(p['ip'])
                port_list.append(p['port'])
            
            n = len(ip_list)
            data = b''
            threads = []

            if (n == 1):
                # mặc định 3 luồng xử lí cùng, 
                #có thể chỉnh sửa nhập input cho number thread
                number_thread = 3
                if (pieces < number_thread):
                    start_piece, end_piece = [],[]
                    for i in range(pieces):
                        start_piece.append(i)
                        end_piece.append(i+1)
                    for i in range(pieces):
                        thread = threading.Thread(target=self.download_piece, args=(ip_list[0], port_list[0], file_name, start_piece[i]*PIECE_SIZE, end_piece[i]*PIECE_SIZE, part_data))
                        threads.append(thread)
                        thread.start()
                    # for thread in threads:
                    #     thread.join()
                else:
                    chunk_size = pieces // number_thread  # Kích thước của mỗi khoảng
                    remainder = pieces % number_thread  # Phần dư

                    start_piece = [i * chunk_size + min(i, remainder) for i in range(number_thread)]  # Mảng start_byte
                    end_piece = [(i + 1) * chunk_size + min(i + 1, remainder) for i in range(number_thread)]  # Mảng end_byte

                    print(f"Downloading file from {ip_list[0]}:{port_list[0]}")
                    for i in range(number_thread):
                        if i < number_thread - 1:
                            thread = threading.Thread(target=self.download_piece, args=(ip_list[0], port_list[0], file_name, start_piece[i]*PIECE_SIZE, end_piece[i]*PIECE_SIZE, part_data))
                        else:
                            if lastpiece_size == 0:
                                thread = threading.Thread(target=self.download_piece, args=(ip_list[0], port_list[0], file_name, start_piece[i]*PIECE_SIZE, end_piece[i]*PIECE_SIZE, part_data))
                            else:
                                thread = threading.Thread(target=self.download_piece, args=(ip_list[0], port_list[0], file_name, start_piece[i]*PIECE_SIZE, (end_piece[i]-1)*PIECE_SIZE + lastpiece_size, part_data))
                        threads.append(thread)
                        thread.start()
                        
                        # threading.Thread(target=peer.download_file, args=(ip_list[i], port_list[i], requested_file, start_byte[i], end_byte[i])).start()
                
                    # for thread in threads:
                    #     thread.join()
            else:
                if(pieces < n):
                    start_piece, end_piece = [],[]
                    for i in range(pieces):
                        start_piece.append(i)
                        end_piece.append(i+1)
                    for i in range(pieces):
                        thread = threading.Thread(target=self.download_piece, args=(ip_list[i], port_list[i], file_name, start_piece[i]*PIECE_SIZE, end_piece[i]*PIECE_SIZE, part_data))
                        threads.append(thread)
                        thread.start()
                    # for thread in threads:
                    #     thread.join()
                else:
                    chunk_size = pieces // n  # Kích thước của mỗi khoảng
                    
                    remainder = pieces % n  # Phần dư

                    start_piece = [i * chunk_size + min(i, remainder) for i in range(n)]  # Mảng start_byte
                    end_piece = [(i + 1) * chunk_size + min(i + 1, remainder) for i in range(n)]  # Mảng end_byte

                    # print(start_piece)
                    # print(end_piece)

                    for i in range(len(ip_list)):
                        print(f"Downloading file from {ip_list[i]}:{port_list[i]}")
                        if i < len(ip_list) - 1:
                            thread = threading.Thread(target=self.download_piece, args=(ip_list[i], port_list[i], file_name, start_piece[i]*PIECE_SIZE, end_piece[i]*PIECE_SIZE, part_data))
                        else:
                            if lastpiece_size == 0:
                                thread = threading.Thread(target=self.download_piece, args=(ip_list[i], port_list[i], file_name, start_piece[i]*PIECE_SIZE, end_piece[i]*PIECE_SIZE, part_data))
                            else:
                                thread = threading.Thread(target=self.download_piece, args=(ip_list[i], port_list[i], file_name, start_piece[i]*PIECE_SIZE, (end_piece[i]-1)*PIECE_SIZE + lastpiece_size, part_data))
                        threads.append(thread)
                        thread.start()
                        
                        # threading.Thread(target=peer.download_file, args=(ip_list[i], port_list[i], requested_file, start_byte[i], end_byte[i])).start()
            
            for thread in threads:
                thread.join()

            part_data.sort(key=lambda x: x[0])

            data = b"".join([part[1] for part in part_data])

            sum_hash = self.create_hash_data(data)

            # with part_data_lock:
            #     for i, result in enumerate(part_data):
            #         data += result
            
            try:
                if sum_hash == hash:
                    file = open(file_name, "wb")
                    file.write(data)

                    file.close()
            except Exception as e:
                print(e)
            
            print(f"File {file_name} has been downloaded.")
        else:
            print("No peer found with the requested file.")

    def manage_downloads(self, requested_files):
        threads = []
        # part_data = []

        for file_name in requested_files:
            thread = threading.Thread(target=self.download_file, args=(file_name,[]))

            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        print(f"All files have been downloaded.")
    
if __name__ == "__main__":
    TRACKER_IP = input("Please enter Tracker's IP you want to connect:")
    print(TRACKER_IP)
    TRACKER_PORT = input("Please enter port of the Tracker above:")
    print(TRACKER_PORT)
    # my_ip = sys.argv[1]

    my_port = input("Please enter your port number:")
    files = []
    
    # if len(sys.argv) > 3:
    #     files = sys.argv[3].split(',')

    peer = Peer(TRACKER_IP, TRACKER_PORT, MY_IP, my_port, files)

    # if the peer need to download a file
    # if len(sys.argv) > 4:
    #     requested_files = sys.argv[4].split(',')
    #     peer.manage_downloads(requested_files)

    peer.sen()