import socket, math
import json, hashlib
import threading, queue
import sys
import os
import tqdm
import queue


TRACKER_IP = ''
TRACKER_PORT = None
MY_IP = socket.gethostbyname(socket.gethostname())
PIECE_SIZE = 2 ** 20
FORMAT = 'utf-8'
MAX_LISTEN = 100
# SHARE_PATH = "./share/"
DOWNLOAD_PATH = "./download/"

class Peer:
    # init peer
    def __init__(self,  my_ip, my_port, files = None, tracker_host = None, tracker_port = None):
        self.tracker_host = tracker_host
        self.tracker_port = tracker_port
        self.my_ip = my_ip
        self.my_port = int(my_port)
        
        if files is None:
            self.files = []
        else:
            self.files = file

        self.part_data_lock = threading.Lock()

        sizes, hashes = [],[]
        for file in self.files:
            sizes.append(os.path.getsize(file))
            part_hash = self.create_hash_file(file)
            hashes.append(part_hash)
        
        self.hashes = hashes
        self.sizes = sizes
        
        # connect to tracker
        if (tracker_host is not None) or (tracker_port is not None):
            try: 
                self.tracker_port = int(tracker_port)
            except ValueError:
                print ("Tracker port is not an integer")
                exit()
            flag = self.connect_tracker(tracker_host=self.tracker_host, tracker_port=self.tracker_port)
            if(flag):
                self.register_with_tracker()
            
                if(os.path.exists(SHARE_PATH) == False):
                    os.mkdir(SHARE_PATH)
                else:
                    metainfo = self.create_metainfo(SHARE_PATH)
                    
                    # print(metainfo)

                    message = json.dumps({'command': 'upload', 'metainfo': metainfo}).encode()
                    # print(message)
                    self.client_to_tracker.send(message)

                    response = self.client_to_tracker.recv(1024).decode()
                    print(response)
                
                if(os.path.exists(DOWNLOAD_PATH) == False):
                    os.mkdir(DOWNLOAD_PATH)
            
                # socket to connect other peer
                self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.server_socket.bind((self.my_ip, self.my_port))
                self.server_socket.listen(MAX_LISTEN)
                
                # while True:   
                #     client_socket, addr = self.server_socket.accept()
                threading.Thread(target=self.accept_connections, daemon=False).start()

        
        self.part_data_lock = threading.Lock()
        

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

    def connect_tracker(self, tracker_host, tracker_port ):
        try:
            self.client_to_tracker = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # print(self.tracker_host)
            # print(self.tracker_port)
            self.client_to_tracker.connect((tracker_host, tracker_port))
            print("Connect to tracker successfully.")
            return True
        except Exception as e:
            print (tracker_host)
            print (tracker_port)
            print (e)
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
        self.client_to_tracker.recv(PIECE_SIZE)

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

    # receive file (dữ liệu nhận ghi vào filename)
    def download_piece(self, ip_sender, port_sender, filename, start, end, part_data):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((ip_sender, port_sender))

            
            message = f"{filename}*{start}*{end}"
            s.send(message.encode())

            # Await confirmation before continuing
            response = s.recv(PIECE_SIZE).decode()
            if response == "done":
                print(f"Start: {start}, End: {end} sent successfully.")
            else:
                print("Failed to send data correctly.")

            # file_bytes = b""
            arr = []
            done = False
            progress = tqdm.tqdm(unit="B", unit_scale=True, unit_divisor=1000, total=int(end-start))
            
            # start_time = time.time()
            
            # Nhận dữ liệu từ sender
            buffer_size = 1024*1024
            while not done:
                # part_bytes = b""
                data = s.recv(buffer_size)
                if data[-5:] == b"<END>":
                    done = True
                    # part_bytes = data[:-5]
                    arr.append(data[:-5])
                else:
                    # part_bytes = data
                    arr.append(data)
                # arr.append(part_bytes)
                progress.update(len(data))
            
            # for file_data in arr:
            #     file_bytes += file_data
            print(f"start merge piece")
            
            file_bytes = b"".join(part for part in arr)
            
            print("end merge piece")
            # end_time = time.time()
            
            # # Thêm vào heap
            # addr = (ip_sender, port_sender)
            # speed = (end-start)/(end_time-start_time) #byte/second
            # isExisted = False

            # for mem in self.download_rates:
            #     if addr == mem[1]:
            #         isExisted = True
            #         if speed > abs(mem[0]):
            #             self.download_rates.remove((mem[0], mem[1]))
            #             heapq.heappush(self.download_rates, (-speed, addr))
            #             isExisted = True
            # if isExisted == False:
            #     heapq.heappush(self.download_rates, (-speed, addr))
            
            # if len(self.download_rates) >= 4:
            #     heapq.heappop(self.download_rates)

            # Ghi dữ liệu piece
            print('start add arr')
            with self.part_data_lock:
                part_data.append((start, file_bytes))
                s.send("done".encode())
            print('end add arr')
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
            data = client_socket.recv(PIECE_SIZE).decode()
            # print(data)
            if data:
                parts = data.split('*')  # Split the received data by ':'
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

            #######
            #NEED TO DEBUG
            #######
            print(self.files)
            for f in self.files:
                # print(f)
                # if filename in f:
                # if(filename)
                if f.endswith(filename):
                # file_size = os.path.getsize(filename)
                # client_socket.sendall(f"{filename:<PIECE_SIZE}".encode())
                # client_socket.sendall(f"{file_size:<PIECE_SIZE}".encode())
                    # path = os.path.join(SHARE_PATH, f)
                    print(f)
                    with open(f, 'rb') as file:
                        print(f)
                        file.seek(start)
                        numbytes = end - start
                        buffer_size = 1024*1024
                        while numbytes:
                            data = file.read(min(numbytes, buffer_size))
                            client_socket.send(data)
                            # print(numbytes)
                            # print(data)
                            # print(len(data))
                            # input()
                            if(len(data) == 0):
                                break
                            numbytes -= len(data)

                        client_socket.send(b"<END>")
                        if(client_socket.recv(PIECE_SIZE).decode() == "done"):
                            pass
                        else:
                            print("data wrong")
                    file.close()

        except Exception as e:
            print(f"Error: {e}")
        finally:
            client_socket.close()
            client_socket.close()

    def normalize_path(self, path):
        return os.path.normpath(path).replace('\\', "/")

    def create_metainfo(self, file_paths):
        metainfo = []
        files = []

        file_paths = file_paths.split(",")

        for file_path in file_paths:
            # Check if the input path is a file or a directory
            # file_path = self.normalize_path(file_path)
            # print(file_path)
            # print(SHARE_PATH)
            if os.path.isdir(file_path):
                # Multiple-file mode
                temp_path = file_path
                try:
                    # print(1)
                    if(temp_path.find(":") > -1):
                        # print(2)
                        temp_path = self.normalize_path(temp_path)
                        slash_id = temp_path.rindex('/')

                        temp_path = temp_path[slash_id + 1:]
                except Exception as e:
                    print(e)
                sizes = []
                pieces = []
                hashes = []
                
                for root, _, filenames in os.walk(file_path):
                    # print(root)
                    # print(filenames)
                    for filename in filenames:
                        file_abs_path = os.path.join(root, filename)
                        # print(file_abs_path)
                        file_abs_path = self.normalize_path(file_abs_path)
                        # file_abs_path.replace('\\', "/")
                        
                        file_rel_path = os.path.relpath(file_abs_path, file_path)
                        file_rel_path = self.normalize_path(file_rel_path)
                        # print(file_abs_path)
                        # print(file_rel_path)

                        try:
                            # print(1)
                            if(file_rel_path.find(":") > -1):
                                # print(2)
                                slash_id = file_rel_path.rindex('/')

                                file_rel_path = file_rel_path[slash_id + 1:]
                        except Exception as e:
                            print(e)
                        
                        file_size = os.path.getsize(file_abs_path)
                        files.append(file_rel_path)
                        sizes.append(file_size)
                        hash = self.create_hash_file(file_abs_path)
                        hashes.append(hash)

                        self.files.append(file_abs_path)
                        # print(self.files)
                        self.sizes.append(file_size)
                        self.hashes.append(hash)

                        pieces.append(math.ceil(file_size/PIECE_SIZE))
                
                metainfo.append({
                    'name': temp_path,
                    'is_folder': True,
                    'files': files, #['b.txt','temp.png']
                    'sizes': sizes, #[23,1500]
                    'num_pieces': pieces, #[1,2]
                    'hashes': hashes 
                })
            
            elif os.path.isfile(file_path):
                file_path = self.normalize_path(file_path)

                self.files.append(file_path)
                
                size = os.path.getsize(file_path)
                files.append(('', size))
                hash = self.create_hash_file(file_path)

                try:
                    # print(1)
                    if(file_path.find(":") > -1):
                        file_path = self.normalize_path(file_path)
                        # print(2)
                        slash_id = file_path.rindex('/')

                        file_path = file_path[slash_id + 1:]
                except Exception as e:
                    print(e)
                
                
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
                # invalid = True
                print("Invalid input path.")
                return

            print(self.files)
            files = []
        return metainfo

    def sen_process(self, data, q):
        # print(data)
        # data = data.split(" ")
        # cmd = data[0].strip().lower()
        global_response = ""
        # data = data.split(" ")
        cmd_id = data.find(" ")

        if(cmd_id < 0):
            cmd = data
        else:
            cmd = data[:cmd_id].strip().lower()
        
        remain_data = data[cmd_id + 1:]
        if cmd == "help":
            message = json.dumps({'command': 'help'})
            
            self.client_to_tracker.send(message.encode())
            
            res = self.client_to_tracker.recv(PIECE_SIZE).decode()

            # print(res)
            # self.response = res
            global_response = res
        elif cmd == "logout":
            # print("Disconnected from the server.")
            message = json.dumps({'command': 'logout'})
            
            self.client_to_tracker.send(message.encode())
            
            # print(1)
            res = self.client_to_tracker.recv(PIECE_SIZE).decode()
            # print(2)
            # print(res)
            # self.response = res
            global_response = res
            q.put(global_response)
            return
        elif cmd == "list":
            message = json.dumps({'command': 'list'})
            
            self.client_to_tracker.send(message.encode())
            
            response = self.client_to_tracker.recv(1024).decode()
            peer_list = json.loads(response)
            
            print(peer_list)
            # self.response = peer_list
            global_response = peer_list
            # print(peer_list)
            
        elif cmd == "upload":
            file_paths = remain_data
            print (file_paths)
            metainfo = self.create_metainfo(file_paths)
            
            print(metainfo)

            message = json.dumps({'command': 'upload', 'metainfo': metainfo}).encode()
            print(message)
            self.client_to_tracker.send(message)
            print (1)
            response = self.client_to_tracker.recv(1024).decode()
            
            # self.response = response
            global_response = response
            
        elif cmd == "download":
            filename = remain_data

            # peerIp = data[2]
            # peerport = data[3]

            filename = filename.split(",")
            temp_list = []

            for file in filename:
                if(file[-1:] == "/"):
                    path = os.path.join(DOWNLOAD_PATH, file)
                    # print(path)
                    # print(os.path.exists(path))
                    if(os.path.exists(path) == False):
                        os.mkdir(path)
                    peer_req = self.request_peerS_info(file)
                    # print(peer_req)
                    for p in peer_req['peers']:
                        temp_list.append(p['file'])
                    filename.remove(file)

            for f in temp_list:
                filename.append(f)                        

            # print(filename)

            self.manage_downloads(filename)
            # self.response = ""
            global_response = ""
        else:
            # self.response = "pass"
            global_response = "pass"
            # self.client_to_tracker.send("pass".encode())
        q.put(global_response)

    def sen(self):
        while True:
            data = input("> ")
            # data = data.split(" ")

            # print("endloop")
            q = queue.Queue()
            thrSen = threading.Thread(target=self.sen_process, args=(data, q))
            thrSen.start()
            # print("endloop")
            # print(self.response)
            answer = q.get()
            print(answer)
            if(answer == "Disconnected from the server."):
                break
            
            
    def run(self, tk_to_peer_q:queue.Queue, peer_to_tk_q:queue.Queue) -> None: #similar to send, wait for a command
        q = queue.Queue()
        while True:
            message = tk_to_peer_q.get() #block here
            print (message)
            if message is None:  # None is our signal to exit the thread
                break
            
            elif message == "CONNECT":
                tracker_host, tracker_port = tk_to_peer_q.get()
                
                result = self.connect_tracker(tracker_host=tracker_host, tracker_port=tracker_port)
                if(result):
                    self.register_with_tracker()
            
                    if(os.path.exists(SHARE_PATH) == False):
                        os.mkdir(SHARE_PATH)
                    else:
                        metainfo = self.create_metainfo(SHARE_PATH)
                        
                        # print(metainfo)

                        message = json.dumps({'command': 'upload', 'metainfo': metainfo}).encode()
                        # print(message)
                        self.client_to_tracker.send(message)

                        response = self.client_to_tracker.recv(1024).decode()
                        print(response)
                    
                    if(os.path.exists(DOWNLOAD_PATH) == False):
                        os.mkdir(DOWNLOAD_PATH)
                
                    # socket to connect other peer
                    self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self.server_socket.bind((self.my_ip, self.my_port))
                    self.server_socket.listen(MAX_LISTEN)
                    
                    # while True:   
                    #     client_socket, addr = self.server_socket.accept()
                    threading.Thread(target=self.accept_connections, daemon=True).start()
                peer_to_tk_q.put(result)
            elif message == "CONSOLE":
                message = tk_to_peer_q.get() #block here
                self.sen_process (data=message, q=q)
                response = q.get(timeout=5)
                peer_to_tk_q.put(response)
            elif message == "GET LIST":
                self.sen_process (data="list", q=q)
                response = q.get(timeout=5)
                peer_to_tk_q.put(response)
            elif message == "UPLOAD":
                message = tk_to_peer_q.get()
                print (message)
                self.sen_process (data=message, q=q)
                response = q.get(timeout=5)
            elif message == "DOWNLOAD":
                message = tk_to_peer_q.get()
                print (message)
                self.sen_process (data=message, q=q)
                response = q.get(timeout=5)
            else:
                pass
            
    
    def download_file(self, file_name, part_data):
        peer_info = self.request_peerS_info(file_name)
        # print(peer_info)
        if peer_info['peers']:
            size, pieces, hash = 0,0,''
            # print(peer_info)
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
            # print(data)
            sum_hash = self.create_hash_data(data)
            
            # print(sum_hash)
            # print(hash)

            # with part_data_lock:
            #     for i, result in enumerate(part_data):
            #         data += result
            
            try:
                if sum_hash == hash:
                    with self.part_data_lock:
                        check = input(f"Do you want to rename {file_name}? Enter \"yes\" to rename, else press 'enter' again:")
                        if(check.strip().lower() == "yes"):
                            new_filename = input("Please enter other name:")
                            try:
                                slash_id = file_name.rindex('/')

                                file_name = file_name[:slash_id + 1] + new_filename
                            except:
                                file_name = new_filename
                        
                    path = os.path.join(DOWNLOAD_PATH, file_name)
                    # path = self.normalize_path(path)
                    # print(os.path.isfile(path))
                    # print(os.path.dirname(path))

                    if(os.path.exists(os.path.dirname(path)) == False):
                        os.mkdir(os.path.dirname(path))
                    
                    file = open(path, "wb")
                    
                    file.write(data)

                    file.close()
                    print(f"File {file_name} has been downloaded.")
                else:
                    print(f"Hash difference.")
            except Exception as e:
                print(e)
            
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

        print(f"Download finish.")

        # for speed in self.download_rates:
        #     print(speed[0]," ",speed[1], end='\n')
    
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

    peer = Peer(MY_IP, my_port, tracker_host=TRACKER_IP, tracker_port=TRACKER_PORT)

    # if the peer need to download a file
    # if len(sys.argv) > 4:
    #     requested_files = sys.argv[4].split(',')
    #     peer.manage_downloads(requested_files)

    peer.sen()
    print("end")
    # sys.exit()
    
