from typing import Dict, Any
from pathlib import Path

class MetadataStore:
    def __init__(self):
        self._metadata = []
        self.file_count = 0
        self.folder_count = 0

    def add_file_metadata(self, file_path: Path, metadata: Dict[str, Any]):
        self._metadata.append(metadata)
        self.file_count += 1

    def get_all_metadata(self):
        return self._metadata