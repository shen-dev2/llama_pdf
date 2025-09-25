# Integration layer to bridge Flask app with backend logic

import sys
import os
BACKEND_DIR = os.path.join(os.path.dirname(__file__), 'backend')
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# Dynamically import backend modules
import importlib.util

def import_backend_module(module_name):
    backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
    module_path = os.path.join(backend_dir, f'{module_name}.py')
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

metadata_store = import_backend_module('metadata_store')
neo4j_handler = import_backend_module('neo4j_handler')
file_processor = import_backend_module('file_processor')

def get_all_metadata():
    return metadata_store.get_all_metadata()

def run_neo4j_query(query):
    handler = neo4j_handler.Neo4jHandler()
    return handler.run_query(query)

def process_file(filepath):
    return file_processor.process_file(filepath)
