from pathlib import Path

# Root global variable
root_path = None

# Root setter
def setRootPath(path):
    """Set the root path

    Args:
        path (Path): The root path
    """

    # Set the root path
    global root_path
    root_path = Path(str(Path(path).resolve())+"/")