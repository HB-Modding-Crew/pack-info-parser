import os
import shutil
import logging
from pathlib import Path

# List of all valid characters for a path
# Contain all the characters that are allowed in a path
# Contain all the basic numbers and lowercase letters
# Contain / _ - .
valid_chars = "abcdefghijklmnopqrstuvwxyz0123456789_.-/\\"

# Replace table
replace_table = {
    " ": "_",
    "é": "e",
    "è": "e",
    "ê": "e",
    "ë": "e",
    "à": "a",
    "â": "a",
    "ä": "a",
    "ù": "u",
    "û": "u",
    "ü": "u",
    "î": "i",
    "ï": "i",
    "ô": "o",
    "ö": "o",
    "É": "E",
    "È": "E",
    "Ê": "E",
    "Ë": "E",
    "À": "A",
    "Â": "A",
    "Ä": "A",
    "Ù": "U",
    "Û": "U",
    "Ü": "U",
    "Î": "I",
    "Ï": "I",
    "Ô": "O",
    "Ö": "O",
    "ç": "c",
    "Ç": "C",
    "œ": "oe",
    "Œ": "OE",
    "æ": "ae",
    "Æ": "AE",
    "[": "_",
    "]": "_",
    "(": "_",
    ")": "_",
    "{": "_",
    "}": "_",
    "’": "_",
    "'": "_",
}

# Repair a broken path
def repair_path(path: Path) -> Path:
    # Replace replace_table characters
    for char in replace_table.keys():
        path = Path(str(path).replace(char, replace_table[char]))

    # Put all in lowercase
    path = Path(str(path).lower())

    # Remove all the invalid characters
    for char in str(path):
        if char not in valid_chars:
            path = Path(str(path).replace(char, ""))
    
    # Return the repaired path
    return path