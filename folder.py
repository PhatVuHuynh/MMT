import socket, math
import json, hashlib
import threading, queue
import sys
import os
import tqdm

PIECE_SIZE = 2 ** 20

class InvalidPathError(Exception):
    pass

class File:
    def __init__(self, path:str, file_hash=None, name = None, parent_folder=None, status='Downloaded'):
        path = path.replace("\\", "/").strip()
        if not os.path.exists(path): raise InvalidPathError(f"The new path \"{path}\" is not a valid path.")
        if name is None: self.name = os.path.basename(path)
        else:            self.name = name
        
        self.path = path
        self.size = os.path.getsize(path)
        self.local_size = self.size
        
        if file_hash is None:
            self.file_hash = self._calculate_hash(self.path)
        else:
            self.file_hash = file_hash
            
        self.parent_folder = parent_folder
        self.status = status #downllaoed, '' downnloading (80%)
        
        global test
        if test: print (f"CREATING file name \"{self.name}\" with the path \"{self.path}\" in parent \"{self.parent_folder.name}\"")
    
    def remove_path(self):
        self.path = None
    
    def set_path(self, new_path):
        # Normalize the new path and ensure it ends with a slash
        new_path = new_path.replace("\\", "/").strip()
        # if not os.path.exists(new_path): raise InvalidPathError(f"The new path \"{new_path}\" is not a valid path.")
        new_path = os.path.join(os.path.normpath(new_path), '')
        
        # Update the file's path
        self.path = os.path.join(new_path, self.name)
        self.path = self.path.replace("\\", "/").strip()
        global test
        if test: print (f"The file name \"{self.name}\" now has the path \"{self.path}\"")
    def _calculate_hash(self, file_path) -> str:
        hash_sum = ""
        with open(file_path, 'rb') as file:
            piece_offset = 0
            piece = file.read(PIECE_SIZE)
            while piece:
                piece_hash = hashlib.sha256(piece).hexdigest()
                hash_sum += piece_hash
                piece_offset += len(piece)
                piece = file.read(PIECE_SIZE)
        return hash_sum
    
    def detach_parent(self):
        if self.parent_folder:
            self.parent_folder.files.remove(self)
            self.parent_folder = None
class Folder:
    def __init__(self, path:str, name = None, parent_folder=None, status ="Downloaded"):
        path = path.replace("\\", "/").strip()
        if not os.path.isdir(path):
            raise InvalidPathError(f"The path \"{path}\" is not a valid directory.")
        
        if name is None: self.name = os.path.basename(os.path.normpath(path))
        else:            self.name = name
        
        self.size = 0
        self.local_size = 0
        self.path = path
        self.parent_folder = parent_folder
        self.child_folders = []
        self.files = []
        self.status = status
        global test
        if test: print (f"CREATING folder name \"{self.name}\" with the path \"{self.path}\"")
        self._initialize_folder_structure()
    
    def _initialize_folder_structure(self):
        for root, dirs, files in os.walk(self.path):
            # Skip files if the current root is not the folder's path
            if os.path.normpath(root) != os.path.normpath(self.path):
                continue

            # Add folders
            for dir_name in dirs:
                folder_path = os.path.join(root, dir_name)
                folder = Folder(folder_path, parent_folder=self, status=self.status)
                self.add_folder(folder)
            
            # Add files
            for file_name in files:
                file_path = os.path.join(root, file_name)
                file_hash = self._calculate_hash(file_path)
                file = File(file_path, file_hash=file_hash,  name=file_name, parent_folder=self, status=self.status)
                self.add_file(file)
                
        self.size = sum(file.size for file in self.files) + sum(folder.size for folder in self.child_folders)
        self.local_size = 0 + self.size
    
    def add_file(self, file):
        file.path = f"{self.path}/{file.name}"
        file.parent_folder = self
        self.files.append(file)

    def add_folder(self, folder):
        folder.path = f"{self.path}/{folder.name}"
        folder.parent_folder = self
        self.child_folders.append(folder)

    def remove_path(self):
        # Set the folder's path to None
        self.path = None
        # Set the path of each file in this folder to None
        for file in self.files:
            file.remove_path()
        # Recursively set the path of each child folder to None
        for folder in self.child_folders:
            folder.remove_path()
    
    def set_path(self, new_path):
        # Normalize the new path and ensure it ends with a slash
        new_path = new_path.replace("\\", "/").strip()
        # if not os.path.isdir(new_path): raise InvalidPathError(f"The path \"{new_path}\" is not a valid directory.")
        new_path = os.path.join(os.path.normpath(new_path), '')
        # Update the folder's path
        self.path = os.path.join(new_path, self.name)
        self.path = self.path.replace("\\", "/").strip()
        
        global test
        if test: print (f"The folder name \"{self.name}\" now has the path \"{self.path}\"")
        
        # Update the paths of all files in this folder
        for file in self.files:
            file.set_path(self.path)
        
        # Recursively update the paths of all child folders
        for folder in self.child_folders:
            folder.set_path(self.path)
    
    def _calculate_hash(self, file_path)->str:
        hash_sum = ""
        with open(file_path, 'rb') as file:
            piece_offset = 0
            piece = file.read(PIECE_SIZE)
            while piece:
                piece_hash = hashlib.sha256(piece).hexdigest()
                hash_sum += piece_hash
                piece_offset += len(piece)
                piece = file.read(PIECE_SIZE)

        return hash_sum

    def get_subfolder(self, subfolder_path: str):
        subfolder_path = subfolder_path.replace("\\", "/").strip().rstrip('/')
        subfolder_names = subfolder_path.split("/")
        current_folder = self

        for subfolder_name in subfolder_names:
            found_subfolder = None
            for folder in current_folder.child_folders:
                if folder.name == subfolder_name:
                    found_subfolder = folder
                    break

            if found_subfolder:
                current_folder = found_subfolder
            else:
                return None  # Subfolder not found

        if isinstance(current_folder, Folder):
            return current_folder
        else: 
            return None
        
    def get_file(self, file_path:str, hash=None):
        if file_path:
            file_path = file_path.replace("\\", "/").strip()
            if file_path != file_path.rstrip('/'): return None
            
            parts = file_path.split('/')
            file_name = parts[-1]
            subfolder_names = parts[:-1]

            # Traverse the subfolders
            current_folder = self
            for subfolder_name in subfolder_names:
                found = False
                for folder in current_folder.child_folders:
                    if folder.name == subfolder_name:
                        current_folder = folder
                        found = True
                        break
                if not found:
                    return None  # Subfolder not found

            # Look for the file in the final subfolder
            for file in current_folder.files:
                if (file.name == file_name) and isinstance(file, File) and ((hash is None) or (file.file_hash == hash)):
                    return file  # File found

            return None 
        elif hash:
            for file in self.files:
                if file.file_hash == hash:
                    return file

            # Recursively check all subfolders
            for folder in self.child_folders:
                found_file = folder.get_file(file_path=None, hash=hash)
                if found_file:
                    return found_file

            return None


    def detach_parent(self):
        if self.parent_folder:
            self.parent_folder.child_folders.remove(self)
            self.parent_folder = None

def tree(folder:Folder, indent='')->str:
    lines = []  # List to hold the lines of the folder structure

    # Function to add lines to the list
    def add_line(text):
        lines.append(text)

    # Recursive function to build the folder structure
    def build_tree(folder:Folder, indent=''):
        add_line(f"{indent}{folder.name}/")
        new_indent = indent + '│   '

        for file in folder.files:
            add_line(f"{new_indent}{file.name}")

        for i, child_folder in enumerate(folder.child_folders):
            if i == len(folder.child_folders) - 1:
                sub_indent = indent + '    '
            else:
                sub_indent = indent + '│   '
            build_tree(child_folder, sub_indent)

    build_tree(folder)  # Start building the tree from the root folder
    return '\n'.join(lines)  # Join all the lines into a single string and return




test = False
if __name__ == "__main__":
    # test = True
    path = "C:/Users/tuankiet/Desktop/MMT"
    my_folder = Folder(path)
    # my_folder.set_path("C:/")
    # print(tree(my_folder))

    
    file = my_folder.get_file("download/peer_data/New folder/New folder/New folder/New folder/text.txt")
    if file: print(file.path)
    else: print ("not found")
