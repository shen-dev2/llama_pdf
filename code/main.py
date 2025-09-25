# main.py

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Any

from modules.logger import setup_logger
from modules.traversal import AsyncDirectoryWalker
from modules.file_processor import FileProcessor
from modules.metadata_store import MetadataStore
from modules.output_writer import OutputWriter
# from modules.graph_mapper import KnowledgeGraphMapper  # For future use

# -------------------- Step 1: Initialization --------------------

def parse_args():
    parser = argparse.ArgumentParser(description="Async Folder Metadata Extractor")
    parser.add_argument("root_folder", type=str, help="Root folder to scan")
    parser.add_argument("--log_file", type=str, default="scan.log", help="Log file path")
    parser.add_argument("--output", type=str, default="metadata.json", help="Metadata output file")
    parser.add_argument("--format", type=str, choices=["json", "csv"], default="json", help="Output format")
    parser.add_argument("--concurrency", type=int, default=8, help="Number of concurrent workers")
    return parser.parse_args()

async def main():
    args = parse_args()
    logger = setup_logger(args.log_file)
    logger.info("Initialization complete.")

    metadata_store = MetadataStore()
    file_processor = FileProcessor(logger, metadata_store)
    walker = AsyncDirectoryWalker(
        root_folder=args.root_folder,
        file_callback=file_processor.enqueue_file,
        logger=logger
    )

    # -------------------- Step 2: Directory Traversal (Async) --------------------
    logger.info("Starting async directory traversal.")
    await walker.walk()

    # -------------------- Step 3: File Processing (Async Workers) --------------------
    logger.info("Starting async file processing.")
    await file_processor.run_workers(concurrency=args.concurrency)

    # -------------------- Step 4: Metadata Aggregation --------------------
    logger.info("Aggregating metadata.")
    metadata = metadata_store.get_all_metadata()

    # -------------------- Step 5: Logging --------------------
    logger.info(f"Processed {metadata_store.file_count} files and {metadata_store.folder_count} folders.")

    # -------------------- Step 6: Output Generation --------------------
    writer = OutputWriter(args.output, args.format, logger)
    writer.write(metadata)
    logger.info(f"Metadata written to {args.output} in {args.format} format.")

    # -------------------- Step 7: Knowledge Graph Mapping (Future) --------------------
    # graph_mapper = KnowledgeGraphMapper()
    # graph_mapper.ingest(metadata)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)