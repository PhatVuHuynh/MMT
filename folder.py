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
    def __init__(self, path, file_hash=None, name = None, parent_folder=None):
        path = path.replace("\\", "/")
        if not os.path.exists(path): raise InvalidPathError(f"The new path \"{path}\" is not a valid path.")
        if name is None: self.name = os.path.basename(path)
        else:            self.name = name
        
        self.path = path
        
        if file_hash is None:
            self.file_hash = self._calculate_hash(self.path)
        else:
            self.file_hash = file_hash
        self.parent_folder = parent_folder
        
        global test
        if test: print (f"CREATING file name \"{self.name}\" with the path \"{self.path}\"")
    
    def remove_path(self):
        self.path = None
    
    def set_path(self, new_path):
        # Normalize the new path and ensure it ends with a slash
        new_path = new_path.replace("\\", "/")
        # if not os.path.exists(new_path): raise InvalidPathError(f"The new path \"{new_path}\" is not a valid path.")
        new_path = os.path.join(os.path.normpath(new_path), '')
        
        # Update the file's path
        self.path = os.path.join(new_path, self.name)
        self.path = self.path.replace("\\", "/")
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
class Folder:
    def __init__(self, path, name = None, parent_folder=None):
        path = path.replace("\\", "/")
        if not os.path.isdir(path):
            raise InvalidPathError(f"The path \"{path}\" is not a valid directory.")
        
        if name is None: self.name = os.path.basename(os.path.normpath(path))
        else:            self.name = name
        
        self.path = path
        self.parent_folder = parent_folder
        self.child_folders = []
        self.files = []
        global test
        if test: print (f"CREATING folder name \"{self.name}\" with the path \"{self.path}\"")
        self._initialize_folder_structure()
    
    def _initialize_folder_structure(self):
        for root, dirs, files in os.walk(self.path):
            # Add folders
            for dir_name in dirs:
                folder_path = os.path.join(root, dir_name)
                folder = Folder(folder_path, parent_folder=self)
                self.add_folder(folder)
            
            # Add files
            for file_name in files:
                file_path = os.path.join(root, file_name)
                file_hash = self._calculate_hash(file_path)
                file = File(file_path, file_hash=file_hash,  name=file_name, parent_folder=self)
                self.add_file(file)

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
        new_path = new_path.replace("\\", "/")
        # if not os.path.isdir(new_path): raise InvalidPathError(f"The path \"{new_path}\" is not a valid directory.")
        new_path = os.path.join(os.path.normpath(new_path), '')
        # Update the folder's path
        self.path = os.path.join(new_path, self.name)
        self.path = self.path.replace("\\", "/")
        
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


def print_tree(folder:Folder, indent=''):
    # Print the current folder name
    print(f"{indent}{folder.name}/")
    new_indent = indent + '│   '

    # Print all the files in the current folder
    for file in folder.files:
        print(f"{new_indent}{file.name}")

    # Recursively print the child folders
    for i, child_folder in enumerate(folder.child_folders):
        # Check if this is the last child folder to adjust the tree branch symbol
        if i == len(folder.child_folders) - 1:
            sub_indent = indent + '    '
        else:
            sub_indent = indent + '│   '
        print_tree(child_folder, sub_indent)


test = False
if __name__ == "__main__":
    # test = True
    path = "C:/Users/tuankiet/Desktop/MMT/"
    my_folder = Folder(path)
    # my_folder.set_path("C:/")
    print_tree(my_folder)

