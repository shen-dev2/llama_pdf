import json
import csv
from typing import List, Dict, Any

class OutputWriter:
    def __init__(self, output_path: str, fmt: str, logger):
        self.output_path = output_path
        self.fmt = fmt
        self.logger = logger

    def write(self, metadata: List[Dict[str, Any]]):
        if self.fmt == "json":
            with open(self.output_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
        elif self.fmt == "csv":
            if metadata:
                keys = metadata[0].keys()
                with open(self.output_path, "w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=keys)
                    writer.writeheader()
                    writer.writerows(metadata)
        self.logger.info(f"Output written to {self.output_path}")