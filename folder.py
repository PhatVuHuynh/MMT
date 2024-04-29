import os

class InvalidPathError(Exception):
    pass

class File:
    def __init__(self, path, file_hash, name = None, parent_folder=None):
        path = path.replace("\\", "/")
        if name is None: self.name = os.path.basename(path)
        else:            self.name = name
        
        self.path = path
        self.file_hash = file_hash
        self.parent_folder = parent_folder
        
        global test
        if test: print (f"Creating file NAME: {self.name} with the FULL PATH: {self.path}")

class Folder:
    def __init__(self, path, name = None, parent_folder=None):
        path = path.replace("\\", "/")
        if not os.path.isdir(path):
            raise InvalidPathError(f"The path {path} is not a valid directory.")
        
        if name is None: self.name = os.path.basename(os.path.normpath(path))
        else:            self.name = name
        
        self.path = path
        self.parent_folder = parent_folder
        self.child_folders = []
        self.files = []
        global test
        if test: print (f"Creating folder NAME: {self.name} with the FULL PATH: {self.path}")
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
                file = File(file_path, file_hash,  name=file_name, parent_folder=self)
                self.add_file(file)

    def add_file(self, file):
        file.path = f"{self.path}/{file.name}"
        file.parent_folder = self
        self.files.append(file)

    def add_folder(self, folder):
        folder.path = f"{self.path}/{folder.name}"
        folder.parent_folder = self
        self.child_folders.append(folder)

    

    def _calculate_hash(self, file_path):
        # Placeholder for hash calculation logic
        return "hash_placeholder"

test = False
if __name__ == "__main__":
    test = True
    # my_folder = Folder(r"C:\Users\tuankiet\Google Drive\Study in HCMUT\232\Software Engineering")
    path = "C:/Users/tuankiet/Desktop/MMT/"
    
    print(path)
    my_folder = Folder(path)

