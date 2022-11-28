import globvar
from FileTypes import generateFiles, File
from argparse import ArgumentParser
from zipfile import ZipFile
import logging
import os
import mylog
from PathMachine import PathMachine
from broken_path import repair_path
import shutil
import cProfile
from concurrent.futures import ProcessPoolExecutor
from config.config import OUTPUT_PATH
from pathlib import Path

# Unzip the resource pack
def unzip():
    # Get the name of the resource pack
    name = args.path.split("/")[-1].replace(".zip", "/")
    # Exatract the resource pack
    print("Extracting resource pack...")
    logging.info("Extracting resource pack...")
    if os.path.exists(f"./extracts/{name}"):
        logging.info("Removing old extract...")
        os.system(f"rm -r ./extracts/{name}")
    with ZipFile(args.path, 'r') as zip:
        # list of all files to unzip
        files = zip.namelist()
    # determine chunksize
    n_workers = 8
    chunksize = round(len(files) / n_workers)
    with ProcessPoolExecutor(n_workers) as exe:
        # split the copy operations into chunks
        for i in range(0, len(files), chunksize):
            # select a chunk of filenames
            filenames = files[i:(i + chunksize)]
            # submit the batch copy task
            _ = exe.submit(unzip_files, args.path, filenames, f"./extracts/{name}")
    # Return the path to the extracted resource pack
    print("Extracted resource pack to ./extracts/" + name)
    logging.info("Resource pack extracted at ./extracts/" + name)
    return f"./extracts/{name}"

# unzip files from an archive
def unzip_files(zip_filename, filenames, path):
    # open the zip file
    with ZipFile(zip_filename, 'r') as handle:
        # unzip multiple files
        for filename in filenames:
            # unzip the file
            handle.extract(filename, path)
            # report progress
            print(f'.unzipped {filename}')

# Zip to output directory
def zip():
    # Get the name of the resource pack
    name = args.path.split("/")[-1]
    # Zip the resource pack
    print("Zipping resource pack...")
    logging.info("Zipping resource pack...")
    with ZipFile(str(Path(OUTPUT_PATH).resolve()) + f"/{name}", 'w') as zip:
        for file in PathMachine.getModifiedTree():
            zip.write(str(PathMachine.transformPathToSystemPath(file)), str(file))
    # Return the path to the extracted resource pack
    print("Zipped resource pack to ./output/" + name)
    logging.info("Resource pack zipped at ./output/" + name)

# Actions
# Analyze the resource pack
def analyse():
    # Analyse references
    mylog.display("Analyzing references...")
    # For each file
    for file in File.file_dict.values():
        # Analyze the file
        file.handleReferences()
    # Finding all broken paths
    mylog.display("Finding broken paths:")
    for file in PathMachine.getOriginalTree():
        if not file.name == repair_path(file.name).name:
            mylog.display(f"Found broken path in '{str(file)}' Correct path: '{str(repair_path(file))}'")

# Repair the resource pack
def repair():
    # Analyse references
    mylog.display("Analyzing and correct references...")
    # For each file
    for file in File.file_dict.values():
        # Analyze the file
        file.handleReferences()
        file.rewrite()
    # Sort the paths
    files = sorted(PathMachine.getOriginalTree(), key=lambda x: len(str(x)), reverse=True)
    # Finding all broken paths
    mylog.display("Finding broken paths:")
    for file in files:
        if not file.name == repair_path(file.name).name:
            mylog.display(f"Found broken path in '{str(file)}' Correct path: '{str(repair_path(file))}'")
            # Move
            shutil.move(str(PathMachine.transformPathToSystemPath(file)), str(PathMachine.transformPathToSystemPath(repair_path(file))))
            # Update the path
        PathMachine.update(file, repair_path(file))
    # Zip resource pack
    zip()


# Format the resource pack
def format():
    pass

# Actions that can be performed
actions = {
    "repair": repair,
    "format": None,
    "analyse": analyse
}

# Parse the arguments
# Init the argument parser
parser = ArgumentParser(prog="Resource pack handler", description="Handle different actions on resource packs")
# Add the arguments
# Action
parser.add_argument('action', help='The action to perform on your resource pack', choices=['repair', 'analyse'], metavar='ACTION')
# Path
parser.add_argument("-p", "--path", dest="path", help="Path of your resource pack", metavar="PATH", required=True)
# Enable profiling
parser.add_argument("-pr", "--profile", dest="profile", help="Enable profiling", action="store_true")
args = parser.parse_args()

def run():
    print()
    # Log start
    mylog.display("Starting resource pack handler...")
    mylog.display("Action: " + args.action)
    # Convert windows path to linux path
    args.path = args.path.replace("\\", "/")
    # Set the root path
    path=unzip()
    globvar.setRootPath(path)
    mylog.display("Analyzing resource pack...")
    PathMachine.init(globvar.root_path)
    generateFiles()
    # Execute the action
    mylog.display(f"Executing action {args.action}")
    action = actions[args.action]
    if action != None:
        action()

if __name__ == "__main__":
    if args.profile:
        cProfile.run("run()", sort="cumtime")
    else:
        run()
