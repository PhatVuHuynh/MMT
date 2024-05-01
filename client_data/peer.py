import socket, math, pickle
import json, hashlib
import threading, queue
from folder import *
import os
import tqdm

TRACKER_IP = ''
TRACKER_PORT = None
MY_IP = socket.gethostbyname(socket.gethostname())
PIECE_SIZE = 2 ** 20
FORMAT = 'utf-8'
MAX_LISTEN = 100
DOWNLOAD_PATH = "./download/"

class Peer:
    # init peer
    def __init__(self, tracker_host, tracker_port, my_ip, my_port, files=[]):
        self.tracker_host = tracker_host
        self.tracker_port = int(tracker_port)
        self.my_ip = my_ip
        self.my_port = int(my_port)
        self.container = files
        self.download_rates = []
        # self.update = False
        # self.hashes = []
        # self.sizes = []

        # connect to tracker
        flag = self.connect_tracker()
        if(flag):
            self.register_with_tracker()

            if(os.path.exists(DOWNLOAD_PATH) == False):
                os.mkdir(DOWNLOAD_PATH)
            
            # socket to connect other peer
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.bind((self.my_ip, self.my_port))
            self.server_socket.listen(MAX_LISTEN)
            
            # while True:   
            #     client_socket, addr = self.server_socket.accept()
            threading.Thread(target=self.accept_connections, daemon=True).start()

        self.part_data_lock = threading.Lock()
    
    # def print_container(self):
    #     for c in self.container:
    #         print(c.get_name() + " - " + c.get_path())
    # def print_folder(self, folder):
    #     print(folder.path)
    #     print(folder.name)
    #     print(folder.parent_folder)
    #     print(folder.files)

    def get_tracker_host(self):
        return self.tracker_host
    
    def get_tracker_port(self):
        return self.tracker_port
    
    def get_my_ip(self):
        return self.my_ip
    
    def get_my_port(self):
        return self.my_port
    
    def get_container(self):
        return self.container

    def connect_tracker(self):
        try:
            self.client_to_tracker = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # print(self.tracker_host)
            # print(self.tracker_port)
            self.client_to_tracker.connect((self.tracker_host, self.tracker_port))
            print("Connect to tracker successfully.")
            return True
        except:
            print("Can't connect to tracker")
            return False

    def register_with_tracker(self):
        message = json.dumps({
            'command': 'register',
            'container': self.container,
            'ip': self.my_ip,
            'port': self.my_port,
            # 'sizes': self.sizes,
            # 'hashes': self.hashes
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
    def request_peerS_info(self, filename, file_hash):
        # with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        #     client_socket.connect((self.tracker_host, self.tracker_port))
        message = json.dumps({'command': 'request', 'file': filename, 'hash': file_hash})
        # print(1)
        print(message)
        with self.part_data_lock:
            self.client_to_tracker.send(message.encode())
            response = self.client_to_tracker.recv(PIECE_SIZE)
        if not response:
            print("No data received")
            return None
        try:
            return pickle.loads(response)
        except Exception as e:
            print(e)
            return None

    # receive file (dữ liệu nhận ghi vào filename)
    def download_piece(self, ip_sender, port_sender, filename, start, end, part_data, hash):
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
            message = f"{filename}*{start}*{end}*{hash}"
            # print(message)
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

            arr = []
            done = False
            progress = tqdm.tqdm(unit="B", unit_scale=True, unit_divisor=1000, total=int(end-start))
            
            # start_time = time.time()
            
            # Nhận dữ liệu từ sender
            buffer_size = PIECE_SIZE
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
            
            file_path = f"{filename}_{start}.bin"
            file_path = file_path.replace("/","_")
            
            with open(file_path, 'wb') as file_part:
                for item in arr:
                    file_part.write(item)
            file_part.close()
            print(f"Successfully wrote array to file: {file_path}")
            
            print("end merge piece")
            # end_time = time.time()
            
            # Ghi dữ liệu piece
            print('start add with lock')

            with self.part_data_lock:
                print("lock")
                part_data.append((start, file_path))
                print("open")
                s.send("done".encode())

            print('end add with lock')
            # file.write(file_bytes)

        except Exception as e:
            print(f"Error in download_file: {e}")
        finally:
            s.close()

        #     file_bytes = b""

        #     done = False

        #     progress = tqdm.tqdm(unit="B", unit_scale=True, 
        #                          unit_divisor=1000, 
        #                          total=int(end-start))
            
        #     while not done:
        #         data = s.recv(PIECE_SIZE)
        #         # print(data)
        #         if data[-5:] == b"<END>":
        #             done = True
        #             file_bytes += data[:-5]
        #         else:
        #             file_bytes += data
        #         progress.update(PIECE_SIZE)
        #         # input("wait")

        #     with self.part_data_lock:
        #         part_data.append((start, file_bytes))
        #         s.send("done".encode())

        #     # file.write(file_bytes)

        # except Exception as e:
        #     print(f"Error in download_file: {e}")
        # finally:
        #     s.close()

    
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
            # print(data)
            if data:
                parts = data.split('*')  # Split the received data by ':'
                if len(parts) == 4:
                    filename, start_str, end_str, hash = parts
                    print(f"Filename: {filename}, hash: {hash}")
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
            # #self.print_container()
            path=""
            for c in self.container:
                if(isinstance(c, Folder)):
                    file = c.get_file(filename)
                    if(file is not None):
                        print(file.name)
                        print(file.path)
                        if(file.file_hash == hash):
                            path = file.path
                            break
                else:
                    if(filename in c.name and hash == c.file_hash):
                        print(c.name)
                        print(c.path)
                        path = c.path
                        break
                # if(filename)
                # if f.get_name() in (filename):
                # file_size = os.path.getsize(filename)
                # client_socket.sendall(f"{filename:<PIECE_SIZE}".encode())
                # client_socket.sendall(f"{file_size:<PIECE_SIZE}".encode())
                    # path = os.path.join(SHARE_PATH, f)
            print(c.path)
            with open(path, 'rb') as file:
                file.seek(start)
                numbytes = end - start
                buffer_size = PIECE_SIZE
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
                # file.seek(start)
                # numbytes = end - start

                # #####
                # data = file.read(numbytes)
                # # print(data)
                # client_socket.sendall(data)
                # #####

                # print("end")
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

    def normalize_path(self, path):
        return os.path.normpath(path).replace('\\', "/")

    def create_metainfo(self, file_paths):
        metainfo = []
        # files = []
        container = []

        file_paths = file_paths.split(",")

        for file_path in file_paths:
            # Check if the input path is a file or a directory
            # file_path = self.normalize_path(file_path)
            # print(file_path)
            # print(SHARE_PATH)
            file_path = self.normalize_path(os.path.abspath(file_path))

            print(file_path)
            if os.path.isdir(file_path):
                # Multiple-file mode
                temp_path = os.path.basename(file_path)
                # dir_path = os.path.dirname(file_path)
                # print(temp_path)
                # print(1)
                # print(os.path.dirname(file_path))
                # print(2)
                # print(os.path.realpath(file_path))
                # print(3)
                # print(os.path.relpath(file_path))
                # print(4)
                # print(os.path.abspath(file_path))
                # print(5)
                # # print(os.path.commonpath(os.p(file_path)))
                # # print(6)
                # print(os.path.normpath(file_path))
                # print(7)

                folder = Folder(path=file_path, name=temp_path)
                print_tree(folder)
                

                # try:
                #     # print(1)
                #     if(temp_path.find(":") > -1):
                #         # print(2)
                #         temp_path = self.normalize_path(temp_path)
                #         slash_id = temp_path.rindex('/')

                #         temp_path = temp_path[slash_id + 1:]
                # except Exception as e:
                #     print(e)
                # sizes = []
                # pieces = []
                # hashes = []
                
                # for root, dirnames, filenames in os.walk(file_path):
                #     print(root)
                #     print(dirnames)
                #     print(filenames)
                #     rel_path = self.normalize_path(os.path.relpath(root, dir_path))
                #     print(rel_path)
                #     for dirname in dirnames:
                #         print(dirname)
                #         # if(temp_path == os.path.basename(root)):
                #         #     rel_path = temp_path
                #         # else:
                        
                        
                #             # + os.path.dirname()
                #         cont = Container(name=rel_path + f"/{dirname}", type="folder", path=self.normalize_path(os.path.join(root, dirname)))
                #         container.append(cont.toJSON())
                #         self.container.append(cont)

                #     for filename in filenames:
                #         print("-----\n")
                #         print(filename)
                #         file_abs_path = os.path.join(root, filename)
                #         # print(file_abs_path)
                #         file_abs_path = self.normalize_path(file_abs_path)
                #         # file_abs_path.replace('\\', "/")
                        
                #         # file_rel_path = os.path.relpath(file_abs_path, file_path)
                #         file_rel_path = rel_path + f"/{filename}"
                #         # file_rel_path = self.normalize_path(file_rel_path)
                        
                #         # try:
                #         #     # print(1)
                #         #     if(file_rel_path.find(":") > -1):
                #         #         # print(2)
                #         #         slash_id = file_rel_path.rindex('/')

                #         #         file_rel_path = file_rel_path[slash_id + 1:]
                #         # except Exception as e:
                #         #     print(e)
                #         print(file_abs_path)
                #         print(file_rel_path)

                        

                #         file_size = os.path.getsize(file_abs_path)
                #         # files.append(file_rel_path)
                #         # sizes.append(file_size)
                #         hash = self.create_hash_file(file_abs_path)
                #         # hashes.append(hash)

                #         cont = Container(name=file_rel_path, type="file", hash=hash,path=file_abs_path, size=file_size, pieces=math.ceil(file_size/PIECE_SIZE))

                #         # self.files.append(file_abs_path)
                #         container.append(cont.toJSON())
                #         self.container.append(cont)
                #         # print(self.files)
                #         # self.sizes.append(file_size)
                #         # self.hashes.append(hash)

                #         # pieces.append(math.ceil(file_size/PIECE_SIZE))

                self.container.append(folder)
                metainfo.append({
                    'folder': True,
                    'container': folder
                    # 'container': folder.toJSON()
                    # 'name': temp_path,
                    # 'type': 'folder',
                    # 'files': files, #['b.txt','temp.png']
                    # 'sizes': sizes, #[23,1500]
                    # 'num_pieces': pieces, #[1,2]
                    # 'hashes': hashes 
                })
            
            elif os.path.isfile(file_path):
                file = File(file_path)
                # print_tree(file)
                # file_path = os.path.abspath(file_path)

                # file_path = self.normalize_path(file_path)

                # size = os.path.getsize(file_path)
                # # files.append(('', size))
                # hash = self.create_hash_file(file_path)

                # # try:
                # #     # print(1)
                # #     if(file_path.find(":") > -1):
                # #         file_path = self.normalize_path(file_path)
                # #         # print(2)
                # #         slash_id = file_path.rindex('/')

                # #         file_path = file_path[slash_id + 1:]
                # # except Exception as e:
                # #     print(e)
                
                # cont = Container(name=os.path.basename(file_path), type="file", size=size, hash=hash,path=file_path, pieces=math.ceil(size/PIECE_SIZE))
                # self.container.append(cont)
                # self.sizes.append(size)
                # self.hashes.append(hash)

                # num_piece = math.ceil(size/PIECE_SIZE)
                self.container.append(file)
                metainfo.append({
                    'folder': 'False',
                    'container': file
                    # 'container': file.toJSON()
                    # 'name': '',
                    # 'type': 'file',
                    # 'files': file_path,
                    # 'sizes': size,
                    # 'num_pieces': num_piece,
                    # 'hashes': hash
                })

            else:
                # invalid = True
                print("Invalid input path.")
                return None

            #self.print_container()
            files = []
        return metainfo
    
    def update_file_list(self):
        for c in self.container:
            # print(c.path)
            # print("???????????")
            # print(os.path.abspath(DOWNLOAD_PATH))
            c.set_path(os.path.abspath(DOWNLOAD_PATH))
            c.change_status("Downloaded")
            # print(c.path)
    
    def request_file_list(self):
        message = json.dumps({'command': 'list'})
            
        self.client_to_tracker.send(message.encode())
        
        response = self.client_to_tracker.recv(PIECE_SIZE)
        
        share_list = pickle.loads(response)

        for share in share_list:
            try:
                print(share.name)
                id = self.container.index(share)
                print(id)
                if(id > -1):
                    share.change_status("Downloaded")
            except Exception as e:
                print(e)
                share.change_status("")
                share.remove_path()
            # print(share.name)
            # print(share.status)
            # print(share.path)
            # print("-------")
        return share_list
    
    def upload_folder(self, folder: Folder): #TODO: Gửi folder lên tracker
        message = json.dumps({'command': 'upload'}).encode()
        # print(message)
        self.client_to_tracker.send(message)
        res = self.client_to_tracker.recv(PIECE_SIZE).decode()
        if(res == "received"):

            message = pickle.dumps({'metainfo': folder})
            # print(message)
            self.client_to_tracker.sendall(message)

            # print(1)
            flag = self.client_to_tracker.recv(1024).decode()
            # print(2)
            # print(flag)
            if(flag == "True"):
                self.container.append(folder)
            self.client_to_tracker.send("a".encode())
        
    
    def upload_file (self, file: File): #TODO: GỬI FILE
        message = json.dumps({'command': 'upload'}).encode()
        # print(message)
        self.client_to_tracker.send(message)
        res = self.client_to_tracker.recv(PIECE_SIZE).decode()
        if(res == "received"):

            message = pickle.dumps({'metainfo': file})
            # print(file.file_hash)
            self.client_to_tracker.sendall(message)
            # print(1)
            flag = self.client_to_tracker.recv(1024).decode()
            # print(2)
            # print(flag)
            if(flag == "True"):
                self.container.append(file)
            self.client_to_tracker.send("a".encode())

    def request_download_file(self, file_name: str, hash: str):
        # share_list = self.request_file_list()
        # temp_list = []
        # hash_list = []
        # out = False
        # # for c in self.container:
        # for c in share_list:
        #     print(c.name)
        #     print(c.status)
        #     print(c.path)
        #     # if(c.status == "Downloaded"):
        #     #     if(folder_name in c.name or (isinstance(c, Folder) and c.get_subfolder(folder_name) is not None)):
        #     #         out = True
        #     #         break
        #     # else:
        #     if(file_name in c.name):
        #         if(c.status == "Downloaded"):
        #             out = True
        #             break
        #         else:
        #             temp_list.append(file_name)
        #             hash_list.append(c.file_hash)
                
        #     else:
        #         if (isinstance(c, Folder)):
        #             path = c.get_file(file_name)
        #             if(path.status == "Downloaded"):
        #                 out = True
        #                 break
        #             if(path is not None):
        #                 temp_list.append(file_name)
        #                 hash_list.append(path.file_hash)
        
        # if(out):
        #     print(f"You already have {file_name}.")
        #     return
        
        self.manage_downloads([file_name], [hash])
    
    def request_download_folder(self, folder_name:str):
        path = os.path.join(DOWNLOAD_PATH, folder_name)
        # print(path)
        # print(os.path.exists(path))
        if(os.path.exists(path) == False):
            os.mkdir(path)

        share_list = self.request_file_list()
        temp_list = []
        hash_list = []
        out = False
        # for c in self.container:
        for c in share_list:
            print(c.name)
            print(c.status)
            print(c.path)
            # if(c.status == "Downloaded"):
            #     if(folder_name in c.name or (isinstance(c, Folder) and c.get_subfolder(folder_name) is not None)):
            #         out = True
            #         break
            # else:
            if(folder_name in c.name):
                if(c.status == "Downloaded"):
                    out = True
                    break
                else:
                    file_list = c.get_all_files()
                
            else:
                if (isinstance(c, Folder)):
                    path = c.get_subfolder(folder_name)
                    if(path.status == "Downloaded"):
                        out = True
                        break
                    if(path is not None):
                        file_list = path.get_all_files()
        if(file_list is not None):
            for f in file_list:
                temp_list.append(f.name)
                hash_list.append(f.file_hash)
        if(out):
            print(f"You already have {folder_name}.")
            return
            
        self.manage_downloads(temp_list, hash_list)
        # peer_req = self.request_peerS_info(folder_name)
        # print(peer_req)
        # for p in peer_req['peers']:
        #     temp_list.append(p['file'])
        # filename.remove(file)

    def sen_process(self, data, q):
        global_response = ""
        
        cmd_id = data.find(" ")

        if(cmd_id < 0):
            cmd = data
            remain_data = ""
        else:
            cmd = data[:cmd_id].strip().lower()
            remain_data = data[cmd_id + 1:]
        
        print(cmd)
        print(remain_data)
        if cmd == "help":
            message = json.dumps({'command': 'help'})
            
            self.client_to_tracker.send(message.encode())
            
            res = self.client_to_tracker.recv(PIECE_SIZE).decode()

            global_response = res
        elif cmd == "logout":
            message = json.dumps({'command': 'logout'})
            
            self.client_to_tracker.send(message.encode())
            
            res = self.client_to_tracker.recv(PIECE_SIZE).decode()
            
            global_response = res
            q.put(global_response)
            return
        elif cmd == "list":
            #self.print_container()
            
            share_list = self.request_file_list()
            for share in share_list:
                if(type(share) == File):
                    global_response += share.name
                else:
                    global_response += tree(share)
                global_response += "\n"
            
            print(share_list)

            self.container = share_list

            # for c in self.container:
            #     print(f"{c.name} - {c.status}")
            
            # for c in share_list:
            #     print(f"{c.name} - {c.status}")

            # message = json.dumps({'command': 'list'})
            
            # self.client_to_tracker.send(message.encode())
            
            # response = self.client_to_tracker.recv(1024).decode()
            
            # peer_list = json.loads(response)
            
            # # self.response = peer_list
            # global_response = peer_list
            # print(peer_list)
        elif cmd == "upload":
            file_paths = remain_data

            # metainfo = []
            # files = []
            # container = []

            file_paths = file_paths.split(",")

            for file_path in file_paths:
                # Check if the input path is a file or a directory
                # file_path = self.normalize_path(file_path)
                # print(file_path)
                # print(SHARE_PATH)
                file_path = self.normalize_path(os.path.abspath(file_path))

                print(file_path)
                if os.path.isdir(file_path):
                    # Multiple-file mode
                    temp_path = os.path.basename(file_path)
                    folder = Folder(path=file_path, name=temp_path)
                    # print(folder.files)
                    print_tree(folder)
                    self.upload_folder(folder)
                    
                    
                    # metainfo.append({
                    #     'folder': True,
                    #     'container': folder
                    # })
                
                elif os.path.isfile(file_path):
                    file = File(file_path)
                    self.upload_file(file)

                    # metainfo.append({
                    #     'folder': 'False',
                    #     'container': file
                    # })

                else:
                    print("Invalid input path.")
                    continue
                response = self.client_to_tracker.recv(PIECE_SIZE).decode()
                print(response)
                #self.print_container()
                # files = []
            # return metainfo

            
            # self.response = response
            global_response = response

            # metainfo = self.create_metainfo(file_paths)
            
            # print(metainfo)
            # if metainfo is not None:
            #     message = json.dumps({'command': 'upload'}).encode()
            #     # print(message)
            #     self.client_to_tracker.send(message)
            #     if(self.client_to_tracker.recv(PIECE_SIZE).decode() == "received"):

            #         message = pickle.dumps({'metainfo': metainfo})
            #         # print(message)
            #         self.client_to_tracker.sendall(message)

            #         response = self.client_to_tracker.recv(1024).decode()
            #         # self.response = response
            #         global_response = response
            
        elif cmd == "download":
            filename = remain_data.split("*")[0]
            # filename = filename.split("")

            # peerIp = data[2]
            # peerport = data[3]

            filename = filename.split(",")
            try:
                hash_list = remain_data.split("*")[1]
                hash_list = hash_list.split(",")
            except:
                print("No hash input")
                hash_list = []
                
            # share_list = self.request_file_list()
            
            temp_list = []
            remove_list = []
            out = False
            print(filename)
            for file in filename:
                print(file)
                print(1)
                if(file[-1:] == "/"):
                    # for c in self.container:
                    for c in self.container:
                        print(2)
                        print(c.name)
                        print(c.status)
                        print(c.path)
                        # if(c.status == "Downloaded"):
                        #     if(file in c.name or (isinstance(c, Folder) and c.get_subfolder(file) is not None)):
                        #         out = True
                        #         break
                        # else:
                        file_list = None
                        if(file in c.name):
                            if(c.status == "Downloaded"):
                                out = True
                                break
                            else:
                                file_list = c.get_all_files()
                            
                        else:
                            if (isinstance(c, Folder)):
                                path = c.get_subfolder(file)
                                if(path is not None):
                                    if(path.status == "Downloaded"):
                                        out = True
                                        break
                                    file_list = path.get_all_files()
                        
                        if(file_list is not None):
                            print(4)
                            print(file_list)
                            for f in file_list:
                                # name = f.name
                                # root_folder = f.parent_folder
                                # temp_folder = f.parent_folder
                                # while root_folder is not None:
                                #     name = f"{root_folder.name}/{name}"
                                #     root_folder = temp_folder.parent_folder
                                #     temp_folder = root_folder
                                temp_list.append(f)
                                # hash_list.append(f.hash)
                            # print(file)
                            # print(filename)
                            # filename.remove(file)
                            remove_list.append(file)
                            break
                        

                                
                        # if(c.status == "Downloaded" and isinstance(c, Folder)):
                        #     if(c.get_subfolder(file) is not None):
                        #         out = True
                        #         break
                    print(3)
                    if(out):
                        # filename.remove(file)
                        remove_list.append(file)
                        print(f"You already have {file}.")
                        continue

                #     # self.request_download_folder(file)
                else:
                    print("????")
                    for c in self.container:
                    # for c in self.container:
                        print(c.name)
                        print(c.status)
                        print(c.path)
                        if(file in c.name):
                            if(c.status == "Downloaded"):
                                out = True
                                break
                            else:
                                # name = c.name
                                # root_folder = c.parent_folder
                                # temp_folder = c.parent_folder
                                # while root_folder is not None:
                                #     name = f"{root_folder.name}{name}"
                                #     root_folder = temp_folder.parent_folder
                                #     temp_folder = root_folder
                                temp_list.append(c)
                                remove_list.append(file)
                                # hash_list.append(c.file_hash)
                                break
                        else:
                            if(isinstance(c, Folder)):
                                path = c.get_file(file)
                                
                                if(path is not None):
                                    print(path.name)
                                    print(path.status)
                                    print(path.path)
                                    if(path.status == "Downloaded"):
                                        out = True
                                        break
                                    else:
                                        # name = c.name
                                        # root_folder = path.parent_folder
                                        # temp_folder = path.parent_folder
                                        # while root_folder is not None:
                                        #     name = f"{root_folder.name}{name}"
                                        #     root_folder = temp_folder.parent_folder
                                        #     temp_folder = root_folder
                                        temp_list.append(path)
                                        remove_list.append(file)
                                        # hash_list.append(path.file_hash)
                                        break

                            
                        # if(c.status == "Downloaded"):
                        #     if(file in c.name or (isinstance(c, Folder) and path is not None)):
                        #         out = True
                        #         break
                        # else:
                        # file_list = c.get_all_files()
                            # for f in file_list:
                            
                    print(out)
                    if(out):
                        # filename.remove(file)
                        remove_list.append(file)
                        print(f"You already have {file}.")
                        continue
                # if(file[-1:] == "/"):
                #     # for c in self.container:
                #     for c in share_list:
                #         print(2)
                #         print(c.name)
                #         print(c.status)
                #         print(c.path)
                #         # if(c.status == "Downloaded"):
                #         #     if(file in c.name or (isinstance(c, Folder) and c.get_subfolder(file) is not None)):
                #         #         out = True
                #         #         break
                #         # else:
                #         file_list = None
                #         if(file in c.name):
                #             if(c.status == "Downloaded"):
                #                 out = True
                #                 break
                #             else:
                #                 file_list = c.get_all_files()
                            
                #         else:
                #             if (isinstance(c, Folder)):
                #                 path = c.get_subfolder(file)
                #                 if(path is not None):
                #                     if(path.status == "Downloaded"):
                #                         out = True
                #                         break
                #                     file_list = path.get_all_files()
                        
                #         if(file_list is not None):
                #             print(4)
                #             print(file_list)
                #             for f in file_list:
                #                 # name = f.name
                #                 # root_folder = f.parent_folder
                #                 # temp_folder = f.parent_folder
                #                 # while root_folder is not None:
                #                 #     name = f"{root_folder.name}/{name}"
                #                 #     root_folder = temp_folder.parent_folder
                #                 #     temp_folder = root_folder
                #                 temp_list.append(f)
                #                 # hash_list.append(f.hash)
                #             # print(file)
                #             # print(filename)
                #             # filename.remove(file)
                #             remove_list.append(file)
                #             break
                        

                                
                #         # if(c.status == "Downloaded" and isinstance(c, Folder)):
                #         #     if(c.get_subfolder(file) is not None):
                #         #         out = True
                #         #         break
                #     print(3)
                #     if(out):
                #         # filename.remove(file)
                #         remove_list.append(file)
                #         print(f"You already have {file}.")
                #         continue

                # #     # self.request_download_folder(file)
                # else:
                #     print("????")
                #     for c in share_list:
                #     # for c in self.container:
                #         print(c.name)
                #         print(c.status)
                #         print(c.path)
                #         if(file in c.name):
                #             if(c.status == "Downloaded"):
                #                 out = True
                #                 break
                #             else:
                #                 # name = c.name
                #                 # root_folder = c.parent_folder
                #                 # temp_folder = c.parent_folder
                #                 # while root_folder is not None:
                #                 #     name = f"{root_folder.name}{name}"
                #                 #     root_folder = temp_folder.parent_folder
                #                 #     temp_folder = root_folder
                #                 temp_list.append(c)
                #                 remove_list.append(file)
                #                 # hash_list.append(c.file_hash)
                #                 break
                #         else:
                #             if(isinstance(c, Folder)):
                #                 path = c.get_file(file)
                                
                #                 if(path is not None):
                #                     print(path.name)
                #                     print(path.status)
                #                     print(path.path)
                #                     if(path.status == "Downloaded"):
                #                         out = True
                #                         break
                #                     else:
                #                         # name = c.name
                #                         # root_folder = path.parent_folder
                #                         # temp_folder = path.parent_folder
                #                         # while root_folder is not None:
                #                         #     name = f"{root_folder.name}{name}"
                #                         #     root_folder = temp_folder.parent_folder
                #                         #     temp_folder = root_folder
                #                         temp_list.append(path)
                #                         remove_list.append(file)
                #                         # hash_list.append(path.file_hash)
                #                         break

                            
                #         # if(c.status == "Downloaded"):
                #         #     if(file in c.name or (isinstance(c, Folder) and path is not None)):
                #         #         out = True
                #         #         break
                #         # else:
                #         # file_list = c.get_all_files()
                #             # for f in file_list:
                            
                #     print(out)
                #     if(out):
                #         # filename.remove(file)
                #         remove_list.append(file)
                #         print(f"You already have {file}.")
                #         continue

                    # self.request_download_file(file, hash_list)
                # check = self.normalize_path(os.path.abspath(file))
                # print(check)
                #check if file in self.container, if true, continue
                # path = ""
                # out = False

                # if(os.path.isabs(file)):
                #     print(1)
                #     for c in self.container:
                #         if(file in c.get_path()):
                #             out = True
                #             break

                #     print(out)
                #     if(out):
                #         # global_response = 
                #         print(f"You already have {file}.")
                #         continue

                #     if(os.path.isdir(file)):
                #         # if(os.path.isabs(file)):
                #         #     path = 
                #         path = os.path.join(DOWNLOAD_PATH, os.path.basename(file))
                #         # print(path)
                #         # print(os.path.exists(path))
                #         print(path)
                #         if(os.path.exists(path) == False):
                #             os.mkdir(path)
                #         peer_req = self.request_peerS_info(file)
                #         # print(peer_req)
                #         for p in peer_req['peers']:
                #             temp_list.append(p['file'])
                #         filename.remove(file)    
                # else:
                #     print(2)
                #     # for c in self.container:
                #     #     if(file in c.name):
                #     #         out = True
                #     #         break
                #     #     # print(file + f" {c.get_name()}")
                #     #     # if(file in c.get_name()):
                #     #         # out = True
                #     #         # break

                #     # if(out):
                #     #     # global_response = 
                #     #     print(f"You already have {file}.")
                #     #     continue

                #     if(os.path.isdir(file)):
                #         # if(os.path.isabs(file)):
                #         #     path = 
                #         path = os.path.join(DOWNLOAD_PATH, os.path.basename(file))
                #         # print(path)
                #         # print(os.path.exists(path))
                #         print(path)
                #         if(os.path.exists(path) == False):
                #             os.mkdir(path)
                #         peer_req = self.request_peerS_info(file)
                #         # print(peer_req)
                #         for p in peer_req['peers']:
                #             temp_list.append(p['file'])
                #         filename.remove(file)

                # for c in self.container:
                #     if(os.path.isabs(file)):
                #         if(file in c.get_path()):
                #             out = True
                #             break    
                #     else:
                #         if(check in c.get_name()):
                #             out = True
                #             break
                # print(out)
                # if(out):
                #     # global_response = 
                #     print(f"You already have {file}.")
                #     continue
                # print(path)
                # print(os.path.isdir(path))
                # print(os.path.isfile(path))
                
                # if(file[-1:] == "/"):
                #     path = os.path.join(DOWNLOAD_PATH, file)
                #     # print(path)
                #     # print(os.path.exists(path))
                #     print(path)
                #     if(os.path.exists(path) == False):
                #         os.mkdir(path)
                #     peer_req = self.request_peerS_info(file)
                #     # print(peer_req)
                #     for p in peer_req['peers']:
                #         temp_list.append(p['file'])
                #     filename.remove(file)

            # print(remove_list)
            for r in remove_list:
                filename.remove(r)
            # print(temp_list)
            for f in temp_list:
                # filename.append(f)                        
                name = f.name
                root_folder = f.parent_folder
                temp_folder = f.parent_folder
                # print("----")
                # print(name)
                # print(f.parent_folder)
                while root_folder is not None:
                    # print("----")
                    # print(name)
                    name = f"{root_folder.name}{name}"
                    
                    root_folder = temp_folder.parent_folder
                    temp_folder = root_folder
                filename.append(name)
                hash_list.append(f.file_hash)

            print(filename)
            print(hash_list)

            self.manage_downloads(filename, hash_list)
            self.update_file_list()
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
            q = queue.Queue()
            thrSen = threading.Thread(target=self.sen_process, args=(data, q))
            thrSen.start()
            # print("endloop")
            # print(self.response)
            answer = q.get()
            print(answer)
            if(answer == "Disconnected from the server."):
                break
    
    def download_file(self, file_name, part_data, file_hash=""):
        peer_info = self.request_peerS_info(file_name, file_hash)
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
                        thread = threading.Thread(target=self.download_piece, args=(ip_list[0], port_list[0], file_name, start_piece[i]*PIECE_SIZE, end_piece[i]*PIECE_SIZE, part_data, file_hash))
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
                            thread = threading.Thread(target=self.download_piece, args=(ip_list[0], port_list[0], file_name, start_piece[i]*PIECE_SIZE, end_piece[i]*PIECE_SIZE, part_data, file_hash))
                        else:
                            if lastpiece_size == 0:
                                thread = threading.Thread(target=self.download_piece, args=(ip_list[0], port_list[0], file_name, start_piece[i]*PIECE_SIZE, end_piece[i]*PIECE_SIZE, part_data, file_hash))
                            else:
                                thread = threading.Thread(target=self.download_piece, args=(ip_list[0], port_list[0], file_name, start_piece[i]*PIECE_SIZE, (end_piece[i]-1)*PIECE_SIZE + lastpiece_size, part_data, file_hash))
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
                        thread = threading.Thread(target=self.download_piece, args=(ip_list[i], port_list[i], file_name, start_piece[i]*PIECE_SIZE, end_piece[i]*PIECE_SIZE, part_data, file_hash))
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
                            thread = threading.Thread(target=self.download_piece, args=(ip_list[i], port_list[i], file_name, start_piece[i]*PIECE_SIZE, end_piece[i]*PIECE_SIZE, part_data, file_hash))
                        else:
                            if lastpiece_size == 0:
                                thread = threading.Thread(target=self.download_piece, args=(ip_list[i], port_list[i], file_name, start_piece[i]*PIECE_SIZE, end_piece[i]*PIECE_SIZE, part_data, file_hash))
                            else:
                                thread = threading.Thread(target=self.download_piece, args=(ip_list[i], port_list[i], file_name, start_piece[i]*PIECE_SIZE, (end_piece[i]-1)*PIECE_SIZE + lastpiece_size, part_data, file_hash))
                        threads.append(thread)
                        thread.start()
                        
                        # threading.Thread(target=peer.download_file, args=(ip_list[i], port_list[i], requested_file, start_byte[i], end_byte[i])).start()
            
            for thread in threads:
                thread.join()

            part_data.sort(key=lambda x: x[0])

            # data = b"".join([part[1] for part in part_data])
            # print(data)
            # sum_hash = self.create_hash_data(data)
            
            # print(sum_hash)
            # print(hash)

            # with part_data_lock:
            #     for i, result in enumerate(part_data):
            #         data += result
            
            try:
                if(file_hash == ""):
                    if file_hash == hash:
                        # with self.part_data_lock:
                        #     check = input(f"Do you want to rename {file_name}? Enter \"yes\" to rename, else press 'enter' again:")
                        #     if(check.strip().lower() == "yes"):
                        #         new_filename = input("Please enter other name:")
                        #         try:
                        #             slash_id = file_name.rindex('/')

                        #             file_name = file_name[:slash_id + 1] + new_filename
                        #         except:
                        #             file_name = new_filename
                            
                        path = os.path.join(DOWNLOAD_PATH, file_name)
                        print(path)
                        # path = self.normalize_path(path)
                        # print(os.path.isfile(path))
                        # print(os.path.dirname(path))

                        try:
                            if(os.path.exists(os.path.dirname(path)) == False):
                                os.mkdir(os.path.dirname(path))
                        except:
                            os.makedirs(os.path.dirname(path))
                        
                        with open(path, 'wb') as result_file:
                        # print(part_data)
                            for _ , file_bin in part_data:
                                # print(file_bin)
                                with open(file_bin, 'rb') as file_read:
                                    while True:
                                        chunk = file_read.read(PIECE_SIZE)
                                        # print(chunk)
                                        if not chunk:
                                            break
                                        else:
                                            piece_hash = hashlib.sha256(chunk).hexdigest()
                                            hash_sum += piece_hash
                                            result_file.write(chunk)
                                os.remove(file_bin)
                        result_file.close()
                        print(f"File {file_name} has been downloaded.")
                    else:
                        print(f"Hash difference.")
                else:
                    hash_sum = ""
                    # with self.part_data_lock:
                    #     check = input(f"Do you want to rename {file_name}? Enter \"yes\" to rename, else press 'enter' again:")
                    #     if(check.strip().lower() == "yes"):
                    #         new_filename = input("Please enter other name:")
                    #         try:
                    #             slash_id = file_name.rindex('/')

                    #             file_name = file_name[:slash_id + 1] + new_filename
                    #         except:
                    #             file_name = new_filename
                    path = os.path.join(DOWNLOAD_PATH, file_name)
                    print(path)
                    # path = self.normalize_path(path)
                    # print(os.path.isfile(path))
                    # print(os.path.dirname(path))
                    try:
                        if(os.path.exists(os.path.dirname(path)) == False):
                            os.mkdir(os.path.dirname(path))
                    except:
                        os.makedirs(os.path.dirname(path))
                    with open(path, 'wb') as result_file:
                        # print(part_data)
                        for _ , file_bin in part_data:
                            # print(file_bin)
                            with open(file_bin, 'rb') as file_read:
                                while True:
                                    chunk = file_read.read(PIECE_SIZE)
                                    # print(chunk)
                                    if not chunk:
                                        break
                                    else:
                                        piece_hash = hashlib.sha256(chunk).hexdigest()
                                        hash_sum += piece_hash
                                        result_file.write(chunk)
                            os.remove(file_bin)
                    result_file.close()

                    if(hash_sum == hash):
                        print(f"File {file_name} has been downloaded.")
                    else:
                        print(f"Hash difference.")
            except Exception as e:
                print(e)
            
        else:
            print("No peer found with the requested file.")

    def manage_downloads(self, requested_files, hash_list):
        threads = []
        # part_data = []

        for file_name in requested_files:
            # if(hash == ""):
            #     thread = threading.Thread(target=self.download_file, args=(file_name,[]))
            # else:
            thread = threading.Thread(target=self.download_file, args=(file_name,[], hash_list[requested_files.index(file_name)]))

            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        print(f"Download finish.")
        for speed in self.download_rates:
            print(speed[0]," ",speed[1], end='\n')
    
if __name__ == "__main__":
    TRACKER_IP = input("Please enter Tracker's IP you want to connect:")
    print(TRACKER_IP)
    TRACKER_PORT = input("Please enter port of the Tracker above:")
    print(TRACKER_PORT)
    # my_ip = sys.argv[1]

    my_port = input("Please enter your port number:")
    # files = []
    
    # if len(sys.argv) > 3:
    #     files = sys.argv[3].split(',')

    peer = Peer(TRACKER_IP, TRACKER_PORT, MY_IP, my_port)

    # if the peer need to download a file
    # if len(sys.argv) > 4:
    #     requested_files = sys.argv[4].split(',')
    #     peer.manage_downloads(requested_files)

    peer.sen()
    print("end")
    # sys.exit()