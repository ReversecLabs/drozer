import os
import shutil
import sys
import zipfile

from xml.etree import ElementTree as xml

from reversec.common import fs

class RepositoryBuilder(object):
    """
    RepositoryBuilder converts Python packages into drozer Module Repositories.
    """
    
    __banned_folders = [".git"]
    
    def __init__(self, source, target):
        self.source = source
        self.target = target
    
    def build(self):
        """
        Build the module repository.
        """
        
        if os.path.exists(self.target):
            print("The selected target (%s) already exists. Do you want to overwrite it?" % self.target)
            if input().lower() == "y":
                shutil.rmtree(self.target)
            else:
                sys.exit(-1)
            
        print("Creating target...")
        os.mkdir(self.target)
        
        print("Preparing INDEX file...")
        index = xml.Element("repository")
        
        print("Writing modules...")
        for source in self.__find_sources():
            print("Processing %s (%s)..." % (source.name(), source.type()))
            
            source.emit(self.target)
            
            source.add_to_index(index)
        
        print("Generating INDEX file...")
        xml.ElementTree(index).write(os.path.sep.join([self.target, "INDEX.xml"]))
        
        print("Done.")
    
    def __find_sources(self):
        """
        Searches the source folder, to identify source files and packages, and
        isolate them ready for building.
        """
        
        for root, folders, files in os.walk(self.source):
            self.__skip_folders(folders)
            
            if ".drozer_package" in files:
                yield SourcePackage(self.source, root, files)
            else:
                for f in files:
                    if f.endswith(".py") and not f == "__init__.py":
                        yield SourceFile(self.source, os.sep.join([root, f]))
    
    def __skip_folders(self, folders):
        """
        Remove folders that should be skipped from the a collection.
        """
        
        for f in self.__banned_folders:
            if f in folders:
                folders.remove(f)
                

class Source(object):
    """
    A Source represents a drozer Module identified for packaging by the Repository
    Builder.
    """
    
    def __init__(self, root, path):
        self.root = root
        self.path = path
    
    def add_to_index(self, index):
        """
        Add this source file to the specified XML index (passed in as an eTree).
        """
        
        module = xml.Element("module")
        module.attrib["name"] = self.name()
        description = xml.Element("description")
        description.text = self.description()
        module.append(description)
        index.append(module)
    
    def name(self):
        """
        Get the name of this module, by flattening the directory structure into
        a Python module path.
        """
        
        relative_path = self.path.endswith(".py") and self.path[len(self.root)+1:-3] or self.path[len(self.root)+1:]
        
        return relative_path.replace(os.path.sep, ".")
    
    
class SourceFile(Source):
    """
    A SourceFile represents a drozer Module for packaging, where it is contained
    within a single Python source file.
    """
    
    def description(self):
        """
        Fetch the human-readable description of this module, by extracting the first
        multi-line comment.
        """
        
        delim = "\"\"\""
        source = fs.read(self.path).decode('utf-8')
        
        if delim in source:
            start_idx = source.index(delim) + len(delim)
            finish_idx = source.index(delim, start_idx)
            
            return source[start_idx:finish_idx].strip()
        else:
            return ""
    
    def emit(self, target):
        """
        Copy this SourceFile into a remote repository structure, at target.
        """
        
        shutil.copyfile(self.path, os.path.sep.join([target, self.name()]))
    
    def type(self):
        """
        This Source is a 'file'.
        """
        
        return "file"
    
    def __str__(self):
        return "[+] %s is a source" % (self.name())


class SourcePackage(Source):
    """
    A SourceFile represents a drozer Module for packaging, where it is contained
    within a Python package, with a .drozer_module file.
    """
    
    def __init__(self, root, path, contents):
        Source.__init__(self, root, path)
        
        self.contents = contents
    
    def description(self):
        """
        Fetch the human-readable description of this module, from the .drozer_module
        file.
        """
        
        return fs.read(os.path.join(self.path, ".drozer_package")).strip()
        
    def emit(self, target):
        """
        Copy this SourcePackage into a remote repository structure, at target.
        """
        
        archive = zipfile.ZipFile(os.path.sep.join([target, self.name()]), 'w')
        
        for base, dirs, files in os.walk(self.path):
            for f in files:
                print(" - adding %s to the archive..." % f)
                
                filename = os.path.join(base, f)
                archive.write(filename, filename[len(self.path):])
        
        archive.close()
    
    def type(self):
        """
        This Source is a 'package'.
        """
        
        return "package"
    
    def __str__(self):
        return "[+] %s is a package:\n    %s" % (self.name(), "\n    ".join(self.contents))
        
