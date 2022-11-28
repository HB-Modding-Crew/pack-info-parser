from __future__ import annotations
from pathlib import Path
import re
from broken_path import repair_path
import globvar
import logging
import shutil
from PathMachine import PathMachine
from mylog import display
from config.config import PROPERTY_CONFIG

# Regex to match a path
regex_path = re.compile(r"(?:(?:[A-Z]:[/\\])|(?:[/\\]?))(?:[^\n\r><:*\"/\\|?]*[/\\]?)")

# Bad path root in content regex
bad_path_root = re.compile(r"~\/")
bad_path_root_alt = re.compile(r"~\\")

# Files extensions to consider as resources
exts = [".properties", ".mcmeta", ".png", ".json", ".jemc", ".jem", ".jpm", ".jpmc"]

class File:

    file_dict = {}

    def __init__(self, path: Path):
        # Path variable
        self._packRelativePath = path.resolve()
        self.path = PathMachine.transformPathToSystemPath(self._packRelativePath)

        # Parent directory
        self._packRelativeParent = self._packRelativePath.parent

        # Add the file to the file dictionary
        File.addFile(self)

    # Method to add a file to the file dictionary
    @classmethod
    def addFile(cls, file: File):
        """_summary_

        Args:
            file (_type_): A file object
        """

        # Add the file to the file dictionary
        cls.file_dict[str(file._packRelativePath)] = file

    # Length of the path
    def __len__(self):
        return len(str(self._packRelativePath))

    # Generic findReferences method
    def handleReferences(self):
        pass

    # Generic rewrite method
    def rewrite(self):
        pass

    # File name
    @property
    def name(self):
        return self._packRelativePath.name

    # Correct name
    @property
    def correctName(self):
        return repair_path(self.name).name

    # Correct path relative to the pack
    @property
    def correctPackRelativePath(self) -> Path:
        return repair_path(self._packRelativePath)

    # Correct path relative to the pack
    @property
    def correctNameRealPath(self) -> Path:
        return self.path.parent / self.correctName

    # Verify if the name of the file is correct
    def isNameCorrect(self):
        return self.name == self.correctName

    # Move to the correct name path
    def renameForCorrectPath(self):
        shutil.move(str(self.path), str(self.correctNameRealPath))

class PropertyFile(File):

    def __init__(self, path: Path):
        # Call the super class constructor
        super().__init__(path)

        # Dictionary of properties
        self.parse()

    # Verify if property can contain a path
    def possiblePathProperty(self, key: str):
        # Check if the key is in the non path properties
        for non_path in PROPERTY_CONFIG.non_path_properties:
            # If the non_path is a regex
            if PROPERTY_CONFIG.non_path_properties[non_path] and re.match(non_path, key):
                # Return false
                return False
            elif key == non_path:
                # Return false
                return False
        # Return true
        return True

    # Get expected extensions for a key
    def getExpectedExtensions(self, key: str):
        # Check if the key is in the expected extensions
        for expected_extension in PROPERTY_CONFIG.properties_expected_extensions:
            # If match
            if re.match(expected_extension, key):
                # Return the expected extensions
                return PROPERTY_CONFIG.properties_expected_extensions[expected_extension]
        # Return empty list
        return []

    # Get all the values in the file
    def parse(self):
        """_summary_

        Returns:
            dict: A dictionary containing all the properties
        """

        # Dictionary of properties
        self._properties = {}

        # Read the file
        with open(self.path, "r", encoding="ISO-8859-1") as f:
            content = f.read()

        # Loop through all the lines
        for line in content.splitlines():
            try:
                # If the line is a comment or empty
                if line.strip().startswith("#") or line.strip().startswith("#"):
                    # Skip the comment
                    continue
                elif not line.strip():
                    # Skip empty lines
                    continue
                # Split the line into key and value
                key = line.split("=")[0]
                value = '='.join(line.split("=")[1:])
                # If key or value is empty
                if not key or not value:
                    # Skip the line
                    continue
                # Add the key and value to the dictionary
                self._properties[key.strip()] = value.strip()
            except:
                print("Error reading line: " + line + " in file: " + str(self.path) + ". Skipping line because it's not recognized as property.", fflush=True)
                logging.warning("Error reading line: " + line + " in file: " + str(self.path) + ". Skipping line because it's not recognized as property.")

    # Find all the references in the file and add them to the references list
    def handleReferences(self):
        """_summary_
        """
        # If file in excluded paths
        for excluded_path in PROPERTY_CONFIG.excluded_pack_paths:
            if re.match(excluded_path, str(self._packRelativePath)):
                # Log
                display("Skipping file: " + str(self._packRelativePath) + " because it's in the excluded paths list.", "info")
                # Skip file
                return
        # Log
        display("Finding references in property file: " + str(self._packRelativePath), "info")
        # Loop through all the properties
        for key, value in self._properties.items():
            # If the key is a non path property
            if not self.possiblePathProperty(key):
                continue
            # Log
            display("Checking property: " + key, "info")
            # Get expected extensions
            expected_extensions = self.getExpectedExtensions(key)
            # If no expected extensions
            if not expected_extensions and expected_extensions != None:
                # Warn
                display("Exepected extensions are not defined for key: '" + key + "' . Even if it does not break the process, it will be less precise. Contact the developper to add expected extensions.", "warning")
            # If the value is not a path, warning
            if not regex_path.match(value) and (expected_extensions or expected_extensions == None):
                display("Value: '" + value + "' for property '" + key + " is not a path.", "warning")
                continue
            
            # Try to resolve the path
            display("Resolving path: " + value + " for property: " + key, "info")
            path = PathMachine.resolvePath(Path(value), self._packRelativePath, expected_extensions)

            # If the path is not None, warn and continue
            if path == None:
                display("Path: '" + value + "' for property '" + key + "' can't be resolved.", "warning")
                continue
            else:
                display("Path: '" + value + "' for property '" + key + "' resolved to: " + str(path), "info")

            # Try to convert to relative path
            relative_path = PathMachine.getRelativePath(self._packRelativePath, path)
            if relative_path == None:
                display("Path: '" + str(path) + "' for property '" + key + "' can't be converted to good relative path, continue with absolute.", "info")
            else:
                display("Path: '" + str(path) + "' for property '" + key + "' converted to relative path: " + str(relative_path), "info")
                path = relative_path

            # If the path had no extension
            if not Path(value).suffix:
                # Remove the extension of the path
                path = Path(path).with_suffix("")

            # Repair broken path
            path = PathMachine.repairPath(path)

            # Change value in properties
            self._properties[key] = path

    # Rewrite property file
    def rewrite(self):
        """_summary_
        """
        # Log
        display("Rewriting property file: " + str(self.path), "info")
        # List of property lines
        lines = [key + " = " + str(value) + "\n" for key, value in self._properties.items()]
        # Open the file
        with open(self.path, "w", encoding="ISO-8859-1") as f:
            # Write properties
            f.writelines(lines)

file_type_table = {
    ".properties": PropertyFile
}

# Function that generates all the files recursively
def generateFiles():
    """_summary_
    """
    # Loop through all the files recursively from the root path
    for path in PathMachine.getOriginalTree():
        # If the path is a file
        if PathMachine.transformPathToSystemPath(path).is_file():
            # Get the extension
            extension = path.suffix
            # If the extension is in the file type table
            if extension in file_type_table.keys():
                # Create the file object
                file_type_table[extension](path)
