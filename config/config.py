from dataclasses import dataclass
from dacite import from_dict
import json
import os
from typing import List

@dataclass
class PropertyFileConfig:
    """The configuration for the property file"""
    # Properties expected extensions
    properties_expected_extensions: dict[str, List[str]]
    # Excluded paths (regex or not)
    excluded_pack_paths: list[str]
    # Non path properties
    non_path_properties: dict[str, bool]
    

@dataclass
class Config:
    output_path: str
    property_file_config: PropertyFileConfig

# If config file exists, load it
if os.path.exists("config/config.json"):
    with open("config/config.json") as f:
        config = from_dict(Config, json.load(f))
else:
    # Load default config
    with open("config/default/config.json") as f:
        config = from_dict(Config, json.load(f))

PROPERTY_CONFIG = config.property_file_config
OUTPUT_PATH = config.output_path