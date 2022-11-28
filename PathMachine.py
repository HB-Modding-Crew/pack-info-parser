from pathlib import Path
import re
import globvar
from typing import List
from mylog import display
from broken_path import repair_path
import os

# Non instantiable class to handle all the path related stuff
class PathMachine:

    ### Privates properties ###

    # Root path
    _root_path: Path = None

    # Original tree
    _original_tree: List[Path]

    # Modified tree
    _modified_tree: List[Path]

    # Dictionary of replaceable pathroot
    replaceable_pathroot = {
        "~/": "/assets/minecraft/optifine/",
    }

    ### Init ###

    # Init path machine
    @classmethod
    def init(cls, root_path: Path):
        """Init the path machine

        Args:
            root_path (Path): The root path
        """

        # Set the root path
        cls._root_path = root_path

        # Generate original tree
        cls._original_tree = cls.generateTree()

        # Init modified tree
        cls._modified_tree = cls._original_tree.copy()

    # Update modified tree
    @classmethod
    def update(cls, original_path: Path, modified_path: Path):
        """Update the modified tree

        Args:
            original_path (Path): The original path
            modified_path (Path): The modified path
        """

        # Get the index of the original path
        index = cls._original_tree.index(original_path)

        # Update the modified tree
        cls._modified_tree[index] = modified_path

    # Generate the tree
    @classmethod
    def generateTree(cls):
        """Generate the tree and return it
        """
        return [Path(str(path).replace('\\', "/").replace(str(cls._root_path), "")) for path in cls._root_path.rglob("*")]
    
    ### All setters ###

    # Set the root path
    @classmethod
    def setRootpath(cls):
        # Init the root path
        cls._root_path = globvar.root_path

    ### All getters ###

    # Get the root path
    @classmethod
    def getRootPath(cls) -> Path:
        # Return the root path
        return cls._root_path

    # Get all original tree
    @classmethod
    def getOriginalTree(cls) -> List[Path]:
        # Return the original tree
        return cls._original_tree

    # Get all modified tree
    @classmethod
    def getModifiedTree(cls) -> List[Path]:
        # Return the modified tree
        return cls._modified_tree

    ### Paths actions ###

    # Transform PathMachine absolute path to System absolute path
    @classmethod
    def transformPathToSystemPath(cls, path: Path) -> Path:
        """Transform Path absolute path to System absolute path

        Args:
            path (Path): The path to transform

        Returns:
            Path: The transformed path
        """

        # Should be an absolute path
        if not path.is_absolute():
            raise ValueError("The path must be absolute")

        # Build the path
        newPath = Path(str(cls._root_path).rstrip("/") + str(path))

        # Return the path
        return newPath

    # Transform path to PathMachine absolute path
    @classmethod
    def transformPathToPathMachinePath(cls, path: Path) -> Path:
        """Transform path to PathMachine absolute path

        Args:
            path (Path): The path to transform

        Returns:
            Path: The transformed path
        """

        # Should be an absolute path
        if not path.is_absolute():
            raise ValueError("The path must be absolute")

        # Build the path
        newPath = Path("/" + str(path).replace('\\', "/").replace(str(cls._root_path), ""))

        # Return the path
        return newPath

    # Validate absolute path
    @classmethod
    def validateAbsolutePath(cls, path: Path, expected_extensions: List[str] = []) -> bool:
        """Validate absolute path

        Args:
            path (Path): The path to validate

        Returns:
            bool: True if the path is valid, False otherwise
        """

        # Should be an absolute path
        if not path.is_absolute():
            raise ValueError("The path must be absolute")

        # Validate the path from original list and return it
        if path in cls._original_tree:
            return path
        # Else if no suffix, and expected extensions is not empty
        elif path.suffix == "" and expected_extensions != []:
            # For each expected extension
            for extension in expected_extensions:
                # If the path exists
                if (path.with_suffix(extension) in cls._original_tree):
                    # Return the path with the extension
                    return path.with_suffix(extension)
        # Else return none
        else:
            return None

    # Find absolute path from directory and relative path
    @classmethod
    def pathFromDirectoryRelative(cls, directory: Path, relativePath: Path, expected_extensions: List[str] = []) -> Path:
        """Find absolute path from directory and relative path

        Args:
            directory (Path): The directory
            relativePath (Path): The relative path

        Returns:
            Path: The absolute path
        """

        # Directory should be an absolute path
        if not directory.is_absolute():
            raise ValueError("The directory must be absolute")

        # Directory should be a directory
        if not cls.transformPathToSystemPath(directory).is_dir():
            raise ValueError("The directory must be a directory")

        # Relative path should be a relative path
        if relativePath.is_absolute():
            raise ValueError("The relative path must be relative")

        # Build the path
        newPath = (directory / relativePath).resolve()

        # Validate the path
        return cls.validateAbsolutePath(newPath, expected_extensions)

    # Ambiguous path resolver (for unresolvable paths)
    @classmethod
    def ambiguousPathResolver(cls, path: Path, expect_extensions: List[str]) -> Path:
        """Ambiguous path resolver (for unresolvable paths)

        Args:
            path (Path): The path to resolve

        Returns:
            Path: The resolved path
        """

        # Raise error if path have suffix and expect_extensions
        if path.suffix and expect_extensions:
            raise ValueError("The path have suffix and expect an extension")

        # Path part to search
        pathPart = str(path)

        # Get list of all the paths that contains the path part in original tree
        paths = [p for p in cls._original_tree if pathPart in str(p)]

        # If no paths found
        if len(paths) == 0:
            return None

        # Remove all the paths that are not the final target
        # Path is not the final target if it's stem is not equal to the path stem
        paths = [p for p in paths if p.stem in path.stem]

        # If no paths found
        if len(paths) == 0:
            return None

        # If an extension is expected
        if expect_extensions:
            # Filter the paths to keep only the ones with the expected extension
            paths = [p for p in paths if p.suffix in expect_extensions]

        # If no paths found
        if len(paths) == 0:
            return None

        # Verify if all the paths have the same parent
        if not all([p.parent == paths[0].parent for p in paths]):
            display("The path is ambiguous: " + str(path) + "\nMaybe it's not a path ? In that case, you can ignore this warning.\nElse, try to make it more precise so it can be identified.", "warning")
            return None

        # If more than one path found
        if len(paths) > 1 and not expect_extensions:
            display("Multiples corresponding files found: " + str(path) + "\n No file extension expected, keep trouble path.", "debug")

        # Return the first path
        return paths[0]

    # Resolve path from path and current file path
    @classmethod
    def resolvePath(cls, path: Path, currentPath: Path, expected_extensions: List[str] = []) -> Path:
        """Resolve path from path and current file path

        Args:
            path (Path): The path to resolve
            currentPath (Path): The current file path

        Returns:
            Path: The resolved path
        """

        # Log
        display("Resolving path: " + str(path) + " from path: " + str(currentPath), "debug")

        # If path already have extension empty expected_extensions
        if path.suffix:
            expected_extensions = []

        # Replace path root if needed
        for root in cls.replaceable_pathroot:
            if str(path).startswith(root):
                path = Path(str(path).replace(root, cls.replaceable_pathroot[root]))
                display("Path root replaced: " + str(path), "info")

        # Current path should be an absolute path
        if not currentPath.is_absolute():
            raise ValueError("The current path must be absolute")

        # Set context
        # If current path is a file, set the parent as context
        # Else, set the current path as context
        context = currentPath.parent if cls.transformPathToSystemPath(currentPath).is_file() else currentPath

        # If path is absolute, try to validate it
        # Path is absolute if it start with a slash
        if str(path).startswith("/"):
            # Make the path as simple as possible
            path = path.resolve()
            # Validate the path
            resolved = cls.validateAbsolutePath(path, expected_extensions)
            # If path is valid, return it
            if resolved:
                return resolved
            # Else, warn and return None
            else:
                display("The absolute path is not valid: " + str(path), "debug")
                return None

        # If path is relative, try to resolve it
        else:
            # Resolve the path
            resolved = cls.pathFromDirectoryRelative(context, path, expected_extensions)
            # If the path is resolved, return it
            if resolved:
                return resolved
            # Else, try to resolve the ambiguous path
            else:
                # If the path already have an extension, empty expected_extensions
                if path.suffix:
                    expected_extensions = []
                # Resolve the ambiguous path
                resolved = cls.ambiguousPathResolver(path, expected_extensions)
                # If the path is resolved, return it
                if resolved:
                    return resolved
                # Else, return None
                else:
                    display("The path is not resolvable: " + str(path), "debug")
                    return None

    # Get relative path between departure path and arrival path
    @classmethod
    def getRelativePath(cls, departurePath: Path, arrivalPath: Path, max_path_parts: int = 4, max_back_step: int = 2, max_forward_step: int = 3) -> Path:
        """Get relative path between departure path and arrival path

        Args:
            departurePath (Path): The departure path
            arrivalPath (Path): The arrival path

        Returns:
            Path: The relative path
        """

        # Validate the paths
        if not cls.validateAbsolutePath(departurePath):
            raise ValueError("The departure path is not valid")
        if not cls.validateAbsolutePath(arrivalPath):
            raise ValueError("The arrival path is not valid")

        # If departure path is a file, set the parent as departure path
        if cls.transformPathToSystemPath(departurePath).is_file():
            departurePath = departurePath.parent

        # Get the relative path
        relativePath = Path(os.path.relpath(str(arrivalPath), str(departurePath)))

        # Create test path from relative path by removing "./" at the beginning
        testPath = Path(str(relativePath).replace("./", "", 1))

        # If the relative path is too long
        if len(testPath.parts) > max_path_parts:
            return None
        
        # If to many back steps
        if len([p for p in testPath.parts if p == ".."]) > max_back_step:
            return None
        
        # If to many forward steps
        if len([p for p in testPath.parts if p != ".."]) > max_forward_step:
            return None

        # Return the relative path
        return relativePath

    # Repair path
    @classmethod
    def repairPath(cls, path: Path) -> Path:
        # Return repaired path
        return repair_path(path)