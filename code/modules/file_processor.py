import asyncio
from pathlib import Path
from typing import Any
from .handlers.pdf_handler import extract_pdf_metadata
from .handlers.txt_handler import extract_txt_metadata

SUPPORTED_TYPES = {
    ".pdf": extract_pdf_metadata,
    ".txt": extract_txt_metadata,
}

class FileProcessor:
    def __init__(self, logger, metadata_store):
        self.logger = logger
        self.metadata_store = metadata_store
        self.queue = asyncio.Queue()

    async def enqueue_file(self, file_path: Path):
        await self.queue.put(file_path)

    async def run_workers(self, concurrency: int = 8):
        tasks = [asyncio.create_task(self.worker()) for _ in range(concurrency)]
        await self.queue.join()
        for t in tasks:
            t.cancel()

    async def worker(self):
        while True:
            file_path = await self.queue.get()
            try:
                ext = file_path.suffix.lower()
                if ext in SUPPORTED_TYPES:
                    extractor = SUPPORTED_TYPES[ext]
                    metadata = await extractor(file_path)
                    self.metadata_store.add_file_metadata(file_path, metadata)
                    self.logger.info(f"Processed file: {file_path}")
                else:
                    self.logger.warning(f"Unsupported file type: {file_path}")
            except Exception as e:
                self.logger.error(f"Error processing {file_path}: {e}")
            finally:
                self.queue.task_done()